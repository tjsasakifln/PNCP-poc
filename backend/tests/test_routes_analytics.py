"""Tests for routes.analytics — analytics summary, time series, top dimensions.

STORY-224 Track 4 (AC23): Analytics route coverage.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from routes.analytics import router


MOCK_USER = {"id": "user-123-uuid", "email": "test@example.com", "role": "authenticated"}


def _create_client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    return TestClient(app)


def _mock_sb(execute_data=None, rpc_data=None):
    """Build a fluent-chainable Supabase mock.

    Args:
        execute_data: Data returned by table().select()...execute()
        rpc_data: Data returned by rpc().execute()
    """
    sb = Mock()
    # Table chain
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.eq.return_value = sb
    sb.gte.return_value = sb
    sb.order.return_value = sb
    sb.range.return_value = sb
    sb.limit.return_value = sb
    table_result = Mock(data=execute_data or [])
    sb.execute.return_value = table_result

    # RPC chain
    rpc_mock = Mock()
    rpc_result = Mock(data=rpc_data)
    rpc_mock.execute.return_value = rpc_result
    sb.rpc.return_value = rpc_mock

    return sb


# ============================================================================
# GET /analytics/summary
# ============================================================================

class TestAnalyticsSummary:

    @patch("routes.analytics._get_sb")
    def test_summary_with_data(self, mock_get_sb):
        rpc_row = {
            "total_searches": 10,
            "total_downloads": 5,
            "total_opportunities": 80,
            "total_value_discovered": 500000.0,
            "member_since": "2025-06-15T00:00:00+00:00",
        }
        mock_get_sb.return_value = _mock_sb(rpc_data=[rpc_row])
        client = _create_client()

        resp = client.get("/analytics/summary")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_searches"] == 10
        assert body["total_downloads"] == 5
        assert body["total_opportunities"] == 80
        assert body["total_value_discovered"] == 500000.0
        assert body["estimated_hours_saved"] == 20.0  # 10 * 2
        assert body["avg_results_per_search"] == 8.0  # 80 / 10
        assert body["success_rate"] == 50.0  # 5/10*100
        assert body["member_since"] == "2025-06-15T00:00:00+00:00"

    @patch("routes.analytics._get_sb")
    def test_summary_empty_no_data(self, mock_get_sb):
        mock_get_sb.return_value = _mock_sb(rpc_data=[])
        client = _create_client()

        resp = client.get("/analytics/summary")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_searches"] == 0
        assert body["total_downloads"] == 0
        assert body["total_opportunities"] == 0
        assert body["total_value_discovered"] == 0.0
        assert body["estimated_hours_saved"] == 0.0
        assert body["avg_results_per_search"] == 0.0
        assert body["success_rate"] == 0.0

    @patch("routes.analytics._get_sb")
    def test_summary_none_rpc_result(self, mock_get_sb):
        """RPC returns None data — should fall back to zeros."""
        mock_get_sb.return_value = _mock_sb(rpc_data=None)
        client = _create_client()

        resp = client.get("/analytics/summary")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_searches"] == 0

    @patch("routes.analytics._get_sb")
    def test_summary_null_fields_default_to_zero(self, mock_get_sb):
        """RPC row has None values for counters — should coalesce to 0."""
        rpc_row = {
            "total_searches": None,
            "total_downloads": None,
            "total_opportunities": None,
            "total_value_discovered": None,
            "member_since": None,
        }
        mock_get_sb.return_value = _mock_sb(rpc_data=[rpc_row])
        client = _create_client()

        resp = client.get("/analytics/summary")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_searches"] == 0
        assert body["total_downloads"] == 0


# ============================================================================
# GET /analytics/searches-over-time
# ============================================================================

class TestSearchesOverTime:

    @patch("routes.analytics._get_sb")
    def test_time_series_week_grouping(self, mock_get_sb):
        sessions = [
            {"created_at": "2026-02-02T10:00:00+00:00", "total_filtered": 5, "valor_total": 10000},
            {"created_at": "2026-02-03T10:00:00+00:00", "total_filtered": 3, "valor_total": 5000},
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/searches-over-time?period=week&range_days=90")

        assert resp.status_code == 200
        body = resp.json()
        assert body["period"] == "week"
        # Both dates are in the same week (Mon 2026-02-02), so should be 1 group
        assert len(body["data"]) == 1
        point = body["data"][0]
        assert point["searches"] == 2
        assert point["opportunities"] == 8  # 5 + 3
        assert point["value"] == 15000.0

    @patch("routes.analytics._get_sb")
    def test_time_series_day_grouping(self, mock_get_sb):
        sessions = [
            {"created_at": "2026-02-01T10:00:00+00:00", "total_filtered": 5, "valor_total": 10000},
            {"created_at": "2026-02-02T10:00:00+00:00", "total_filtered": 3, "valor_total": 5000},
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/searches-over-time?period=day&range_days=30")

        assert resp.status_code == 200
        body = resp.json()
        assert body["period"] == "day"
        assert len(body["data"]) == 2  # Two different days

    @patch("routes.analytics._get_sb")
    def test_time_series_month_grouping(self, mock_get_sb):
        sessions = [
            {"created_at": "2026-01-15T10:00:00+00:00", "total_filtered": 2, "valor_total": 1000},
            {"created_at": "2026-02-10T10:00:00+00:00", "total_filtered": 7, "valor_total": 3000},
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/searches-over-time?period=month&range_days=90")

        assert resp.status_code == 200
        body = resp.json()
        assert body["period"] == "month"
        assert len(body["data"]) == 2  # Two different months

    @patch("routes.analytics._get_sb")
    def test_time_series_empty_sessions(self, mock_get_sb):
        mock_get_sb.return_value = _mock_sb(execute_data=[])
        client = _create_client()

        resp = client.get("/analytics/searches-over-time")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []

    def test_invalid_period_rejected(self):
        client = _create_client()
        resp = client.get("/analytics/searches-over-time?period=invalid")
        assert resp.status_code == 422

    @patch("routes.analytics._get_sb")
    def test_time_series_null_values_handled(self, mock_get_sb):
        """Sessions with null total_filtered and valor_total should default to 0."""
        sessions = [
            {"created_at": "2026-02-01T10:00:00+00:00", "total_filtered": None, "valor_total": None},
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/searches-over-time?period=day")

        assert resp.status_code == 200
        point = resp.json()["data"][0]
        assert point["opportunities"] == 0
        assert point["value"] == 0.0


# ============================================================================
# GET /analytics/top-dimensions
# ============================================================================

class TestTopDimensions:

    @patch("routes.analytics._get_sb")
    def test_top_dimensions_with_data(self, mock_get_sb):
        sessions = [
            {"ufs": ["SP", "RJ"], "sectors": ["facilities"], "valor_total": 100000},
            {"ufs": ["SP"], "sectors": ["facilities", "saude"], "valor_total": 200000},
            {"ufs": ["MG"], "sectors": ["saude"], "valor_total": 50000},
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/top-dimensions?limit=5")

        assert resp.status_code == 200
        body = resp.json()

        # SP: 2 searches, RJ: 1, MG: 1 — SP should be first
        assert body["top_ufs"][0]["name"] == "SP"
        assert body["top_ufs"][0]["count"] == 2

        # facilities: 2, saude: 2 — both count=2
        sector_names = {s["name"] for s in body["top_sectors"]}
        assert "facilities" in sector_names
        assert "saude" in sector_names

    @patch("routes.analytics._get_sb")
    def test_top_dimensions_empty(self, mock_get_sb):
        mock_get_sb.return_value = _mock_sb(execute_data=[])
        client = _create_client()

        resp = client.get("/analytics/top-dimensions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["top_ufs"] == []
        assert body["top_sectors"] == []

    @patch("routes.analytics._get_sb")
    def test_top_dimensions_null_ufs_and_sectors(self, mock_get_sb):
        """Sessions with null ufs/sectors should not crash."""
        sessions = [
            {"ufs": None, "sectors": None, "valor_total": 100000},
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/top-dimensions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["top_ufs"] == []
        assert body["top_sectors"] == []

    @patch("routes.analytics._get_sb")
    def test_top_dimensions_limit_respected(self, mock_get_sb):
        """Only top N dimensions should be returned."""
        sessions = [
            {"ufs": [f"UF{i}"], "sectors": [f"sector{i}"], "valor_total": 1000 * i}
            for i in range(10)
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/top-dimensions?limit=3")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["top_ufs"]) <= 3
        assert len(body["top_sectors"]) <= 3

    @patch("routes.analytics._get_sb")
    def test_top_dimensions_value_aggregation(self, mock_get_sb):
        """Value should be summed across all sessions for each UF."""
        sessions = [
            {"ufs": ["SP"], "sectors": [], "valor_total": 100000},
            {"ufs": ["SP"], "sectors": [], "valor_total": 200000},
        ]
        mock_get_sb.return_value = _mock_sb(execute_data=sessions)
        client = _create_client()

        resp = client.get("/analytics/top-dimensions")

        assert resp.status_code == 200
        sp_item = resp.json()["top_ufs"][0]
        assert sp_item["name"] == "SP"
        assert sp_item["value"] == 300000.0
