"""HARDEN-016: Tests for /health/live and /health/ready endpoints."""
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# AC1: /health/live — pure liveness, always 200
# ---------------------------------------------------------------------------

class TestHealthLive:
    """AC1: /health/live returns 200 if process alive (no dependency checks)."""

    def test_live_returns_200_when_startup_complete(self):
        with patch("startup.state.startup_time", time.monotonic()):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["live"] is True
            assert data["ready"] is True
            assert "uptime_seconds" in data
            assert "process_uptime_seconds" in data

    def test_live_returns_200_before_startup(self):
        """Always 200 even if startup not complete."""
        with patch("startup.state.startup_time", None):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["live"] is True
            assert data["ready"] is False
            assert data["uptime_seconds"] == 0.0

    def test_live_responds_fast(self):
        """No I/O — should respond in <50ms."""
        with patch("startup.state.startup_time", time.monotonic()):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            start = time.monotonic()
            response = client.get("/health/live")
            elapsed_ms = (time.monotonic() - start) * 1000
            assert response.status_code == 200
            assert elapsed_ms < 500  # generous CI margin


# ---------------------------------------------------------------------------
# AC2 + AC4: /health/ready — dependency checks, 200/503
# ---------------------------------------------------------------------------

class TestHealthReady:
    """AC2: /health/ready returns 200 if Redis + Supabase OK, 503 if not."""

    def _mock_redis_ok(self):
        """Helper: Redis pool returns a mock that pings successfully."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        return patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis)

    def _mock_redis_down(self, error="Connection refused"):
        """Helper: Redis pool raises an exception."""
        return patch(
            "redis_pool.get_redis_pool",
            new_callable=AsyncMock,
            side_effect=ConnectionError(error),
        )

    def _mock_redis_none(self):
        """Helper: Redis pool returns None (pool unavailable)."""
        return patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None)

    def _mock_supabase_ok(self):
        """Helper: Supabase query succeeds."""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.limit.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "test"}]
        return patch(
            "supabase_client.sb_execute",
            new_callable=AsyncMock,
            return_value=mock_response,
        ), patch("supabase_client.get_supabase", return_value=mock_sb)

    def _mock_supabase_down(self, error="Connection refused"):
        """Helper: Supabase query raises an exception."""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.limit.return_value = MagicMock()
        return patch(
            "supabase_client.sb_execute",
            new_callable=AsyncMock,
            side_effect=ConnectionError(error),
        ), patch("supabase_client.get_supabase", return_value=mock_sb)

    def test_ready_200_when_all_deps_ok(self):
        """AC2: Returns 200 when Redis + Supabase are both up."""
        with (
            patch("startup.state.startup_time", time.monotonic()),
            self._mock_redis_ok(),
        ):
            sb_exec_patch, sb_get_patch = self._mock_supabase_ok()
            with sb_exec_patch, sb_get_patch:
                from main import app
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get("/health/ready")
                assert response.status_code == 200
                data = response.json()
                assert data["ready"] is True
                assert data["checks"]["redis"]["status"] == "up"
                assert data["checks"]["supabase"]["status"] == "up"
                assert "latency_ms" in data["checks"]["redis"]
                assert "latency_ms" in data["checks"]["supabase"]

    def test_ready_503_when_redis_down(self):
        """AC2/AC7: Returns 503 when Redis is down."""
        with (
            patch("startup.state.startup_time", time.monotonic()),
            self._mock_redis_down(),
        ):
            sb_exec_patch, sb_get_patch = self._mock_supabase_ok()
            with sb_exec_patch, sb_get_patch:
                from main import app
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["ready"] is False
                assert data["checks"]["redis"]["status"] == "down"
                assert "error" in data["checks"]["redis"]
                # Supabase should still be up
                assert data["checks"]["supabase"]["status"] == "up"

    def test_ready_503_when_supabase_down(self):
        """AC2/AC7: Returns 503 when Supabase is down."""
        with (
            patch("startup.state.startup_time", time.monotonic()),
            self._mock_redis_ok(),
        ):
            sb_exec_patch, sb_get_patch = self._mock_supabase_down()
            with sb_exec_patch, sb_get_patch:
                from main import app
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["ready"] is False
                assert data["checks"]["supabase"]["status"] == "down"
                assert "error" in data["checks"]["supabase"]
                # Redis should still be up
                assert data["checks"]["redis"]["status"] == "up"

    def test_ready_503_when_both_deps_down(self):
        """AC7: Returns 503 when both Redis and Supabase are down."""
        with (
            patch("startup.state.startup_time", time.monotonic()),
            self._mock_redis_down(),
        ):
            sb_exec_patch, sb_get_patch = self._mock_supabase_down()
            with sb_exec_patch, sb_get_patch:
                from main import app
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["ready"] is False
                assert data["checks"]["redis"]["status"] == "down"
                assert data["checks"]["supabase"]["status"] == "down"

    def test_ready_503_before_startup(self):
        """AC7: Returns 503 when startup not complete (even if deps ok)."""
        with (
            patch("startup.state.startup_time", None),
            self._mock_redis_ok(),
        ):
            sb_exec_patch, sb_get_patch = self._mock_supabase_ok()
            with sb_exec_patch, sb_get_patch:
                from main import app
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["ready"] is False

    def test_ready_503_when_redis_pool_none(self):
        """AC7: Returns 503 when Redis pool returns None."""
        with (
            patch("startup.state.startup_time", time.monotonic()),
            self._mock_redis_none(),
        ):
            sb_exec_patch, sb_get_patch = self._mock_supabase_ok()
            with sb_exec_patch, sb_get_patch:
                from main import app
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["ready"] is False
                assert data["checks"]["redis"]["status"] == "down"
                assert data["checks"]["redis"]["error"] == "pool unavailable"


# ---------------------------------------------------------------------------
# AC3: Timeout behavior
# ---------------------------------------------------------------------------

class TestHealthReadyTimeouts:
    """AC3: Readiness checks respect individual timeouts."""

    def test_redis_timeout_constant(self):
        """AC3: Redis timeout is 2s."""
        from routes.health_core import _READINESS_REDIS_TIMEOUT_S
        assert _READINESS_REDIS_TIMEOUT_S == 2.0

    def test_supabase_timeout_constant(self):
        """AC3: Supabase timeout is 3s."""
        from routes.health_core import _READINESS_SUPABASE_TIMEOUT_S
        assert _READINESS_SUPABASE_TIMEOUT_S == 3.0

    def test_ready_503_on_redis_timeout(self):
        """AC3/AC7: Redis timeout produces 503 with 'timeout' error."""
        async def slow_redis():
            await asyncio.sleep(10)

        with (
            patch("startup.state.startup_time", time.monotonic()),
            patch("routes.health_core._READINESS_REDIS_TIMEOUT_S", 0.01),
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, side_effect=slow_redis),
        ):
            mock_sb = MagicMock()
            mock_sb.table.return_value.select.return_value.limit.return_value = MagicMock()
            mock_resp = MagicMock()
            mock_resp.data = [{"id": "x"}]
            with (
                patch("supabase_client.sb_execute", new_callable=AsyncMock, return_value=mock_resp),
                patch("supabase_client.get_supabase", return_value=mock_sb),
            ):
                from main import app
                client = TestClient(app, raise_server_exceptions=False)
                response = client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["checks"]["redis"]["status"] == "down"
                assert data["checks"]["redis"]["error"] == "timeout"

    def test_ready_503_on_supabase_timeout(self):
        """AC3/AC7: Supabase timeout produces 503 with 'timeout' error."""
        async def slow_supabase(*args, **kwargs):
            await asyncio.sleep(10)

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.limit.return_value = MagicMock()

        with (
            patch("startup.state.startup_time", time.monotonic()),
            patch("routes.health_core._READINESS_SUPABASE_TIMEOUT_S", 0.01),
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
            patch("supabase_client.sb_execute", new_callable=AsyncMock, side_effect=slow_supabase),
            patch("supabase_client.get_supabase", return_value=mock_sb),
        ):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["checks"]["supabase"]["status"] == "down"
            assert data["checks"]["supabase"]["error"] == "timeout"


# ---------------------------------------------------------------------------
# AC4: Response body details
# ---------------------------------------------------------------------------

class TestHealthReadyResponseBody:
    """AC4: Response body includes details of each check."""

    def test_response_includes_checks_detail(self):
        """AC4: Response has checks dict with status, latency_ms per dependency."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.limit.return_value = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = [{"id": "x"}]

        with (
            patch("startup.state.startup_time", time.monotonic()),
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
            patch("supabase_client.sb_execute", new_callable=AsyncMock, return_value=mock_resp),
            patch("supabase_client.get_supabase", return_value=mock_sb),
        ):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")
            data = response.json()

            assert "checks" in data
            assert "redis" in data["checks"]
            assert "supabase" in data["checks"]

            # Each check has at least status and latency_ms
            for name in ("redis", "supabase"):
                assert "status" in data["checks"][name]
                assert "latency_ms" in data["checks"][name]
                assert isinstance(data["checks"][name]["latency_ms"], int)

            # Top-level fields
            assert "ready" in data
            assert "uptime_seconds" in data


# ---------------------------------------------------------------------------
# AC5: /health backward compatibility
# ---------------------------------------------------------------------------

class TestHealthBackwardCompat:
    """AC5: /health existing endpoint is maintained for backward compatibility."""

    def test_health_endpoint_still_exists(self):
        """AC5: GET /health still returns 200."""
        from main import app
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
