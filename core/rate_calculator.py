from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select

from database.schemas import ExchangeRateSchema


async def get_unit_rate(db, currency: str) -> Decimal:
    if currency == "BYN":
        return Decimal(1)

    result = await db.execute(select(ExchangeRateSchema)
             .filter(ExchangeRateSchema.currency_code == currency)
             .order_by(ExchangeRateSchema.rate_date.desc())
             .limit(1))
    rate = result.scalar_one_or_none()

    if rate is None:
        raise ValueError(f"No exchange rate found for {currency}")

    return rate.official_rate / rate.scale


def calculate_exchange(amount: Decimal, unit_rate_from: Decimal, unit_rate_to: Decimal):
    rate = unit_rate_from / unit_rate_to
    amount_to = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return amount_to, rate
