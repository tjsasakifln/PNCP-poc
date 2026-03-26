"""Tests for DEBT-127: Dashboard Actionable Insights.

Covers:
- GET /analytics/new-opportunities (AC6-AC9)
- GET /pipeline/alerts with 7-day window (AC1-AC5)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import require_auth
from routes.analytics import router as analytics_router
from routes.pipeline import router as pipeline_router

MOCK_USER = {"id": "user-123", "email": "test@test.com"}


def _create_analytics_client():
    app = FastAPI()
    app.include_router(analytics_router, prefix="/v1")
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    return TestClient(app)


def _create_pipeline_client():
    app = FastAPI()
    app.include_router(pipeline_router, prefix="/v1")
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    return TestClient(app)


def _mock_db():
    """Create a fluent-chainable Supabase mock."""
    db = Mock()
    chain = Mock()
    db.table.return_value = chain
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.lte.return_value = chain
    chain.not_.return_value = chain
    chain.in_.return_value = chain
    chain.is_.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    return db, chain


# ============================================================================
# GET /analytics/new-opportunities — DEBT-127 AC6-AC9
# ============================================================================


class TestNewOpportunities:
    """DEBT-127 AC6-AC9: New opportunities since last search."""

    @patch("routes.analytics.sb_execute")
    @patch("routes.analytics.get_db")
    def test_with_previous_search(self, mock_get_db, mock_sb_execute):
        """AC6/AC7: Shows count from latest search with days context."""
        db, chain = _mock_db()
        mock_get_db.return_value = db

        last_search_at = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        mock_sb_execute.return_value = Mock(data=[
            {"created_at": last_search_at, "total_filtered": 42},
        ])

        client = _create_analytics_client()
        resp = client.get("/v1/analytics/new-opportunities")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 42
        assert body["has_previous_search"] is True
        assert body["days_since_last_search"] == 3
        assert body["last_search_at"] == last_search_at

    @patch("routes.analytics.sb_execute")
    @patch("routes.analytics.get_db")
    def test_no_previous_search(self, mock_get_db, mock_sb_execute):
        """AC9: No previous search returns onboarding prompt data."""
        db, chain = _mock_db()
        mock_get_db.return_value = db
        mock_sb_execute.return_value = Mock(data=[])

        client = _create_analytics_client()
        resp = client.get("/v1/analytics/new-opportunities")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["has_previous_search"] is False
        assert body["last_search_at"] is None
        assert body["days_since_last_search"] is None

    @patch("routes.analytics.sb_execute")
    @patch("routes.analytics.get_db")
    def test_search_today(self, mock_get_db, mock_sb_execute):
        """AC8: Search done today shows 0 days."""
        db, chain = _mock_db()
        mock_get_db.return_value = db

        now = datetime.now(timezone.utc).isoformat()
        mock_sb_execute.return_value = Mock(data=[
            {"created_at": now, "total_filtered": 15},
        ])

        client = _create_analytics_client()
        resp = client.get("/v1/analytics/new-opportunities")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 15
        assert body["days_since_last_search"] == 0

    @patch("routes.analytics.sb_execute")
    @patch("routes.analytics.get_db")
    def test_null_total_filtered(self, mock_get_db, mock_sb_execute):
        """Edge case: total_filtered is null (incomplete session)."""
        db, chain = _mock_db()
        mock_get_db.return_value = db

        mock_sb_execute.return_value = Mock(data=[
            {"created_at": datetime.now(timezone.utc).isoformat(), "total_filtered": None},
        ])

        client = _create_analytics_client()
        resp = client.get("/v1/analytics/new-opportunities")

        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    @patch("routes.analytics.sb_execute")
    @patch("routes.analytics.get_db")
    def test_db_error_returns_safe_default(self, mock_get_db, mock_sb_execute):
        """Graceful degradation on DB error."""
        db, chain = _mock_db()
        mock_get_db.return_value = db
        mock_sb_execute.side_effect = Exception("DB connection failed")

        client = _create_analytics_client()
        resp = client.get("/v1/analytics/new-opportunities")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["has_previous_search"] is False

    @patch("routes.analytics.sb_execute")
    @patch("routes.analytics.get_db")
    def test_z_suffix_datetime_parsing(self, mock_get_db, mock_sb_execute):
        """Handles Z-suffix ISO datetime from Supabase."""
        db, chain = _mock_db()
        mock_get_db.return_value = db

        mock_sb_execute.return_value = Mock(data=[
            {"created_at": "2026-03-08T10:00:00Z", "total_filtered": 30},
        ])

        client = _create_analytics_client()
        resp = client.get("/v1/analytics/new-opportunities")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 30
        assert body["has_previous_search"] is True


# ============================================================================
# GET /pipeline/alerts — DEBT-127 AC1-AC5 (7-day window)
# ============================================================================


class TestPipelineAlertsDebt127:
    """DEBT-127 AC1-AC5: Pipeline alerts with 7-day deadline window."""

    @patch("routes.pipeline.sb_execute")
    @patch("routes.pipeline.get_supabase")
    @patch("routes.pipeline._check_pipeline_read_access")
    def test_7_day_window(self, mock_check, mock_get_sb, mock_sb_execute):
        """AC1: Alerts use 7-day window (not 3 days)."""
        mock_check.return_value = None
        sb, chain = _mock_db()
        mock_get_sb.return_value = sb
        mock_sb_execute.return_value = Mock(data=[])

        client = _create_pipeline_client()
        resp = client.get("/v1/pipeline/alerts")

        assert resp.status_code == 200
        # Verify 7-day deadline was used in the query chain
        lte_call = sb.table.return_value.select.return_value.eq.return_value.not_.return_value.not_.return_value.lte
        if lte_call.called:
            deadline_arg = lte_call.call_args[0][1]
            deadline_dt = datetime.fromisoformat(deadline_arg.replace("Z", "+00:00"))
            expected_min = datetime.now(timezone.utc) + timedelta(days=6, hours=23)
            expected_max = datetime.now(timezone.utc) + timedelta(days=7, hours=1)
            assert expected_min <= deadline_dt <= expected_max

    @patch("routes.pipeline.sb_execute")
    @patch("routes.pipeline.get_supabase")
    @patch("routes.pipeline._check_pipeline_read_access")
    def test_alerts_with_items(self, mock_check, mock_get_sb, mock_sb_execute):
        """AC2: Shows items with approaching deadlines and total count."""
        mock_check.return_value = None
        sb, chain = _mock_db()
        mock_get_sb.return_value = sb

        items = [
            {
                "id": "item-1", "user_id": "user-123", "pncp_id": "pncp-1",
                "objeto": "Obra de construcao", "orgao": "Prefeitura",
                "uf": "SP", "valor_estimado": 100000, "stage": "analise",
                "data_encerramento": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
                "link_pncp": None, "notes": None, "search_id": None,
                "created_at": "2026-03-01T00:00:00Z", "updated_at": "2026-03-01T00:00:00Z",
                "version": 1,
            },
            {
                "id": "item-2", "user_id": "user-123", "pncp_id": "pncp-2",
                "objeto": "Reforma predial", "orgao": "Governo",
                "uf": "RJ", "valor_estimado": 200000, "stage": "descoberta",
                "data_encerramento": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                "link_pncp": None, "notes": None, "search_id": None,
                "created_at": "2026-03-01T00:00:00Z", "updated_at": "2026-03-01T00:00:00Z",
                "version": 1,
            },
        ]
        mock_sb_execute.return_value = Mock(data=items)

        client = _create_pipeline_client()
        resp = client.get("/v1/pipeline/alerts")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    @patch("routes.pipeline.sb_execute")
    @patch("routes.pipeline.get_supabase")
    @patch("routes.pipeline._check_pipeline_read_access")
    def test_no_alerts_empty_state(self, mock_check, mock_get_sb, mock_sb_execute):
        """AC4: No upcoming deadlines returns empty list."""
        mock_check.return_value = None
        sb, chain = _mock_db()
        mock_get_sb.return_value = sb
        mock_sb_execute.return_value = Mock(data=[])

        client = _create_pipeline_client()
        resp = client.get("/v1/pipeline/alerts")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    @patch("routes.pipeline._check_pipeline_read_access")
    def test_requires_auth(self, mock_check):
        """AC5: Endpoint requires authentication."""
        app = FastAPI()
        app.include_router(pipeline_router, prefix="/v1")
        # No auth override — require_auth will fail
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/pipeline/alerts")
        assert resp.status_code in (401, 403, 422)
