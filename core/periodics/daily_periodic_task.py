from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.rates_updater import update_rates

scheduler = AsyncIOScheduler()


def start_daily_periodic_task():
    scheduler.add_job(
        update_rates,
        trigger=CronTrigger(hour=0, minute=0, timezone="Europe/Minsk"),
        id="daily_rates_update",
        replace_existing=True
    )
    scheduler.start()


def stop_daily_periodic_task():
    scheduler.shutdown()
