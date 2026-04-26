"""Tests for Zectrix calendar sync logic."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from cyber_persona.plugins.zectrix.calendar_sync import sync as sync_module
from cyber_persona.plugins.zectrix.calendar_sync.sync import (
    CalendarSync,
    _event_to_todo,
    _parse_event,
)
from cyber_persona.plugins.zectrix.models import (
    SyncedEventRecord,
    SyncState,
    Todo,
)


# ── _parse_event ──────────────────────────────────────────────


def test_parse_event_timed():
    raw = {
        "id": "evt-1",
        "status": "confirmed",
        "summary": "Meeting",
        "description": "with team",
        "start": {"dateTime": "2026-04-26T14:00:00Z"},
    }
    parsed = _parse_event(raw)
    assert parsed is not None
    assert parsed.event_id == "evt-1"
    assert parsed.title == "Meeting"
    assert parsed.is_all_day is False
    assert parsed.start_time == datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc)
    assert parsed.start_date is None


def test_parse_event_all_day():
    raw = {
        "id": "evt-2",
        "status": "confirmed",
        "summary": "Holiday",
        "start": {"date": "2026-05-01"},
    }
    parsed = _parse_event(raw)
    assert parsed is not None
    assert parsed.is_all_day is True
    assert parsed.start_date == date(2026, 5, 1)
    assert parsed.start_time is None


def test_parse_event_cancelled_returns_none():
    raw = {"id": "evt-3", "status": "cancelled"}
    assert _parse_event(raw) is None


def test_parse_event_missing_summary():
    raw = {
        "id": "evt-4",
        "status": "confirmed",
        "start": {"dateTime": "2026-04-26T09:00:00Z"},
    }
    parsed = _parse_event(raw)
    assert parsed is not None
    assert parsed.title == "(无标题)"


# ── _event_to_todo ────────────────────────────────────────────


def test_event_to_todo_timed():
    from cyber_persona.plugins.zectrix.models import CalendarEvent

    event = CalendarEvent(
        event_id="evt-1",
        title="Meeting",
        description="team sync",
        start_time=datetime(2026, 4, 26, 14, 30, tzinfo=timezone.utc),
    )
    todo = _event_to_todo(event, "dev-1")
    assert todo.dueDate == "2026-04-26"
    assert todo.dueTime == "14:30"
    assert todo.title == "Meeting"
    assert todo.deviceId == "dev-1"


def test_event_to_todo_all_day():
    from cyber_persona.plugins.zectrix.models import CalendarEvent

    event = CalendarEvent(
        event_id="evt-2",
        title="Holiday",
        start_date=date(2026, 5, 1),
        is_all_day=True,
    )
    todo = _event_to_todo(event, "dev-1")
    assert todo.dueDate == "2026-05-01"
    assert todo.dueTime == ""


def test_event_to_todo_truncates_description():
    from cyber_persona.plugins.zectrix.models import CalendarEvent

    event = CalendarEvent(
        event_id="evt-1",
        title="x",
        description="a" * 200,
        start_time=datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc),
    )
    todo = _event_to_todo(event, "dev-1")
    assert len(todo.description) == 100


# ── CalendarSync.run helpers ──────────────────────────────────


def _patch_state_path(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Redirect SYNC_STATE_PATH to a tmp file so tests don't touch real data."""
    state_file = tmp_path / "sync_state.json"
    monkeypatch.setattr(sync_module, "SYNC_STATE_PATH", state_file)


def _make_service_mock(pages: list[dict]) -> MagicMock:
    """Build a MagicMock that mimics googleapiclient's chained service calls."""
    service = MagicMock()
    service.events.return_value.list.return_value.execute.side_effect = pages
    return service


def _patch_google(monkeypatch: pytest.MonkeyPatch, service: MagicMock) -> None:
    monkeypatch.setattr(sync_module, "build", lambda *a, **kw: service)
    monkeypatch.setattr(
        sync_module, "get_valid_credentials", lambda: object()
    )


def _patch_zectrix_client(
    monkeypatch: pytest.MonkeyPatch, client_mock: AsyncMock
) -> None:
    """Patch ZectrixClient so `async with ZectrixClient() as c:` yields client_mock."""

    def _factory(*_args, **_kwargs):
        cm = AsyncMock()
        cm.__aenter__.return_value = client_mock
        cm.__aexit__.return_value = None
        return cm

    monkeypatch.setattr(sync_module, "ZectrixClient", _factory)


# ── CalendarSync.run: create branch ──────────────────────────


@pytest.mark.asyncio
async def test_run_creates_new_event(monkeypatch, tmp_path):
    _patch_state_path(monkeypatch, tmp_path)

    service = _make_service_mock([
        {
            "items": [
                {
                    "id": "evt-1",
                    "status": "confirmed",
                    "summary": "New",
                    "start": {"dateTime": "2026-04-27T10:00:00Z"},
                }
            ]
        }
    ])
    _patch_google(monkeypatch, service)

    client = AsyncMock()
    client.get_first_device_id = AsyncMock(return_value="dev-1")
    client.create_todo = AsyncMock(
        return_value=Todo(id=42, title="New", deviceId="dev-1")
    )
    client.update_todo = AsyncMock()
    client.delete_todo = AsyncMock()
    _patch_zectrix_client(monkeypatch, client)

    sync = CalendarSync(device_id="dev-1")
    sync.state = SyncState()  # start fresh
    counts = await sync.run()

    assert counts == {"created": 1, "updated": 0, "deleted": 0}
    client.create_todo.assert_awaited_once()
    client.update_todo.assert_not_awaited()
    client.delete_todo.assert_not_awaited()
    assert "evt-1" in sync.state.synced_events
    assert sync.state.synced_events["evt-1"].todo_id == 42


# ── CalendarSync.run: update branch ──────────────────────────


@pytest.mark.asyncio
async def test_run_updates_changed_event(monkeypatch, tmp_path):
    _patch_state_path(monkeypatch, tmp_path)

    service = _make_service_mock([
        {
            "items": [
                {
                    "id": "evt-1",
                    "status": "confirmed",
                    "summary": "New Title",  # changed from "Old Title"
                    "start": {"dateTime": "2026-04-27T10:00:00Z"},
                }
            ]
        }
    ])
    _patch_google(monkeypatch, service)

    client = AsyncMock()
    client.get_first_device_id = AsyncMock(return_value="dev-1")
    client.create_todo = AsyncMock()
    client.update_todo = AsyncMock(
        return_value=Todo(id=42, title="New Title", deviceId="dev-1")
    )
    client.delete_todo = AsyncMock()
    _patch_zectrix_client(monkeypatch, client)

    sync = CalendarSync(device_id="dev-1")
    sync.state = SyncState(
        synced_events={
            "evt-1": SyncedEventRecord(
                event_id="evt-1",
                todo_id=42,
                synced_at=datetime(2026, 4, 25, tzinfo=timezone.utc),
                title="Old Title",
                dueDate="2026-04-27",
                dueTime="10:00",
            )
        }
    )

    counts = await sync.run()

    assert counts == {"created": 0, "updated": 1, "deleted": 0}
    client.update_todo.assert_awaited_once()
    client.create_todo.assert_not_awaited()
    client.delete_todo.assert_not_awaited()
    assert sync.state.synced_events["evt-1"].title == "New Title"


# ── CalendarSync.run: delete branch ──────────────────────────


@pytest.mark.asyncio
async def test_run_deletes_gone_event(monkeypatch, tmp_path):
    _patch_state_path(monkeypatch, tmp_path)

    service = _make_service_mock([{"items": []}])  # no events anymore
    _patch_google(monkeypatch, service)

    client = AsyncMock()
    client.get_first_device_id = AsyncMock(return_value="dev-1")
    client.create_todo = AsyncMock()
    client.update_todo = AsyncMock()
    client.delete_todo = AsyncMock()
    _patch_zectrix_client(monkeypatch, client)

    sync = CalendarSync(device_id="dev-1")
    sync.state = SyncState(
        synced_events={
            "evt-1": SyncedEventRecord(
                event_id="evt-1",
                todo_id=99,
                synced_at=datetime(2026, 4, 25, tzinfo=timezone.utc),
                title="Gone",
            )
        }
    )

    counts = await sync.run()

    assert counts == {"created": 0, "updated": 0, "deleted": 1}
    client.delete_todo.assert_awaited_once_with(99)
    assert "evt-1" not in sync.state.synced_events


# ── CalendarSync.run: no-op branch ───────────────────────────


@pytest.mark.asyncio
async def test_run_no_op_when_unchanged(monkeypatch, tmp_path):
    _patch_state_path(monkeypatch, tmp_path)

    service = _make_service_mock([
        {
            "items": [
                {
                    "id": "evt-1",
                    "status": "confirmed",
                    "summary": "Same",
                    "description": "",
                    "start": {"dateTime": "2026-04-27T10:00:00Z"},
                }
            ]
        }
    ])
    _patch_google(monkeypatch, service)

    client = AsyncMock()
    client.get_first_device_id = AsyncMock(return_value="dev-1")
    client.create_todo = AsyncMock()
    client.update_todo = AsyncMock()
    client.delete_todo = AsyncMock()
    _patch_zectrix_client(monkeypatch, client)

    sync = CalendarSync(device_id="dev-1")
    sync.state = SyncState(
        synced_events={
            "evt-1": SyncedEventRecord(
                event_id="evt-1",
                todo_id=42,
                synced_at=datetime(2026, 4, 25, tzinfo=timezone.utc),
                title="Same",
                dueDate="2026-04-27",
                dueTime="10:00",
                description="",
            )
        }
    )

    counts = await sync.run()

    assert counts == {"created": 0, "updated": 0, "deleted": 0}
    client.create_todo.assert_not_awaited()
    client.update_todo.assert_not_awaited()
    client.delete_todo.assert_not_awaited()


# ── CalendarSync.run: pagination ─────────────────────────────


@pytest.mark.asyncio
async def test_run_handles_pagination(monkeypatch, tmp_path):
    _patch_state_path(monkeypatch, tmp_path)

    pages = [
        {
            "items": [
                {
                    "id": "evt-A",
                    "status": "confirmed",
                    "summary": "A",
                    "start": {"dateTime": "2026-04-27T10:00:00Z"},
                }
            ],
            "nextPageToken": "page2",
        },
        {
            "items": [
                {
                    "id": "evt-B",
                    "status": "confirmed",
                    "summary": "B",
                    "start": {"dateTime": "2026-04-28T10:00:00Z"},
                }
            ]
        },
    ]
    service = _make_service_mock(pages)
    _patch_google(monkeypatch, service)

    client = AsyncMock()
    client.get_first_device_id = AsyncMock(return_value="dev-1")
    counter = {"n": 0}

    async def _fake_create(_todo: Todo) -> Todo:
        counter["n"] += 1
        return Todo(id=counter["n"], title=_todo.title, deviceId="dev-1")

    client.create_todo = AsyncMock(side_effect=_fake_create)
    client.update_todo = AsyncMock()
    client.delete_todo = AsyncMock()
    _patch_zectrix_client(monkeypatch, client)

    sync = CalendarSync(device_id="dev-1")
    sync.state = SyncState()
    counts = await sync.run()

    assert counts == {"created": 2, "updated": 0, "deleted": 0}
    assert {"evt-A", "evt-B"} == set(sync.state.synced_events.keys())
    # Pagination: list called once per page (2 calls total)
    assert (
        service.events.return_value.list.return_value.execute.call_count == 2
    )
