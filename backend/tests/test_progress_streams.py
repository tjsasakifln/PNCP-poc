"""STORY-276: Tests for Redis Streams progress tracking migration.

AC1: ProgressTracker uses Redis Streams (XADD) instead of Pub/Sub (PUBLISH)
AC2: SSE Consumer uses XREAD BLOCK instead of subscribe
AC3: Fallback in-memory preserved
AC4: subscribe_to_events removed, pub/sub logic eliminated
AC5: End-to-end cross-worker simulation

Tests verify:
- XADD stores correct fields in stream
- EXPIRE set on terminal events (5 min TTL)
- XREAD BLOCK replays full history for late subscribers
- Fallback to asyncio.Queue when Redis unavailable
- Cross-worker: tracker on worker A, SSE reads from worker B
- Stream key cleanup on remove_tracker()
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport

from progress import (
    ProgressEvent,
    ProgressTracker,
    _STREAM_EXPIRE_TTL,
    _TERMINAL_STAGES,
    _active_trackers,
    create_tracker,
    get_tracker,
    remove_tracker,
)


@pytest.fixture(autouse=True)
def cleanup_trackers():
    """Clean up global tracker registry after each test."""
    yield
    _active_trackers.clear()


@pytest.fixture
def mock_redis_unavailable():
    """Mock Redis as unavailable — forces in-memory fallback."""
    with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool, \
         patch("progress.is_redis_available", new_callable=AsyncMock) as mock_available:
        mock_pool.return_value = None
        mock_available.return_value = False
        yield {"pool": mock_pool, "available": mock_available}


# ============================================================================
# AC1: XADD publishes correct fields
# ============================================================================


class TestXADDPublishing:
    """AC1: ProgressTracker._publish_to_redis() uses XADD with correct fields."""

    @pytest.mark.asyncio
    async def test_xadd_stores_stage_progress_message_detail(self):
        """AC1: Each stream entry has stage, progress, message, detail_json fields."""
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")
        mock_redis.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            tracker = ProgressTracker("stream-test-1", uf_count=3, use_redis=True)
            await tracker.emit(
                stage="fetching", progress=30, message="Buscando...",
                uf="SP", items_found=50,
            )

        mock_redis.xadd.assert_called_once()
        args = mock_redis.xadd.call_args
        stream_key = args[0][0]
        fields = args[0][1]

        assert stream_key == "smartlic:progress:stream-test-1:stream"
        assert fields["stage"] == "fetching"
        assert fields["progress"] == "30"
        assert fields["message"] == "Buscando..."
        detail = json.loads(fields["detail_json"])
        assert detail["uf"] == "SP"
        assert detail["items_found"] == 50

    @pytest.mark.asyncio
    async def test_xadd_preserves_correlation_fields(self):
        """AC1: trace_id, search_id, request_id stored when present."""
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("middleware.search_id_var") as mock_sid, \
             patch("middleware.request_id_var") as mock_rid, \
             patch("telemetry.get_trace_id", return_value="trace-abc"):
            mock_sid.get.return_value = "search-xyz"
            mock_rid.get.return_value = "req-123"

            tracker = ProgressTracker("stream-corr", uf_count=1, use_redis=True)
            await tracker.emit(stage="connecting", progress=5, message="Init")

        fields = mock_redis.xadd.call_args[0][1]
        assert fields.get("trace_id") == "trace-abc"
        assert fields.get("search_id") == "search-xyz"
        assert fields.get("request_id") == "req-123"


# ============================================================================
# AC1: EXPIRE set on terminal events
# ============================================================================


class TestStreamExpire:
    """AC1: EXPIRE set on stream key after terminal events."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("terminal_stage", list(_TERMINAL_STAGES))
    async def test_expire_set_on_terminal_event(self, terminal_stage):
        """AC1: EXPIRE called with 300s TTL for each terminal stage."""
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")
        mock_redis.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            tracker = ProgressTracker("stream-expire", uf_count=1, use_redis=True)
            # Manually call _publish_to_redis with terminal event
            event = ProgressEvent(
                stage=terminal_stage, progress=100, message="Terminal"
            )
            await tracker._publish_to_redis(event)

        mock_redis.expire.assert_called_once_with(
            "smartlic:progress:stream-expire:stream",
            _STREAM_EXPIRE_TTL,
        )

    @pytest.mark.asyncio
    async def test_no_expire_on_non_terminal_event(self):
        """AC1: No EXPIRE for non-terminal events like 'fetching'."""
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")
        mock_redis.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            tracker = ProgressTracker("stream-no-expire", uf_count=1, use_redis=True)
            await tracker.emit(stage="fetching", progress=30, message="Working...")

        mock_redis.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_complete_publishes_and_expires(self):
        """STORY-276: emit_complete() now publishes to stream and sets EXPIRE."""
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")
        mock_redis.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            tracker = ProgressTracker("stream-complete", uf_count=1, use_redis=True)
            await tracker.emit_complete()

        # emit_complete should now publish to Redis
        mock_redis.xadd.assert_called_once()
        fields = mock_redis.xadd.call_args[0][1]
        assert fields["stage"] == "complete"
        assert fields["progress"] == "100"
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_error_publishes_and_expires(self):
        """STORY-276: emit_error() now publishes to stream and sets EXPIRE."""
        mock_redis = AsyncMock()
        mock_redis.xadd = AsyncMock(return_value="1-0")
        mock_redis.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            tracker = ProgressTracker("stream-error", uf_count=1, use_redis=True)
            await tracker.emit_error("Connection failed")

        mock_redis.xadd.assert_called_once()
        fields = mock_redis.xadd.call_args[0][1]
        assert fields["stage"] == "error"
        assert fields["progress"] == "-1"
        mock_redis.expire.assert_called_once()


# ============================================================================
# AC3: Fallback in-memory preserved
# ============================================================================


class TestInMemoryFallback:
    """AC3: When Redis unavailable, asyncio.Queue fallback works unchanged."""

    @pytest.mark.asyncio
    async def test_emit_uses_queue_when_redis_unavailable(self, mock_redis_unavailable):
        """AC3: Events go to local queue when Redis is down."""
        tracker = await create_tracker("fallback-1", uf_count=3)

        assert tracker._use_redis is False
        await tracker.emit(stage="fetching", progress=25, message="Local")
        assert tracker.queue.qsize() == 1

        event = await tracker.queue.get()
        assert event.stage == "fetching"
        assert event.progress == 25

    @pytest.mark.asyncio
    async def test_no_xadd_called_without_redis(self, mock_redis_unavailable):
        """AC3: No Redis calls when use_redis=False."""
        tracker = await create_tracker("fallback-2", uf_count=1)
        assert tracker._use_redis is False

        # Mock to verify no Redis calls
        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = None
            await tracker.emit(stage="connecting", progress=5, message="Init")

        # Queue should have the event
        assert tracker.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_complete_flow_without_redis(self, mock_redis_unavailable):
        """AC3: Full lifecycle works without Redis."""
        tracker = await create_tracker("fallback-flow", uf_count=2)

        await tracker.emit(stage="connecting", progress=5, message="Start")
        await tracker.emit_uf_complete("SP", 100)
        await tracker.emit_uf_complete("RJ", 50)
        await tracker.emit(stage="filtering", progress=60, message="Filtering")
        await tracker.emit_complete()

        assert tracker._is_complete is True
        assert tracker.queue.qsize() == 5


# ============================================================================
# AC4: subscribe_to_events removed
# ============================================================================


class TestPubSubRemoved:
    """AC4: subscribe_to_events() and all pub/sub logic eliminated."""

    def test_subscribe_to_events_not_importable(self):
        """AC4: subscribe_to_events no longer exported from progress module."""
        import progress
        assert not hasattr(progress, "subscribe_to_events") or \
            not callable(getattr(progress, "subscribe_to_events", None))

    def test_no_pubsub_in_progress_module(self):
        """AC4: No pubsub references in progress module."""
        import inspect
        import progress
        source = inspect.getsource(progress)
        assert "pubsub" not in source.lower() or "pub/sub" not in source
        assert ".publish(" not in source
        assert ".subscribe(" not in source


# ============================================================================
# AC5: End-to-end cross-worker simulation
# ============================================================================


class TestCrossWorkerE2E:
    """AC5: Simulate tracker on worker A, SSE consumer on worker B."""

    @pytest.mark.asyncio
    async def test_late_subscriber_receives_full_history(self):
        """AC5: XREAD with id=0 replays ALL events from stream beginning.

        Simulates: worker A emits 5 events, worker B connects late and reads all.
        """
        # Simulate stream state: 5 events already in stream
        stream_entries = [
            ("1-0", {"stage": "connecting", "progress": "5", "message": "Init", "detail_json": "{}"}),
            ("2-0", {"stage": "fetching", "progress": "20", "message": "UF 1/3", "detail_json": '{"uf": "SP"}'}),
            ("3-0", {"stage": "fetching", "progress": "35", "message": "UF 2/3", "detail_json": '{"uf": "RJ"}'}),
            ("4-0", {"stage": "filtering", "progress": "60", "message": "Filtering", "detail_json": "{}"}),
            ("5-0", {"stage": "complete", "progress": "100", "message": "Done", "detail_json": "{}"}),
        ]
        stream_key = "smartlic:progress:cross-worker-1:stream"

        mock_redis = AsyncMock()

        async def mock_xread(streams, block=None, count=None):
            last_id = streams[stream_key]
            # Filter entries with ID > last_id
            if last_id == "0":
                return [[stream_key, stream_entries]]
            return None

        mock_redis.xread = mock_xread

        # Simulate: worker B gets tracker from Redis metadata (no local queue)
        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()  # Empty — worker B has no local events

        from main import app
        from auth import require_auth
        app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "t@t.com"}

        try:
            with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
                 patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
                 patch("routes.search.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
                 patch("routes.search.release_sse_connection", new_callable=AsyncMock), \
                 patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/buscar-progress/cross-worker-1")
        finally:
            app.dependency_overrides.pop(require_auth, None)

        assert response.status_code == 200

        # Parse all SSE data events
        data_lines = [
            line for line in response.text.split("\n")
            if line.startswith("data: ")
        ]
        events = [json.loads(line.replace("data: ", "")) for line in data_lines]

        # AC5: ALL 5 events received (zero loss)
        assert len(events) == 5, f"Expected 5 events, got {len(events)}: {events}"
        assert events[0]["stage"] == "connecting"
        assert events[1]["stage"] == "fetching"
        assert events[1]["progress"] == 20
        assert events[2]["stage"] == "fetching"
        assert events[3]["stage"] == "filtering"
        assert events[4]["stage"] == "complete"

    @pytest.mark.asyncio
    async def test_subscriber_receives_events_incrementally(self):
        """AC5: XREAD returns events as they arrive, updating last_id.

        Simulates: subscriber connects, gets first batch, waits, gets second batch.
        """
        stream_key = "smartlic:progress:incremental-1:stream"
        xread_call = 0

        async def mock_xread(streams, block=None, count=None):
            nonlocal xread_call
            xread_call += 1
            last_id = streams[stream_key]

            if xread_call == 1:
                # First call (id=0): return initial events
                return [[stream_key, [
                    ("1-0", {"stage": "connecting", "progress": "5", "message": "Init", "detail_json": "{}"}),
                    ("2-0", {"stage": "fetching", "progress": "30", "message": "Fetching", "detail_json": "{}"}),
                ]]]
            elif xread_call == 2:
                # Second call (id=2-0): return more events
                return [[stream_key, [
                    ("3-0", {"stage": "complete", "progress": "100", "message": "Done", "detail_json": "{}"}),
                ]]]
            return None

        mock_redis = AsyncMock()
        mock_redis.xread = mock_xread

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        from main import app
        from auth import require_auth
        app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "t@t.com"}

        try:
            with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
                 patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
                 patch("routes.search.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
                 patch("routes.search.release_sse_connection", new_callable=AsyncMock), \
                 patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/buscar-progress/incremental-1")
        finally:
            app.dependency_overrides.pop(require_auth, None)

        data_lines = [
            line for line in response.text.split("\n")
            if line.startswith("data: ")
        ]
        events = [json.loads(line.replace("data: ", "")) for line in data_lines]

        assert len(events) == 3
        assert events[0]["stage"] == "connecting"
        assert events[1]["stage"] == "fetching"
        assert events[2]["stage"] == "complete"

    @pytest.mark.asyncio
    async def test_stream_key_cleanup_on_remove(self):
        """AC5: remove_tracker() deletes both metadata and stream keys."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_redis.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=True):
            await create_tracker("cleanup-test", uf_count=2)
            await remove_tracker("cleanup-test")

        mock_redis.delete.assert_called_once_with(
            "smartlic:progress:cleanup-test",
            "smartlic:progress:cleanup-test:stream",
        )

    @pytest.mark.asyncio
    async def test_xread_detail_json_parsed_correctly(self):
        """AC2/AC5: detail_json field in stream entries is parsed back to dict."""
        stream_key = "smartlic:progress:detail-test:stream"
        detail = {"uf": "SP", "items_found": 150, "uf_index": 1, "uf_total": 3}

        async def mock_xread(streams, block=None, count=None):
            return [[stream_key, [
                ("1-0", {
                    "stage": "complete",
                    "progress": "100",
                    "message": "Done",
                    "detail_json": json.dumps(detail),
                }),
            ]]]

        mock_redis = AsyncMock()
        mock_redis.xread = mock_xread

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        from main import app
        from auth import require_auth
        app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "t@t.com"}

        try:
            with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
                 patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
                 patch("routes.search.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
                 patch("routes.search.release_sse_connection", new_callable=AsyncMock), \
                 patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/buscar-progress/detail-test")
        finally:
            app.dependency_overrides.pop(require_auth, None)

        data_lines = [
            line for line in response.text.split("\n")
            if line.startswith("data: ")
        ]
        assert len(data_lines) == 1
        event = json.loads(data_lines[0].replace("data: ", ""))
        assert event["detail"] == detail

    @pytest.mark.asyncio
    async def test_fallback_to_queue_when_redis_down_at_sse(self):
        """AC3: If tracker._use_redis=True but Redis is down at SSE time, fall back to queue."""
        mock_tracker = MagicMock()
        mock_tracker._use_redis = True  # Was redis when created
        mock_tracker.queue = asyncio.Queue()
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done via queue")
        )

        from main import app
        from auth import require_auth
        app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "t@t.com"}

        try:
            with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
                 patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=None), \
                 patch("routes.search.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
                 patch("routes.search.release_sse_connection", new_callable=AsyncMock):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/buscar-progress/fallback-sse")
        finally:
            app.dependency_overrides.pop(require_auth, None)

        assert response.status_code == 200
        assert "Done via queue" in response.text

    @pytest.mark.asyncio
    async def test_multiple_events_with_heartbeats(self):
        """AC2/AC5: Mix of events and heartbeats during streaming."""
        stream_key = "smartlic:progress:heartbeat-mix:stream"
        xread_call = 0

        async def mock_xread(streams, block=None, count=None):
            nonlocal xread_call
            xread_call += 1

            if xread_call == 1:
                return [[stream_key, [
                    ("1-0", {"stage": "connecting", "progress": "5", "message": "Init", "detail_json": "{}"}),
                ]]]
            elif xread_call == 2:
                return None  # Timeout → heartbeat
            elif xread_call == 3:
                return [[stream_key, [
                    ("2-0", {"stage": "complete", "progress": "100", "message": "Done", "detail_json": "{}"}),
                ]]]
            return None

        mock_redis = AsyncMock()
        mock_redis.xread = mock_xread

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        from main import app
        from auth import require_auth
        app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "t@t.com"}

        try:
            with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
                 patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
                 patch("routes.search.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
                 patch("routes.search.release_sse_connection", new_callable=AsyncMock), \
                 patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/buscar-progress/heartbeat-mix")
        finally:
            app.dependency_overrides.pop(require_auth, None)

        assert response.status_code == 200
        assert ": heartbeat" in response.text

        data_lines = [
            line for line in response.text.split("\n")
            if line.startswith("data: ")
        ]
        events = [json.loads(line.replace("data: ", "")) for line in data_lines]
        assert len(events) == 2
        assert events[0]["stage"] == "connecting"
        assert events[1]["stage"] == "complete"
