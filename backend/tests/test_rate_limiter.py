"""Tests for rate limiting system (STORY-165)."""

from unittest.mock import patch
from rate_limiter import RateLimiter


class TestRateLimiterInitialization:
    """Test RateLimiter initialization."""

    @patch("rate_limiter.os.getenv")
    def test_uses_in_memory_when_no_redis_url(self, mock_getenv):
        """Should use in-memory when REDIS_URL not set."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        assert limiter.redis_client is None
        assert isinstance(limiter._memory_store, dict)

    @patch("rate_limiter.os.getenv")
    def test_falls_back_to_memory_on_redis_unavailable(self, mock_getenv):
        """Should fall back to memory if Redis connection fails."""
        mock_getenv.return_value = "redis://nonexistent:6379"

        # This will fail to connect but should not raise
        limiter = RateLimiter()

        # Should fallback to None (in-memory mode)
        assert limiter.redis_client is None


class TestRateLimiterInMemory:
    """Test in-memory rate limiting (no Redis)."""

    @patch("rate_limiter.os.getenv")
    def test_allows_request_within_limit_memory(self, mock_getenv):
        """Should allow request when under rate limit."""
        mock_getenv.return_value = None
        limiter = RateLimiter()

        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is True
        assert retry_after == 0

    @patch("rate_limiter.os.getenv")
    def test_blocks_request_over_limit_memory(self, mock_getenv):
        """Should block request when rate limit exceeded."""
        mock_getenv.return_value = None
        limiter = RateLimiter()

        # Make 10 requests (at limit)
        for _ in range(10):
            allowed, _ = limiter.check_rate_limit("user-123", max_requests_per_min=10)
            assert allowed is True

        # 11th request should be blocked
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is False
        assert retry_after > 0

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.datetime")
    def test_resets_after_60_seconds_memory(self, mock_datetime, mock_getenv):
        """Should reset counter after 60 seconds."""
        mock_getenv.return_value = None

        # Mock time progression
        from datetime import datetime
        t1 = datetime(2026, 2, 3, 10, 30, 0)
        t2 = datetime(2026, 2, 3, 10, 31, 0)  # 1 minute later

        # Each check_rate_limit() calls utcnow() twice (line 54 + line 82)
        # 10 calls in minute 1 = 20 utcnow() calls
        # 1 call in minute 2 = 2 utcnow() calls
        # Total = 22 utcnow() calls needed
        mock_datetime.utcnow.side_effect = [t1] * 20 + [t2] * 2

        limiter = RateLimiter()

        # Exhaust limit in minute 1
        for _ in range(10):
            limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Next minute (new key) - should be allowed
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is True
        assert retry_after == 0

    @patch("rate_limiter.os.getenv")
    def test_different_users_independent_limits_memory(self, mock_getenv):
        """Different users should have independent rate limits."""
        mock_getenv.return_value = None
        limiter = RateLimiter()

        # User 1 makes requests
        for _ in range(5):
            limiter.check_rate_limit("user-1", max_requests_per_min=10)

        # User 2 should have independent limit
        allowed, _ = limiter.check_rate_limit("user-2", max_requests_per_min=10)

        assert allowed is True

    @patch("rate_limiter.os.getenv")
    def test_calculates_retry_after_correctly_memory(self, mock_getenv):
        """Should calculate retry_after based on current time."""
        mock_getenv.return_value = None
        limiter = RateLimiter()

        # Exhaust limit
        for _ in range(10):
            limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Next request should be blocked with retry_after > 0
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is False
        assert 0 < retry_after <= 60


class TestRateLimiterEdgeCases:
    """Test edge cases for rate limiter."""

    @patch("rate_limiter.os.getenv")
    def test_handles_very_high_limit(self, mock_getenv):
        """Should handle very high limits without issues."""
        mock_getenv.return_value = None
        limiter = RateLimiter()

        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=999999)

        assert allowed is True
        assert retry_after == 0

    @patch("rate_limiter.os.getenv")
    def test_retry_after_never_negative(self, mock_getenv):
        """Retry-after should never be negative."""
        mock_getenv.return_value = None
        limiter = RateLimiter()

        # Exhaust limit
        for _ in range(10):
            limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Check multiple times
        for _ in range(5):
            allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)
            assert retry_after >= 0
