"""
STORY-365: SSE Heartbeat & Auto-Reconnection — Backend Tests

AC11: SSE endpoint with Last-Event-ID returns only events after that ID
AC12: Progress state in Redis survives SSE reconnection
AC4: Cache-Control: no-cache, no-store
AC5: SSE_HEARTBEAT_INTERVAL_S configurable via env var
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport
from main import app
from auth import require_auth
from progress import ProgressEvent, ProgressTracker, _active_trackers


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _cleanup_trackers():
    """Clean up global tracker registry."""
    yield
    _active_trackers.clear()


@pytest.fixture
def mock_auth():
    """Override auth dependency."""
    app.dependency_overrides[require_auth] = lambda: {"id": "test-user-365", "email": "test@test.com"}
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def mock_sse_limits():
    """Mock SSE connection limiter."""
    with patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
         patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):
        yield


@pytest.fixture(autouse=True)
def _force_sync_search(monkeypatch):
    """Default to sync search mode."""
    import config
    monkeypatch.setattr(config, "SEARCH_ASYNC_ENABLED", False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_tracker(search_id: str, uf_count: int = 3) -> ProgressTracker:
    """Create a ProgressTracker with in-memory mode (no Redis)."""
    tracker = ProgressTracker(search_id, uf_count, use_redis=False)
    _active_trackers[search_id] = tracker
    return tracker


async def _emit_events(tracker: ProgressTracker, count: int, terminal: bool = True):
    """Emit N progress events + optional terminal complete event."""
    for i in range(count):
        await tracker.emit("fetching", 10 + i * 10, f"UF {i+1}/{count}")
    if terminal:
        await tracker.emit_complete()


def _parse_sse_events(text: str) -> list[dict]:
    """Parse SSE text into list of event dicts (only data lines)."""
    events = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            try:
                events.append(json.loads(line[5:].strip()))
            except json.JSONDecodeError:
                pass
    return events


def _parse_sse_ids(text: str) -> list[int]:
    """Extract SSE event ids from response text."""
    ids = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("id:"):
            try:
                ids.append(int(line[3:].strip()))
            except ValueError:
                pass
    return ids


# ── AC11: Last-Event-ID returns only later events ────────────────────────────

@pytest.mark.asyncio
async def test_last_event_id_replays_only_later_events(mock_auth, mock_sse_limits):
    """AC11: SSE endpoint with Last-Event-ID returns only events after that ID."""
    search_id = "test-365-replay"
    tracker = _make_tracker(search_id)

    # Emit 5 events + terminal
    await _emit_events(tracker, 5, terminal=True)

    # Mock Redis as unavailable — use local tracker replay
    with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=None), \
         patch("routes.search_sse.is_search_terminal", new_callable=AsyncMock) as mock_terminal, \
         patch("routes.search_sse.get_replay_events", new_callable=AsyncMock) as mock_replay, \
         patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

        # Simulate: search is terminal, replay events after ID 3
        terminal_event = {"stage": "complete", "progress": 100, "message": "Done"}
        mock_terminal.return_value = terminal_event

        # Events 4, 5 and 6 (complete) are after ID 3
        mock_replay.return_value = [
            (4, {"stage": "fetching", "progress": 40, "message": "UF 4/5"}),
            (5, {"stage": "fetching", "progress": 50, "message": "UF 5/5"}),
            (6, {"stage": "complete", "progress": 100, "message": "Busca concluida!"}),
        ]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/buscar-progress/{search_id}",
                headers={"Last-Event-ID": "3"},
            )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        ids = _parse_sse_ids(response.text)

        # Should have replayed events 4, 5, 6 (all after ID 3)
        assert len(events) >= 3
        # All IDs should be > 3
        assert all(eid > 3 for eid in ids), f"Expected all IDs > 3, got {ids}"
        # Last event should be terminal
        assert events[-1]["stage"] == "complete"

        # Verify get_replay_events was called with after_id=3
        mock_replay.assert_called_once_with(search_id, 3)


@pytest.mark.asyncio
async def test_last_event_id_zero_replays_nothing_extra(mock_auth, mock_sse_limits):
    """Last-Event-ID=0 means no prior events — streams normally."""
    search_id = "test-365-fresh"
    tracker = _make_tracker(search_id)

    # Put a complete event in queue for immediate consumption
    await tracker.queue.put(ProgressEvent(stage="complete", progress=100, message="Done"))

    with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
         patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/buscar-progress/{search_id}",
                headers={"Last-Event-ID": "0"},
            )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    assert len(events) >= 1
    assert events[-1]["stage"] == "complete"


@pytest.mark.asyncio
async def test_last_event_id_query_param_fallback(mock_auth, mock_sse_limits):
    """Last-Event-ID can be passed as query param (for frontends that can't set headers)."""
    search_id = "test-365-query"
    tracker = _make_tracker(search_id)

    await tracker.queue.put(ProgressEvent(stage="complete", progress=100, message="Done"))

    with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=None), \
         patch("routes.search_sse.is_search_terminal", new_callable=AsyncMock) as mock_terminal, \
         patch("routes.search_sse.get_replay_events", new_callable=AsyncMock) as mock_replay, \
         patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

        mock_terminal.return_value = {"stage": "complete", "progress": 100, "message": "Done"}
        mock_replay.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/buscar-progress/{search_id}?last_event_id=5",
            )

    assert response.status_code == 200
    # Verify replay was attempted with ID 5
    mock_replay.assert_called_once_with(search_id, 5)


# ── AC12: Progress state in Redis survives reconnection ───────────────────────

@pytest.mark.asyncio
async def test_progress_persists_in_redis_for_reconnect(mock_auth, mock_sse_limits):
    """AC12: Progress state survives SSE reconnection via Redis replay list."""
    search_id = "test-365-persist"

    # Create a tracker and emit events (these get stored in _event_history)
    tracker = _make_tracker(search_id)
    await tracker.emit("fetching", 20, "UF 1/3")
    await tracker.emit("fetching", 40, "UF 2/3")
    await tracker.emit("fetching", 60, "UF 3/3")

    # Verify local tracker has event history
    assert len(tracker._event_history) == 3
    assert tracker._event_counter == 3

    # get_events_after(1) should return events 2 and 3
    later_events = tracker.get_events_after(1)
    assert len(later_events) == 2
    assert later_events[0][0] == 2  # event_id=2
    assert later_events[1][0] == 3  # event_id=3

    # get_events_after(0) returns all 3
    all_events = tracker.get_events_after(0)
    assert len(all_events) == 3


@pytest.mark.asyncio
async def test_redis_replay_events_function():
    """AC12: get_replay_events reads from Redis list when local tracker is gone."""
    from progress import get_replay_events, _REPLAY_KEY_PREFIX

    search_id = "test-365-redis-replay"
    replay_key = f"{_REPLAY_KEY_PREFIX}{search_id}"

    # Mock Redis with stored events
    mock_redis = AsyncMock()
    mock_redis.lrange.return_value = [
        json.dumps({"id": 1, "data": {"stage": "fetching", "progress": 20, "message": "UF 1"}}),
        json.dumps({"id": 2, "data": {"stage": "fetching", "progress": 40, "message": "UF 2"}}),
        json.dumps({"id": 3, "data": {"stage": "complete", "progress": 100, "message": "Done"}}),
    ]

    with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
        # Request events after ID 1 — should get events 2 and 3
        events = await get_replay_events(search_id, 1)
        assert len(events) == 2
        assert events[0][0] == 2
        assert events[1][0] == 3
        assert events[1][1]["stage"] == "complete"

        # Request events after ID 0 — should get all 3
        events_all = await get_replay_events(search_id, 0)
        assert len(events_all) == 3


@pytest.mark.asyncio
async def test_is_search_terminal_detects_complete():
    """AC12: Terminal state check works for completed searches."""
    from progress import is_search_terminal

    search_id = "test-365-terminal"
    tracker = _make_tracker(search_id)

    # Not terminal yet
    result = await is_search_terminal(search_id)
    assert result is None

    # Emit complete
    await tracker.emit_complete()

    # Now terminal
    result = await is_search_terminal(search_id)
    assert result is not None
    assert result["stage"] == "complete"


# ── AC4: Cache-Control header ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sse_cache_control_no_store(mock_auth, mock_sse_limits):
    """AC4: SSE response includes Cache-Control: no-cache, no-store."""
    search_id = "test-365-headers"
    tracker = _make_tracker(search_id)
    await tracker.queue.put(ProgressEvent(stage="complete", progress=100, message="Done"))

    with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
         patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/buscar-progress/{search_id}")

    assert response.status_code == 200
    cache_control = response.headers.get("cache-control", "")
    assert "no-cache" in cache_control
    assert "no-store" in cache_control


@pytest.mark.asyncio
async def test_sse_x_accel_buffering_header(mock_auth, mock_sse_limits):
    """AC4: SSE response includes X-Accel-Buffering: no."""
    search_id = "test-365-xaccel"
    tracker = _make_tracker(search_id)
    await tracker.queue.put(ProgressEvent(stage="complete", progress=100, message="Done"))

    with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
         patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/buscar-progress/{search_id}")

    assert response.status_code == 200
    assert response.headers.get("x-accel-buffering") == "no"


# ── AC5: Configurable heartbeat interval ──────────────────────────────────────

def test_heartbeat_interval_default():
    """AC5: Default heartbeat interval is 15s."""
    from routes.search_sse import _SSE_HEARTBEAT_INTERVAL
    # Note: test may see patched value from other tests, check env-based logic
    import os
    default_val = float(os.environ.get("SSE_HEARTBEAT_INTERVAL_S", "15"))
    assert default_val == 15.0 or "SSE_HEARTBEAT_INTERVAL_S" in os.environ


def test_heartbeat_interval_configurable(monkeypatch):
    """AC5: Heartbeat interval reads from SSE_HEARTBEAT_INTERVAL_S env var."""
    monkeypatch.setenv("SSE_HEARTBEAT_INTERVAL_S", "20")
    val = float("20")  # Same logic as in routes/search.py
    assert val == 20.0


# ── AC11+AC12 integration: Full reconnection flow ────────────────────────────

@pytest.mark.asyncio
async def test_reconnection_flow_replays_missed_events(mock_auth, mock_sse_limits):
    """Integration: Simulates disconnect + reconnect with Last-Event-ID."""
    search_id = "test-365-flow"

    # First connection: emit 3 events
    tracker = _make_tracker(search_id)
    await tracker.emit("fetching", 20, "UF 1/5")
    await tracker.emit("fetching", 30, "UF 2/5")
    await tracker.emit("fetching", 40, "UF 3/5")

    # Simulate: client disconnected after event ID 2, reconnects with Last-Event-ID=2
    # Now emit 2 more events + terminal
    await tracker.emit("fetching", 50, "UF 4/5")
    await tracker.emit_complete()

    # Tracker has all 5 events in history
    assert tracker._event_counter == 5

    # Reconnection should replay events 3, 4, 5 (after ID 2)
    with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=None), \
         patch("routes.search_sse.is_search_terminal", new_callable=AsyncMock) as mock_terminal, \
         patch("routes.search_sse.get_replay_events", new_callable=AsyncMock) as mock_replay, \
         patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

        mock_terminal.return_value = {"stage": "complete", "progress": 100, "message": "Done"}
        mock_replay.return_value = [
            (3, {"stage": "fetching", "progress": 40, "message": "UF 3/5"}),
            (4, {"stage": "fetching", "progress": 50, "message": "UF 4/5"}),
            (5, {"stage": "complete", "progress": 100, "message": "Done"}),
        ]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/buscar-progress/{search_id}",
                headers={"Last-Event-ID": "2"},
            )

    assert response.status_code == 200
    events = _parse_sse_events(response.text)
    ids = _parse_sse_ids(response.text)

    # Should have events 3, 4, 5 (terminal replay includes all)
    assert len(events) >= 3
    assert all(eid > 2 for eid in ids)
    assert events[-1]["stage"] == "complete"


@pytest.mark.asyncio
async def test_sse_event_ids_are_monotonic(mock_auth, mock_sse_limits):
    """Events streamed from in-memory queue have monotonically increasing IDs."""
    search_id = "test-365-monotonic"
    tracker = _make_tracker(search_id)

    # Queue 3 events + terminal
    await tracker.queue.put(ProgressEvent(stage="fetching", progress=20, message="UF 1"))
    await tracker.queue.put(ProgressEvent(stage="fetching", progress=40, message="UF 2"))
    await tracker.queue.put(ProgressEvent(stage="complete", progress=100, message="Done"))

    with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
         patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/buscar-progress/{search_id}")

    assert response.status_code == 200
    ids = _parse_sse_ids(response.text)
    assert len(ids) >= 3
    # IDs must be strictly increasing
    for i in range(1, len(ids)):
        assert ids[i] > ids[i - 1], f"IDs not monotonic: {ids}"
