import logging
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, union_all, literal_column

from core.rate_calculator import calculate_exchange, get_unit_rate
from database.postgres import AsyncSessionLocal
from database.schemas import DealSchema, DealStatus, ExchangeRateSchema

router = APIRouter()


class DealRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=16, decimal_places=2, examples=["100.00"])
    currency_from: str = Field(min_length=3, max_length=3, examples=["USD"])
    currency_to: str = Field(min_length=3, max_length=3, examples=["BYN"])


class DealResponse(BaseModel):
    deal_id: uuid.UUID
    amount_from: Decimal
    currency_from: str
    amount_to: Decimal
    currency_to: str
    rate: Decimal


class ResolveRequest(BaseModel):
    result: Literal["confirm", "reject"] = Field(examples=["confirm"])


class ResolveResponse(BaseModel):
    deal_id: uuid.UUID
    status: DealStatus


class RateResponse(BaseModel):
    rate_date: date
    currency_code: str
    scale: int
    official_rate: Decimal


class ReportResponse(BaseModel):
    currency: str
    received: Decimal
    paid_out: Decimal
    deals_count: int


@router.get("/v1/exchange/rates", summary="Get Today's Exchange Rates",
            description="Official NBRB rates for today.",
            response_model=list[RateResponse])
async def get_rates():
    today = datetime.now(ZoneInfo("Europe/Minsk")).date()

    async with AsyncSessionLocal() as db:
        latest_date = (select(func.max(ExchangeRateSchema.rate_date))
                       .filter(ExchangeRateSchema.rate_date <= today)
                       .scalar_subquery())
        result = await db.execute(select(ExchangeRateSchema)
                                  .filter(ExchangeRateSchema.rate_date == latest_date)
                                  .order_by(ExchangeRateSchema.currency_code))
        rates = result.scalars().all()

        base_rate = RateResponse(rate_date=today, currency_code="BYN", scale=1, official_rate=Decimal(1))

        return [base_rate] + [RateResponse(
            rate_date=rate.rate_date,
            currency_code=rate.currency_code,
            scale=rate.scale,
            official_rate=rate.official_rate
        ) for rate in rates]


@router.post("/v1/exchange/deals", summary="Create Exchange Deal",
             description="Calculate an exchange and create a deal with status PENDING. "
                         "Then the deal has to be confirmed or rejected.",
             response_model=DealResponse,
             responses={
                 400: {"description": "Source and target currencies are the same"},
                 404: {"description": "Exchange rate for the currency not found"}
             })
async def create_deal(request: DealRequest):
    currency_from = request.currency_from.upper()
    currency_to = request.currency_to.upper()

    if currency_from == currency_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Source and target currencies must be different")

    async with AsyncSessionLocal() as db:
        try:
            unit_rate_from = await get_unit_rate(db, currency_from)
            unit_rate_to = await get_unit_rate(db, currency_to)
        except ValueError as ex:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))

        amount_to, rate = calculate_exchange(request.amount, unit_rate_from, unit_rate_to)

        rate = rate.quantize(Decimal("0.00000001"))
        deal = DealSchema(
            amount_from=request.amount,
            currency_from=currency_from,
            amount_to=amount_to,
            currency_to=currency_to,
            rate=rate,
        )
        db.add(deal)
        await db.commit()

        logging.info(f"Deal {deal.id} created: {deal.amount_from} {deal.currency_from} -> "
                     f"{deal.amount_to} {deal.currency_to}, rate {deal.rate}")

        return DealResponse(
            deal_id=deal.id,
            amount_from=deal.amount_from,
            currency_from=deal.currency_from,
            amount_to=deal.amount_to,
            currency_to=deal.currency_to,
            rate=deal.rate,
        )


@router.post("/v1/exchange/{deal_id}/resolve", summary="Confirm or Reject Exchange",
             description="Confirm or reject a pending deal.",
             response_model=ResolveResponse,
             responses={
                 404: {"description": "Deal not found"},
                 409: {"description": "Deal is already confirmed or rejected"}
             })
async def resolve_deal(deal_id: uuid.UUID, request: ResolveRequest):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DealSchema).filter(DealSchema.id == deal_id).with_for_update())
        deal = result.scalar_one_or_none()

        if deal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

        if deal.status != DealStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Deal is already {deal.status.value.lower()}")

        deal.status = DealStatus.CONFIRMED if request.result == "confirm" else DealStatus.REJECTED
        await db.commit()

        logging.info(f"Deal {deal.id} {deal.status.value.lower()}")

        return ResolveResponse(deal_id=deal.id, status=deal.status)


@router.get("/v1/exchange/pending", summary="Get Pending Deals",
            description="Deals that are in pending status.",
            response_model=list[DealResponse],
            )
async def get_pending_deals():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DealSchema).filter(DealSchema.status == DealStatus.PENDING).order_by(
            DealSchema.created_at))
        pending_deals = result.scalars().all()

        return [DealResponse(
            deal_id=deal.id,
            amount_from=deal.amount_from,
            currency_from=deal.currency_from,
            amount_to=deal.amount_to,
            currency_to=deal.currency_to,
            rate=deal.rate
        ) for deal in pending_deals]


@router.get("/v1/exchange/report", summary="Get Deals Report",
            description="For each currency: how much was received, how much was paid out "
                        "and how many deals. Only confirmed deals are counted.",
            response_model=list[ReportResponse],
            responses={
                400: {"description": "date_from is later than date_to"}
            })
async def get_report(date_from: date = Query(description="Format: YYYY-MM-DD"),
                     date_to: date = Query(description="Format: YYYY-MM-DD"), currency: str | None = None):
    if date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="date_from must not be later than date_to")

    minsk = ZoneInfo("Europe/Minsk")
    period_start = datetime.combine(date_from, time.min, tzinfo=minsk)
    period_end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=minsk)

    period_filter = (DealSchema.status == DealStatus.CONFIRMED,
                     DealSchema.updated_at >= period_start,
                     DealSchema.updated_at < period_end)

    currency_amount_from = select(DealSchema.currency_from.label("currency"),
                                  DealSchema.amount_from.label("received"),
                                  literal_column("0").label("paid_out")).filter(*period_filter)

    currency_amount_to = select(DealSchema.currency_to.label("currency"),
                                literal_column("0").label("received"),
                                DealSchema.amount_to.label("paid_out")).filter(*period_filter)

    movements = union_all(currency_amount_from, currency_amount_to).subquery()

    query = (select(movements.c.currency,
                    func.sum(movements.c.received).label("received"),
                    func.sum(movements.c.paid_out).label("paid_out"),
                    func.count().label("deals_count"))
             .group_by(movements.c.currency))

    if currency:
        query = query.filter(movements.c.currency == currency)

    async with AsyncSessionLocal() as db:
        result = await db.execute(query)
        return [ReportResponse(currency=row.currency, received=row.received,
                               paid_out=row.paid_out, deals_count=row.deals_count) for row in result.all()]
