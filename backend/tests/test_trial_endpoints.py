"""
Tests for GTM-010 trial endpoints.

Tests:
- GET /v1/analytics/trial-value (showcase trial analysis value)
- GET /v1/trial-status (trial time remaining)
- Updated trial expiration error message
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from main import app
from auth import require_auth
from database import get_db
from quota import QuotaInfo, PLAN_CAPABILITIES, get_quota_reset_date


@pytest.fixture(autouse=True)
def setup_overrides():
    """Set up auth and db overrides for all tests."""
    app.dependency_overrides[require_auth] = lambda: {"id": "test-user-123", "email": "test@example.com"}
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    # Don't pop individual keys — autouse fixture clears all overrides


# ============================================================================
# Trial Value Endpoint Tests
# ============================================================================

def _make_table_side_effect(profile_mock, sessions_mock):
    """Create a side_effect for db.table() that returns different mocks per table name."""
    def table_side_effect(name):
        if name == "profiles":
            return profile_mock
        elif name == "search_sessions":
            return sessions_mock
        return MagicMock()
    return table_side_effect


def test_trial_value_with_sessions(client, mock_db):
    """Test trial value endpoint with search session history."""
    # Profile mock chain
    profile_mock = MagicMock()
    profile_result = MagicMock()
    profile_result.data = {
        "created_at": "2026-02-05T10:00:00+00:00",
        "trial_expires_at": "2026-02-12T10:00:00+00:00",
    }
    profile_mock.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

    # Sessions mock chain
    sessions_mock = MagicMock()
    sessions_result = MagicMock()
    sessions_result.data = [
        {
            "total_filtered": 25,
            "valor_total": "5000000.00",
            "objeto_resumo": "Uniformes escolares - SP",
            "created_at": "2026-02-10T10:00:00+00:00",
        },
        {
            "total_filtered": 22,
            "valor_total": "3500000.00",
            "objeto_resumo": "Materiais de limpeza - RJ",
            "created_at": "2026-02-12T14:00:00+00:00",
        },
    ]
    sessions_mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = sessions_result

    mock_db.table.side_effect = _make_table_side_effect(profile_mock, sessions_mock)

    response = client.get("/v1/analytics/trial-value")

    assert response.status_code == 200
    data = response.json()

    # Verify response matches TrialValueResponse schema
    assert data["total_opportunities"] == 47  # 25 + 22
    assert data["total_value"] == 8500000.0  # 5M + 3.5M
    assert data["searches_executed"] == 2
    assert data["avg_opportunity_value"] == pytest.approx(180851.06, abs=1)  # 8.5M / 47
    assert data["top_opportunity"] is not None
    assert data["top_opportunity"]["title"] == "Uniformes escolares - SP"
    assert data["top_opportunity"]["value"] == 5000000.0


def test_trial_value_no_sessions(client, mock_db):
    """Test trial value endpoint with no search history."""
    profile_mock = MagicMock()
    profile_result = MagicMock()
    profile_result.data = {
        "created_at": "2026-02-05T10:00:00+00:00",
        "trial_expires_at": "2026-02-12T10:00:00+00:00",
    }
    profile_mock.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

    sessions_mock = MagicMock()
    sessions_result = MagicMock()
    sessions_result.data = []
    sessions_mock.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = sessions_result

    mock_db.table.side_effect = _make_table_side_effect(profile_mock, sessions_mock)

    response = client.get("/v1/analytics/trial-value")

    assert response.status_code == 200
    data = response.json()

    assert data["total_opportunities"] == 0
    assert data["total_value"] == 0.0
    assert data["searches_executed"] == 0
    assert data["avg_opportunity_value"] == 0.0
    assert data["top_opportunity"] is None


def test_trial_value_db_error(client, mock_db):
    """Test trial value endpoint handles database errors gracefully."""
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception(
        "Database connection error"
    )

    response = client.get("/v1/analytics/trial-value")

    # Should return zeros instead of 500 error
    assert response.status_code == 200
    data = response.json()

    assert data["total_opportunities"] == 0
    assert data["total_value"] == 0.0
    assert data["searches_executed"] == 0
    assert data["avg_opportunity_value"] == 0.0
    assert data["top_opportunity"] is None


# ============================================================================
# Trial Status Endpoint Tests
# ============================================================================

def test_trial_status_active_trial(client):
    """Test trial status endpoint with active trial."""
    future_date = datetime.now(timezone.utc) + timedelta(days=5)

    mock_quota = QuotaInfo(
        allowed=True,
        plan_id="free_trial",
        plan_name="FREE Trial",
        capabilities=PLAN_CAPABILITIES["free_trial"],
        quota_used=2,
        quota_remaining=1,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=future_date,
        error_message=None,
    )

    with patch("quota.check_quota", return_value=mock_quota):
        response = client.get("/v1/trial-status")

    assert response.status_code == 200
    data = response.json()

    assert data["plan"] == "free_trial"
    assert data["days_remaining"] >= 4  # ~5 days
    assert data["searches_used"] == 2
    assert data["searches_limit"] == 3  # free_trial limit
    assert data["expires_at"] is not None
    assert data["is_expired"] is False


def test_trial_status_expired_trial(client):
    """Test trial status endpoint with expired trial."""
    past_date = datetime.now(timezone.utc) - timedelta(days=1)

    mock_quota = QuotaInfo(
        allowed=False,
        plan_id="free_trial",
        plan_name="FREE Trial",
        capabilities=PLAN_CAPABILITIES["free_trial"],
        quota_used=3,
        quota_remaining=0,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=past_date,
        error_message="Seu trial expirou.",
    )

    with patch("quota.check_quota", return_value=mock_quota):
        response = client.get("/v1/trial-status")

    assert response.status_code == 200
    data = response.json()

    assert data["plan"] == "free_trial"
    assert data["days_remaining"] == 0
    assert data["searches_used"] == 3
    assert data["expires_at"] is not None
    assert data["is_expired"] is True


def test_trial_status_paid_user(client):
    """Test trial status endpoint for paid user (not on trial)."""
    mock_quota = QuotaInfo(
        allowed=True,
        plan_id="smartlic_pro",
        plan_name="SmartLic Pro",
        capabilities=PLAN_CAPABILITIES["smartlic_pro"],
        quota_used=50,
        quota_remaining=950,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=None,
        error_message=None,
    )

    with patch("quota.check_quota", return_value=mock_quota):
        response = client.get("/v1/trial-status")

    assert response.status_code == 200
    data = response.json()

    assert data["plan"] == "smartlic_pro"
    assert data["days_remaining"] == 999  # Sentinel for paid
    assert data["searches_used"] == 50
    assert data["searches_limit"] == 1000
    assert data["expires_at"] is None
    assert data["is_expired"] is False


# ============================================================================
# Quota Error Message Test
# ============================================================================

def test_trial_expired_message_updated():
    """Test that trial expiration error message matches GTM-010 spec."""
    from quota import PLAN_CAPABILITIES, PLAN_NAMES

    # Verify the message is in the codebase by importing and checking
    # The actual check is done by reading the quota.py source
    import quota
    import inspect

    source = inspect.getsource(quota.check_quota)
    assert "Veja o valor que você analisou" in source
    assert "continue tendo vantagem" in source
