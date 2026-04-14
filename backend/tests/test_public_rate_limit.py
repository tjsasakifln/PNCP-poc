"""STORY-2.10 (EPIC-TD-2026Q2 P0): Tests for public endpoint rate limiting.

Covers:
- AC1 rate_limit_public factory + Depends contract
- AC2 X-Forwarded-For last-IP extraction + fallback
- AC3 Prometheus counter + Sentry burst alert (deduped)
- AC4 429 response body + Retry-After header
- Fail-open on unexpected errors
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from public_rate_limit import (
    _burst_counters,
    _extract_ip,
    _last_sentry_alert,
    rate_limit_public,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_burst_state():
    """Zera o tracker de burst entre testes pra não vazar estado."""
    _burst_counters.clear()
    _last_sentry_alert.clear()
    yield
    _burst_counters.clear()
    _last_sentry_alert.clear()


@pytest.fixture
def app_with_rl():
    """App minimalista com endpoint protegido por rate_limit_public."""
    app = FastAPI()

    @app.get(
        "/stats/public",
        dependencies=[
            Depends(
                rate_limit_public(
                    limit_unauth=3,
                    limit_auth=10,
                    endpoint_name="stats_public",
                )
            )
        ],
    )
    async def stats():
        return {"ok": True}

    return app


# ---------------------------------------------------------------------------
# AC2: IP extraction
# ---------------------------------------------------------------------------


def test_extract_ip_prefers_last_xff_ip():
    """XFF '1.1.1.1, 2.2.2.2' → último IP (edge proxy mais confiável)."""
    req = SimpleNamespace(
        headers={"X-Forwarded-For": "1.1.1.1, 2.2.2.2, 3.3.3.3"},
        client=None,
    )
    assert _extract_ip(req) == "3.3.3.3"


def test_extract_ip_single_xff():
    req = SimpleNamespace(
        headers={"X-Forwarded-For": "9.9.9.9"},
        client=None,
    )
    assert _extract_ip(req) == "9.9.9.9"


def test_extract_ip_falls_back_to_client_host():
    req = SimpleNamespace(
        headers={},
        client=SimpleNamespace(host="127.0.0.1"),
    )
    assert _extract_ip(req) == "127.0.0.1"


def test_extract_ip_unknown_when_no_client():
    req = SimpleNamespace(headers={}, client=None)
    assert _extract_ip(req) == "unknown"


def test_extract_ip_lowercase_header_also_works():
    req = SimpleNamespace(
        headers={"x-forwarded-for": "5.5.5.5"},
        client=None,
    )
    assert _extract_ip(req) == "5.5.5.5"


# ---------------------------------------------------------------------------
# AC1 + AC4: 429 after threshold with Retry-After header
# ---------------------------------------------------------------------------


def test_rate_limit_returns_429_after_threshold(app_with_rl):
    """3 reqs allowed, 4th blocked com 429 + Retry-After."""

    async def fake_check(key, limit):
        # Simula 3 allowed, 4a bloqueia com 60s retry
        calls = fake_check.calls
        fake_check.calls = calls + 1
        if calls < 3:
            return (True, 0)
        return (False, 60)

    fake_check.calls = 0

    fake_rl = SimpleNamespace(check_rate_limit=fake_check)

    with patch("public_rate_limit.RATE_LIMIT_HITS" if False else "rate_limiter.rate_limiter", fake_rl):
        client = TestClient(app_with_rl)
        for _ in range(3):
            r = client.get("/stats/public")
            assert r.status_code == 200
        r = client.get("/stats/public")
        assert r.status_code == 429
        body = r.json()
        assert body["detail"]["error"] == "rate_limit_exceeded"
        assert body["detail"]["retry_after_sec"] == 60
        assert body["detail"]["endpoint"] == "stats_public"
        assert r.headers.get("Retry-After") == "60"


def test_rate_limit_allows_when_under_limit(app_with_rl):
    async def fake_check(key, limit):
        return (True, 0)

    fake_rl = SimpleNamespace(check_rate_limit=fake_check)
    with patch("rate_limiter.rate_limiter", fake_rl):
        client = TestClient(app_with_rl)
        r = client.get("/stats/public")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# AC3: Prometheus counter incremented on 429
# ---------------------------------------------------------------------------


def test_rate_limit_increments_prometheus_counter_on_429(app_with_rl):
    async def fake_check(key, limit):
        return (False, 30)

    fake_rl = SimpleNamespace(check_rate_limit=fake_check)

    mock_counter = MagicMock()
    mock_labels = MagicMock()
    mock_counter.labels.return_value = mock_labels

    with patch("rate_limiter.rate_limiter", fake_rl), patch(
        "metrics.RATE_LIMIT_HITS", mock_counter
    ):
        client = TestClient(app_with_rl)
        r = client.get("/stats/public")
        assert r.status_code == 429
        mock_counter.labels.assert_called_once_with(
            endpoint="stats_public", caller_type="ip"
        )
        mock_labels.inc.assert_called_once()


# ---------------------------------------------------------------------------
# AC3: Sentry burst alert (dedup 60s)
# ---------------------------------------------------------------------------


def test_burst_alert_fires_after_100_hits_same_key(app_with_rl):
    """Mesmo caller com >100 hits/min dispara sentry.capture_message 1x (deduped)."""

    async def fake_check(key, limit):
        return (True, 0)  # Sempre allowed, só testando o tracker de burst

    fake_rl = SimpleNamespace(check_rate_limit=fake_check)

    with patch("rate_limiter.rate_limiter", fake_rl), patch(
        "sentry_sdk.capture_message"
    ) as mock_capture:
        client = TestClient(app_with_rl)
        # 101 requests do mesmo IP (TestClient reusa client host)
        for _ in range(101):
            r = client.get("/stats/public")
            assert r.status_code == 200

        # Sentry chamado exatamente 1x (após 100 hits, com dedup 60s)
        assert mock_capture.call_count == 1
        args, kwargs = mock_capture.call_args
        assert "rate_limit_burst" in args[0]
        assert kwargs.get("level") == "warning"


def test_burst_alert_deduped_within_60s(app_with_rl):
    """Bursts consecutivos não re-alertam Sentry dentro de 60s."""
    async def fake_check(key, limit):
        return (True, 0)

    fake_rl = SimpleNamespace(check_rate_limit=fake_check)

    with patch("rate_limiter.rate_limiter", fake_rl), patch(
        "sentry_sdk.capture_message"
    ) as mock_capture:
        client = TestClient(app_with_rl)
        # 150 hits → ainda só 1 alerta
        for _ in range(150):
            client.get("/stats/public")
        assert mock_capture.call_count == 1


# ---------------------------------------------------------------------------
# Fail-open: RateLimiter crash não quebra request
# ---------------------------------------------------------------------------


def test_rate_limit_fails_open_on_limiter_exception(app_with_rl):
    """Se o RateLimiter levantar exceção, request segue (fail-open)."""

    class _BrokenRL:
        async def check_rate_limit(self, key, limit):
            raise RuntimeError("Redis exploded")

    with patch("rate_limiter.rate_limiter", _BrokenRL()):
        client = TestClient(app_with_rl)
        r = client.get("/stats/public")
        assert r.status_code == 200
