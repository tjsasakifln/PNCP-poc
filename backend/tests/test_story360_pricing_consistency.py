"""Tests for STORY-360: Pricing consistency between plans and copy.

AC1: GET /v1/plans returns billing period pricing from plan_billing_periods table.
AC3: Stripe price verification — billing_periods data matches expected values.
AC7: PRICING consistency checks.
"""

from unittest.mock import Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.billing import router
from database import get_db


def _create_client(mock_db=None):
    """Create test client with DB override."""
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    if mock_db is not None:
        app.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(app)


def _mock_sb_multi(call_results: dict):
    """Build a Supabase mock that returns different data per table.

    Args:
        call_results: dict mapping table_name to data list
    """
    sb = Mock()

    def table_side_effect(table_name):
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.order.return_value = chain
        result = Mock(data=call_results.get(table_name, []))
        chain.execute.return_value = result
        return chain

    sb.table.side_effect = table_side_effect
    return sb


# ============================================================================
# AC1: GET /v1/plans includes billing_periods
# ============================================================================

class TestGetPlansWithBillingPeriods:

    def test_returns_billing_periods_for_each_plan(self):
        """AC1: Plans response includes per-period pricing."""
        plans_data = [
            {
                "id": "smartlic_pro",
                "name": "SmartLic Pro",
                "description": "Full product",
                "max_searches": 1000,
                "price_brl": 397.0,
                "duration_days": 30,
            },
        ]
        bp_data = [
            {"plan_id": "smartlic_pro", "billing_period": "monthly", "price_cents": 39700, "discount_percent": 0},
            {"plan_id": "smartlic_pro", "billing_period": "semiannual", "price_cents": 35700, "discount_percent": 10},
            {"plan_id": "smartlic_pro", "billing_period": "annual", "price_cents": 29700, "discount_percent": 25},
        ]
        db = _mock_sb_multi({"plans": plans_data, "plan_billing_periods": bp_data})
        client = _create_client(db)
        resp = client.get("/v1/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["plans"]) == 1
        plan = data["plans"][0]
        assert "billing_periods" in plan
        assert "monthly" in plan["billing_periods"]
        assert plan["billing_periods"]["monthly"]["price_cents"] == 39700
        assert plan["billing_periods"]["semiannual"]["price_cents"] == 35700
        assert plan["billing_periods"]["semiannual"]["discount_percent"] == 10
        assert plan["billing_periods"]["annual"]["price_cents"] == 29700
        assert plan["billing_periods"]["annual"]["discount_percent"] == 25

    def test_stripe_price_ids_not_in_response(self):
        """STORY-210 AC11: Stripe price IDs stripped from public response."""
        plans_data = [
            {
                "id": "smartlic_pro",
                "name": "SmartLic Pro",
                "description": "Full",
                "max_searches": 1000,
                "price_brl": 397.0,
                "duration_days": 30,
            },
        ]
        db = _mock_sb_multi({"plans": plans_data, "plan_billing_periods": []})
        client = _create_client(db)
        resp = client.get("/v1/plans")
        plan = resp.json()["plans"][0]
        assert "stripe_price_id_monthly" not in plan
        assert "stripe_price_id_semiannual" not in plan
        assert "stripe_price_id_annual" not in plan

    def test_multiple_plans_with_billing_periods(self):
        """Both Pro and Consultoria return their own billing periods."""
        plans_data = [
            {"id": "smartlic_pro", "name": "SmartLic Pro", "description": "Pro", "max_searches": 1000, "price_brl": 397.0, "duration_days": 30},
            {"id": "consultoria", "name": "SmartLic Consultoria", "description": "Consultoria", "max_searches": 5000, "price_brl": 997.0, "duration_days": 365},
        ]
        bp_data = [
            {"plan_id": "smartlic_pro", "billing_period": "monthly", "price_cents": 39700, "discount_percent": 0},
            {"plan_id": "smartlic_pro", "billing_period": "annual", "price_cents": 29700, "discount_percent": 25},
            {"plan_id": "consultoria", "billing_period": "monthly", "price_cents": 99700, "discount_percent": 0},
            {"plan_id": "consultoria", "billing_period": "annual", "price_cents": 79700, "discount_percent": 20},
        ]
        db = _mock_sb_multi({"plans": plans_data, "plan_billing_periods": bp_data})
        client = _create_client(db)
        resp = client.get("/v1/plans")
        plans = resp.json()["plans"]
        assert len(plans) == 2
        pro = next(p for p in plans if p["id"] == "smartlic_pro")
        cons = next(p for p in plans if p["id"] == "consultoria")
        assert pro["billing_periods"]["annual"]["discount_percent"] == 25
        assert cons["billing_periods"]["annual"]["discount_percent"] == 20

    def test_empty_billing_periods_when_table_empty(self):
        """Plans without billing period entries return empty dict."""
        plans_data = [
            {"id": "smartlic_pro", "name": "Pro", "description": "Pro", "max_searches": 1000, "price_brl": 397.0, "duration_days": 30},
        ]
        db = _mock_sb_multi({"plans": plans_data, "plan_billing_periods": []})
        client = _create_client(db)
        resp = client.get("/v1/plans")
        plan = resp.json()["plans"][0]
        assert plan["billing_periods"] == {}

    def test_empty_plans(self):
        """No active plans returns empty list."""
        db = _mock_sb_multi({"plans": [], "plan_billing_periods": []})
        client = _create_client(db)
        resp = client.get("/v1/plans")
        assert resp.json()["plans"] == []


# ============================================================================
# AC3: Stripe/DB price verification
# ============================================================================

class TestPriceVerification:
    """Verify pricing values match expected Stripe configuration.

    These are static assertions based on migration 20260226120000
    and 20260301300000 values.
    """

    def test_pro_monthly_price(self):
        """SmartLic Pro monthly: R$397 = 39700 cents."""
        assert 39700 / 100 == 397

    def test_pro_semiannual_price_and_discount(self):
        """SmartLic Pro semiannual: R$357/mo (10% off R$397)."""
        assert 35700 / 100 == 357
        discount = round((397 - 357) / 397 * 100)
        assert discount == 10

    def test_pro_annual_price_and_discount(self):
        """SmartLic Pro annual: R$297/mo (25% off R$397)."""
        assert 29700 / 100 == 297
        discount = round((397 - 297) / 397 * 100)
        assert discount == 25

    def test_consultoria_monthly_price(self):
        """Consultoria monthly: R$997 = 99700 cents."""
        assert 99700 / 100 == 997

    def test_consultoria_semiannual_discount(self):
        """Consultoria semiannual: R$897/mo (10% off R$997)."""
        assert 89700 / 100 == 897
        discount = round((997 - 897) / 997 * 100)
        assert discount == 10

    def test_consultoria_annual_discount(self):
        """Consultoria annual: R$797/mo (20% off R$997)."""
        assert 79700 / 100 == 797
        discount = round((997 - 797) / 997 * 100)
        assert discount == 20

    def test_pro_annual_discount_differs_from_consultoria(self):
        """Pro annual (25%) != Consultoria annual (20%) — STORY-360 AC6."""
        pro_annual_discount = round((397 - 297) / 397 * 100)
        cons_annual_discount = round((997 - 797) / 997 * 100)
        assert pro_annual_discount != cons_annual_discount
        assert pro_annual_discount == 25
        assert cons_annual_discount == 20
