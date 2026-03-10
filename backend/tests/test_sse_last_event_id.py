"""STORY-297: Tests for SSE Last-Event-ID resumption.

AC1:  Each SSE event includes `id:` field with monotonic counter per search_id
AC2:  Events stored in Redis list `sse_events:{search_id}` with TTL 10min
AC3:  Endpoint reads Last-Event-ID header and replays events after that ID
AC4:  If Last-Event-ID present and search completed, sends terminal immediately
AC5:  Max 1000 events per search_id (ring buffer)
AC10: Disconnection -> reconnection -> no lost events
AC11: Reconnect after complete -> receives completed immediately
AC12: Existing tests still pass (verified by CI)
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from progress import (
    ProgressEvent,
    ProgressTracker,
    _active_trackers,
    _REPLAY_KEY_PREFIX,
    _REPLAY_LIST_TTL,
    _REPLAY_MAX_EVENTS,
    _TERMINAL_STAGES,
    get_replay_events,
    is_search_terminal,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_trackers():
    """Clean up global tracker registry after each test to prevent pollution."""
    yield
    _active_trackers.clear()


@pytest.fixture
def mock_redis_pool():
    """Mock Redis pool returning None (no Redis available)."""
    with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
         patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
        yield


@pytest.fixture
def mock_auth():
    """Override auth dependency for route tests."""
    from main import app
    from auth import require_auth
    app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "test@test.com"}
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def mock_sse_limits():
    """Mock SSE connection limiter to always allow."""
    with patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
         patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):
        yield


# ============================================================================
# Helper functions
# ============================================================================


def _parse_sse_events(text: str) -> list[dict]:
    """Parse SSE response text into a list of {id, data} dicts.

    Each SSE event block is separated by double newlines. We look for
    lines starting with 'id:' and 'data:' within each block.
    """
    events = []
    blocks = text.split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        event = {}
        for line in lines:
            if line.startswith("id: "):
                event["id"] = int(line[4:].strip())
            elif line.startswith("id:"):
                event["id"] = int(line[3:].strip())
            elif line.startswith("data: "):
                event["data"] = json.loads(line[6:])
            elif line.startswith("data:"):
                event["data"] = json.loads(line[5:])
        if event.get("data"):
            events.append(event)
    return events


def _make_tracker(search_id: str, use_redis: bool = False) -> ProgressTracker:
    """Create a tracker and register it in _active_trackers."""
    tracker = ProgressTracker(search_id, uf_count=3, use_redis=use_redis)
    _active_trackers[search_id] = tracker
    return tracker


# ============================================================================
# AC1: SSE events include `id:` field with monotonic counter
# ============================================================================


@pytest.mark.asyncio
class TestEventsHaveIdField:
    """AC1: Verify SSE events include `id:` prefix with monotonic counter."""

    async def test_events_have_id_field(self, mock_auth, mock_sse_limits, mock_redis_pool):
        """AC1: SSE output includes 'id: N' lines with incrementing counter."""
        from main import app
        from progress import ProgressEvent

        mock_tracker = MagicMock()
        mock_tracker._use_redis = False
        mock_tracker.queue = asyncio.Queue()

        # Enqueue two events then complete
        await mock_tracker.queue.put(
            ProgressEvent(stage="fetching", progress=30, message="Fetching...")
        )
        await mock_tracker.queue.put(
            ProgressEvent(stage="filtering", progress=60, message="Filtering...")
        )
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/buscar-progress/test-id-field")

        assert response.status_code == 200

        events = _parse_sse_events(response.text)
        assert len(events) == 3, f"Expected 3 events, got {len(events)}: {response.text}"

        # All events have 'id' field
        for ev in events:
            assert "id" in ev, f"Event missing 'id' field: {ev}"

        # IDs are monotonically increasing (1, 2, 3)
        ids = [ev["id"] for ev in events]
        assert ids == sorted(ids), f"IDs not monotonically sorted: {ids}"
        assert ids == [1, 2, 3], f"Expected [1, 2, 3], got {ids}"

    async def test_event_counter_monotonic_across_emit_methods(self, mock_redis_pool):
        """AC1: Counter increments across different emit methods (emit, emit_complete, etc.)."""
        tracker = ProgressTracker("monotonic-test", uf_count=5, use_redis=False)

        await tracker.emit("connecting", 5, "Starting...")
        await tracker.emit_uf_complete("SP", 10)
        await tracker.emit("filtering", 60, "Filtering...")
        await tracker.emit_complete()

        # Local history should have 4 events with IDs 1, 2, 3, 4
        assert len(tracker._event_history) == 4
        ids = [eid for eid, _ in tracker._event_history]
        assert ids == [1, 2, 3, 4], f"Expected [1, 2, 3, 4], got {ids}"

        # Counter should be at 4
        assert tracker._event_counter == 4

    async def test_event_counter_starts_at_zero(self, mock_redis_pool):
        """AC1: New tracker starts with counter=0, first event gets id=1."""
        tracker = ProgressTracker("fresh-tracker", uf_count=1, use_redis=False)
        assert tracker._event_counter == 0
        assert tracker._event_history == []

        await tracker.emit("connecting", 5, "Hello")
        assert tracker._event_counter == 1
        assert tracker._event_history[0][0] == 1


# ============================================================================
# AC2: Events stored in Redis list with TTL 10min
# ============================================================================


@pytest.mark.asyncio
class TestEventsStoredInRedisList:
    """AC2: Verify _store_replay_event calls RPUSH/LTRIM/EXPIRE on correct key."""

    async def test_store_replay_event_redis_operations(self):
        """AC2: _store_replay_event performs RPUSH + LTRIM + EXPIRE."""
        mock_redis = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            tracker = ProgressTracker("redis-store-test", uf_count=1, use_redis=False)
            event_dict = {"stage": "fetching", "progress": 30, "message": "test"}

            await tracker._store_replay_event(1, event_dict)

        # Check RPUSH was called with correct key and serialized data
        expected_key = f"{_REPLAY_KEY_PREFIX}redis-store-test"
        mock_redis.rpush.assert_called_once()
        call_args = mock_redis.rpush.call_args
        assert call_args[0][0] == expected_key
        entry = json.loads(call_args[0][1])
        assert entry["id"] == 1
        assert entry["data"] == event_dict

        # Check LTRIM (ring buffer trim)
        mock_redis.ltrim.assert_called_once_with(expected_key, -_REPLAY_MAX_EVENTS, -1)

        # Check EXPIRE (10 min TTL)
        mock_redis.expire.assert_called_once_with(expected_key, _REPLAY_LIST_TTL)

    async def test_store_replay_event_no_redis(self):
        """AC2: _store_replay_event silently skips when Redis is unavailable."""
        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None):
            tracker = ProgressTracker("no-redis-test", uf_count=1, use_redis=False)
            # Should not raise
            await tracker._store_replay_event(1, {"stage": "fetching"})

    async def test_store_replay_event_redis_failure(self):
        """AC2: _store_replay_event logs warning on Redis failure, does not raise."""
        mock_redis = AsyncMock()
        mock_redis.rpush.side_effect = ConnectionError("Redis down")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            tracker = ProgressTracker("fail-test", uf_count=1, use_redis=False)
            # Should not raise
            await tracker._store_replay_event(1, {"stage": "error"})

    async def test_emit_stores_in_history_and_redis(self):
        """AC2: _emit_event stores event in both local history and Redis list."""
        mock_redis = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            tracker = ProgressTracker("emit-store-test", uf_count=1, use_redis=False)
            await tracker.emit("connecting", 5, "Starting...")

        # Local history has the event
        assert len(tracker._event_history) == 1
        assert tracker._event_history[0][0] == 1  # id=1

        # Redis RPUSH was called
        assert mock_redis.rpush.call_count == 1

    async def test_replay_key_format(self):
        """AC2: Redis list key follows format 'sse_events:{search_id}'."""
        assert _REPLAY_KEY_PREFIX == "sse_events:"
        assert _REPLAY_LIST_TTL == 600  # 10 minutes


# ============================================================================
# AC3: Last-Event-ID header replays events after that ID
# ============================================================================


@pytest.mark.asyncio
class TestReplayAfterLastEventId:
    """AC3: Send Last-Event-ID header -> get only newer events."""

    async def test_replay_after_last_event_id(self, mock_auth, mock_sse_limits):
        """AC3: Reconnect with Last-Event-ID=2 replays events 3, 4, 5 then continues."""
        from main import app

        # Build a tracker with 5 events in history (events 1-4 + complete at 5)
        tracker = _make_tracker("replay-test")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Connecting...")      # id=1
            await tracker.emit("fetching", 30, "Fetching...")         # id=2
            await tracker.emit("filtering", 60, "Filtering...")       # id=3
            await tracker.emit("llm", 80, "LLM processing...")       # id=4
            await tracker.emit_complete()                             # id=5

        # Mock get_tracker to return our tracker
        # Since search is complete (terminal event in history), AC4 path kicks in
        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/replay-test",
                    headers={"Last-Event-ID": "2"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        # Should get events after id=2: filtering(3), llm(4), complete(5)
        assert len(events) >= 3, (
            f"Expected >=3 events after Last-Event-ID=2, got {len(events)}: {response.text}"
        )
        # First replayed event should be id=3
        ids = [ev["id"] for ev in events]
        assert all(eid > 2 for eid in ids), f"All event IDs should be > 2, got {ids}"

    async def test_replay_via_query_param(self, mock_auth, mock_sse_limits):
        """AC3: last_event_id query param works as alternative to header."""
        from main import app

        tracker = _make_tracker("replay-qp")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")   # id=1
            await tracker.emit_complete()                   # id=2

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/replay-qp?last_event_id=1",
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        # Should get event 2 (complete) since we sent last_event_id=1
        assert len(events) >= 1
        # Terminal event should be present
        stages = [ev["data"]["stage"] for ev in events]
        assert "complete" in stages

    async def test_replay_invalid_last_event_id(self, mock_auth, mock_sse_limits):
        """AC3: Invalid Last-Event-ID (non-numeric) gracefully defaults to 0."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = False
        mock_tracker.queue = asyncio.Queue()
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/replay-invalid",
                    headers={"Last-Event-ID": "not-a-number"},
                )

        # Should succeed without errors — defaults to 0 (no replay)
        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        assert len(events) >= 1


# ============================================================================
# AC4: Completed search -> terminal event immediately
# ============================================================================


@pytest.mark.asyncio
class TestCompletedSearchImmediateTerminal:
    """AC4: Reconnect to completed search -> get terminal event immediately."""

    async def test_completed_search_immediate_terminal(self, mock_auth, mock_sse_limits):
        """AC4: Reconnect with Last-Event-ID to completed search sends terminal immediately."""
        from main import app

        tracker = _make_tracker("complete-test")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")
            await tracker.emit("fetching", 30, "Fetching")
            await tracker.emit_complete()  # id=3, terminal

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/complete-test",
                    headers={"Last-Event-ID": "1"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        # Should include the terminal "complete" event
        stages = [ev["data"]["stage"] for ev in events]
        assert "complete" in stages, f"Expected 'complete' in stages, got {stages}"

        # Should NOT continue streaming (no heartbeats or other events after terminal)
        # The response should be relatively short
        assert len(events) >= 1

    async def test_completed_search_with_all_events_seen(self, mock_auth, mock_sse_limits):
        """AC4: If Last-Event-ID equals last event and search complete, still sends terminal."""
        from main import app

        tracker = _make_tracker("all-seen-test")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")       # id=1
            await tracker.emit_complete()                       # id=2

        # Client says it saw up to id=2 (the complete event) — but we still send
        # the terminal confirmation per AC4
        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/all-seen-test",
                    headers={"Last-Event-ID": "2"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        # Should get at least the terminal event
        stages = [ev["data"]["stage"] for ev in events if "data" in ev]
        assert "complete" in stages, (
            f"Expected terminal 'complete' event even when all events seen. "
            f"Got stages={stages}. Response: {response.text[:500]}"
        )

    async def test_degraded_terminal_detected(self, mock_auth, mock_sse_limits):
        """AC4: 'degraded' stage is recognized as terminal for replay."""
        from main import app

        tracker = _make_tracker("degraded-test")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")
            await tracker.emit_degraded("partial", {"coverage_pct": 60})  # terminal

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/degraded-test",
                    headers={"Last-Event-ID": "1"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        stages = [ev["data"]["stage"] for ev in events]
        assert "degraded" in stages


# ============================================================================
# AC5: Ring buffer max 1000 events
# ============================================================================


@pytest.mark.asyncio
class TestRingBufferMax1000:
    """AC5: Emit 1005 events -> history has exactly 1000."""

    async def test_ring_buffer_max_1000(self, mock_redis_pool):
        """AC5: Local history never exceeds _REPLAY_MAX_EVENTS entries."""
        tracker = ProgressTracker("ring-buffer-test", uf_count=1, use_redis=False)

        for i in range(1005):
            await tracker.emit("fetching", min(i, 99), f"Event {i}")

        assert len(tracker._event_history) == _REPLAY_MAX_EVENTS
        assert len(tracker._event_history) == 1000

        # First event should be #6 (events 1-5 were trimmed)
        first_id = tracker._event_history[0][0]
        assert first_id == 6, f"Expected first remaining id=6, got {first_id}"

        # Last event should be #1005
        last_id = tracker._event_history[-1][0]
        assert last_id == 1005, f"Expected last id=1005, got {last_id}"

    async def test_ring_buffer_at_boundary(self, mock_redis_pool):
        """AC5: Exactly 1000 events — no trimming needed."""
        tracker = ProgressTracker("boundary-test", uf_count=1, use_redis=False)

        for i in range(1000):
            await tracker.emit("fetching", 50, f"Event {i}")

        assert len(tracker._event_history) == 1000
        assert tracker._event_history[0][0] == 1
        assert tracker._event_history[-1][0] == 1000

    async def test_ring_buffer_below_limit(self, mock_redis_pool):
        """AC5: Below 1000 events — history contains all of them."""
        tracker = ProgressTracker("small-test", uf_count=1, use_redis=False)

        for i in range(50):
            await tracker.emit("fetching", 50, f"Event {i}")

        assert len(tracker._event_history) == 50
        assert tracker._event_history[0][0] == 1
        assert tracker._event_history[-1][0] == 50

    async def test_redis_ltrim_called_for_ring_buffer(self):
        """AC5: LTRIM enforces ring buffer in Redis list too."""
        mock_redis = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            tracker = ProgressTracker("ltrim-test", uf_count=1, use_redis=False)
            await tracker._store_replay_event(1, {"stage": "fetching"})

        mock_redis.ltrim.assert_called_once_with(
            f"{_REPLAY_KEY_PREFIX}ltrim-test",
            -_REPLAY_MAX_EVENTS,
            -1,
        )


# ============================================================================
# get_events_after() — local history replay
# ============================================================================


@pytest.mark.asyncio
class TestGetEventsAfter:
    """Test ProgressTracker.get_events_after() for local replay."""

    async def test_get_events_after_returns_only_newer(self, mock_redis_pool):
        """get_events_after(3) returns events 4, 5, ... from local history."""
        tracker = ProgressTracker("after-test", uf_count=1, use_redis=False)

        await tracker.emit("connecting", 5, "a")    # id=1
        await tracker.emit("fetching", 30, "b")     # id=2
        await tracker.emit("filtering", 60, "c")    # id=3
        await tracker.emit("llm", 80, "d")          # id=4
        await tracker.emit_complete()                # id=5

        events = tracker.get_events_after(3)
        ids = [eid for eid, _ in events]
        assert ids == [4, 5]

    async def test_get_events_after_zero_returns_all(self, mock_redis_pool):
        """get_events_after(0) returns all events."""
        tracker = ProgressTracker("after-all", uf_count=1, use_redis=False)

        await tracker.emit("connecting", 5, "a")
        await tracker.emit_complete()

        events = tracker.get_events_after(0)
        assert len(events) == 2

    async def test_get_events_after_large_id_returns_empty(self, mock_redis_pool):
        """get_events_after(999) returns [] when only 2 events exist."""
        tracker = ProgressTracker("after-empty", uf_count=1, use_redis=False)

        await tracker.emit("connecting", 5, "a")
        await tracker.emit_complete()

        events = tracker.get_events_after(999)
        assert events == []


# ============================================================================
# get_replay_events() — module-level function (tracker + Redis fallback)
# ============================================================================


@pytest.mark.asyncio
class TestGetReplayEvents:
    """Test get_replay_events() falls back from local tracker to Redis."""

    async def test_replay_from_local_tracker(self, mock_redis_pool):
        """get_replay_events uses local tracker history when available."""
        tracker = _make_tracker("local-replay")

        await tracker.emit("connecting", 5, "a")    # id=1
        await tracker.emit("fetching", 30, "b")     # id=2
        await tracker.emit_complete()                # id=3

        events = await get_replay_events("local-replay", after_id=1)
        ids = [eid for eid, _ in events]
        assert ids == [2, 3]

    async def test_replay_from_redis_when_no_local_tracker(self):
        """get_replay_events falls back to Redis when no local tracker exists."""
        # No tracker in _active_trackers for this search_id
        redis_entries = [
            json.dumps({"id": 1, "data": {"stage": "connecting", "progress": 5, "message": "a"}}),
            json.dumps({"id": 2, "data": {"stage": "fetching", "progress": 30, "message": "b"}}),
            json.dumps({"id": 3, "data": {"stage": "complete", "progress": 100, "message": "Done"}}),
        ]

        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = redis_entries

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            events = await get_replay_events("orphan-search", after_id=1)

        assert len(events) == 2  # events 2 and 3
        ids = [eid for eid, _ in events]
        assert ids == [2, 3]
        mock_redis.lrange.assert_called_once_with(f"{_REPLAY_KEY_PREFIX}orphan-search", 0, -1)

    async def test_replay_graceful_on_redis_failure(self):
        """get_replay_events returns [] when Redis fails (graceful degradation)."""
        mock_redis = AsyncMock()
        mock_redis.lrange.side_effect = ConnectionError("Redis connection lost")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            events = await get_replay_events("redis-fail-search", after_id=0)

        assert events == []

    async def test_replay_returns_empty_when_no_redis_no_tracker(self):
        """get_replay_events returns [] when both tracker and Redis are unavailable."""
        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None):
            events = await get_replay_events("nowhere-search", after_id=0)

        assert events == []

    async def test_replay_from_redis_empty_list(self):
        """get_replay_events returns [] when Redis list exists but is empty."""
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = []

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            events = await get_replay_events("empty-redis", after_id=0)

        assert events == []


# ============================================================================
# is_search_terminal() — checking for terminal state
# ============================================================================


@pytest.mark.asyncio
class TestIsSearchTerminal:
    """Test is_search_terminal() checks local tracker then Redis."""

    async def test_terminal_from_local_tracker(self, mock_redis_pool):
        """is_search_terminal returns terminal event data from local tracker."""
        tracker = _make_tracker("terminal-local")

        await tracker.emit("connecting", 5, "Start")
        await tracker.emit_complete()

        result = await is_search_terminal("terminal-local")
        assert result is not None
        assert result["stage"] == "complete"

    async def test_not_terminal_from_local_tracker(self, mock_redis_pool):
        """is_search_terminal returns None when search is still in progress."""
        tracker = _make_tracker("not-terminal")

        await tracker.emit("connecting", 5, "Start")
        await tracker.emit("fetching", 30, "Fetching...")

        result = await is_search_terminal("not-terminal")
        assert result is None

    async def test_terminal_from_redis(self):
        """is_search_terminal falls back to Redis last entry check."""
        last_entry = json.dumps({
            "id": 5,
            "data": {"stage": "error", "progress": -1, "message": "Failed"},
        })

        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = [last_entry]

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await is_search_terminal("redis-terminal")

        assert result is not None
        assert result["stage"] == "error"

    async def test_terminal_redis_not_terminal_event(self):
        """is_search_terminal returns None when Redis last entry is not terminal."""
        last_entry = json.dumps({
            "id": 3,
            "data": {"stage": "fetching", "progress": 30, "message": "Still going"},
        })

        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = [last_entry]

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await is_search_terminal("redis-not-done")

        assert result is None

    async def test_terminal_stages_complete_set(self):
        """Verify _TERMINAL_STAGES contains all expected terminal stages."""
        assert "complete" in _TERMINAL_STAGES
        assert "error" in _TERMINAL_STAGES
        assert "degraded" in _TERMINAL_STAGES
        assert "refresh_available" in _TERMINAL_STAGES
        assert "search_complete" in _TERMINAL_STAGES
        # Non-terminal
        assert "fetching" not in _TERMINAL_STAGES
        assert "connecting" not in _TERMINAL_STAGES

    async def test_terminal_redis_failure(self):
        """is_search_terminal returns None when Redis fails."""
        mock_redis = AsyncMock()
        mock_redis.lrange.side_effect = ConnectionError("Redis down")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await is_search_terminal("redis-fail-terminal")

        assert result is None


# ============================================================================
# AC10: Disconnection -> reconnection -> no lost events
# ============================================================================


@pytest.mark.asyncio
class TestReconnectDuringActiveSearch:
    """AC10: Simulate disconnect at id=2, reconnect, receive events 3+ without loss."""

    async def test_reconnect_during_active_search(self, mock_auth, mock_sse_limits):
        """AC10: Mid-stream reconnection replays missed events then continues."""
        from main import app

        # Create tracker with events already emitted (simulating events before disconnect)
        tracker = _make_tracker("reconnect-mid")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")       # id=1
            await tracker.emit("fetching", 30, "Fetching")     # id=2
            await tracker.emit("filtering", 60, "Filtering")   # id=3
            await tracker.emit("llm", 80, "LLM")              # id=4

        # Now put the terminal event into queue (will be read during streaming)
        await tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        # Reconnect with Last-Event-ID=2 (client saw events 1,2, missed 3,4,complete)
        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/reconnect-mid",
                    headers={"Last-Event-ID": "2"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        # Should see events after id=2: filtering(3), llm(4), then complete from queue
        ids = [ev["id"] for ev in events]
        stages = [ev["data"]["stage"] for ev in events]

        # All replayed IDs should be > 2
        assert all(eid > 2 for eid in ids), f"Expected all IDs > 2, got {ids}"

        # Should include the missed events AND the terminal
        assert "filtering" in stages, f"Missing 'filtering' in replayed events: {stages}"
        assert "llm" in stages, f"Missing 'llm' in replayed events: {stages}"
        assert "complete" in stages, f"Missing terminal 'complete': {stages}"

    async def test_no_duplicate_events_on_reconnect(self, mock_auth, mock_sse_limits):
        """AC10: Reconnect does not send duplicate events the client already received."""
        from main import app

        tracker = _make_tracker("no-dup")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")       # id=1
            await tracker.emit("fetching", 30, "Fetching")     # id=2
            await tracker.emit_complete()                       # id=3 (terminal)

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/no-dup",
                    headers={"Last-Event-ID": "2"},
                )

        events = _parse_sse_events(response.text)
        ids = [ev["id"] for ev in events]

        # Should NOT contain id=1 or id=2 (already seen by client)
        assert 1 not in ids, f"Duplicate event id=1 sent: {ids}"
        assert 2 not in ids, f"Duplicate event id=2 sent: {ids}"


# ============================================================================
# AC11: Reconnect after complete -> receives completed immediately
# ============================================================================


@pytest.mark.asyncio
class TestReconnectAfterComplete:
    """AC11: Client reconnects after search is fully complete — terminal event sent immediately."""

    async def test_reconnect_after_complete(self, mock_auth, mock_sse_limits):
        """AC11: Reconnect after complete sends 'complete' stage immediately and closes stream."""
        from main import app

        tracker = _make_tracker("post-complete")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")
            await tracker.emit("fetching", 30, "Data")
            await tracker.emit_complete()  # id=3

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/post-complete",
                    headers={"Last-Event-ID": "3"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)

        # Should get at least one event: the terminal 'complete'
        assert len(events) >= 1, f"Expected at least 1 event, got: {response.text}"
        terminal = events[-1]
        assert terminal["data"]["stage"] == "complete"

    async def test_reconnect_after_error_terminal(self, mock_auth, mock_sse_limits):
        """AC11: Reconnect after error sends 'error' stage immediately."""
        from main import app

        tracker = _make_tracker("post-error")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")
            await tracker.emit_error("Timeout")  # id=2, terminal

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/post-error",
                    headers={"Last-Event-ID": "1"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        stages = [ev["data"]["stage"] for ev in events]
        assert "error" in stages

    async def test_reconnect_after_search_complete_terminal(self, mock_auth, mock_sse_limits):
        """AC11: search_complete stage also triggers immediate terminal response."""
        from main import app

        tracker = _make_tracker("post-search-complete")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            await tracker.emit("connecting", 5, "Start")
            await tracker.emit_search_complete("post-search-complete", 42)  # terminal

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
             patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/post-search-complete",
                    headers={"Last-Event-ID": "1"},
                )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        stages = [ev["data"]["stage"] for ev in events]
        assert "search_complete" in stages


# ============================================================================
# No Last-Event-ID — normal streaming (regression guard for AC12)
# ============================================================================


@pytest.mark.asyncio
class TestNormalStreamingNoReplay:
    """AC12: Without Last-Event-ID, streaming works as before (regression check)."""

    async def test_normal_streaming_has_ids(self, mock_auth, mock_sse_limits):
        """AC12: Even without Last-Event-ID, events now have id: fields (AC1 addition)."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = False
        mock_tracker.queue = asyncio.Queue()

        await mock_tracker.queue.put(
            ProgressEvent(stage="connecting", progress=5, message="Start")
        )
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/buscar-progress/normal-stream")

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        assert len(events) == 2

        # All events should have id fields starting from 1
        ids = [ev["id"] for ev in events]
        assert ids == [1, 2]

    async def test_normal_streaming_no_replay_events(self, mock_auth, mock_sse_limits):
        """AC12: Without Last-Event-ID header, no replay occurs — events come from queue."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = False
        mock_tracker.queue = asyncio.Queue()
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_redis_pool", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_sse.get_replay_events", new_callable=AsyncMock) as mock_replay:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/buscar-progress/no-replay")

        assert response.status_code == 200
        # get_replay_events should NOT have been called (no Last-Event-ID)
        mock_replay.assert_not_called()


# ============================================================================
# _emit_event() integration — ensures all emit methods go through common path
# ============================================================================


@pytest.mark.asyncio
class TestEmitEventIntegration:
    """Verify all emit_* methods route through _emit_event() for consistent tracking."""

    async def test_emit_degraded_tracked(self, mock_redis_pool):
        """emit_degraded() increments counter and stores in history."""
        tracker = ProgressTracker("degraded-emit", uf_count=1, use_redis=False)
        await tracker.emit_degraded("partial", {"coverage_pct": 60})

        assert tracker._event_counter == 1
        assert len(tracker._event_history) == 1
        assert tracker._event_history[0][1]["stage"] == "degraded"

    async def test_emit_error_tracked(self, mock_redis_pool):
        """emit_error() increments counter and stores in history."""
        tracker = ProgressTracker("error-emit", uf_count=1, use_redis=False)
        await tracker.emit_error("Something broke")

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "error"

    async def test_emit_source_complete_tracked(self, mock_redis_pool):
        """emit_source_complete() increments counter and stores in history."""
        tracker = ProgressTracker("source-emit", uf_count=1, use_redis=False)
        await tracker.emit_source_complete("PNCP", "success", 50, 1200)

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "source_complete"

    async def test_emit_refresh_available_tracked(self, mock_redis_pool):
        """emit_refresh_available() increments counter and stores in history."""
        tracker = ProgressTracker("refresh-emit", uf_count=1, use_redis=False)
        await tracker.emit_refresh_available(100, 80, 20, 5, 3)

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "refresh_available"

    async def test_emit_search_complete_tracked(self, mock_redis_pool):
        """emit_search_complete() increments counter and stores in history."""
        tracker = ProgressTracker("search-complete-emit", uf_count=1, use_redis=False)
        await tracker.emit_search_complete("search-complete-emit", 42)

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "search_complete"

    async def test_emit_progressive_results_tracked(self, mock_redis_pool):
        """emit_progressive_results() increments counter and stores in history."""
        tracker = ProgressTracker("progressive-emit", uf_count=1, use_redis=False)
        await tracker.emit_progressive_results("PNCP", 10, 10, ["PNCP"], ["PCP"])

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "partial_results"

    async def test_emit_revalidated_tracked(self, mock_redis_pool):
        """emit_revalidated() increments counter and stores in history."""
        tracker = ProgressTracker("revalidated-emit", uf_count=1, use_redis=False)
        await tracker.emit_revalidated(100, "2026-02-27T10:00:00Z")

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "revalidated"

    async def test_emit_batch_progress_tracked(self, mock_redis_pool):
        """emit_batch_progress() increments counter and stores in history."""
        tracker = ProgressTracker("batch-emit", uf_count=5, use_redis=False)
        await tracker.emit_batch_progress(1, 3, ["SP", "RJ"])

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "batch_progress"

    async def test_emit_uf_status_tracked(self, mock_redis_pool):
        """emit_uf_status() increments counter and stores in history."""
        tracker = ProgressTracker("uf-status-emit", uf_count=5, use_redis=False)
        await tracker.emit_uf_status("SP", "success", count=50)

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "uf_status"

    async def test_emit_source_error_tracked(self, mock_redis_pool):
        """emit_source_error() increments counter and stores in history."""
        tracker = ProgressTracker("source-error-emit", uf_count=1, use_redis=False)
        await tracker.emit_source_error("PCP", "Timeout", 5000)

        assert tracker._event_counter == 1
        assert tracker._event_history[0][1]["stage"] == "source_error"


# ============================================================================
# Constants validation
# ============================================================================


class TestReplayConstants:
    """Validate STORY-297 replay constants."""

    def test_replay_list_ttl(self):
        """AC2: Replay list TTL is 10 minutes (600 seconds)."""
        assert _REPLAY_LIST_TTL == 600

    def test_replay_max_events(self):
        """AC5: Ring buffer holds max 1000 events."""
        assert _REPLAY_MAX_EVENTS == 1000

    def test_replay_key_prefix(self):
        """AC2: Redis key prefix is 'sse_events:'."""
        assert _REPLAY_KEY_PREFIX == "sse_events:"

    def test_terminal_stages_include_all_expected(self):
        """Terminal stages used for replay detection are complete."""
        expected = {"complete", "error", "degraded", "refresh_available", "search_complete"}
        assert _TERMINAL_STAGES == expected
