"""Pydantic models for Zectrix plugin."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Device(BaseModel):
    """Zectrix device info."""

    deviceId: str
    alias: str
    board: str


class Todo(BaseModel):
    """Zectrix todo item."""

    id: int | None = None
    title: str
    description: str = ""
    dueDate: str = ""  # YYYY-MM-DD
    dueTime: str = ""  # HH:MM
    repeatType: str = "none"
    status: int = 0  # 0=pending, 1=completed
    priority: int = 1
    deviceId: str = ""
    createDate: str | None = None  # YYYY-MM-DD HH:MM:SS

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(**kwargs)
        if self.id is None:
            d.pop("id", None)
        if not self.createDate:
            d.pop("createDate", None)
        return d


class DisplayPushResult(BaseModel):
    """Result of pushing content to device display."""

    totalPages: int
    pushedPages: int
    pageId: str


class SyncedEventRecord(BaseModel):
    """Snapshot of a calendar event already synced to a Zectrix todo.

    Stored in SyncState so the next sync can diff against it and decide
    whether to issue create / update / delete API calls.
    """

    event_id: str
    todo_id: int
    synced_at: datetime
    title: str
    dueDate: str = ""
    dueTime: str = ""
    description: str = ""


class SyncState(BaseModel):
    """Persistent sync state.

    Maps Google Calendar event_id -> the Zectrix todo we created for it.
    """

    synced_events: dict[str, SyncedEventRecord] = Field(default_factory=dict)
    last_sync_at: datetime | None = None
    legacy_format_detected: bool = Field(default=False, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy(cls, data: Any) -> Any:
        """Migrate the v1 format `{synced_event_ids: [...]}` to v2 empty dict.

        v1 only stored event IDs, with no todo_id mapping, so we cannot
        reconstruct a useful state. We start fresh and flag the migration so
        the CLI can warn the user that duplicates may appear on the device.
        """
        if not isinstance(data, dict):
            return data
        if "synced_event_ids" in data and "synced_events" not in data:
            return {
                "synced_events": {},
                "last_sync_at": data.get("last_sync_at"),
                "legacy_format_detected": True,
            }
        return data


class CalendarEvent(BaseModel):
    """Normalized calendar event from Google Calendar."""

    event_id: str
    title: str
    description: str = ""
    start_time: datetime | None = None  # for timed events
    start_date: date | None = None  # for all-day events
    is_all_day: bool = False
    status: str = "confirmed"  # confirmed, tentative, cancelled
