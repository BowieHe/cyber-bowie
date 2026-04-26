"""APScheduler jobs for the Zectrix plugin.

Periodic sync: every 12 hours by default, pull Google Calendar events and
push diffs (create / update / delete) to the Zectrix device.
"""

import logging
from datetime import datetime

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
        counts = await sync.run()
        logger.info(
            "[Zectrix] Scheduled sync done: +%d ~%d -%d",
            counts["created"],
            counts["updated"],
            counts["deleted"],
        )
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
        run_immediately: Whether to fire a sync as soon as the loop runs.
            Implemented via APScheduler's ``next_run_time`` to avoid the
            ``asyncio.create_task`` race against ``loop.run_forever()``.
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
        next_run_time=datetime.now() if run_immediately else None,
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "[Zectrix] Scheduler started. Sync interval: %dh %dm (run_immediately=%s)",
        hours,
        minutes,
        run_immediately,
    )

    return _scheduler


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown()
        logger.info("[Zectrix] Scheduler stopped")
    _scheduler = None
