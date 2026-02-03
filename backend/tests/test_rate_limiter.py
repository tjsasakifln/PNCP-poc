"""Tests for rate limiting system (STORY-165)."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from rate_limiter import RateLimiter


class TestRateLimiterInitialization:
    """Test RateLimiter initialization and Redis connection."""

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_connects_to_redis_when_url_provided(self, mock_redis_module, mock_getenv):
        """Should connect to Redis when REDIS_URL is set."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_client

        limiter = RateLimiter()

        assert limiter.redis_client == mock_redis_client
        mock_redis_client.ping.assert_called_once()

    @patch("rate_limiter.os.getenv")
    def test_uses_in_memory_when_no_redis_url(self, mock_getenv):
        """Should use in-memory store when REDIS_URL not set."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        assert limiter.redis_client is None
        assert isinstance(limiter._memory_store, dict)

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_falls_back_to_memory_on_redis_import_error(self, mock_redis_module, mock_getenv):
        """Should fallback to in-memory if redis library not installed."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_module.from_url.side_effect = ImportError("No module named 'redis'")

        limiter = RateLimiter()

        assert limiter.redis_client is None

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_falls_back_to_memory_on_redis_connection_error(self, mock_redis_module, mock_getenv):
        """Should fallback to in-memory if Redis connection fails."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = Exception("Connection refused")
        mock_redis_module.from_url.return_value = mock_redis_client

        limiter = RateLimiter()

        assert limiter.redis_client is None


class TestRateLimiterRedis:
    """Test rate limiting with Redis backend."""

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_allows_request_within_limit(self, mock_redis_module, mock_getenv):
        """Should allow request when under rate limit."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_client

        # Mock Redis responses
        mock_redis_client.incr.return_value = 5  # 5th request this minute

        limiter = RateLimiter()
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is True
        assert retry_after == 0

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_blocks_request_over_limit(self, mock_redis_module, mock_getenv):
        """Should block request when rate limit exceeded."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_client

        # Mock Redis responses
        mock_redis_client.incr.return_value = 11  # 11th request (over 10 limit)
        mock_redis_client.ttl.return_value = 42  # 42 seconds until reset

        limiter = RateLimiter()
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is False
        assert retry_after == 42

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_sets_ttl_on_first_request(self, mock_redis_module, mock_getenv):
        """Should set 60s TTL on first request of the minute."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_client

        # Mock first request (count = 1)
        mock_redis_client.incr.return_value = 1

        limiter = RateLimiter()
        limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Verify TTL was set
        mock_redis_client.expire.assert_called_once()
        call_args = mock_redis_client.expire.call_args
        assert call_args[0][1] == 60  # 60 seconds TTL

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_fails_open_on_redis_error(self, mock_redis_module, mock_getenv):
        """Should allow request on Redis errors (fail open)."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_client

        # Mock Redis error
        mock_redis_client.incr.side_effect = Exception("Redis timeout")

        limiter = RateLimiter()
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is True  # Fail open
        assert retry_after == 0

    @patch("rate_limiter.os.getenv")
    @patch("rate_limiter.redis")
    def test_uses_minute_granularity_key(self, mock_redis_module, mock_getenv):
        """Should use minute-level keys (YYYY-MM-DDTHH:MM)."""
        mock_getenv.return_value = "redis://localhost:6379"
        mock_redis_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_redis_client.incr.return_value = 1

        with patch("rate_limiter.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 2, 3, 14, 35, 42)

            limiter = RateLimiter()
            limiter.check_rate_limit("user-123", max_requests_per_min=10)

            # Check key format
            call_args = mock_redis_client.incr.call_args
            key = call_args[0][0]
            assert key == "rate_limit:user-123:2026-02-03T14:35"


class TestRateLimiterInMemory:
    """Test rate limiting with in-memory fallback."""

    @patch("rate_limiter.os.getenv")
    def test_allows_request_within_limit_memory(self, mock_getenv):
        """Should allow request when under limit (in-memory)."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        # Make 5 requests (limit is 10)
        for i in range(5):
            allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)
            assert allowed is True
            assert retry_after == 0

    @patch("rate_limiter.os.getenv")
    def test_blocks_request_over_limit_memory(self, mock_getenv):
        """Should block request when limit exceeded (in-memory)."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        # Make 10 requests (at limit)
        for i in range(10):
            limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # 11th request should be blocked
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is False
        assert retry_after > 0  # Should have retry_after value

    @patch("rate_limiter.os.getenv")
    def test_resets_after_60_seconds_memory(self, mock_getenv):
        """Should reset counter after 60 seconds (in-memory)."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        with patch("rate_limiter.datetime") as mock_datetime:
            # First request at T=0
            mock_datetime.utcnow.return_value.timestamp.return_value = 0.0
            mock_datetime.utcnow.return_value.strftime.return_value = "2026-02-03T14:35"

            # Fill the limit (10 requests)
            for i in range(10):
                limiter.check_rate_limit("user-123", max_requests_per_min=10)

            # 11th request should be blocked
            allowed, _ = limiter.check_rate_limit("user-123", max_requests_per_min=10)
            assert allowed is False

            # Advance time by 61 seconds (past 60s window)
            mock_datetime.utcnow.return_value.timestamp.return_value = 61.0
            mock_datetime.utcnow.return_value.strftime.return_value = "2026-02-03T14:36"

            # Should be allowed again (new minute)
            allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)
            assert allowed is True
            assert retry_after == 0

    @patch("rate_limiter.os.getenv")
    def test_different_users_independent_limits_memory(self, mock_getenv):
        """Different users should have independent rate limits (in-memory)."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        # User 1 makes 10 requests (at limit)
        for i in range(10):
            limiter.check_rate_limit("user-1", max_requests_per_min=10)

        # User 1 blocked
        allowed, _ = limiter.check_rate_limit("user-1", max_requests_per_min=10)
        assert allowed is False

        # User 2 should still be allowed
        allowed, _ = limiter.check_rate_limit("user-2", max_requests_per_min=10)
        assert allowed is True

    @patch("rate_limiter.os.getenv")
    def test_cleanup_old_entries_memory(self, mock_getenv):
        """Should cleanup old entries from in-memory store."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        with patch("rate_limiter.datetime") as mock_datetime:
            # Add entry at T=0
            mock_datetime.utcnow.return_value.timestamp.return_value = 0.0
            mock_datetime.utcnow.return_value.strftime.return_value = "2026-02-03T14:35"
            limiter.check_rate_limit("user-old", max_requests_per_min=10)

            # Advance time by 120 seconds (way past expiry)
            mock_datetime.utcnow.return_value.timestamp.return_value = 120.0
            mock_datetime.utcnow.return_value.strftime.return_value = "2026-02-03T14:37"

            # Add new entry (should trigger cleanup)
            limiter.check_rate_limit("user-new", max_requests_per_min=10)

            # Old entry should be cleaned up (not in store anymore)
            old_key = "rate_limit:user-old:2026-02-03T14:35"
            assert old_key not in limiter._memory_store

    @patch("rate_limiter.os.getenv")
    def test_calculates_retry_after_correctly_memory(self, mock_getenv):
        """Should calculate retry_after as remaining time in window (in-memory)."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        with patch("rate_limiter.datetime") as mock_datetime:
            # Start at T=0
            mock_datetime.utcnow.return_value.timestamp.return_value = 0.0
            mock_datetime.utcnow.return_value.strftime.return_value = "2026-02-03T14:35"

            # Fill limit
            for i in range(10):
                limiter.check_rate_limit("user-123", max_requests_per_min=10)

            # Advance to T=20 (40 seconds remaining in window)
            mock_datetime.utcnow.return_value.timestamp.return_value = 20.0

            # Next request should be blocked with ~40s retry_after
            allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

            assert allowed is False
            assert 39 <= retry_after <= 40  # Allow for rounding


class TestRateLimiterEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("rate_limiter.os.getenv")
    def test_handles_zero_limit(self, mock_getenv):
        """Should handle edge case of max_requests_per_min=0."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        # Even first request should be blocked
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=0)

        assert allowed is False
        assert retry_after > 0

    @patch("rate_limiter.os.getenv")
    def test_handles_very_high_limit(self, mock_getenv):
        """Should handle very high limits (e.g., 1000 req/min)."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        # Should allow many requests
        for i in range(500):
            allowed, _ = limiter.check_rate_limit("user-123", max_requests_per_min=1000)
            assert allowed is True

    @patch("rate_limiter.os.getenv")
    def test_retry_after_never_negative(self, mock_getenv):
        """retry_after should never be negative."""
        mock_getenv.return_value = None

        limiter = RateLimiter()

        # Fill limit
        for i in range(10):
            limiter.check_rate_limit("user-123", max_requests_per_min=10)

        # Block next request
        allowed, retry_after = limiter.check_rate_limit("user-123", max_requests_per_min=10)

        assert allowed is False
        assert retry_after >= 1  # Should be at least 1 second
