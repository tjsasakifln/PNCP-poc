"""Tests for routes.plans — GET /api/plans endpoint.

STORY-224 Track 4 (AC27): Plans route coverage (public endpoint, no auth).
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.plans import router
from database import get_db


def _create_client(mock_db=None, mock_db_fn=None):
    """Create test client with optional database dependency override.

    Args:
        mock_db: Supabase client mock to return (value)
        mock_db_fn: Function to call for dependency (for raising exceptions)
    """
    app = FastAPI()
    app.include_router(router)
    if mock_db is not None:
        app.dependency_overrides[get_db] = lambda: mock_db
    elif mock_db_fn is not None:
        app.dependency_overrides[get_db] = mock_db_fn
    return TestClient(app)


def _mock_sb(data=None):
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.eq.return_value = sb
    sb.order.return_value = sb
    result = Mock(data=data)
    sb.execute.return_value = result
    return sb


# ============================================================================
# GET /api/plans
# ============================================================================

class TestGetPlans:

    @patch("quota.get_plan_capabilities")
    def test_successful_fetch_with_capabilities(self, mock_caps):
        plans_data = [
            {
                "id": "free_trial",
                "name": "Free Trial",
                "description": "Teste gratis por 7 dias",
                "price_brl": 0.0,
                "duration_days": 7,
                "max_searches": 3,
                "is_active": True,
            },
            {
                "id": "consultor_agil",
                "name": "Consultor Agil",
                "description": "Plano para consultores",
                "price_brl": 297.0,
                "duration_days": 30,
                "max_searches": 50,
                "is_active": True,
            },
        ]
        sb = _mock_sb(data=plans_data)

        mock_caps.return_value = {
            "free_trial": {
                "max_history_days": 7,
                "allow_excel": False,
                "max_requests_per_month": 3,
                "max_requests_per_min": 5,
                "max_summary_tokens": 100,
                "priority": "low",
            },
            "consultor_agil": {
                "max_history_days": 90,
                "allow_excel": True,
                "max_requests_per_month": 50,
                "max_requests_per_min": 15,
                "max_summary_tokens": 500,
                "priority": "normal",
            },
        }

        client = _create_client(mock_db=sb)
        resp = client.get("/api/plans")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["plans"]) == 2

        free = body["plans"][0]
        assert free["id"] == "free_trial"
        assert free["price_brl"] == 0.0
        assert free["capabilities"]["allow_excel"] is False
        assert free["capabilities"]["max_history_days"] == 7

        consultor = body["plans"][1]
        assert consultor["id"] == "consultor_agil"
        assert consultor["price_brl"] == 297.0
        assert consultor["capabilities"]["allow_excel"] is True
        assert consultor["capabilities"]["max_requests_per_month"] == 50

    @patch("quota.get_plan_capabilities")
    def test_no_active_plans_returns_empty(self, mock_caps):
        sb = _mock_sb(data=None)  # No plans
        mock_caps.return_value = {}
        client = _create_client(mock_db=sb)

        resp = client.get("/api/plans")

        assert resp.status_code == 200
        body = resp.json()
        assert body["plans"] == []
        assert body["total"] == 0

    @patch("quota.get_plan_capabilities")
    def test_empty_data_list_returns_empty(self, mock_caps):
        sb = _mock_sb(data=[])  # Empty list is falsy
        mock_caps.return_value = {}
        client = _create_client(mock_db=sb)

        resp = client.get("/api/plans")

        assert resp.status_code == 200
        body = resp.json()
        assert body["plans"] == []
        assert body["total"] == 0

    def test_db_error_returns_500(self):
        """Database connection error should return 500 with user-friendly message."""
        # Create a mock that raises when accessed
        sb = Mock()
        sb.table.side_effect = Exception("Database connection failed")

        client = _create_client(mock_db=sb)

        resp = client.get("/api/plans")

        assert resp.status_code == 500
        assert "planos" in resp.json()["detail"].lower()

    @patch("quota.get_plan_capabilities")
    def test_plan_without_capabilities_gets_defaults(self, mock_caps):
        """Plan not in capabilities dict should get default values."""
        plans_data = [
            {
                "id": "new_plan",
                "name": "New Plan",
                "description": "Brand new",
                "price_brl": 500.0,
                "duration_days": 30,
                "max_searches": 100,
                "is_active": True,
            },
        ]
        sb = _mock_sb(data=plans_data)
        mock_caps.return_value = {}  # No capabilities for new_plan

        client = _create_client(mock_db=sb)
        resp = client.get("/api/plans")

        assert resp.status_code == 200
        plan = resp.json()["plans"][0]
        assert plan["id"] == "new_plan"
        # Should have default capability values
        assert plan["capabilities"]["max_history_days"] == 30
        assert plan["capabilities"]["allow_excel"] is False
        assert plan["capabilities"]["max_requests_per_month"] == 100  # Falls back to max_searches
        assert plan["capabilities"]["priority"] == "normal"

    @patch("quota.get_plan_capabilities")
    def test_null_duration_days_defaults_to_30(self, mock_caps):
        """Plan with null duration_days should default to 30."""
        plans_data = [
            {
                "id": "test_plan",
                "name": "Test",
                "description": "Test plan",
                "price_brl": 100.0,
                "duration_days": None,
                "max_searches": 10,
                "is_active": True,
            },
        ]
        sb = _mock_sb(data=plans_data)
        mock_caps.return_value = {}

        client = _create_client(mock_db=sb)
        resp = client.get("/api/plans")

        assert resp.status_code == 200
        assert resp.json()["plans"][0]["duration_days"] == 30

    @patch("quota.get_plan_capabilities")
    def test_plans_ordered_by_price(self, mock_caps):
        """Verify that plans maintain the price-ordered query result."""
        plans_data = [
            {"id": "cheap", "name": "Cheap", "description": "Cheap", "price_brl": 50.0, "duration_days": 30, "max_searches": 5, "is_active": True},
            {"id": "mid", "name": "Mid", "description": "Mid", "price_brl": 200.0, "duration_days": 30, "max_searches": 20, "is_active": True},
            {"id": "expensive", "name": "Expensive", "description": "Expensive", "price_brl": 500.0, "duration_days": 30, "max_searches": 100, "is_active": True},
        ]
        sb = _mock_sb(data=plans_data)
        mock_caps.return_value = {}

        client = _create_client(mock_db=sb)
        resp = client.get("/api/plans")

        assert resp.status_code == 200
        prices = [p["price_brl"] for p in resp.json()["plans"]]
        assert prices == [50.0, 200.0, 500.0]
        assert resp.json()["total"] == 3
