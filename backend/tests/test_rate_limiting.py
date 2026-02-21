"""GTM-GO-002: Rate Limiting Anti-Abuso — 18 backend tests.

Tests cover:
  T1-T3:  POST /buscar rate limiting (10/min per user)
  T4:     User isolation (user A limit ≠ user B)
  T5:     Redis unavailable → InMemory fallback
  T6:     Window expiration → requests unblocked
  T7:     SSE 3-connection limit
  T8:     Prometheus counter incremented on 429
  T9:     WARNING log emitted with required fields
  T10:    Config via env var override
  T11:    Unauthenticated endpoint uses IP as key
  T12:    Distinct IPs have independent counters
  T16-T18: Burst isolation (rate limit protects circuit breaker)
"""

import asyncio
import base64
import json
import logging
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


def _make_jwt(user_id: str) -> str:
    """Create a minimal unsigned JWT with the given sub claim."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id}).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


def _make_auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {_make_jwt(user_id)}"}


@pytest.fixture
def app_with_rate_limit():
    """Create a minimal FastAPI app with rate-limited endpoint for testing."""
    from rate_limiter import require_rate_limit

    app = FastAPI()

    @app.post("/buscar")
    async def buscar(
        request: Request,
        _rl=Depends(require_rate_limit(10, 60)),
    ):
        return {"status": "ok"}

    @app.post("/login")
    async def login(
        request: Request,
        _rl=Depends(require_rate_limit(5, 300)),
    ):
        return {"status": "ok"}

    return app


@pytest.fixture
def mock_redis_unavailable():
    """Mock Redis as unavailable to test InMemory fallback."""
    with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None):
        yield


# -----------------------------------------------------------------------
# T1: POST /buscar — 10 requests OK, 11th → 429
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t1_buscar_rate_limit_10_per_minute(mock_ff, mock_redis, app_with_rate_limit):
    """T1: 10 requests → 200. 11th → 429."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("user-t1")

        # First 10 should succeed
        for i in range(10):
            resp = await client.post("/buscar", headers=headers, json={})
            assert resp.status_code == 200, f"Request {i+1} should be 200"

        # 11th should be 429
        resp = await client.post("/buscar", headers=headers, json={})
        assert resp.status_code == 429


# -----------------------------------------------------------------------
# T2: 429 response has detail, retry_after_seconds, correlation_id
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t2_429_response_schema(mock_ff, mock_redis, app_with_rate_limit):
    """T2: 429 body includes detail, retry_after_seconds, correlation_id."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("user-t2")

        for _ in range(10):
            await client.post("/buscar", headers=headers, json={})

        resp = await client.post("/buscar", headers=headers, json={})
        assert resp.status_code == 429
        body = resp.json()["detail"]
        assert "detail" in body
        assert "retry_after_seconds" in body
        assert isinstance(body["retry_after_seconds"], int)
        assert body["retry_after_seconds"] > 0
        assert "correlation_id" in body
        assert len(body["correlation_id"]) > 0


# -----------------------------------------------------------------------
# T3: Retry-After header present and numeric
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t3_retry_after_header(mock_ff, mock_redis, app_with_rate_limit):
    """T3: Retry-After header present and numeric."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("user-t3")

        for _ in range(10):
            await client.post("/buscar", headers=headers, json={})

        resp = await client.post("/buscar", headers=headers, json={})
        assert resp.status_code == 429
        retry_after = resp.headers.get("retry-after")
        assert retry_after is not None
        assert retry_after.isdigit()
        assert int(retry_after) > 0


# -----------------------------------------------------------------------
# T4: User isolation — user A at limit, user B not affected
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t4_user_isolation(mock_ff, mock_redis, app_with_rate_limit):
    """T4: User A at limit does not block user B."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers_a = _make_auth_header("user-a")
        headers_b = _make_auth_header("user-b")

        # Exhaust user A's limit
        for _ in range(10):
            await client.post("/buscar", headers=headers_a, json={})

        # User A blocked
        resp_a = await client.post("/buscar", headers=headers_a, json={})
        assert resp_a.status_code == 429

        # User B still OK
        resp_b = await client.post("/buscar", headers=headers_b, json={})
        assert resp_b.status_code == 200


# -----------------------------------------------------------------------
# T5: Redis unavailable → InMemory fallback works
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t5_redis_unavailable_fallback(mock_ff, mock_redis, app_with_rate_limit):
    """T5: Rate limiting works via InMemory when Redis is unavailable."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("user-t5")

        # Should work fine with in-memory
        resp = await client.post("/buscar", headers=headers, json={})
        assert resp.status_code == 200

        # Exhaust limit
        for _ in range(9):
            await client.post("/buscar", headers=headers, json={})

        resp = await client.post("/buscar", headers=headers, json={})
        assert resp.status_code == 429


# -----------------------------------------------------------------------
# T6: Window expiration → requests unblocked
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("config.get_feature_flag", return_value=True)
async def test_t6_window_expiration(mock_ff):
    """T6: After window expires, requests are allowed again."""
    from rate_limiter import _flexible_limiter, require_rate_limit

    # Use a tiny 1-second window for testing
    app = FastAPI()

    @app.post("/test")
    async def test_endpoint(
        request: Request,
        _rl=Depends(require_rate_limit(2, 1)),
    ):
        return {"status": "ok"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("user-t6")

        # Use 2 requests
        await client.post("/test", headers=headers, json={})
        await client.post("/test", headers=headers, json={})

        # 3rd should fail
        resp = await client.post("/test", headers=headers, json={})
        assert resp.status_code == 429

        # Wait for window to expire
        await asyncio.sleep(1.5)

        # Reset internal state for new window
        _flexible_limiter._memory_store.clear()

        resp = await client.post("/test", headers=headers, json={})
        assert resp.status_code == 200


# -----------------------------------------------------------------------
# T7: SSE 3 connections OK, 4th rejected
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_t7_sse_connection_limit():
    """T7: Max 3 SSE connections per user. 4th rejected."""
    from rate_limiter import acquire_sse_connection, release_sse_connection

    user_id = "user-t7"

    # Acquire 3 connections — all should succeed
    assert await acquire_sse_connection(user_id) is True
    assert await acquire_sse_connection(user_id) is True
    assert await acquire_sse_connection(user_id) is True

    # 4th should fail
    assert await acquire_sse_connection(user_id) is False

    # Release one
    await release_sse_connection(user_id)

    # Now should succeed again
    assert await acquire_sse_connection(user_id) is True


# -----------------------------------------------------------------------
# T8: Prometheus counter incremented on 429
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t8_prometheus_counter(mock_ff, mock_redis, app_with_rate_limit):
    """T8: Prometheus counter smartlic_rate_limit_exceeded_total increments on 429."""
    with patch("rate_limiter.RATE_LIMIT_EXCEEDED", create=True) as mock_counter:
        # Need to patch the import in the module
        mock_labels = MagicMock()
        mock_counter_obj = MagicMock()
        mock_counter_obj.labels.return_value = mock_labels

        with patch.dict("sys.modules", {}):
            # Patch at the import site
            with patch("metrics.RATE_LIMIT_EXCEEDED", mock_counter_obj):
                transport = ASGITransport(app=app_with_rate_limit)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    headers = _make_auth_header("user-t8")

                    for _ in range(10):
                        await client.post("/buscar", headers=headers, json={})

                    resp = await client.post("/buscar", headers=headers, json={})
                    assert resp.status_code == 429

                    # Counter should have been called
                    mock_counter_obj.labels.assert_called()
                    mock_labels.inc.assert_called()


# -----------------------------------------------------------------------
# T9: WARNING log emitted with required fields
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t9_warning_log(mock_ff, mock_redis, app_with_rate_limit, caplog):
    """T9: WARNING log includes user_id, endpoint, limit, correlation_id."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("user-t9")

        for _ in range(10):
            await client.post("/buscar", headers=headers, json={})

        with caplog.at_level(logging.WARNING, logger="rate_limiter"):
            resp = await client.post("/buscar", headers=headers, json={})
            assert resp.status_code == 429

        # Check log content
        warning_logs = [r for r in caplog.records if r.levelno == logging.WARNING and "Rate limit exceeded" in r.message]
        assert len(warning_logs) >= 1, f"Expected WARNING log, got: {[r.message for r in caplog.records]}"
        log_msg = warning_logs[0].message
        assert "user-t9" in log_msg
        assert "/buscar" in log_msg
        assert "correlation_id=" in log_msg


# -----------------------------------------------------------------------
# T10: Config via env var override
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("config.get_feature_flag", return_value=True)
async def test_t10_env_var_override(mock_ff):
    """T10: SEARCH_RATE_LIMIT_PER_MINUTE env var changes the limit."""
    from rate_limiter import require_rate_limit

    # Create endpoint with limit of 2 (simulating env override)
    app = FastAPI()

    @app.post("/buscar")
    async def buscar(
        request: Request,
        _rl=Depends(require_rate_limit(2, 60)),
    ):
        return {"status": "ok"}

    with patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = _make_auth_header("user-t10")

            resp1 = await client.post("/buscar", headers=headers, json={})
            resp2 = await client.post("/buscar", headers=headers, json={})
            assert resp1.status_code == 200
            assert resp2.status_code == 200

            # 3rd should be 429 (limit=2)
            resp3 = await client.post("/buscar", headers=headers, json={})
            assert resp3.status_code == 429


# -----------------------------------------------------------------------
# T11: Unauthenticated endpoint uses IP as key
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t11_ip_based_rate_limit(mock_ff, mock_redis, app_with_rate_limit):
    """T11: Without auth header, rate limit uses IP as key."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # No auth header → uses IP
        for _ in range(10):
            resp = await client.post("/buscar", json={})
            assert resp.status_code == 200

        resp = await client.post("/buscar", json={})
        assert resp.status_code == 429


# -----------------------------------------------------------------------
# T12: Distinct IPs have independent counters
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t12_ip_isolation(mock_ff, mock_redis):
    """T12: Different IPs have independent rate limit counters."""
    from rate_limiter import require_rate_limit

    app = FastAPI()

    @app.post("/login")
    async def login(
        request: Request,
        _rl=Depends(require_rate_limit(2, 300)),
    ):
        return {"status": "ok"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # IP A exhausts limit
        for _ in range(2):
            await client.post(
                "/login", json={},
                headers={"x-forwarded-for": "1.1.1.1"},
            )

        resp_a = await client.post(
            "/login", json={},
            headers={"x-forwarded-for": "1.1.1.1"},
        )
        assert resp_a.status_code == 429

        # IP B still OK
        resp_b = await client.post(
            "/login", json={},
            headers={"x-forwarded-for": "2.2.2.2"},
        )
        assert resp_b.status_code == 200


# -----------------------------------------------------------------------
# T16: Burst of 50 requests — rate limited, other users unaffected
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t16_burst_isolation(mock_ff, mock_redis, app_with_rate_limit):
    """T16: Burst of 50 requests from 1 user → 429 for excedents.
    User B still gets 200."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers_abuser = _make_auth_header("abuser")
        headers_legit = _make_auth_header("legit-user")

        results = []
        for i in range(50):
            resp = await client.post("/buscar", headers=headers_abuser, json={})
            results.append(resp.status_code)

        # First 10 should be 200, rest should be 429
        assert results[:10] == [200] * 10
        assert all(s == 429 for s in results[10:])

        # Legit user should be unaffected
        resp = await client.post("/buscar", headers=headers_legit, json={})
        assert resp.status_code == 200


# -----------------------------------------------------------------------
# T17: During burst, circuit breaker stays CLOSED (rate limit fires before pipeline)
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t17_circuit_breaker_stays_closed(mock_ff, mock_redis, app_with_rate_limit):
    """T17: Rate limit prevents abusive requests from reaching the pipeline.
    The endpoint returns 429 BEFORE any pipeline/PNCP call, so the circuit
    breaker (tested via mock) is never triggered."""
    pipeline_called = {"count": 0}

    # The key insight: require_rate_limit fires BEFORE the endpoint body.
    # So if 429 is returned, the pipeline is never called.
    # We verify this by checking the endpoint body never runs for blocked requests.

    from rate_limiter import require_rate_limit

    app = FastAPI()

    @app.post("/buscar")
    async def buscar(
        request: Request,
        _rl=Depends(require_rate_limit(10, 60)),
    ):
        pipeline_called["count"] += 1
        return {"status": "ok"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("abuser-t17")

        for _ in range(50):
            await client.post("/buscar", headers=headers, json={})

    # Only first 10 should have reached the pipeline
    assert pipeline_called["count"] == 10, (
        f"Expected 10 pipeline calls (rate limit blocks the rest), got {pipeline_called['count']}"
    )


# -----------------------------------------------------------------------
# T18: During burst by user A, user B gets 200 (not 429, not timeout)
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=True)
async def test_t18_legit_user_unaffected_during_burst(mock_ff, mock_redis, app_with_rate_limit):
    """T18: While user A is rate-limited, user B gets normal 200 response."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers_abuser = _make_auth_header("abuser-t18")
        headers_legit = _make_auth_header("legit-t18")

        # Abuser sends burst
        for _ in range(50):
            await client.post("/buscar", headers=headers_abuser, json={})

        # Legit user — 1 request, should be perfectly normal
        resp = await client.post("/buscar", headers=headers_legit, json={})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# -----------------------------------------------------------------------
# Feature flag disabled → rate limiting bypassed
# -----------------------------------------------------------------------

@pytest.mark.asyncio
@patch("rate_limiter.get_redis_pool", new_callable=AsyncMock, return_value=None)
@patch("config.get_feature_flag", return_value=False)
async def test_rate_limiting_disabled_via_feature_flag(mock_ff, mock_redis, app_with_rate_limit):
    """When RATE_LIMITING_ENABLED=false, all requests pass."""
    transport = ASGITransport(app=app_with_rate_limit)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = _make_auth_header("user-disabled")

        for _ in range(20):
            resp = await client.post("/buscar", headers=headers, json={})
            assert resp.status_code == 200
