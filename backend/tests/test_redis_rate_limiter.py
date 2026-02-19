"""Tests for RedisRateLimiter (B-06 AC6, AC7, AC10, AC12).

Tests use mock Redis to verify token bucket behavior.
When Redis is unavailable, verifies fail-open behavior.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rate_limiter import RedisRateLimiter, pncp_rate_limiter, pcp_rate_limiter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_redis(token_result=1):
    """Create mock Redis with proper pipeline support."""
    mock_redis = AsyncMock()
    mock_redis.eval = AsyncMock(return_value=token_result)
    # Pipeline: sync methods + async execute
    mock_pipe = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[1, True])
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)
    return mock_redis, mock_pipe


# ===========================================================================
# AC6 — RedisRateLimiter token bucket
# ===========================================================================

class TestAC6TokenBucket:
    """AC6: Token bucket via Redis Lua script."""

    @pytest.mark.asyncio
    async def test_acquire_returns_true_when_token_available(self):
        mock_redis, _ = _make_mock_redis(token_result=1)

        rl = RedisRateLimiter(name="test_ac6", max_tokens=10, refill_rate=10.0)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await rl.acquire()
        assert result is True
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_waits_when_rate_limited(self):
        """When token not available, acquire waits with backoff."""
        call_count = 0

        async def mock_eval(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return 1 if call_count >= 3 else 0

        mock_redis, _ = _make_mock_redis()
        mock_redis.eval = AsyncMock(side_effect=mock_eval)

        rl = RedisRateLimiter(name="test_wait", max_tokens=10, refill_rate=10.0)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            start = time.time()
            result = await rl.acquire(timeout=5.0)
            elapsed = time.time() - start

        assert result is True
        assert call_count == 3
        assert elapsed >= 0.05  # At least one backoff sleep

    @pytest.mark.asyncio
    async def test_acquire_timeout_returns_false(self):
        """When consistently rate limited, acquire returns False after timeout."""
        mock_redis, _ = _make_mock_redis(token_result=0)

        rl = RedisRateLimiter(name="test_timeout", max_tokens=10, refill_rate=10.0)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await rl.acquire(timeout=0.2)
        assert result is False

    @pytest.mark.asyncio
    async def test_lua_script_receives_correct_args(self):
        mock_redis, _ = _make_mock_redis(1)

        rl = RedisRateLimiter(name="test_args", max_tokens=10, refill_rate=10.0)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            await rl.acquire()

        call_args = mock_redis.eval.call_args
        assert call_args[0][1] == 1  # numkeys
        assert call_args[0][2] == "rate_limiter:test_args:bucket"  # KEYS[1]
        assert call_args[0][3] == "10"  # max_tokens
        assert call_args[0][4] == "10.0"  # refill_rate
        assert float(call_args[0][5]) > 0  # timestamp

    @pytest.mark.asyncio
    async def test_request_count_incremented_on_acquire(self):
        mock_redis, mock_pipe = _make_mock_redis(1)

        rl = RedisRateLimiter(name="test_count", max_tokens=10, refill_rate=10.0)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            await rl.acquire()

        mock_pipe.incr.assert_called_once_with("rate_limiter:test_count:requests_count")
        mock_pipe.expire.assert_called_once_with("rate_limiter:test_count:requests_count", 60)

    @pytest.mark.asyncio
    async def test_multiple_acquires_all_tracked(self):
        """Multiple sequential acquires all go through Redis."""
        mock_redis, _ = _make_mock_redis(1)

        rl = RedisRateLimiter(name="test_multi", max_tokens=10, refill_rate=10.0)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            for _ in range(5):
                result = await rl.acquire()
                assert result is True

        assert mock_redis.eval.call_count == 5


# ===========================================================================
# AC6 — Rate limiting correctness (simulated)
# ===========================================================================

class TestAC6RateLimitCorrectness:
    """AC6: From 2 processes, 15 calls in 1s → exactly 10 approved."""

    @pytest.mark.asyncio
    async def test_exact_token_count_simulation(self):
        """Simulate 15 calls where only 10 tokens are available."""
        tokens_granted = 0

        async def mock_eval(*args, **kwargs):
            nonlocal tokens_granted
            if tokens_granted < 10:
                tokens_granted += 1
                return 1
            return 0

        mock_redis, _ = _make_mock_redis()
        mock_redis.eval = AsyncMock(side_effect=mock_eval)

        rl = RedisRateLimiter(name="test_exact", max_tokens=10, refill_rate=10.0)
        results = []
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            for _ in range(15):
                result = await rl.acquire(timeout=0.01)
                results.append(result)

        approved = sum(1 for r in results if r)
        assert approved == 10


# ===========================================================================
# AC7 — Integration with pncp_client
# ===========================================================================

class TestAC7Integration:
    """AC7: RedisRateLimiter is used in pncp_client._rate_limit()."""

    def test_pncp_rate_limiter_exists(self):
        assert pncp_rate_limiter is not None
        assert pncp_rate_limiter.name == "pncp"
        assert pncp_rate_limiter.max_tokens == 10

    def test_pcp_rate_limiter_exists(self):
        assert pcp_rate_limiter is not None
        assert pcp_rate_limiter.name == "pcp"
        assert pcp_rate_limiter.max_tokens == 5

    @pytest.mark.asyncio
    async def test_rate_limiter_called_in_rate_limit_method(self):
        """Verify _rate_limit() calls pncp_rate_limiter.acquire()."""
        from pncp_client import AsyncPNCPClient

        mock_acquire = AsyncMock(return_value=True)

        async with AsyncPNCPClient() as client:
            with patch("rate_limiter.pncp_rate_limiter") as mock_rl:
                mock_rl.acquire = mock_acquire
                await client._rate_limit()

            mock_acquire.assert_called_once_with(timeout=5.0)


# ===========================================================================
# AC8 — Fallback when Redis unavailable
# ===========================================================================

class TestAC8RateLimiterFallback:
    """AC8: Rate limiter returns True (fail-open) when Redis unavailable."""

    @pytest.mark.asyncio
    async def test_no_redis_returns_true(self):
        rl = RedisRateLimiter(name="test_fallback")
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None):
            result = await rl.acquire()
        assert result is True

    @pytest.mark.asyncio
    async def test_redis_error_returns_true(self):
        """Redis exception → fail-open."""
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=Exception("Connection refused"))

        rl = RedisRateLimiter(name="test_error")
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await rl.acquire()
        assert result is True


# ===========================================================================
# AC10 — Rate limiter metrics for health endpoint
# ===========================================================================

class TestAC10Metrics:
    """AC10: get_stats() returns tokens_available and requests_last_minute."""

    @pytest.mark.asyncio
    async def test_stats_from_redis(self):
        mock_redis = AsyncMock()
        mock_redis.hmget = AsyncMock(return_value=["7.5", str(time.time())])
        mock_redis.get = AsyncMock(return_value="42")

        rl = RedisRateLimiter(name="test_stats", max_tokens=10)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            stats = await rl.get_stats()

        assert stats["backend"] == "redis"
        assert stats["tokens_available"] == 7.5
        assert stats["requests_last_minute"] == 42

    @pytest.mark.asyncio
    async def test_stats_no_redis(self):
        rl = RedisRateLimiter(name="test_stats_local")
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None):
            stats = await rl.get_stats()

        assert stats["backend"] == "local"
        assert stats["tokens_available"] is None

    @pytest.mark.asyncio
    async def test_stats_empty_bucket(self):
        mock_redis = AsyncMock()
        mock_redis.hmget = AsyncMock(return_value=[None, None])
        mock_redis.get = AsyncMock(return_value=None)

        rl = RedisRateLimiter(name="test_empty", max_tokens=10)
        with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            stats = await rl.get_stats()

        assert stats["tokens_available"] == 10.0
        assert stats["requests_last_minute"] == 0


# ===========================================================================
# AC12 — TTL on rate limiter keys
# ===========================================================================

class TestAC12RateLimiterTTL:
    """AC12: Lua script sets EXPIRE(key, 60) on every operation."""

    @pytest.mark.asyncio
    async def test_bucket_script_has_expire(self):
        """Verify Lua script contains EXPIRE call."""
        assert "EXPIRE" in RedisRateLimiter._BUCKET_SCRIPT
        assert "60" in RedisRateLimiter._BUCKET_SCRIPT
