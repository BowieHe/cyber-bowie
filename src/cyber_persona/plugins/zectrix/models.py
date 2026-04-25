"""Pydantic models for Zectrix plugin."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


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
    """Record of a calendar event that has been synced to Zectrix."""

    event_id: str
    synced_at: datetime
    todo_id: int | None = None


class SyncState(BaseModel):
    """Persistent sync state."""

    synced_event_ids: list[str] = Field(default_factory=list)
    last_sync_at: datetime | None = None

    def add_event(self, event_id: str) -> None:
        if event_id not in self.synced_event_ids:
            self.synced_event_ids.append(event_id)

    def is_synced(self, event_id: str) -> bool:
        return event_id in self.synced_event_ids


class CalendarEvent(BaseModel):
    """Normalized calendar event from Google Calendar."""

    event_id: str
    title: str
    description: str = ""
    start_time: datetime | None = None
    is_all_day: bool = False
    status: str = "confirmed"  # confirmed, tentative, cancelled
