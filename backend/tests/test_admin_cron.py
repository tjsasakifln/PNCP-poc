"""STORY-1.1 (EPIC-TD-2026Q2 P0): Tests for /v1/admin/cron-status endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from admin import require_admin
from auth import require_auth


@pytest.fixture
def admin_user():
    return {"id": "admin-001", "email": "admin@smartlic.tech", "role": "admin"}


@pytest.fixture
def client_as_admin(admin_user):
    """TestClient with auth + admin bypass via FastAPI dependency overrides.

    IMPORTANT: never `patch('routes.X.require_auth')` — breaks on startup.
    """
    app.dependency_overrides[require_auth] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def client_no_auth():
    """TestClient without overrides — triggers real auth path (expected 401/403)."""
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)
    return TestClient(app)


# ---------------------------------------------------------------------------
# happy path
# ---------------------------------------------------------------------------


def test_cron_status_returns_normalized_rows(client_as_admin):
    """Shape: {status, queried_at, count, jobs[]}; numeric + datetime normalized."""
    fake_rows = [
        {
            "jobname": "purge-old-bids",
            "schedule": "0 7 * * *",
            "active": True,
            "last_status": "succeeded",
            "last_run_at": datetime(2026, 4, 14, 7, 0, 3, tzinfo=timezone.utc),
            "runs_24h": 1,
            "failures_24h": 0,
            "latency_avg_ms": 120,
            "last_return_message": None,
        },
        {
            "jobname": "cleanup-search-cache",
            "schedule": "0 4 * * *",
            "active": True,
            "last_status": "succeeded",
            "last_run_at": "2026-04-14T04:00:01+00:00",
            "runs_24h": 1,
            "failures_24h": 0,
            "latency_avg_ms": None,
            "last_return_message": None,
        },
    ]

    mock_sb = MagicMock()
    mock_sb.rpc.return_value = MagicMock(name="rpc_call")

    async def fake_execute(_query):
        return SimpleNamespace(data=fake_rows)

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb), patch(
        "routes.admin_cron.sb_execute_direct", side_effect=fake_execute
    ):
        response = client_as_admin.get("/v1/admin/cron-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["count"] == 2
    assert len(payload["jobs"]) == 2

    first = payload["jobs"][0]
    assert first["jobname"] == "purge-old-bids"
    assert first["active"] is True
    # datetime is serialized to ISO string
    assert first["last_run_at"].startswith("2026-04-14T07:00")
    # numeric fields preserved
    assert first["runs_24h"] == 1
    assert first["latency_avg_ms"] == 120

    second = payload["jobs"][1]
    assert second["latency_avg_ms"] is None


def test_cron_status_handles_rpc_exception_gracefully(client_as_admin):
    """When Supabase RPC raises, endpoint returns status=error with empty list (never 500)."""
    mock_sb = MagicMock()
    mock_sb.rpc.return_value = MagicMock(name="rpc_call")

    async def failing_execute(_query):
        raise RuntimeError("connection refused")

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb), patch(
        "routes.admin_cron.sb_execute_direct", side_effect=failing_execute
    ):
        response = client_as_admin.get("/v1/admin/cron-status")

    # Dashboards should degrade gracefully — 200 with status=error, not 500.
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["count"] == 0
    assert payload["jobs"] == []
    assert "connection refused" in payload.get("detail", "")


def test_cron_status_ignores_non_dict_rows(client_as_admin):
    """Defensive: rows that aren't dicts are filtered out instead of crashing."""
    mock_sb = MagicMock()
    mock_sb.rpc.return_value = MagicMock(name="rpc_call")

    async def fake_execute(_query):
        return SimpleNamespace(data=["not-a-dict", {"jobname": "valid", "last_status": "succeeded"}])

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb), patch(
        "routes.admin_cron.sb_execute_direct", side_effect=fake_execute
    ):
        response = client_as_admin.get("/v1/admin/cron-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["jobs"][0]["jobname"] == "valid"


def test_cron_status_normalizes_missing_fields(client_as_admin):
    """Rows with missing keys fall back to defaults (never_ran / 0 / None)."""
    mock_sb = MagicMock()
    mock_sb.rpc.return_value = MagicMock(name="rpc_call")

    async def fake_execute(_query):
        return SimpleNamespace(data=[{"jobname": "bare-job"}])

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb), patch(
        "routes.admin_cron.sb_execute_direct", side_effect=fake_execute
    ):
        response = client_as_admin.get("/v1/admin/cron-status")

    assert response.status_code == 200
    job = response.json()["jobs"][0]
    assert job["jobname"] == "bare-job"
    assert job["last_status"] == "never_ran"
    assert job["runs_24h"] == 0
    assert job["failures_24h"] == 0
    assert job["latency_avg_ms"] is None
    assert job["last_run_at"] is None
