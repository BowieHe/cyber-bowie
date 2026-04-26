"""Tests for Zectrix plugin models."""

from datetime import date, datetime, timezone

from cyber_persona.plugins.zectrix.models import (
    CalendarEvent,
    SyncedEventRecord,
    SyncState,
    Todo,
)


def test_todo_model_dump_drops_none_id():
    todo = Todo(title="t", deviceId="d1")
    dumped = todo.model_dump()
    assert "id" not in dumped


def test_todo_model_dump_keeps_set_id():
    todo = Todo(id=42, title="t", deviceId="d1")
    dumped = todo.model_dump()
    assert dumped["id"] == 42


def test_todo_model_dump_drops_empty_create_date():
    todo = Todo(title="t", deviceId="d1")
    dumped = todo.model_dump()
    assert "createDate" not in dumped


def test_todo_model_dump_keeps_create_date_when_set():
    todo = Todo(title="t", deviceId="d1", createDate="2026-04-26 10:00:00")
    dumped = todo.model_dump()
    assert dumped["createDate"] == "2026-04-26 10:00:00"


def test_sync_state_legacy_migration_resets_to_empty_dict():
    legacy = {
        "synced_event_ids": ["evt-a", "evt-b"],
        "last_sync_at": "2026-04-25T12:00:00+00:00",
    }
    state = SyncState.model_validate(legacy)
    assert state.synced_events == {}
    assert state.last_sync_at == datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc)
    assert state.legacy_format_detected is True


def test_sync_state_new_format_preserved():
    record = SyncedEventRecord(
        event_id="evt-1",
        todo_id=10,
        synced_at=datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc),
        title="x",
    )
    payload = {
        "synced_events": {"evt-1": record.model_dump()},
        "last_sync_at": "2026-04-25T12:00:00+00:00",
    }
    state = SyncState.model_validate(payload)
    assert state.legacy_format_detected is False
    assert "evt-1" in state.synced_events
    assert state.synced_events["evt-1"].todo_id == 10


def test_sync_state_default_empty():
    state = SyncState()
    assert state.synced_events == {}
    assert state.last_sync_at is None
    assert state.legacy_format_detected is False


def test_sync_state_serialization_excludes_legacy_flag():
    state = SyncState()
    state.legacy_format_detected = True
    dumped = state.model_dump()
    assert "legacy_format_detected" not in dumped


def test_calendar_event_timed():
    event = CalendarEvent(
        event_id="evt-1",
        title="Meeting",
        start_time=datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc),
    )
    assert event.start_time is not None
    assert event.start_date is None
    assert event.is_all_day is False


def test_calendar_event_all_day():
    event = CalendarEvent(
        event_id="evt-2",
        title="Holiday",
        start_date=date(2026, 5, 1),
        is_all_day=True,
    )
    assert event.start_date == date(2026, 5, 1)
    assert event.start_time is None
    assert event.is_all_day is True
