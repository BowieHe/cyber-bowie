"""APScheduler jobs for the Zectrix plugin.

- Periodic sync: every 12 hours, pull Google Calendar events and push to Zectrix.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from cyber_persona.plugins.zectrix.calendar_sync.sync import CalendarSync
from cyber_persona.plugins.zectrix.config import ensure_data_dirs

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _sync_job() -> None:
    """The actual sync job executed by the scheduler."""
    logger.info("[Zectrix] Starting scheduled calendar sync...")
    try:
        sync = CalendarSync()
        count = await sync.run()
        logger.info("[Zectrix] Scheduled sync finished. Created %d todos.", count)
    except Exception:
        logger.exception("[Zectrix] Scheduled sync failed")


def start_scheduler(
    *,
    hours: int = 12,
    minutes: int = 0,
    run_immediately: bool = True,
) -> AsyncIOScheduler:
    """Start the background scheduler.

    Args:
        hours: Interval between syncs.
        minutes: Additional minutes between syncs.
        run_immediately: Whether to run a sync immediately on start.
    """
    global _scheduler

    ensure_data_dirs()

    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler already running")
        return _scheduler

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _sync_job,
        trigger=IntervalTrigger(hours=hours, minutes=minutes),
        id="zectrix_calendar_sync",
        name="Zectrix Calendar Sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "[Zectrix] Scheduler started. Sync interval: %dh %dm",
        hours,
        minutes,
    )

    if run_immediately:
        # Schedule an immediate run
        asyncio.create_task(_sync_job())

    return _scheduler


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown()
        logger.info("[Zectrix] Scheduler stopped")
    _scheduler = None
