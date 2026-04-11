"""STORY-416 AC4: Graceful degradation for read-only endpoints when CB is open.

When the Supabase read CB is OPEN, analytics and sessions endpoints must
return a 200 with empty/default data + ``X-Cache-Status: stale-due-to-cb-open``
header instead of propagating a 503 to the user.

Pipeline already had CB-open handling (ISSUE-038) — this suite verifies the
header was added and the pattern was extended to analytics + sessions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from auth import require_auth


# ---------------------------------------------------------------------------
# Auth stub — returns a fake user dict so we don't need a real Supabase token
# ---------------------------------------------------------------------------

_FAKE_USER = {"id": "test-user-cb-open-0000", "email": "cb-test@example.com"}


@pytest.fixture(autouse=True)
def _stub_auth() -> None:
    app.dependency_overrides[require_auth] = lambda: _FAKE_USER
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cb_open_side_effect(*args, **kwargs):
    from supabase_client import CircuitBreakerOpenError
    raise CircuitBreakerOpenError("read CB OPEN (test)")


# ---------------------------------------------------------------------------
# analytics /summary
# ---------------------------------------------------------------------------

def test_analytics_summary_cb_open_returns_200_with_header(client: TestClient) -> None:
    """GET /analytics/summary must return 200 (not 503) when CB is open."""
    with patch("routes.analytics.sb_execute", side_effect=_cb_open_side_effect):
        resp = client.get("/v1/analytics/summary")

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers.get("x-cache-status") == "stale-due-to-cb-open", (
        "Missing X-Cache-Status header on CB-open degraded response"
    )
    body = resp.json()
    assert body["total_searches"] == 0
    assert body["total_opportunities"] == 0


# ---------------------------------------------------------------------------
# analytics /searches-over-time
# ---------------------------------------------------------------------------

def test_analytics_time_series_cb_open_returns_200_with_header(client: TestClient) -> None:
    with patch("routes.analytics.sb_execute", side_effect=_cb_open_side_effect):
        resp = client.get("/v1/analytics/searches-over-time")

    assert resp.status_code == 200
    assert resp.headers.get("x-cache-status") == "stale-due-to-cb-open"
    body = resp.json()
    assert body["data"] == []
    assert body.get("degraded") is True


# ---------------------------------------------------------------------------
# analytics /top-dimensions
# ---------------------------------------------------------------------------

def test_analytics_top_dimensions_cb_open_returns_200_with_header(client: TestClient) -> None:
    with patch("routes.analytics.sb_execute", side_effect=_cb_open_side_effect):
        resp = client.get("/v1/analytics/top-dimensions")

    assert resp.status_code == 200
    assert resp.headers.get("x-cache-status") == "stale-due-to-cb-open"
    body = resp.json()
    assert body["top_ufs"] == []
    assert body["top_sectors"] == []
    assert body.get("degraded") is True


# ---------------------------------------------------------------------------
# sessions /sessions
# ---------------------------------------------------------------------------

def test_sessions_cb_open_returns_200_with_header(client: TestClient) -> None:
    with patch("routes.sessions.sb_execute", side_effect=_cb_open_side_effect):
        resp = client.get("/v1/sessions")

    assert resp.status_code == 200
    assert resp.headers.get("x-cache-status") == "stale-due-to-cb-open"
    body = resp.json()
    assert body["sessions"] == []
    assert body["total"] == 0
    assert body.get("degraded") is True


# ---------------------------------------------------------------------------
# Non-CB exceptions must still return 503 (regression guard)
# ---------------------------------------------------------------------------

def test_analytics_summary_generic_error_still_503(client: TestClient) -> None:
    """Random exceptions (not CB-open) must still propagate as 503."""
    with patch("routes.analytics.sb_execute", side_effect=RuntimeError("connection refused")):
        resp = client.get("/v1/analytics/summary")

    assert resp.status_code == 503


def test_sessions_generic_error_still_503(client: TestClient) -> None:
    with patch("routes.sessions.sb_execute", side_effect=RuntimeError("connection refused")):
        resp = client.get("/v1/sessions")

    assert resp.status_code == 503
