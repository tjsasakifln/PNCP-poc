"""Tests for analytics endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# Mock auth to return a test user
def _mock_require_auth():
    return {"id": "test-user-123", "email": "test@example.com", "role": "authenticated"}


@pytest.fixture
def client():
    """Create test client with mocked auth."""
    from main import app
    from auth import require_auth
    app.dependency_overrides[require_auth] = _mock_require_auth
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    """Mock supabase client for analytics queries."""
    with patch("routes.analytics._get_sb") as mock:
        sb = MagicMock()
        mock.return_value = sb
        yield sb


class TestAnalyticsSummary:
    def test_summary_empty_user(self, client, mock_supabase):
        """New user with no search sessions."""
        # Mock sessions query returns empty
        sessions_chain = MagicMock()
        sessions_chain.select.return_value = sessions_chain
        sessions_chain.eq.return_value = sessions_chain
        sessions_result = MagicMock()
        sessions_result.data = []
        sessions_chain.execute.return_value = sessions_result

        # Mock profile query
        profile_chain = MagicMock()
        profile_chain.select.return_value = profile_chain
        profile_chain.eq.return_value = profile_chain
        profile_result = MagicMock()
        profile_result.data = [{"created_at": "2026-01-15T00:00:00Z"}]
        profile_chain.execute.return_value = profile_result

        mock_supabase.table.side_effect = lambda t: sessions_chain if t == "search_sessions" else profile_chain

        res = client.get("/analytics/summary", headers={"Authorization": "Bearer fake"})
        assert res.status_code == 200
        data = res.json()
        assert data["total_searches"] == 0
        assert data["total_opportunities"] == 0
        assert data["member_since"] == "2026-01-15T00:00:00Z"

    def test_summary_with_sessions(self, client, mock_supabase):
        """User with search sessions."""
        sessions_chain = MagicMock()
        sessions_chain.select.return_value = sessions_chain
        sessions_chain.eq.return_value = sessions_chain
        sessions_result = MagicMock()
        sessions_result.data = [
            {"id": "s1", "total_raw": 100, "total_filtered": 15, "valor_total": 500000, "created_at": "2026-02-01"},
            {"id": "s2", "total_raw": 200, "total_filtered": 0, "valor_total": 0, "created_at": "2026-02-02"},
            {"id": "s3", "total_raw": 50, "total_filtered": 8, "valor_total": 250000, "created_at": "2026-02-03"},
        ]
        sessions_chain.execute.return_value = sessions_result

        profile_chain = MagicMock()
        profile_chain.select.return_value = profile_chain
        profile_chain.eq.return_value = profile_chain
        profile_result = MagicMock()
        profile_result.data = [{"created_at": "2026-01-10T00:00:00Z"}]
        profile_chain.execute.return_value = profile_result

        mock_supabase.table.side_effect = lambda t: sessions_chain if t == "search_sessions" else profile_chain

        res = client.get("/analytics/summary", headers={"Authorization": "Bearer fake"})
        assert res.status_code == 200
        data = res.json()
        assert data["total_searches"] == 3
        assert data["total_downloads"] == 2  # s1 and s3 have filtered > 0
        assert data["total_opportunities"] == 23  # 15 + 0 + 8
        assert data["total_value_discovered"] == 750000.0
        assert data["estimated_hours_saved"] == 6.0  # 3 * 2
        assert data["success_rate"] == 66.7  # 2/3 * 100 rounded


class TestSearchesOverTime:
    def test_empty_time_series(self, client, mock_supabase):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.gte.return_value = chain
        chain.order.return_value = chain
        result = MagicMock()
        result.data = []
        chain.execute.return_value = result

        mock_supabase.table.return_value = chain

        res = client.get("/analytics/searches-over-time?period=week", headers={"Authorization": "Bearer fake"})
        assert res.status_code == 200
        data = res.json()
        assert data["period"] == "week"
        assert data["data"] == []

    def test_invalid_period(self, client, mock_supabase):
        res = client.get("/analytics/searches-over-time?period=invalid", headers={"Authorization": "Bearer fake"})
        assert res.status_code == 422


class TestTopDimensions:
    def test_top_dimensions(self, client, mock_supabase):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        result = MagicMock()
        result.data = [
            {"ufs": ["SP", "RJ"], "sectors": ["Facilities"], "valor_total": 500000},
            {"ufs": ["SP", "MG"], "sectors": ["Uniformes"], "valor_total": 300000},
            {"ufs": ["SP"], "sectors": ["Facilities"], "valor_total": 200000},
        ]
        chain.execute.return_value = result

        mock_supabase.table.return_value = chain

        res = client.get("/analytics/top-dimensions?limit=3", headers={"Authorization": "Bearer fake"})
        assert res.status_code == 200
        data = res.json()

        # SP appears in all 3 sessions
        assert data["top_ufs"][0]["name"] == "SP"
        assert data["top_ufs"][0]["count"] == 3

        # Facilities appears in 2 sessions
        assert data["top_sectors"][0]["name"] == "Facilities"
        assert data["top_sectors"][0]["count"] == 2

    def test_empty_dimensions(self, client, mock_supabase):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        result = MagicMock()
        result.data = []
        chain.execute.return_value = result

        mock_supabase.table.return_value = chain

        res = client.get("/analytics/top-dimensions", headers={"Authorization": "Bearer fake"})
        assert res.status_code == 200
        data = res.json()
        assert data["top_ufs"] == []
        assert data["top_sectors"] == []
