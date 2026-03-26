"""STORY-332 AC6: Tests for Redis fallback observability.

Covers:
  - AC1: smartlic_redis_available gauge (0/1) updated on health checks
  - AC2: smartlic_redis_fallback_duration_seconds gauge
  - AC3: GET /health/cache includes redis_status: "connected" | "fallback"
  - AC5: WARNING log throttled to every 60s when fallback > 5min
  - AC6: Simulate Redis timeout -> verify all metrics

Run from backend/:
    python -m pytest tests/test_redis_fallback_metrics.py -v
"""

import logging
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Pre-mock heavy third-party modules not needed for these tests
for _mod_name in ("openai",):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()

import redis_pool  # noqa: E402
from redis_pool import (  # noqa: E402
    get_redis_pool,
    get_redis_status,
    get_fallback_duration_seconds,
    is_redis_available,
    _mark_redis_connected,
    _update_redis_metrics,
    _emit_fallback_warning_if_needed,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_redis_pool_state():
    """Reset all singleton and tracking state between tests."""
    redis_pool._redis_pool = None
    redis_pool._pool_initialized = False
    redis_pool._fallback_cache = None
    redis_pool._fallback_since = None
    redis_pool._last_fallback_warning = 0.0
    yield
    redis_pool._redis_pool = None
    redis_pool._pool_initialized = False
    redis_pool._fallback_cache = None
    redis_pool._fallback_since = None
    redis_pool._last_fallback_warning = 0.0


# ============================================================================
# AC1: smartlic_redis_available gauge
# ============================================================================

class TestRedisAvailableGauge:
    """AC1: smartlic_redis_available gauge set on connection/fallback."""

    def test_gauge_set_to_0_on_fallback(self):
        """When Redis is unavailable, gauge is set to 0."""
        from metrics import REDIS_AVAILABLE
        with patch.object(REDIS_AVAILABLE, "set") as mock_set:
            _update_redis_metrics(available=False)
            mock_set.assert_called_with(0)

    def test_gauge_set_to_1_on_connected(self):
        """When Redis is available, gauge is set to 1."""
        from metrics import REDIS_AVAILABLE
        with patch.object(REDIS_AVAILABLE, "set") as mock_set:
            _update_redis_metrics(available=True)
            mock_set.assert_called_with(1)

    async def test_gauge_updated_on_get_redis_pool_failure(self, monkeypatch):
        """get_redis_pool() connection failure updates gauge to 0."""
        monkeypatch.setenv("REDIS_URL", "redis://bad-host:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=ConnectionError("refused"))

        from metrics import REDIS_AVAILABLE
        with patch("redis.asyncio.from_url", return_value=mock_client), \
             patch.object(REDIS_AVAILABLE, "set") as mock_set:
            result = await get_redis_pool()

        assert result is None
        mock_set.assert_called_with(0)

    async def test_gauge_updated_on_get_redis_pool_success(self, monkeypatch):
        """get_redis_pool() successful connection updates gauge to 1."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        from metrics import REDIS_AVAILABLE
        with patch("redis.asyncio.from_url", return_value=mock_client), \
             patch.object(REDIS_AVAILABLE, "set") as mock_set:
            result = await get_redis_pool()

        assert result is not None
        mock_set.assert_called_with(1)

    async def test_gauge_updated_on_missing_redis_url(self, monkeypatch):
        """get_redis_pool() without REDIS_URL sets gauge to 0."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        from metrics import REDIS_AVAILABLE
        with patch.object(REDIS_AVAILABLE, "set") as mock_set:
            result = await get_redis_pool()

        assert result is None
        mock_set.assert_called_with(0)


# ============================================================================
# AC2: smartlic_redis_fallback_duration_seconds gauge
# ============================================================================

class TestRedisFallbackDurationGauge:
    """AC2: smartlic_redis_fallback_duration_seconds tracks fallback duration."""

    def test_duration_0_when_connected(self):
        """When Redis is connected, fallback duration is 0."""
        assert get_fallback_duration_seconds() == 0.0

    def test_duration_increases_in_fallback(self):
        """When in fallback, duration increases over time."""
        redis_pool._fallback_since = time.monotonic() - 120  # 2 min ago
        duration = get_fallback_duration_seconds()
        assert 119 < duration < 125  # ~120 seconds with tolerance

    def test_duration_resets_on_reconnect(self):
        """When Redis reconnects, fallback duration resets to 0."""
        redis_pool._fallback_since = time.monotonic() - 300
        _mark_redis_connected()
        assert get_fallback_duration_seconds() == 0.0

    def test_fallback_duration_gauge_set_on_health_check(self):
        """_update_redis_metrics sets REDIS_FALLBACK_DURATION gauge."""
        redis_pool._fallback_since = time.monotonic() - 60  # 1 min fallback

        from metrics import REDIS_FALLBACK_DURATION
        with patch.object(REDIS_FALLBACK_DURATION, "set") as mock_set:
            _update_redis_metrics(available=False)
            args = mock_set.call_args[0]
            assert 58 < args[0] < 65  # ~60 seconds

    def test_fallback_duration_gauge_0_when_available(self):
        """_update_redis_metrics sets duration to 0 when Redis is up."""
        from metrics import REDIS_FALLBACK_DURATION
        with patch.object(REDIS_FALLBACK_DURATION, "set") as mock_set:
            _update_redis_metrics(available=True)
            mock_set.assert_called_with(0)


# ============================================================================
# AC3: redis_status in /health/cache response
# ============================================================================

class TestRedisStatusField:
    """AC3: get_redis_status() returns 'connected' or 'fallback'."""

    def test_status_fallback_when_no_pool(self):
        """When _redis_pool is None, status is 'fallback'."""
        redis_pool._redis_pool = None
        assert get_redis_status() == "fallback"

    def test_status_connected_when_pool_exists(self):
        """When _redis_pool exists, status is 'connected'."""
        redis_pool._redis_pool = MagicMock()  # fake pool object
        assert get_redis_status() == "connected"

    def test_status_fallback_after_connection_failure(self, monkeypatch):
        """After connection failure sets _redis_pool=None, status is 'fallback'."""
        redis_pool._redis_pool = None
        redis_pool._pool_initialized = True
        assert get_redis_status() == "fallback"


# ============================================================================
# AC3: /health/cache endpoint integration
# ============================================================================

class TestHealthCacheEndpoint:
    """AC3: /health/cache response includes redis_status."""

    async def test_health_cache_includes_redis_status_fallback(self):
        """Health endpoint includes redis_status='fallback' when no Redis."""
        redis_pool._redis_pool = None
        redis_pool._pool_initialized = True
        redis_pool._fallback_since = time.monotonic() - 30

        from routes.health import _check_redis_cache
        result = _check_redis_cache()

        assert "redis_status" in result
        assert result["redis_status"] == "fallback"
        assert "fallback_duration_seconds" in result
        assert result["fallback_duration_seconds"] > 0

    async def test_health_cache_includes_redis_status_connected(self):
        """Health endpoint includes redis_status='connected' when Redis is up."""
        redis_pool._redis_pool = MagicMock()
        redis_pool._pool_initialized = True

        from routes.health import _check_redis_cache
        result = _check_redis_cache()

        assert "redis_status" in result
        assert result["redis_status"] == "connected"
        assert "fallback_duration_seconds" not in result

    async def test_health_cache_no_fallback_duration_when_connected(self):
        """Connected state should not include fallback_duration_seconds."""
        redis_pool._redis_pool = MagicMock()
        redis_pool._pool_initialized = True

        from routes.health import _check_redis_cache
        result = _check_redis_cache()

        assert "fallback_duration_seconds" not in result


# ============================================================================
# AC5: Periodic WARNING log when fallback > 5min
# ============================================================================

class TestFallbackWarningLog:
    """AC5: WARNING every 60s when fallback > 5min."""

    def test_no_warning_when_connected(self, caplog):
        """No warning emitted when not in fallback."""
        redis_pool._fallback_since = None
        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            _emit_fallback_warning_if_needed()
        assert len(caplog.records) == 0

    def test_no_warning_when_fallback_under_5min(self, caplog):
        """No warning when fallback is less than 5 minutes."""
        redis_pool._fallback_since = time.monotonic() - 200  # 3.3 min
        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            _emit_fallback_warning_if_needed()
        assert len(caplog.records) == 0

    def test_warning_emitted_after_5min(self, caplog):
        """WARNING emitted when fallback exceeds 5 minutes."""
        redis_pool._fallback_since = time.monotonic() - 310  # 5min10s
        redis_pool._last_fallback_warning = 0.0
        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            _emit_fallback_warning_if_needed()
        assert len(caplog.records) == 1
        assert "fallback mode" in caplog.records[0].message.lower()

    def test_warning_throttled_to_60s(self, caplog):
        """Second warning within 60s is suppressed."""
        redis_pool._fallback_since = time.monotonic() - 400  # well over 5min
        redis_pool._last_fallback_warning = 0.0

        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            _emit_fallback_warning_if_needed()  # first: emitted
            _emit_fallback_warning_if_needed()  # second: suppressed

        assert len(caplog.records) == 1

    def test_warning_emitted_again_after_interval(self, caplog):
        """Warning emitted again after 60s interval passes."""
        redis_pool._fallback_since = time.monotonic() - 400
        redis_pool._last_fallback_warning = time.monotonic() - 65  # 65s ago

        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            _emit_fallback_warning_if_needed()

        assert len(caplog.records) == 1
        assert "fallback mode" in caplog.records[0].message.lower()

    def test_warning_cleared_on_reconnect(self, caplog):
        """After reconnection, no more fallback warnings."""
        redis_pool._fallback_since = time.monotonic() - 600
        redis_pool._last_fallback_warning = 0.0

        _mark_redis_connected()

        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            _emit_fallback_warning_if_needed()

        assert len(caplog.records) == 0


# ============================================================================
# AC6: Full integration — simulate Redis timeout -> verify metrics
# ============================================================================

class TestRedisTimeoutIntegration:
    """AC6: End-to-end: Redis timeout -> all metrics + status correct."""

    async def test_full_fallback_lifecycle(self, monkeypatch):
        """Simulate: connect -> timeout -> fallback -> reconnect -> verify metrics."""
        # Phase 1: Successful connection
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url", return_value=mock_client):
            pool = await get_redis_pool()

        assert pool is not None
        assert get_redis_status() == "connected"
        assert get_fallback_duration_seconds() == 0.0

        # Phase 2: Redis goes down (ping fails on is_redis_available)
        mock_client.ping = AsyncMock(side_effect=ConnectionError("timeout"))

        available = await is_redis_available()
        assert available is False

        # Phase 3: Verify fallback state
        # Note: is_redis_available doesn't change _redis_pool (it's already initialized)
        # but it does update metrics

        # Phase 4: Simulate full reconnect by resetting state
        redis_pool._redis_pool = None
        redis_pool._pool_initialized = False

        mock_client2 = AsyncMock()
        mock_client2.ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url", return_value=mock_client2):
            pool2 = await get_redis_pool()

        assert pool2 is not None
        assert get_redis_status() == "connected"
        assert get_fallback_duration_seconds() == 0.0

    async def test_fallback_from_missing_url(self, monkeypatch):
        """No REDIS_URL -> immediate fallback with correct metrics."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        pool = await get_redis_pool()

        assert pool is None
        assert get_redis_status() == "fallback"
        assert redis_pool._fallback_since is not None

    async def test_is_redis_available_updates_metrics_on_failure(self, monkeypatch):
        """is_redis_available() calls _update_redis_metrics(False) on failure."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        from metrics import REDIS_AVAILABLE
        with patch.object(REDIS_AVAILABLE, "set") as mock_set:
            result = await is_redis_available()

        assert result is False
        # Should have been called with 0 (at least once from get_redis_pool, once from is_redis_available)
        mock_set.assert_called_with(0)

    async def test_is_redis_available_updates_metrics_on_success(self, monkeypatch):
        """is_redis_available() calls _update_redis_metrics(True) on success."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        from metrics import REDIS_AVAILABLE
        with patch("redis.asyncio.from_url", return_value=mock_client), \
             patch.object(REDIS_AVAILABLE, "set") as mock_set:
            result = await is_redis_available()

        assert result is True
        mock_set.assert_called_with(1)

    async def test_is_redis_available_emits_warning_in_long_fallback(self, monkeypatch, caplog):
        """is_redis_available() emits periodic warning when in long fallback."""
        monkeypatch.delenv("REDIS_URL", raising=False)
        redis_pool._pool_initialized = True  # already known to be unavailable
        redis_pool._fallback_since = time.monotonic() - 400  # >5min
        redis_pool._last_fallback_warning = 0.0

        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            await is_redis_available()

        warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("fallback mode" in msg.lower() for msg in warning_msgs)
