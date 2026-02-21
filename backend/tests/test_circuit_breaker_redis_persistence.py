"""Tests for RedisCircuitBreaker persistence and restore logic (GTM-CRIT-005).

AC6: Circuit breaker persists state in Redis after record_failure()
AC7: Circuit breaker restores degraded state from Redis on initialize()
AC8: Circuit breaker with cooldown expired in Redis resets to healthy
AC9: Circuit breaker works normally when Redis unavailable (in-memory fallback)
AC10: Multiple circuit breaker instances (pncp, pcp) use different keys
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pncp_client import (
    RedisCircuitBreaker,
    get_circuit_breaker,
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
# AC6 — Circuit breaker persists state in Redis after record_failure()
# ===========================================================================


class TestAC6PersistState:
    """AC6: Verify state is written to Redis on record_failure."""

    @pytest.mark.asyncio
    async def test_record_failure_writes_to_redis(self):
        """record_failure() increments failures key via Lua script."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[5, 0])

        cb = RedisCircuitBreaker(name="ac6_persist", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_failure()

        # Verify Lua script was called
        mock_redis.eval.assert_called_once()
        call_args = mock_redis.eval.call_args[0]

        # Check keys
        assert call_args[2] == "circuit_breaker:ac6_persist:failures"
        assert call_args[3] == "circuit_breaker:ac6_persist:degraded_until"

        # Check local state synced
        assert cb.consecutive_failures == 5

    @pytest.mark.asyncio
    async def test_record_failure_persists_degraded_state(self):
        """When threshold reached, degraded_until is persisted to Redis."""
        mock_redis = AsyncMock()
        # Lua returns [50, 1] = threshold reached, degraded_until was set
        mock_redis.eval = AsyncMock(return_value=[50, 1])

        cb = RedisCircuitBreaker(name="ac6_degrade", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_failure()

        # Local state reflects degraded
        assert cb.consecutive_failures == 50
        assert cb.degraded_until is not None
        assert cb.is_degraded is True

        # Redis was called
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_success_resets_redis_state(self):
        """record_success() deletes degraded_until and sets failures=0."""
        mock_redis, mock_pipe = _make_mock_redis()

        cb = RedisCircuitBreaker(name="ac6_success", threshold=50, cooldown_seconds=120)
        cb.consecutive_failures = 10
        cb.degraded_until = time.time() + 100

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.record_success()

        # Verify Redis operations
        mock_pipe.set.assert_called_once_with("circuit_breaker:ac6_success:failures", 0)
        mock_pipe.delete.assert_called_once_with("circuit_breaker:ac6_success:degraded_until")
        mock_pipe.execute.assert_called_once()

        # Local state reset
        assert cb.consecutive_failures == 0
        assert cb.degraded_until is None


# ===========================================================================
# AC7 — Circuit breaker restores degraded state from Redis on initialize()
# ===========================================================================


class TestAC7RestoreDegradedState:
    """AC7: initialize() restores state from Redis."""

    @pytest.mark.asyncio
    async def test_initialize_restores_failures(self):
        """initialize() reads failures key and syncs local state."""
        mock_redis, mock_pipe = _make_mock_redis()
        mock_pipe.execute = AsyncMock(return_value=["30", None])

        cb = RedisCircuitBreaker(name="ac7_failures", threshold=50, cooldown_seconds=120)
        assert cb.consecutive_failures == 0  # Initial

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.initialize()

        # Verify Redis was queried
        mock_pipe.get.assert_any_call("circuit_breaker:ac7_failures:failures")
        mock_pipe.get.assert_any_call("circuit_breaker:ac7_failures:degraded_until")

        # Local state restored
        assert cb.consecutive_failures == 30
        assert cb.degraded_until is None
        assert cb.is_degraded is False

    @pytest.mark.asyncio
    async def test_initialize_restores_degraded_state(self):
        """initialize() restores active degraded state."""
        mock_redis, mock_pipe = _make_mock_redis()
        future = time.time() + 100
        mock_pipe.execute = AsyncMock(return_value=["50", str(future)])

        cb = RedisCircuitBreaker(name="ac7_degraded", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.initialize()

        # Local state reflects degraded
        assert cb.consecutive_failures == 50
        assert cb.degraded_until == future
        assert cb.is_degraded is True

    @pytest.mark.asyncio
    async def test_initialize_no_state_in_redis(self):
        """initialize() when Redis has no state leaves local defaults."""
        mock_redis, mock_pipe = _make_mock_redis()
        mock_pipe.execute = AsyncMock(return_value=[None, None])

        cb = RedisCircuitBreaker(name="ac7_empty", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.initialize()

        # Defaults unchanged
        assert cb.consecutive_failures == 0
        assert cb.degraded_until is None
        assert cb.is_degraded is False

    @pytest.mark.asyncio
    async def test_initialize_restores_partial_state(self):
        """initialize() handles case where only failures exist, no degraded_until."""
        mock_redis, mock_pipe = _make_mock_redis()
        mock_pipe.execute = AsyncMock(return_value=["15", None])

        cb = RedisCircuitBreaker(name="ac7_partial", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.initialize()

        assert cb.consecutive_failures == 15
        assert cb.degraded_until is None
        assert cb.is_degraded is False


# ===========================================================================
# AC8 — Circuit breaker with cooldown expired in Redis resets to healthy
# ===========================================================================


class TestAC8ExpiredCooldown:
    """AC8: initialize() detects expired cooldown and resets."""

    @pytest.mark.asyncio
    async def test_initialize_expired_cooldown_resets(self):
        """When degraded_until is in the past, initialize() calls try_recover()."""
        mock_redis, mock_pipe = _make_mock_redis()
        past = time.time() - 10  # Expired 10 seconds ago
        mock_pipe.execute = AsyncMock(return_value=["50", str(past)])

        cb = RedisCircuitBreaker(name="ac8_expired", threshold=50, cooldown_seconds=120)

        # Track try_recover calls
        mock_try_recover = AsyncMock(return_value=True)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            with patch.object(cb, "try_recover", new=mock_try_recover):
                await cb.initialize()

        # Verify try_recover was called
        mock_try_recover.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_expired_cooldown_deletes_redis_keys(self):
        """initialize() detecting expired cooldown triggers try_recover which deletes keys."""
        mock_redis, mock_pipe = _make_mock_redis()
        past = time.time() - 10
        mock_pipe.execute = AsyncMock(return_value=["50", str(past)])

        # Second pipeline for try_recover (after first for initialize)
        mock_pipe_recover = MagicMock()
        mock_pipe_recover.execute = AsyncMock(return_value=[True, True])
        mock_redis.pipeline = MagicMock(side_effect=[mock_pipe, mock_pipe_recover])

        # Mock get for try_recover
        mock_redis.get = AsyncMock(return_value=str(past))

        cb = RedisCircuitBreaker(name="ac8_delete", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.initialize()

        # Verify deletion pipeline was called
        assert mock_pipe_recover.delete.call_count > 0

    @pytest.mark.asyncio
    async def test_initialize_active_cooldown_preserves_state(self):
        """When degraded_until is in the future, state is preserved."""
        mock_redis, mock_pipe = _make_mock_redis()
        future = time.time() + 100
        mock_pipe.execute = AsyncMock(return_value=["50", str(future)])

        cb = RedisCircuitBreaker(name="ac8_active", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.initialize()

        # State preserved
        assert cb.consecutive_failures == 50
        assert cb.degraded_until == future
        assert cb.is_degraded is True


# ===========================================================================
# AC9 — Circuit breaker works when Redis unavailable (in-memory fallback)
# ===========================================================================


class TestAC9RedisUnavailable:
    """AC9: Graceful fallback when Redis unavailable."""

    @pytest.mark.asyncio
    async def test_initialize_no_redis_is_noop(self):
        """initialize() with no Redis is a no-op, local state unchanged."""
        cb = RedisCircuitBreaker(name="ac9_noredis", threshold=50, cooldown_seconds=120)
        cb.consecutive_failures = 5  # Some local state

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=None)):
            await cb.initialize()

        # Local state unchanged
        assert cb.consecutive_failures == 5

    @pytest.mark.asyncio
    async def test_initialize_redis_exception_is_silent(self):
        """initialize() handles Redis exceptions gracefully."""
        mock_redis, mock_pipe = _make_mock_redis()
        mock_pipe.execute = AsyncMock(side_effect=Exception("Redis connection lost"))

        cb = RedisCircuitBreaker(name="ac9_error", threshold=50, cooldown_seconds=120)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await cb.initialize()  # Should not raise

        # Local state at defaults
        assert cb.consecutive_failures == 0
        assert cb.degraded_until is None

    @pytest.mark.asyncio
    async def test_record_failure_fallback_without_redis(self):
        """record_failure() works with local state when Redis unavailable."""
        cb = RedisCircuitBreaker(name="ac9_fallback", threshold=3, cooldown_seconds=10)

        with patch.object(cb, "_get_redis", new=AsyncMock(return_value=None)):
            for _ in range(3):
                await cb.record_failure()

        # Local state updated
        assert cb.consecutive_failures == 3
        assert cb.is_degraded is True


# ===========================================================================
# AC10 — Multiple circuit breaker instances use different keys
# ===========================================================================


class TestAC10MultipleInstances:
    """AC10: pncp and pcp circuit breakers have separate Redis keys."""

    def test_different_instances_different_keys(self):
        """pncp and pcp use different key prefixes."""
        pncp_cb = RedisCircuitBreaker(name="pncp", threshold=50, cooldown_seconds=120)
        pcp_cb = RedisCircuitBreaker(name="pcp", threshold=30, cooldown_seconds=60)

        assert pncp_cb._key_failures == "circuit_breaker:pncp:failures"
        assert pncp_cb._key_degraded == "circuit_breaker:pncp:degraded_until"

        assert pcp_cb._key_failures == "circuit_breaker:pcp:failures"
        assert pcp_cb._key_degraded == "circuit_breaker:pcp:degraded_until"

    @pytest.mark.asyncio
    async def test_pncp_degraded_does_not_affect_pcp(self):
        """Degrading pncp circuit breaker does not affect pcp."""
        pncp_cb = RedisCircuitBreaker(name="pncp", threshold=50, cooldown_seconds=120)
        pcp_cb = RedisCircuitBreaker(name="pcp", threshold=30, cooldown_seconds=60)

        # Mock Redis for pncp only
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[50, 1])

        with patch.object(pncp_cb, "_get_redis", new=AsyncMock(return_value=mock_redis)):
            await pncp_cb.record_failure()

        # pncp is degraded
        assert pncp_cb.is_degraded is True

        # pcp is unaffected (local state)
        assert pcp_cb.is_degraded is False
        assert pcp_cb.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_module_level_singletons_separate(self):
        """get_circuit_breaker('pncp') and ('pcp') are separate instances."""
        pncp = get_circuit_breaker("pncp")
        pcp = get_circuit_breaker("pcp")

        assert pncp is not pcp
        assert pncp.name == "pncp"
        assert pcp.name == "pcp"

        # Operate on pncp
        if isinstance(pncp, RedisCircuitBreaker):
            mock_redis = AsyncMock()
            mock_redis.eval = AsyncMock(return_value=[25, 0])
            with patch.object(pncp, "_get_redis", new=AsyncMock(return_value=mock_redis)):
                await pncp.record_failure()

            assert pncp.consecutive_failures == 25

        # pcp unaffected
        assert pcp.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_initialize_separate_instances(self):
        """initialize() on pncp and pcp reads different keys."""
        pncp_cb = RedisCircuitBreaker(name="pncp", threshold=50, cooldown_seconds=120)
        pcp_cb = RedisCircuitBreaker(name="pcp", threshold=30, cooldown_seconds=60)

        mock_redis_pncp, mock_pipe_pncp = _make_mock_redis()
        mock_pipe_pncp.execute = AsyncMock(return_value=["45", None])

        mock_redis_pcp, mock_pipe_pcp = _make_mock_redis()
        mock_pipe_pcp.execute = AsyncMock(return_value=["10", None])

        with patch.object(pncp_cb, "_get_redis", new=AsyncMock(return_value=mock_redis_pncp)):
            await pncp_cb.initialize()

        with patch.object(pcp_cb, "_get_redis", new=AsyncMock(return_value=mock_redis_pcp)):
            await pcp_cb.initialize()

        # Separate states
        assert pncp_cb.consecutive_failures == 45
        assert pcp_cb.consecutive_failures == 10

        # Verify different keys were queried
        mock_pipe_pncp.get.assert_any_call("circuit_breaker:pncp:failures")
        mock_pipe_pcp.get.assert_any_call("circuit_breaker:pcp:failures")
