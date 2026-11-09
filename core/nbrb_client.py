import logging
from datetime import date
from decimal import Decimal
from typing import Any

import httpx

from core.config import NBRB_RATES_URL

REQUEST_TIMEOUT_SECONDS = 15


async def fetch_rates() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(NBRB_RATES_URL)
        response.raise_for_status()

    raw_rates = response.json(parse_float=Decimal)

    rates = []
    for item in raw_rates:
        rates.append({
            "rate_date": date.fromisoformat(item["Date"][:10]),
            "currency_code": item["Cur_Abbreviation"],
            "scale": item["Cur_Scale"],
            "official_rate": item["Cur_OfficialRate"],
        })

    logging.info(f"Fetched {len(rates)} rates from NBRB")
    return rates
