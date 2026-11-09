import logging

import uvicorn
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from core.config import APP_PORT, LOG_LEVEL, PRODUCT_NAME
from core.periodics.daily_periodic_task import start_daily_periodic_task, stop_daily_periodic_task
from core.rates_updater import update_rates
from routers.exchange import router as exchange_router

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await update_rates()
    start_daily_periodic_task()
    logging.info("Service is started")

    yield

    stop_daily_periodic_task()
    logging.info("Service is stopped")


app = FastAPI(
    lifespan=lifespan,
    title=f"{PRODUCT_NAME} API",
    description="Currency exchange at the official National Bank of Belarus rates",
    version="1.0.0",
)

app.include_router(exchange_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
