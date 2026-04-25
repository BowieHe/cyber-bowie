"""Google Calendar sync logic: pull events and push to Zectrix as todos."""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from googleapiclient.discovery import build

from cyber_persona.plugins.zectrix.api.client import ZectrixClient
from cyber_persona.plugins.zectrix.calendar_sync.auth import get_valid_credentials
from cyber_persona.plugins.zectrix.config import (
    SYNC_DAYS_AHEAD,
    SYNC_STATE_PATH,
    ZECTRIX_DEVICE_ID,
    ensure_data_dirs,
)
from cyber_persona.plugins.zectrix.models import CalendarEvent, SyncState, Todo

logger = logging.getLogger(__name__)


def load_sync_state() -> SyncState:
    """Load sync state from disk."""
    if SYNC_STATE_PATH.exists():
        raw = json.loads(SYNC_STATE_PATH.read_text(encoding="utf-8"))
        return SyncState.model_validate(raw)
    return SyncState()


def save_sync_state(state: SyncState) -> None:
    """Save sync state to disk."""
    ensure_data_dirs()
    SYNC_STATE_PATH.write_text(
        state.model_dump_json(indent=2),
        encoding="utf-8",
    )


def _parse_event(event: dict) -> CalendarEvent | None:
    """Normalize a Google Calendar event."""
    event_id = event.get("id", "")
    status = event.get("status", "confirmed")
    summary = event.get("summary", "(无标题)")
    description = event.get("description", "") or ""

    # Skip cancelled events
    if status == "cancelled":
        return None

    start = event.get("start", {})
    end = event.get("end", {})

    is_all_day = "date" in start

    if is_all_day:
        start_time = None
    else:
        raw = start.get("dateTime")
        if raw:
            # Google returns RFC3339, e.g. 2026-03-20T09:00:00+08:00
            start_time = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        else:
            start_time = None

    return CalendarEvent(
        event_id=event_id,
        title=summary,
        description=description,
        start_time=start_time,
        is_all_day=is_all_day,
        status=status,
    )


def _event_to_todo(event: CalendarEvent, device_id: str) -> Todo:
    """Convert a calendar event to a Zectrix todo."""
    due_date = ""
    due_time = ""

    if event.start_time:
        due_date = event.start_time.strftime("%Y-%m-%d")
        due_time = event.start_time.strftime("%H:%M")
    elif event.is_all_day:
        # All-day events: due date is the event date, no time
        pass  # leave empty since we don't have a specific date here

    # Truncate description to 100 chars
    description = event.description[:100] if event.description else ""

    return Todo(
        title=event.title,
        description=description,
        dueDate=due_date,
        dueTime=due_time,
        repeatType="none",
        status=0,
        priority=1,
        deviceId=device_id,
    )


class CalendarSync:
    """Syncs Google Calendar events to Zectrix todos."""

    def __init__(self, device_id: str | None = None) -> None:
        self.device_id = device_id or ZECTRIX_DEVICE_ID
        self.state = load_sync_state()

    async def run(self) -> int:
        """Pull future events from Google Calendar and push new ones to Zectrix.

        Returns the number of new todos created.
        """
        creds = get_valid_credentials()
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=SYNC_DAYS_AHEAD)).isoformat()

        logger.info(
            "Fetching calendar events from %s to %s",
            time_min[:10],
            time_max[:10],
        )

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        raw_events = events_result.get("items", [])
        logger.info("Fetched %d calendar events", len(raw_events))

        # Parse and filter
        calendar_events: list[CalendarEvent] = []
        for raw in raw_events:
            parsed = _parse_event(raw)
            if parsed:
                calendar_events.append(parsed)

        # Determine target device
        async with ZectrixClient() as client:
            target_device = self.device_id or await client.get_first_device_id()

            created_count = 0
            for event in calendar_events:
                if self.state.is_synced(event.event_id):
                    logger.debug("Event %s already synced, skipping", event.event_id)
                    continue

                todo = _event_to_todo(event, target_device)
                try:
                    created = await client.create_todo(todo)
                    logger.info(
                        "Created todo #%d for event '%s'",
                        created.id,
                        event.title,
                    )
                    self.state.add_event(event.event_id)
                    created_count += 1
                except Exception:
                    logger.exception("Failed to create todo for event '%s'", event.title)
                    # Don't mark as synced so we retry next time

            self.state.last_sync_at = datetime.now(timezone.utc)
            save_sync_state(self.state)
            logger.info("Sync complete. Created %d new todos.", created_count)
            return created_count
