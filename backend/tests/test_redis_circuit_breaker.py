"""Tests for RedisCircuitBreaker (B-06 AC1-AC5, AC8, AC9, AC11, AC12).

Tests use a mock Redis to verify Redis-backed circuit breaker behavior.
When Redis is unavailable, verifies fallback to local PNCPCircuitBreaker.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pncp_client import (
    PNCPCircuitBreaker,
    RedisCircuitBreaker,
    _circuit_breaker,
    _pcp_circuit_breaker,
    get_circuit_breaker,
    USE_REDIS_CIRCUIT_BREAKER,
    CB_REDIS_TTL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_redis():
    """Create a mock Redis client with proper pipeline support.

    In redis.asyncio:
    - redis.pipeline() is SYNC (returns Pipeline object)
    - Pipeline.set(), .delete(), .expire(), .get(), .incr() are SYNC (queue commands)
    - Pipeline.execute() is ASYNC (sends all queued commands)
    """
    mock_redis = AsyncMock()

    mock_pipe = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[True, True, True])
    # pipeline() must be a regular function (not async)
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)

    return mock_redis, mock_pipe


# ===========================================================================
# AC1 — RedisCircuitBreaker has same interface as PNCPCircuitBreaker
# ===========================================================================

class TestAC1Interface:
    """AC1: RedisCircuitBreaker implements all PNCPCircuitBreaker methods."""

    def test_is_subclass(self):
        cb = RedisCircuitBreaker(name="test", threshold=5, cooldown_seconds=10)
        assert isinstance(cb, PNCPCircuitBreaker)

    def test_has_record_failure(self):
        cb = RedisCircuitBreaker()
        assert asyncio.iscoroutinefunction(cb.record_failure)

    def test_has_record_success(self):
        cb = RedisCircuitBreaker()
        assert asyncio.iscoroutinefunction(cb.record_success)

    def test_has_try_recover(self):
        cb = RedisCircuitBreaker()
        assert asyncio.iscoroutinefunction(cb.try_recover)

    def test_has_is_degraded_property(self):
        cb = RedisCircuitBreaker()
        assert not cb.is_degraded

    def test_has_reset(self):
        cb = RedisCircuitBreaker()
        assert callable(cb.reset)

    def test_has_name_threshold_cooldown(self):
        cb = RedisCircuitBreaker(name="test_ac1", threshold=42, cooldown_seconds=99)
        assert cb.name == "test_ac1"
        assert cb.threshold == 42
        assert cb.cooldown_seconds == 99

    def test_has_lock(self):
        cb = RedisCircuitBreaker()
        assert hasattr(cb, "_lock")
        assert isinstance(cb._lock, asyncio.Lock)

    def test_has_redis_specific_attrs(self):
        cb = RedisCircuitBreaker(name="test_attrs")
        assert cb._key_failures == "circuit_breaker:test_attrs:failures"
        assert cb._key_degraded == "circuit_breaker:test_attrs:degraded_until"
        assert cb._ttl == CB_REDIS_TTL

    @pytest.mark.asyncio
    async def test_all_methods_hit_redis(self):
        """Verify operations go to Redis when available."""
        mock_redis, mock_pipe = _make_mock_redis()
        mock_redis.eval = AsyncMock(return_value=[1, 0])
        mock_redis.get = AsyncMock(return_value=None)

        cb = RedisCircuitBreaker(name="test_redis_ops", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_failure()
            mock_redis.eval.assert_called_once()

            await cb.record_success()
            mock_pipe.set.assert_called()
            mock_pipe.delete.assert_called()

            result = await cb.try_recover()
            assert result is True


# ===========================================================================
# AC2 — Shared state between workers
# ===========================================================================

class TestAC2SharedState:
    """AC2: Worker A sets state, Worker B reads it via Redis."""

    @pytest.mark.asyncio
    async def test_worker_b_sees_worker_a_degraded_state(self):
        """Simulate worker A tripping, worker B checking via is_degraded_async."""
        mock_redis = AsyncMock()
        degraded_until = time.time() + 120
        mock_redis.get = AsyncMock(return_value=str(degraded_until))

        cb_worker_b = RedisCircuitBreaker(name="pncp", threshold=50, cooldown_seconds=120)

        with patch.object(cb_worker_b, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            is_deg = await cb_worker_b.is_degraded_async()
            assert is_deg is True
            mock_redis.get.assert_called_with("circuit_breaker:pncp:degraded_until")

    @pytest.mark.asyncio
    async def test_worker_b_sees_healthy_when_no_degraded_key(self):
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        cb = RedisCircuitBreaker(name="pncp")
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            assert await cb.is_degraded_async() is False

    @pytest.mark.asyncio
    async def test_get_state_reflects_redis(self):
        """AC9 depends on this: get_state returns Redis-backed data."""
        mock_redis, mock_pipe = _make_mock_redis()
        mock_pipe.execute = AsyncMock(return_value=["30", None])

        cb = RedisCircuitBreaker(name="pncp", threshold=50)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            state = await cb.get_state()
            assert state["failures"] == 30
            assert state["degraded"] is False
            assert state["backend"] == "redis"


# ===========================================================================
# AC3 — record_failure atomic via Redis
# ===========================================================================

class TestAC3AtomicFailure:
    """AC3: record_failure uses INCR atomically."""

    @pytest.mark.asyncio
    async def test_failure_increments_via_lua_script(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[5, 0])

        cb = RedisCircuitBreaker(name="ac3", threshold=50, cooldown_seconds=120)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_failure()

        mock_redis.eval.assert_called_once()
        call_args = mock_redis.eval.call_args
        assert call_args[0][1] == 2  # numkeys
        assert "circuit_breaker:ac3:failures" in call_args[0][2]
        assert "circuit_breaker:ac3:degraded_until" in call_args[0][3]
        assert cb.consecutive_failures == 5

    @pytest.mark.asyncio
    async def test_failure_trips_at_threshold(self):
        """Lua returns [50, 1] when threshold reached — trips breaker."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[50, 1])

        cb = RedisCircuitBreaker(name="ac3_trip", threshold=50, cooldown_seconds=120)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_failure()

        assert cb.consecutive_failures == 50
        assert cb.degraded_until is not None
        assert cb.is_degraded is True

    @pytest.mark.asyncio
    async def test_concurrent_failures_are_atomic(self):
        """10 concurrent record_failure calls — Redis INCR ensures no race."""
        call_count = 0

        async def mock_eval(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return [call_count, 0]

        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=mock_eval)

        cb = RedisCircuitBreaker(name="ac3_concurrent", threshold=50)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            tasks = [cb.record_failure() for _ in range(10)]
            await asyncio.gather(*tasks)

        assert call_count == 10
        assert mock_redis.eval.call_count == 10


# ===========================================================================
# AC4 — record_success resets in Redis
# ===========================================================================

class TestAC4SuccessReset:
    """AC4: record_success resets failures and deletes degraded_until."""

    @pytest.mark.asyncio
    async def test_success_resets_redis_state(self):
        mock_redis, mock_pipe = _make_mock_redis()

        cb = RedisCircuitBreaker(name="ac4", threshold=5, cooldown_seconds=10)
        cb.consecutive_failures = 10
        cb.degraded_until = time.time() + 100

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_success()

        mock_pipe.set.assert_called_once_with("circuit_breaker:ac4:failures", 0)
        mock_pipe.expire.assert_called_once()
        mock_pipe.delete.assert_called_once_with("circuit_breaker:ac4:degraded_until")
        mock_pipe.execute.assert_called_once()

        assert cb.consecutive_failures == 0
        assert cb.degraded_until is None


# ===========================================================================
# AC5 — try_recover with TTL automatic
# ===========================================================================

class TestAC5TryRecover:
    """AC5: degraded_until has TTL; after expiry is_degraded returns False."""

    @pytest.mark.asyncio
    async def test_recover_when_key_expired_in_redis(self):
        """Redis TTL expired → key gone → try_recover returns True."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        cb = RedisCircuitBreaker(name="ac5")
        cb.degraded_until = time.time() + 100  # Local thinks still degraded

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            result = await cb.try_recover()
            assert result is True
            assert cb.degraded_until is None

    @pytest.mark.asyncio
    async def test_recover_when_cooldown_expired(self):
        """degraded_until in Redis but timestamp in the past."""
        mock_redis, mock_pipe = _make_mock_redis()
        past = time.time() - 10
        mock_redis.get = AsyncMock(return_value=str(past))

        cb = RedisCircuitBreaker(name="ac5_expired", cooldown_seconds=5)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            result = await cb.try_recover()
            assert result is True
            mock_pipe.delete.assert_called()

    @pytest.mark.asyncio
    async def test_still_degraded_when_cooldown_not_expired(self):
        mock_redis = AsyncMock()
        future = time.time() + 300
        mock_redis.get = AsyncMock(return_value=str(future))

        cb = RedisCircuitBreaker(name="ac5_still")
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            result = await cb.try_recover()
            assert result is False


# ===========================================================================
# AC8 — Fallback to per-worker when Redis unavailable
# ===========================================================================

class TestAC8Fallback:
    """AC8: Falls back to local PNCPCircuitBreaker when Redis unavailable."""

    @pytest.mark.asyncio
    async def test_record_failure_fallback_local(self):
        """When _get_redis returns None, use local state."""
        cb = RedisCircuitBreaker(name="ac8", threshold=5, cooldown_seconds=10)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=None)):
            for _ in range(5):
                await cb.record_failure()
        assert cb.consecutive_failures == 5
        assert cb.is_degraded is True

    @pytest.mark.asyncio
    async def test_record_success_fallback_local(self):
        cb = RedisCircuitBreaker(name="ac8_success", threshold=5)
        cb.consecutive_failures = 5
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=None)):
            await cb.record_success()
        assert cb.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_try_recover_fallback_local(self):
        cb = RedisCircuitBreaker(name="ac8_recover", cooldown_seconds=1)
        cb.degraded_until = time.time() - 1  # Expired
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=None)):
            result = await cb.try_recover()
            assert result is True

    @pytest.mark.asyncio
    async def test_redis_error_falls_back(self):
        """Redis raises exception → graceful fallback to local."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=Exception("Redis connection lost"))

        cb = RedisCircuitBreaker(name="ac8_error", threshold=3, cooldown_seconds=10)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            for _ in range(3):
                await cb.record_failure()
        assert cb.consecutive_failures == 3
        assert cb.is_degraded is True

    def test_singleton_is_redis_when_enabled(self):
        """Module-level singletons use RedisCircuitBreaker when enabled."""
        if USE_REDIS_CIRCUIT_BREAKER:
            assert isinstance(_circuit_breaker, RedisCircuitBreaker)
            assert isinstance(_pcp_circuit_breaker, RedisCircuitBreaker)
        else:
            assert type(_circuit_breaker) is PNCPCircuitBreaker
            assert type(_pcp_circuit_breaker) is PNCPCircuitBreaker


# ===========================================================================
# AC9 — Health endpoint reflects shared state
# ===========================================================================

class TestAC9HealthState:
    """AC9: get_state() returns Redis-backed state."""

    @pytest.mark.asyncio
    async def test_get_state_with_failures(self):
        mock_redis, mock_pipe = _make_mock_redis()
        mock_pipe.execute = AsyncMock(return_value=["30", None])

        cb = RedisCircuitBreaker(name="pncp", threshold=50)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            state = await cb.get_state()
        assert state == {
            "status": "healthy",
            "failures": 30,
            "degraded": False,
            "degraded_until": None,
            "backend": "redis",
        }

    @pytest.mark.asyncio
    async def test_get_state_degraded(self):
        mock_redis, mock_pipe = _make_mock_redis()
        future = time.time() + 120
        mock_pipe.execute = AsyncMock(return_value=["50", str(future)])

        cb = RedisCircuitBreaker(name="pncp", threshold=50)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            state = await cb.get_state()
        assert state["status"] == "degraded"
        assert state["failures"] == 50
        assert state["degraded"] is True
        assert state["backend"] == "redis"

    @pytest.mark.asyncio
    async def test_get_state_fallback_local(self):
        cb = RedisCircuitBreaker(name="pncp")
        cb.consecutive_failures = 5
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=None)):
            state = await cb.get_state()
        assert state["failures"] == 5
        assert state["backend"] == "local"


# ===========================================================================
# AC11 — Zero breaking changes on existing callers
# ===========================================================================

class TestAC11BackwardCompatibility:
    """AC11: Existing callers of get_circuit_breaker() work without changes."""

    def setup_method(self):
        _circuit_breaker.reset()
        _pcp_circuit_breaker.reset()

    def teardown_method(self):
        _circuit_breaker.reset()
        _pcp_circuit_breaker.reset()

    def test_get_circuit_breaker_returns_pncp_singleton(self):
        cb1 = get_circuit_breaker()
        cb2 = get_circuit_breaker("pncp")
        assert cb1 is cb2
        assert cb1 is _circuit_breaker

    def test_get_circuit_breaker_returns_pcp_singleton(self):
        cb = get_circuit_breaker("pcp")
        assert cb is _pcp_circuit_breaker

    def test_pncp_and_pcp_are_separate(self):
        pncp = get_circuit_breaker("pncp")
        pcp = get_circuit_breaker("pcp")
        assert pncp is not pcp
        assert pncp.name == "pncp"
        assert pcp.name == "pcp"

    def test_isinstance_pncp_circuit_breaker(self):
        """Existing isinstance checks still work."""
        cb = get_circuit_breaker()
        assert isinstance(cb, PNCPCircuitBreaker)

    def test_direct_attribute_access(self):
        """Tests that write to consecutive_failures/degraded_until still work."""
        _circuit_breaker.consecutive_failures = 42
        assert _circuit_breaker.consecutive_failures == 42

        _circuit_breaker.degraded_until = time.time() + 100
        assert _circuit_breaker.is_degraded is True

        _circuit_breaker.reset()
        assert _circuit_breaker.consecutive_failures == 0
        assert _circuit_breaker.degraded_until is None
        assert _circuit_breaker.is_degraded is False


# ===========================================================================
# AC12 — TTL protection on Redis keys
# ===========================================================================

class TestAC12TTLProtection:
    """AC12: All Redis keys have TTL max 300s."""

    @pytest.mark.asyncio
    async def test_failure_sets_ttl_on_keys(self):
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 0])

        cb = RedisCircuitBreaker(name="ac12", threshold=50, cooldown_seconds=120)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_failure()

        # Lua script receives TTL as ARGV[4]
        call_args = mock_redis.eval.call_args[0]
        ttl_arg = call_args[7]  # ARGV[4] = 8th positional
        assert int(ttl_arg) == CB_REDIS_TTL

    @pytest.mark.asyncio
    async def test_success_sets_ttl_on_failures_key(self):
        mock_redis, mock_pipe = _make_mock_redis()

        cb = RedisCircuitBreaker(name="ac12_s", threshold=50)
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_success()

        mock_pipe.expire.assert_called_once_with(
            "circuit_breaker:ac12_s:failures", CB_REDIS_TTL
        )

    @pytest.mark.asyncio
    async def test_reset_async_deletes_keys(self):
        mock_redis, mock_pipe = _make_mock_redis()

        cb = RedisCircuitBreaker(name="ac12_r")
        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.reset_async()

        assert mock_pipe.delete.call_count == 2
