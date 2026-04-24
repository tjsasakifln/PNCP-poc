"""STORY-1.1 (TD-DB-040): Tests for GET /admin/cron-status endpoint."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app
from auth import require_auth
from admin import require_admin


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    fake_user = {"id": "admin-user-uuid", "email": "admin@test.com"}
    app.dependency_overrides[require_auth] = lambda: fake_user
    app.dependency_overrides[require_admin] = lambda: fake_user

    yield TestClient(app)

    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def client_no_admin():
    """Client without admin override — should return 403."""
    fake_user = {"id": "regular-user-uuid", "email": "user@test.com"}
    app.dependency_overrides[require_auth] = lambda: fake_user
    # require_admin NOT overridden

    yield TestClient(app)

    app.dependency_overrides.pop(require_auth, None)


SAMPLE_HEALTH_ROWS = [
    {
        "jobname": "purge-old-bids",
        "schedule": "0 7 * * *",
        "active": True,
        "last_run_at": "2026-04-14T07:00:00+00:00",
        "last_status": "succeeded",
        "runs_24h": 1,
        "failures_24h": 0,
        "latency_avg_ms": 123.4,
    },
    {
        "jobname": "cleanup-search-cache",
        "schedule": "0 4 * * *",
        "active": True,
        "last_run_at": "2026-04-14T04:00:00+00:00",
        "last_status": "succeeded",
        "runs_24h": 1,
        "failures_24h": 0,
        "latency_avg_ms": 45.0,
    },
]


# ---------------------------------------------------------------------------
# Tests: response format (AC1)
# ---------------------------------------------------------------------------

def test_cron_status_returns_correct_schema(client):
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = SAMPLE_HEALTH_ROWS

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb):
        resp = client.get("/v1/admin/cron-status")

    assert resp.status_code == 200
    data = resp.json()
    assert "jobs" in data
    assert "count" in data
    assert data["count"] == 2
    assert len(data["jobs"]) == 2


def test_cron_status_job_fields(client):
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = SAMPLE_HEALTH_ROWS

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb):
        resp = client.get("/v1/admin/cron-status")

    job = resp.json()["jobs"][0]
    assert job["jobname"] == "purge-old-bids"
    assert job["schedule"] == "0 7 * * *"
    assert job["active"] is True
    assert job["last_status"] == "succeeded"
    assert job["runs_24h"] == 1
    assert job["failures_24h"] == 0


def test_cron_status_empty_when_no_jobs(client):
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = []

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb):
        resp = client.get("/v1/admin/cron-status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["jobs"] == []
    assert data["count"] == 0


def test_cron_status_graceful_on_rpc_error(client):
    mock_sb = MagicMock()
    mock_sb.rpc.side_effect = Exception("Supabase unreachable")

    with patch("routes.admin_cron.get_supabase", return_value=mock_sb):
        resp = client.get("/v1/admin/cron-status")

    # Graceful degradation — returns empty, not 500
    assert resp.status_code == 200
    data = resp.json()
    assert data["jobs"] == []
    assert data["count"] == 0


# ---------------------------------------------------------------------------
# Tests: run_cron_monitor logic (AC3)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_cron_monitor_no_alerts_for_healthy_jobs():
    from jobs.cron.cron_monitor import run_cron_monitor

    # Use timestamp 1h ago — always within the 25h stale window
    recent_run = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    healthy_rows = [
        {
            "jobname": "purge-old-bids",
            "active": True,
            "last_run_at": recent_run,
            "last_status": "succeeded",
            "runs_24h": 1,
            "failures_24h": 0,
        }
    ]
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = healthy_rows

    with patch("jobs.cron.cron_monitor.get_supabase", return_value=mock_sb):
        result = await run_cron_monitor()

    assert result["status"] == "ok"
    assert result["alerts_fired"] == 0
    assert result["jobs_checked"] == 1


@pytest.mark.asyncio
async def test_run_cron_monitor_fires_alert_for_failed_job():
    from jobs.cron.cron_monitor import run_cron_monitor

    failed_rows = [
        {
            "jobname": "purge-old-bids",
            "active": True,
            "last_run_at": "2026-04-14T07:00:00+00:00",
            "last_status": "failed",
            "runs_24h": 1,
            "failures_24h": 1,
        }
    ]
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = failed_rows

    with patch("jobs.cron.cron_monitor.get_supabase", return_value=mock_sb), \
         patch("jobs.cron.cron_monitor._fire_sentry_alert") as mock_sentry:
        result = await run_cron_monitor()

    assert result["alerts_fired"] == 1
    mock_sentry.assert_called_once()
    args = mock_sentry.call_args[0]
    assert args[0] == "purge-old-bids"


@pytest.mark.asyncio
async def test_run_cron_monitor_fires_alert_for_stale_job():
    from jobs.cron.cron_monitor import run_cron_monitor

    # last_run_at is 30 hours ago → stale (>25h threshold)
    stale_run = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    stale_rows = [
        {
            "jobname": "cleanup-search-cache",
            "active": True,
            "last_run_at": stale_run,
            "last_status": "succeeded",
            "runs_24h": 0,
            "failures_24h": 0,
        }
    ]
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = stale_rows

    with patch("jobs.cron.cron_monitor.get_supabase", return_value=mock_sb), \
         patch("jobs.cron.cron_monitor._fire_sentry_alert") as mock_sentry:
        result = await run_cron_monitor()

    assert result["alerts_fired"] == 1
    mock_sentry.assert_called_once()


@pytest.mark.asyncio
async def test_run_cron_monitor_returns_error_on_rpc_failure():
    from jobs.cron.cron_monitor import run_cron_monitor

    mock_sb = MagicMock()
    mock_sb.rpc.side_effect = Exception("DB down")

    with patch("jobs.cron.cron_monitor.get_supabase", return_value=mock_sb):
        result = await run_cron_monitor()

    assert result["status"] == "error"
    assert "DB down" in result["error"]


@pytest.mark.asyncio
async def test_run_cron_monitor_no_rows_is_ok():
    from jobs.cron.cron_monitor import run_cron_monitor

    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = []

    with patch("jobs.cron.cron_monitor.get_supabase", return_value=mock_sb):
        result = await run_cron_monitor()

    assert result["status"] == "ok"
    assert result["jobs_checked"] == 0
    assert result["alerts_fired"] == 0
