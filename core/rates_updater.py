import logging

from sqlalchemy.dialects.postgresql import insert

from core.nbrb_client import fetch_rates
from database.postgres import AsyncSessionLocal
from database.schemas import ExchangeRateSchema


async def update_rates():
    rates = await fetch_rates()

    async with AsyncSessionLocal() as db:
        # insert all rates; rates that already exist for this date and currency are skipped
        query = insert(ExchangeRateSchema).values(rates).on_conflict_do_nothing(
            constraint="uq_exchange_rates_date_currency")
        await db.execute(query)
        await db.commit()

    logging.info(f"Rates updated: {len(rates)} currencies")
