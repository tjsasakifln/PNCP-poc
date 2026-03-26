"""CRIT-048: SSE Pipe Failure Regression — Backend Tests.

AC3: TimeoutError from Redis emits graceful SSE error event
AC4: Supabase polling fallback when Redis timeout
AC5: SSE Redis pool with 60s socket timeout
"""

import asyncio
import json
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
    with patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
         patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):
        yield


# ============================================================================
# AC3: TimeoutError from Redis emits graceful SSE event
# ============================================================================


@pytest.mark.asyncio
class TestRedisTimeoutGraceful:
    """AC3: Redis TimeoutError yields SSE event instead of crashing."""

    async def test_timeout_error_emits_connecting_event(self, mock_auth, mock_sse_limits):
        """AC3: TimeoutError during Redis XREAD emits 'connecting' stage event."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        mock_redis = AsyncMock()
        # First XREAD succeeds, second raises TimeoutError
        mock_redis.xread = AsyncMock(side_effect=TimeoutError("Timeout reading from redis"))

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search_sse.get_search_status", new_callable=AsyncMock, return_value={
                 "status": "completed", "progress": 100, "stage": "complete",
             }), \
             patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/test-timeout-123",
                    headers={"Authorization": "Bearer fake"},
                )
                assert response.status_code == 200

                lines = response.text.strip().split("\n")
                data_lines = [l for l in lines if l.startswith("data:")]  # noqa: E741

                # Should have a 'connecting' event (graceful TimeoutError handling)
                found_connecting = False
                for dl in data_lines:
                    event = json.loads(dl.replace("data: ", ""))
                    if event.get("stage") == "connecting":
                        found_connecting = True
                        assert event["progress"] == -1
                        assert "Reconectando" in event["message"]
                        break
                assert found_connecting, f"Expected 'connecting' event, got: {data_lines}"

    async def test_connection_error_emits_connecting_event(self, mock_auth, mock_sse_limits):
        """AC3: ConnectionError from Redis also triggers graceful handling."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        mock_redis = AsyncMock()
        mock_redis.xread = AsyncMock(side_effect=ConnectionError("Connection refused"))

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search_sse.get_search_status", new_callable=AsyncMock, return_value={
                 "status": "completed", "progress": 100,
             }), \
             patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/test-connrefused-123",
                    headers={"Authorization": "Bearer fake"},
                )
                assert response.status_code == 200

                data_lines = [l for l in response.text.split("\n") if l.startswith("data:")]  # noqa: E741
                events = [json.loads(dl.replace("data: ", "")) for dl in data_lines]
                stages = [e.get("stage") for e in events]
                assert "connecting" in stages

    async def test_timeout_error_increments_metric(self, mock_auth, mock_sse_limits):
        """AC3: SSE_CONNECTION_ERRORS metric incremented with redis_timeout label."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        mock_redis = AsyncMock()
        mock_redis.xread = AsyncMock(side_effect=TimeoutError("Timeout"))

        mock_metric = MagicMock()

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search_sse.get_search_status", new_callable=AsyncMock, return_value={
                 "status": "completed", "progress": 100,
             }), \
             patch("metrics.SSE_CONNECTION_ERRORS", mock_metric), \
             patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get(
                    "/v1/buscar-progress/test-metric-123",
                    headers={"Authorization": "Bearer fake"},
                )

            mock_metric.labels.assert_any_call(error_type="redis_timeout", phase="streaming")


# ============================================================================
# AC4: Supabase polling fallback
# ============================================================================


@pytest.mark.asyncio
class TestSupabasePollingFallback:
    """AC4: When Redis times out, SSE falls back to Supabase polling."""

    async def test_supabase_fallback_delivers_terminal_state(self, mock_auth, mock_sse_limits):
        """AC4: Supabase polling emits 'complete' when search is done."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        mock_redis = AsyncMock()
        mock_redis.xread = AsyncMock(side_effect=TimeoutError("Timeout"))

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search_sse.get_search_status", new_callable=AsyncMock, return_value={
                 "status": "completed", "progress": 100,
                 "search_id": "test-sb-fallback", "stage": "complete",
             }), \
             patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/test-sb-fallback",
                    headers={"Authorization": "Bearer fake"},
                )
                assert response.status_code == 200

                data_lines = [l for l in response.text.split("\n") if l.startswith("data:")]  # noqa: E741
                events = [json.loads(dl.replace("data: ", "")) for dl in data_lines]

                # Should have terminal 'complete' event from Supabase polling
                terminal_events = [e for e in events if e.get("stage") == "complete"]
                assert len(terminal_events) >= 1
                assert terminal_events[0].get("detail", {}).get("transport") == "supabase_fallback"

    async def test_supabase_fallback_maps_failed_to_error(self, mock_auth, mock_sse_limits):
        """AC4: Supabase 'failed' status maps to SSE 'error' stage."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        mock_redis = AsyncMock()
        mock_redis.xread = AsyncMock(side_effect=TimeoutError("Timeout"))

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search_sse.get_search_status", new_callable=AsyncMock, return_value={
                 "status": "failed", "progress": 0,
             }), \
             patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/test-sb-failed",
                    headers={"Authorization": "Bearer fake"},
                )
                assert response.status_code == 200

                data_lines = [l for l in response.text.split("\n") if l.startswith("data:")]  # noqa: E741
                events = [json.loads(dl.replace("data: ", "")) for dl in data_lines]
                error_events = [e for e in events if e.get("stage") == "error"]
                assert len(error_events) >= 1

    async def test_supabase_fallback_heartbeats(self, mock_auth, mock_sse_limits):
        """AC4: Supabase polling emits heartbeats between polls."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        mock_redis = AsyncMock()
        mock_redis.xread = AsyncMock(side_effect=TimeoutError("Timeout"))

        # Return in-progress first, then completed
        poll_count = 0

        async def mock_get_status(search_id):
            nonlocal poll_count
            poll_count += 1
            if poll_count <= 1:
                return {"status": "searching", "progress": 30}
            return {"status": "completed", "progress": 100}

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search_sse.get_search_status", side_effect=mock_get_status), \
             patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01), \
             patch("asyncio.sleep", new_callable=AsyncMock):  # Skip actual sleep

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/test-sb-heartbeat",
                    headers={"Authorization": "Bearer fake"},
                )
                assert response.status_code == 200

                lines = response.text.split("\n")
                heartbeats = [l for l in lines if l.strip() == ": heartbeat"]  # noqa: E741
                assert len(heartbeats) >= 1


# ============================================================================
# AC5: SSE Redis pool with 60s socket timeout
# ============================================================================


class TestSSERedisPool:
    """AC5: Separate Redis pool for SSE with extended socket timeout."""

    def test_sse_socket_timeout_is_60(self):
        """AC5: SSE_SOCKET_TIMEOUT constant is 60s."""
        from redis_pool import SSE_SOCKET_TIMEOUT
        assert SSE_SOCKET_TIMEOUT == 60

    def test_sse_timeout_exceeds_global(self):
        """AC5: SSE timeout > global pool timeout."""
        from redis_pool import SSE_SOCKET_TIMEOUT, POOL_SOCKET_TIMEOUT
        assert SSE_SOCKET_TIMEOUT > POOL_SOCKET_TIMEOUT

    @pytest.mark.asyncio
    async def test_get_sse_redis_pool_returns_none_without_redis_url(self):
        """AC5: Returns None (or regular pool fallback) when REDIS_URL not set."""
        import redis_pool
        # Reset singleton
        redis_pool._sse_redis_pool = None
        redis_pool._sse_pool_initialized = False

        with patch.dict("os.environ", {}, clear=True), \
             patch.object(redis_pool, "_sse_pool_initialized", False), \
             patch.object(redis_pool, "_sse_redis_pool", None):
            # Force re-evaluation
            redis_pool._sse_pool_initialized = False
            result = await redis_pool.get_sse_redis_pool()
            # Without REDIS_URL, returns None
            assert result is None


# ============================================================================
# AC3+AC4: Circuit breaker also triggers Supabase fallback
# ============================================================================


@pytest.mark.asyncio
class TestCircuitBreakerSupabaseFallback:
    """When generic Redis errors trigger circuit breaker, fall to Supabase."""

    async def test_circuit_breaker_triggers_supabase_fallback(self, mock_auth, mock_sse_limits):
        """AC4: 5 consecutive Redis errors → Supabase polling (not just in-memory)."""
        from main import app

        mock_tracker = MagicMock()
        mock_tracker._use_redis = True
        mock_tracker.queue = asyncio.Queue()

        mock_redis = AsyncMock()
        # Generic error (not TimeoutError) — triggers existing circuit breaker
        mock_redis.xread = AsyncMock(side_effect=RuntimeError("Redis WRONGTYPE"))

        with patch("routes.search_sse.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search_sse.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search_sse.get_search_status", new_callable=AsyncMock, return_value={
                 "status": "completed", "progress": 100,
             }), \
             patch("routes.search_sse._SSE_HEARTBEAT_INTERVAL", 0.01), \
             patch("asyncio.sleep", new_callable=AsyncMock):

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/v1/buscar-progress/test-cb-supabase",
                    headers={"Authorization": "Bearer fake"},
                )
                assert response.status_code == 200

                data_lines = [l for l in response.text.split("\n") if l.startswith("data:")]  # noqa: E741
                events = [json.loads(dl.replace("data: ", "")) for dl in data_lines]

                # Should have 'complete' from Supabase polling
                complete_events = [e for e in events if e.get("stage") == "complete"]
                assert len(complete_events) >= 1
                assert complete_events[0].get("detail", {}).get("transport") == "supabase_fallback"
