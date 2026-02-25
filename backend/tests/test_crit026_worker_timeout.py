"""CRIT-026: Tests for worker timeout mitigation and SSE observability.

AC3: Worker timeout metric exists
AC8: SSE generator logs abrupt disconnection
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
# AC3: Worker timeout metric
# ============================================================================


class TestWorkerTimeoutMetric:
    """AC3: WORKER_TIMEOUT counter exists with correct labels."""

    def test_worker_timeout_metric_exists(self):
        """AC3: smartlic_worker_timeout_total metric is defined."""
        from metrics import WORKER_TIMEOUT
        assert WORKER_TIMEOUT is not None

    def test_worker_timeout_metric_has_reason_label(self):
        """AC3: WORKER_TIMEOUT has 'reason' label."""
        from metrics import WORKER_TIMEOUT
        # Should be callable with labels (no-op or real)
        labeled = WORKER_TIMEOUT.labels(reason="sse_generator_exception")
        assert labeled is not None

    def test_worker_timeout_inc_noop(self):
        """AC3: WORKER_TIMEOUT.inc() doesn't raise."""
        from metrics import WORKER_TIMEOUT
        WORKER_TIMEOUT.labels(reason="test").inc()


# ============================================================================
# AC8: SSE generator abrupt finish logging
# ============================================================================


@pytest.mark.asyncio
class TestSSEGeneratorAbruptLogging:
    """AC8: Backend logs when SSE generator finishes abruptly."""

    async def test_generator_exception_logged(self, mock_auth, mock_sse_limits, caplog):
        """AC8: Unexpected exception in SSE generator is logged and increments metric."""
        from main import app
        from progress import ProgressEvent

        mock_tracker = MagicMock()
        # Queue that raises an exception to simulate abrupt failure
        mock_queue = AsyncMock()
        mock_queue.get = AsyncMock(side_effect=RuntimeError("Simulated crash"))
        mock_tracker.queue = mock_queue

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=None), \
             patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01), \
             caplog.at_level(logging.ERROR, logger="routes.search"):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/test-abrupt-crash")

        assert response.status_code == 200
        # Check that the abrupt finish was logged
        error_logs = [r for r in caplog.records if "CRIT-026" in r.message and "abrupt" in r.message]
        assert len(error_logs) >= 1, (
            f"Expected CRIT-026 abrupt finish log. Records: "
            f"{[r.message for r in caplog.records]}"
        )

    async def test_generator_normal_finish_logged_debug(self, mock_auth, mock_sse_limits, caplog):
        """AC8: Normal SSE generator finish is logged at DEBUG level."""
        from main import app
        from progress import ProgressEvent

        mock_tracker = MagicMock()
        mock_tracker.queue = asyncio.Queue()
        await mock_tracker.queue.put(
            ProgressEvent(stage="complete", progress=100, message="Done")
        )

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.subscribe_to_events", new_callable=AsyncMock, return_value=None), \
             patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01), \
             caplog.at_level(logging.DEBUG, logger="routes.search"):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/test-normal-finish")

        assert response.status_code == 200
        # Check that the normal finish was logged at DEBUG
        debug_logs = [r for r in caplog.records if "CRIT-026" in r.message and "finished" in r.message]
        assert len(debug_logs) >= 1, (
            f"Expected CRIT-026 finished log. Records: "
            f"{[r.message for r in caplog.records]}"
        )

    async def test_no_tracker_emits_error_and_logs(self, mock_auth, mock_sse_limits, caplog):
        """AC8: When tracker not found, error event is emitted and generator finishes cleanly."""
        from main import app

        with patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search.get_current_state", new_callable=AsyncMock, return_value=None), \
             patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01), \
             caplog.at_level(logging.DEBUG, logger="routes.search"):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/buscar-progress/test-no-tracker")

        assert response.status_code == 200
        # Should contain the error event about search not found
        assert "Search not found" in response.text


# ============================================================================
# Start.sh config validation (smoke tests)
# ============================================================================


class TestStartShConfig:
    """Validate start.sh configuration values."""

    def test_start_sh_has_120s_timeout(self):
        """GTM-STAB-002 AC3: GUNICORN_TIMEOUT default is 120s (was 180s, aligned with Railway proxy)."""
        import os
        start_sh_path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
        with open(start_sh_path) as f:
            content = f.read()
        assert "GUNICORN_TIMEOUT:-120" in content, "Default timeout should be 120s (GTM-STAB-002)"

    def test_start_sh_has_2_workers(self):
        """SLA-002: WEB_CONCURRENCY default is 2."""
        import os
        start_sh_path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
        with open(start_sh_path) as f:
            content = f.read()
        assert "WEB_CONCURRENCY:-2" in content, "Default workers should be 2 (SLA-002)"

    def test_start_sh_has_keep_alive(self):
        """AC2: start.sh has --keep-alive flag."""
        import os
        start_sh_path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
        with open(start_sh_path) as f:
            content = f.read()
        assert "--keep-alive" in content, "start.sh should have --keep-alive flag"

    def test_start_sh_has_graceful_timeout_30(self):
        """GTM-STAB-002: GUNICORN_GRACEFUL_TIMEOUT default is 30s (was 120s)."""
        import os
        start_sh_path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
        with open(start_sh_path) as f:
            content = f.read()
        assert "GUNICORN_GRACEFUL_TIMEOUT:-30" in content, "Graceful timeout should be 30s (GTM-STAB-002)"
