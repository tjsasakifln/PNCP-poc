"""Tests for rate limiting system (STORY-165, STORY-217).

STORY-217: RateLimiter.check_rate_limit is now async (uses shared redis_pool).
All tests are async and use pytest-asyncio.
"""

import pytest
from unittest.mock import patch, AsyncMock
from rate_limiter import RateLimiter


class TestRateLimiterInitialization:
    """Test RateLimiter initialization."""

    def test_initializes_with_empty_memory_store(self):
        """Should initialize with empty memory store."""
        limiter = RateLimiter()
        assert isinstance(limiter._memory_store, dict)
        assert len(limiter._memory_store) == 0


class TestRateLimiterInMemory:
    """Test in-memory rate limiting (no Redis / redis_pool returns None)."""

    @pytest.mark.asyncio
    @patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
    async def test_allows_request_within_limit_memory(self, mock_pool):
        """Should allow request when under rate limit."""
        limiter = RateLimiter()

        allowed, retry_after = await limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is True
        assert retry_after == 0

    @pytest.mark.asyncio
    @patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
    async def test_blocks_request_over_limit_memory(self, mock_pool):
        """Should block request when rate limit exceeded."""
        limiter = RateLimiter()

        # Make 10 requests (at limit)
        for _ in range(10):
            allowed, _ = await limiter.check_rate_limit("user-123", max_requests_per_min=10)
            assert allowed is True

        # 11th request should be blocked
        allowed, retry_after = await limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    @patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
    @patch("rate_limiter.datetime")
    async def test_resets_after_60_seconds_memory(self, mock_datetime, mock_pool):
        """Should reset counter after 60 seconds via new minute key."""
        from datetime import datetime, timezone

        t1 = datetime(2026, 2, 3, 10, 30, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 2, 3, 10, 31, 0, tzinfo=timezone.utc)

        # check_rate_limit calls datetime.now(timezone.utc) once for strftime (minute_key)
        # _check_memory calls datetime.now(timezone.utc) once for timestamp
        # So each check = 2 calls to now()
        # 10 calls in minute 1 = 20 calls, 1 call in minute 2 = 2 calls
        mock_datetime.now.side_effect = [t1] * 20 + [t2] * 2
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        limiter = RateLimiter()

        # Exhaust limit in minute 1
        for _ in range(10):
            await limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Next minute (new key) - should be allowed
        allowed, retry_after = await limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is True
        assert retry_after == 0

    @pytest.mark.asyncio
    @patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
    async def test_different_users_independent_limits_memory(self, mock_pool):
        """Different users should have independent rate limits."""
        limiter = RateLimiter()

        # User 1 makes requests
        for _ in range(5):
            await limiter.check_rate_limit("user-1", max_requests_per_min=10)

        # User 2 should have independent limit
        allowed, _ = await limiter.check_rate_limit("user-2", max_requests_per_min=10)

        assert allowed is True

    @pytest.mark.asyncio
    @patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
    async def test_calculates_retry_after_correctly_memory(self, mock_pool):
        """Should calculate retry_after based on current time."""
        limiter = RateLimiter()

        # Exhaust limit
        for _ in range(10):
            await limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Next request should be blocked with retry_after > 0
        allowed, retry_after = await limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is False
        assert 0 < retry_after <= 60


class TestRateLimiterEdgeCases:
    """Test edge cases for rate limiter."""

    @pytest.mark.asyncio
    @patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
    async def test_handles_very_high_limit(self, mock_pool):
        """Should handle very high limits without issues."""
        limiter = RateLimiter()

        allowed, retry_after = await limiter.check_rate_limit("user-123", max_requests_per_min=999999)

        assert allowed is True
        assert retry_after == 0

    @pytest.mark.asyncio
    @patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
    async def test_retry_after_never_negative(self, mock_pool):
        """Retry-after should never be negative."""
        limiter = RateLimiter()

        # Exhaust limit
        for _ in range(10):
            await limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Check multiple times
        for _ in range(5):
            allowed, retry_after = await limiter.check_rate_limit("user-123", max_requests_per_min=10)
            assert retry_after >= 0
