"""Google Calendar sync logic: pull events and push to Zectrix as todos.

Diff-based sync: each run computes the set of events currently in the next
30 days, compares it to the persisted state, and issues create / update /
delete calls so the Zectrix todo list mirrors the calendar.
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from googleapiclient.discovery import build

from cyber_persona.plugins.zectrix.api.client import ZectrixClient
from cyber_persona.plugins.zectrix.calendar_sync.auth import get_valid_credentials
from cyber_persona.plugins.zectrix.config import (
    SYNC_DAYS_AHEAD,
    SYNC_STATE_PATH,
    ZECTRIX_DEVICE_ID,
    ensure_data_dirs,
)
from cyber_persona.plugins.zectrix.models import (
    CalendarEvent,
    SyncedEventRecord,
    SyncState,
    Todo,
)

logger = logging.getLogger(__name__)

_MAX_PAGES = 10
_PAGE_SIZE = 250


def load_sync_state() -> SyncState:
    """Load sync state from disk, migrating legacy formats."""
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
    """Normalize a Google Calendar event. Returns None for cancelled events."""
    status = event.get("status", "confirmed")
    if status == "cancelled":
        return None

    event_id = event.get("id", "")
    summary = event.get("summary") or "(无标题)"
    description = event.get("description", "") or ""

    start = event.get("start", {})
    is_all_day = "date" in start

    start_time: datetime | None = None
    start_date: date | None = None

    if is_all_day:
        raw_date = start.get("date")
        if raw_date:
            start_date = date.fromisoformat(raw_date)
    else:
        raw = start.get("dateTime")
        if raw:
            start_time = datetime.fromisoformat(raw.replace("Z", "+00:00"))

    return CalendarEvent(
        event_id=event_id,
        title=summary,
        description=description,
        start_time=start_time,
        start_date=start_date,
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
    elif event.start_date:
        due_date = event.start_date.strftime("%Y-%m-%d")

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

    def _fetch_events(self) -> list[dict]:
        """Pull all upcoming events from Google Calendar with pagination."""
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

        raw_events: list[dict] = []
        page_token: str | None = None
        for _ in range(_MAX_PAGES):
            resp = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=_PAGE_SIZE,
                    pageToken=page_token,
                )
                .execute()
            )
            raw_events.extend(resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        else:
            logger.warning(
                "Hit page limit (%d pages × %d) — some events may be missing",
                _MAX_PAGES,
                _PAGE_SIZE,
            )

        logger.info("Fetched %d calendar events", len(raw_events))
        return raw_events

    @staticmethod
    def _has_changed(existing: SyncedEventRecord, new_todo: Todo) -> bool:
        """True if any user-visible field differs from the last synced snapshot."""
        return (
            existing.title != new_todo.title
            or existing.dueDate != new_todo.dueDate
            or existing.dueTime != new_todo.dueTime
            or existing.description != new_todo.description
        )

    async def run(self) -> dict[str, int]:
        """Sync the upcoming calendar window to Zectrix.

        Returns counts: ``{"created": N, "updated": N, "deleted": N}``.
        Failures on individual todos are logged but do not abort the run.
        """
        raw_events = self._fetch_events()

        current: dict[str, CalendarEvent] = {}
        for raw in raw_events:
            parsed = _parse_event(raw)
            if parsed:
                current[parsed.event_id] = parsed

        counts = {"created": 0, "updated": 0, "deleted": 0}

        async with ZectrixClient() as client:
            target_device = self.device_id or await client.get_first_device_id()

            for event_id, event in current.items():
                todo = _event_to_todo(event, target_device)
                existing = self.state.synced_events.get(event_id)

                if existing is None:
                    try:
                        created = await client.create_todo(todo)
                        if created.id is None:
                            logger.error(
                                "Zectrix returned no id for created todo '%s'",
                                event.title,
                            )
                            continue
                        self.state.synced_events[event_id] = SyncedEventRecord(
                            event_id=event_id,
                            todo_id=created.id,
                            synced_at=datetime.now(timezone.utc),
                            title=todo.title,
                            dueDate=todo.dueDate,
                            dueTime=todo.dueTime,
                            description=todo.description,
                        )
                        counts["created"] += 1
                        logger.info(
                            "Created todo #%d for event '%s'",
                            created.id,
                            event.title,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to create todo for event '%s'",
                            event.title,
                        )
                elif self._has_changed(existing, todo):
                    try:
                        await client.update_todo(existing.todo_id, todo)
                        existing.title = todo.title
                        existing.dueDate = todo.dueDate
                        existing.dueTime = todo.dueTime
                        existing.description = todo.description
                        existing.synced_at = datetime.now(timezone.utc)
                        counts["updated"] += 1
                        logger.info(
                            "Updated todo #%d for event '%s'",
                            existing.todo_id,
                            event.title,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to update todo for event '%s'",
                            event.title,
                        )

            gone = set(self.state.synced_events) - set(current)
            for event_id in gone:
                record = self.state.synced_events[event_id]
                try:
                    await client.delete_todo(record.todo_id)
                    del self.state.synced_events[event_id]
                    counts["deleted"] += 1
                    logger.info(
                        "Deleted todo #%d (event '%s' no longer in window)",
                        record.todo_id,
                        record.title,
                    )
                except Exception:
                    logger.exception(
                        "Failed to delete todo #%d (event '%s')",
                        record.todo_id,
                        record.title,
                    )

            self.state.last_sync_at = datetime.now(timezone.utc)
            save_sync_state(self.state)
            logger.info(
                "Sync done: +%d ~%d -%d",
                counts["created"],
                counts["updated"],
                counts["deleted"],
            )
            return counts
