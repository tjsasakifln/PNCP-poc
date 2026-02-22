"""CRIT-012: Tests for SSE heartbeat improvements.

AC9: Heartbeat during wait-for-tracker phase
AC10: 15s heartbeat interval in main event loop
AC3: DEBUG telemetry logging for heartbeats
AC8: SSE connection error metric
"""

import asyncio
import json
import logging
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_auth():
    """Override auth dependency."""
    from main import app
    from auth import require_auth
    app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "test@test.com"}
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def mock_sse_limits():
    """Mock SSE connection limiter."""
    with patch("routes.search.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
         patch("routes.search.release_sse_connection", new_callable=AsyncMock):
        yield


# ============================================================================
# AC9: Heartbeat during wait-for-tracker
# ============================================================================


@pytest.mark.asyncio
class TestWaitForTrackerHeartbeat:
    """AC9: SSE sends heartbeats during wait-for-tracker phase."""

    async def test_heartbeat_during_slow_tracker(self, mock_auth, mock_sse_limits):
        """AC9: ': waiting' comments emitted every 5s while tracker is not found."""
        from main import app
        from progress import ProgressEvent

        call_count = 0
        mock_tracker = MagicMock()
        mock_tracker.queue = asyncio.Queue()
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        async def delayed_get_tracker(search_id):
            nonlocal call_count
            call_count += 1
            # Return None for first 25 calls (simulates 12.5s delay)
            if call_count <= 25:
                return None
            return mock_tracker

        with patch("routes.search.get_tracker", side_effect=delayed_get_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=None), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/test-hb-wait")

        assert response.status_code == 200
        lines = response.text.split("\n")
        waiting_lines = [line for line in lines if line.strip() == ": waiting"]
        # At i=10 (5s) and i=20 (10s) = 2 heartbeats
        assert len(waiting_lines) >= 2, (
            f"Expected >=2 waiting heartbeats, got {len(waiting_lines)}. "
            f"Content: {response.text[:300]}"
        )

    async def test_no_heartbeat_immediate_tracker(self, mock_auth, mock_sse_limits):
        """No waiting heartbeats when tracker found immediately."""
        from main import app
        from progress import ProgressEvent

        mock_tracker = MagicMock()
        mock_tracker.queue = asyncio.Queue()
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/test-immediate")

        assert response.status_code == 200
        assert ": waiting" not in response.text

    async def test_error_event_when_no_tracker_no_db(self, mock_auth, mock_sse_limits):
        """CRIT-012: Error SSE event when tracker never appears and no DB state."""
        from main import app

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search.get_current_state", new_callable=AsyncMock, return_value=None), \
             patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("metrics.SSE_CONNECTION_ERRORS") as mock_metric:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/nonexistent")

        assert response.status_code == 200
        # Parse the SSE data event
        data_lines = [line for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(data_lines) >= 1, f"Expected at least one data event. Content: {response.text}"
        event = json.loads(data_lines[0].replace("data: ", ""))
        assert event["stage"] == "error"
        assert "not found" in event["message"].lower()

    async def test_db_state_reconnection(self, mock_auth, mock_sse_limits):
        """AC9: Emit current state from DB when tracker not found but DB has state."""
        from main import app

        mock_db_state = {"to_state": "completed"}

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search.get_current_state", new_callable=AsyncMock, return_value=mock_db_state), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/db-reconnect")

        assert response.status_code == 200
        data_lines = [line for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(data_lines) >= 1
        event = json.loads(data_lines[0].replace("data: ", ""))
        assert event["stage"] == "completed"


# ============================================================================
# AC10: Heartbeat every 15s during main event loop
# ============================================================================


@pytest.mark.asyncio
class TestMainLoopHeartbeat:
    """AC10: Heartbeat every 15s during main event loop."""

    async def test_in_memory_heartbeat_on_timeout(self, mock_auth, mock_sse_limits):
        """AC10: In-memory mode emits heartbeat when queue has no events (timeout)."""
        from main import app
        from progress import ProgressEvent

        mock_tracker = MagicMock()
        mock_tracker.queue = asyncio.Queue()

        get_count = 0

        async def mock_queue_get():
            nonlocal get_count
            get_count += 1
            if get_count == 1:
                # First get: block long enough to trigger timeout
                await asyncio.sleep(999)
            return ProgressEvent(stage="complete", progress=100, message="Done")

        mock_tracker.queue.get = mock_queue_get

        # Use very short heartbeat interval for fast test
        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=None), \
             patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/test-hb-15s")

        assert response.status_code == 200
        assert ": heartbeat" in response.text

    async def test_redis_heartbeat_on_timeout(self, mock_auth, mock_sse_limits):
        """AC10: Redis mode also emits heartbeat on timeout."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker.queue = asyncio.Queue()

        # Mock Redis pubsub
        mock_pubsub = AsyncMock()
        get_msg_count = 0

        async def mock_get_message(**kwargs):
            nonlocal get_msg_count
            get_msg_count += 1
            if get_msg_count == 1:
                # First call: block long enough to trigger timeout
                await asyncio.sleep(999)
            # Second call: return complete event
            return {
                "type": "message",
                "data": json.dumps({
                    "stage": "complete", "progress": 100, "message": "Done"
                }),
            }

        mock_pubsub.get_message = mock_get_message
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=mock_pubsub), \
             patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/test-hb-redis")

        assert response.status_code == 200
        assert ": heartbeat" in response.text

    async def test_heartbeat_interval_is_15s(self):
        """AC2: Verify heartbeat interval constant is 15s (was 30s)."""
        from routes.search import _SSE_HEARTBEAT_INTERVAL
        assert _SSE_HEARTBEAT_INTERVAL == 15.0, (
            f"Expected 15.0s heartbeat interval, got {_SSE_HEARTBEAT_INTERVAL}"
        )


# ============================================================================
# AC3: Heartbeat telemetry logging
# ============================================================================


@pytest.mark.asyncio
class TestHeartbeatTelemetry:
    """AC3: DEBUG telemetry logging for heartbeats."""

    async def test_wait_heartbeat_logged(self, mock_auth, mock_sse_limits, caplog):
        """AC3: Wait-phase heartbeats are logged at DEBUG level."""
        from main import app
        from progress import ProgressEvent

        call_count = 0
        mock_tracker = MagicMock()
        mock_tracker.queue = asyncio.Queue()
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        async def delayed_get_tracker(search_id):
            nonlocal call_count
            call_count += 1
            if call_count <= 15:
                return None
            return mock_tracker

        with patch("routes.search.get_tracker", side_effect=delayed_get_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=None), \
             patch("asyncio.sleep", new_callable=AsyncMock), \
             caplog.at_level(logging.DEBUG, logger="routes.search"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/buscar-progress/test-log")

        heartbeat_logs = [
            r for r in caplog.records
            if "CRIT-012" in r.message and "heartbeat" in r.message.lower()
        ]
        assert len(heartbeat_logs) >= 1, (
            f"Expected CRIT-012 heartbeat log entries. "
            f"All logs: {[r.message for r in caplog.records]}"
        )

    async def test_main_loop_heartbeat_logged(self, mock_auth, mock_sse_limits, caplog):
        """AC3: Main-loop heartbeats are logged at DEBUG level with mode."""
        from main import app
        from progress import ProgressEvent

        mock_tracker = MagicMock()
        mock_tracker.queue = asyncio.Queue()

        get_count = 0

        async def mock_queue_get():
            nonlocal get_count
            get_count += 1
            if get_count == 1:
                await asyncio.sleep(999)
            return ProgressEvent(stage="complete", progress=100, message="Done")

        mock_tracker.queue.get = mock_queue_get

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=None), \
             patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01), \
             caplog.at_level(logging.DEBUG, logger="routes.search"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/buscar-progress/test-log-main")

        heartbeat_logs = [
            r for r in caplog.records
            if "CRIT-012" in r.message and "in-memory" in r.message
        ]
        assert len(heartbeat_logs) >= 1, (
            f"Expected in-memory heartbeat log. "
            f"All logs: {[r.message for r in caplog.records]}"
        )


# ============================================================================
# AC8: SSE connection error metric
# ============================================================================


class TestSSEMetric:
    """AC8: Prometheus metric sse_connection_errors_total."""

    def test_metric_exists(self):
        """AC8: SSE_CONNECTION_ERRORS counter is defined with correct labels."""
        from metrics import SSE_CONNECTION_ERRORS
        assert SSE_CONNECTION_ERRORS is not None
        # Verify it has labels method (Counter or NoopMetric)
        labeled = SSE_CONNECTION_ERRORS.labels(error_type="test", phase="test")
        assert labeled is not None

    def test_metric_labels(self):
        """AC8: Metric has error_type and phase labels."""
        from metrics import SSE_CONNECTION_ERRORS
        # Should not raise when called with correct labels
        SSE_CONNECTION_ERRORS.labels(error_type="cancelled", phase="streaming").inc()
        SSE_CONNECTION_ERRORS.labels(error_type="tracker_not_found", phase="wait").inc()
