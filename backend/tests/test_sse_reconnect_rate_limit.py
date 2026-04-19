"""HARDEN-020: SSE Reconnect Rate Limit (10/min per user).

Tests:
  T1: Requests within limit are allowed
  T2: 11th request within 60s returns 429 with Retry-After header
  T3: Different users have independent counters
  T4: 429 response body has correct structure (detail, retry_after_seconds, correlation_id)
  T5: WARNING log emitted on rate limit exceeded
  T6: FlexibleRateLimiter allows up to limit, blocks 11th
  T7: FlexibleRateLimiter keys are independent per user
"""

import time

import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_auth():
    """Override auth dependency."""
    from main import app
    from auth import require_auth

    app.dependency_overrides[require_auth] = lambda: {"id": "test-user-rl", "email": "test@test.com"}
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def mock_sse_deps():
    """Mock SSE connection limiter.

    CIG-BE-sse-reconnect-api: the SSE route was extracted from `routes/search.py`
    into `routes/search_sse.py` (a standalone module, not the package
    `routes/search/`). Patch where the symbol is *used*, not where it is
    defined in `rate_limiter`.
    """
    with patch("routes.search_sse.acquire_sse_connection", new_callable=AsyncMock, return_value=True), \
         patch("routes.search_sse.release_sse_connection", new_callable=AsyncMock):
        yield


@pytest.fixture(autouse=True)
def reset_flexible_limiter():
    """Reset the flexible rate limiter memory store between tests."""
    from rate_limiter import _flexible_limiter
    _flexible_limiter._memory_store = {}
    yield
    _flexible_limiter._memory_store = {}


@pytest.fixture(autouse=True)
def disable_redis():
    """Force in-memory rate limiter (no Redis dependency in tests)."""
    with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None):
        yield


def _exhaust_sse_limit(limiter, user_id: str = "test-user-rl", count: int = 10):
    """Pre-fill the in-memory rate limiter to simulate exhausted SSE reconnect limit."""
    window_seconds = 60
    window_id = int(time.time()) // window_seconds
    key = f"rl:sse_reconnect:user:{user_id}:{window_id}"
    limiter._memory_store[key] = (count, time.time())


@pytest.mark.asyncio
class TestSSEReconnectRateLimit:
    """HARDEN-020: SSE reconnect rate limiting — integration tests."""

    async def test_t2_exceeds_limit_returns_429(self, mock_auth, mock_sse_deps):
        """T2: Request after limit exhausted returns 429 with Retry-After header."""
        from main import app
        from rate_limiter import _flexible_limiter

        _exhaust_sse_limit(_flexible_limiter, "test-user-rl", 10)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/v1/buscar-progress/test-search-blocked")
            assert resp.status_code == 429
            assert "Retry-After" in resp.headers
            retry_after = int(resp.headers["Retry-After"])
            assert retry_after >= 1

    async def test_t3_user_isolation(self, mock_sse_deps):
        """T3: User A blocked, User B allowed — independent counters."""
        from main import app
        from auth import require_auth
        from rate_limiter import _flexible_limiter

        # Exhaust limit for user-a only
        _exhaust_sse_limit(_flexible_limiter, "user-a", 10)

        # User A should be blocked (429)
        app.dependency_overrides[require_auth] = lambda: {"id": "user-a", "email": "a@test.com"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp_a = await client.get("/v1/buscar-progress/iso-a-1")
            assert resp_a.status_code == 429

        # User B: also exhaust but with only 5 (below limit of 10)
        _exhaust_sse_limit(_flexible_limiter, "user-b", 5)
        # User B's next request should still be allowed (count=5, will become 6, still < 10)
        # We verify by checking the limiter directly instead of making a streaming request
        allowed, _ = await _flexible_limiter.check_rate_limit(
            "sse_reconnect:user:user-b", 10, 60
        )
        assert allowed

        app.dependency_overrides.pop(require_auth, None)

    async def test_t4_response_body_structure(self, mock_auth, mock_sse_deps):
        """T4: 429 response body has detail, retry_after_seconds, correlation_id."""
        from main import app
        from rate_limiter import _flexible_limiter

        _exhaust_sse_limit(_flexible_limiter, "test-user-rl", 10)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/v1/buscar-progress/body-test")
            assert resp.status_code == 429
            body = resp.json()["detail"]
            assert "retry_after_seconds" in body
            assert body["retry_after_seconds"] >= 1
            assert "correlation_id" in body
            assert "reconex" in body["detail"].lower()

    async def test_t5_warning_log_on_exceeded(self, mock_auth, mock_sse_deps, caplog):
        """T5: WARNING log emitted when rate limit is exceeded."""
        import logging
        from main import app
        from rate_limiter import _flexible_limiter

        _exhaust_sse_limit(_flexible_limiter, "test-user-rl", 10)

        with caplog.at_level(logging.WARNING, logger="routes.search_sse"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.get("/v1/buscar-progress/log-test")

            assert any("HARDEN-020" in record.message for record in caplog.records)


@pytest.mark.asyncio
class TestFlexibleLimiterSSEReconnect:
    """Unit tests for FlexibleRateLimiter with SSE reconnect key pattern."""

    async def test_t6_allows_up_to_limit(self):
        """T6: 10 calls allowed, 11th blocked."""
        from rate_limiter import FlexibleRateLimiter

        limiter = FlexibleRateLimiter()

        for i in range(10):
            allowed, _ = await limiter.check_rate_limit("sse_reconnect:user:u1", 10, 60)
            assert allowed, f"Call {i+1} should be allowed"

        allowed, retry_after = await limiter.check_rate_limit("sse_reconnect:user:u1", 10, 60)
        assert not allowed
        assert retry_after >= 1

    async def test_t7_different_keys_independent(self):
        """T7: Different user keys don't interfere."""
        from rate_limiter import FlexibleRateLimiter

        limiter = FlexibleRateLimiter()

        # Exhaust user1
        for _ in range(10):
            await limiter.check_rate_limit("sse_reconnect:user:u1", 10, 60)

        # user1 blocked
        allowed, _ = await limiter.check_rate_limit("sse_reconnect:user:u1", 10, 60)
        assert not allowed

        # user2 should be unaffected
        allowed, _ = await limiter.check_rate_limit("sse_reconnect:user:u2", 10, 60)
        assert allowed
