"""Tests for routes.subscriptions — POST /api/subscriptions/update-billing-period.

STORY-224 Track 4 (AC25): Subscription billing period update route coverage.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from routes.subscriptions import router


MOCK_USER = {"id": "user-123-uuid", "email": "test@example.com", "role": "authenticated"}


def _create_client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    return TestClient(app)


def _mock_sb():
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.insert.return_value = sb
    sb.update.return_value = sb
    sb.eq.return_value = sb
    sb.order.return_value = sb
    sb.limit.return_value = sb
    sb.single.return_value = sb
    sb.execute.return_value = Mock(data=[])
    return sb


# ============================================================================
# POST /api/subscriptions/update-billing-period
# ============================================================================

class TestUpdateBillingPeriod:

    @patch("cache.redis_cache")
    @patch("routes.subscriptions.update_stripe_subscription_billing_period")
    @patch("routes.subscriptions.calculate_prorata_credit")
    @patch("routes.subscriptions.get_next_billing_date")
    @patch("supabase_client.get_supabase")
    def test_successful_update_monthly_to_annual(
        self, mock_get_sb, mock_next_billing, mock_prorata, mock_stripe_update, mock_redis
    ):
        sb = _mock_sb()
        next_billing = datetime.now(timezone.utc) + timedelta(days=20)

        # Step 1: fetch subscription
        sub_data = {
            "id": "sub-1",
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe_123",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }
        # Step 2: fetch plan pricing
        plan_data = {
            "price_brl": 297.0,
            "stripe_price_id": "price_main",
            "stripe_price_id_monthly": "price_monthly",
            "stripe_price_id_annual": "price_annual",
        }

        # Configure execute calls in sequence:
        # 1. subscription query
        # 2. plan query (single)
        # 3. DB update
        sb.execute.side_effect = [
            Mock(data=[sub_data]),    # subscription fetch
            Mock(data=plan_data),     # plan fetch (single)
            Mock(data=[]),            # DB update
        ]
        mock_get_sb.return_value = sb

        mock_next_billing.return_value = next_billing

        # ProRata result: not deferred
        from services.billing import ProRataResult
        mock_prorata.return_value = ProRataResult(
            prorated_credit=Decimal("45.00"),
            days_until_renewal=20,
            deferred=False,
            next_billing_date=next_billing,
            reason=None,
        )

        mock_redis.delete = AsyncMock()

        client = _create_client()
        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "annual",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["new_billing_period"] == "annual"
        assert body["deferred"] is False
        assert body["prorated_credit"] == "45.00"
        mock_stripe_update.assert_called_once()

    @patch("supabase_client.get_supabase")
    def test_no_active_subscription_404(self, mock_get_sb):
        sb = _mock_sb()
        sb.execute.return_value = Mock(data=[])  # No subscription found
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "annual",
        })

        assert resp.status_code == 404
        assert "assinatura ativa" in resp.json()["detail"].lower()

    @patch("supabase_client.get_supabase")
    def test_already_on_target_period_400(self, mock_get_sb):
        sb = _mock_sb()
        sub_data = {
            "id": "sub-1",
            "plan_id": "consultor_agil",
            "billing_period": "annual",  # Already annual
            "stripe_subscription_id": "sub_stripe_123",
            "expires_at": None,
        }
        sb.execute.return_value = Mock(data=[sub_data])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "annual",
        })

        assert resp.status_code == 400
        assert "annual" in resp.json()["detail"].lower()

    @patch("supabase_client.get_supabase")
    def test_no_stripe_subscription_id_400(self, mock_get_sb):
        sb = _mock_sb()
        sub_data = {
            "id": "sub-1",
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "stripe_subscription_id": None,  # No Stripe ID
            "expires_at": None,
        }
        sb.execute.return_value = Mock(data=[sub_data])
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "annual",
        })

        assert resp.status_code == 400
        assert "stripe" in resp.json()["detail"].lower()

    @patch("cache.redis_cache")
    @patch("routes.subscriptions.update_stripe_subscription_billing_period")
    @patch("routes.subscriptions.calculate_prorata_credit")
    @patch("routes.subscriptions.get_next_billing_date")
    @patch("supabase_client.get_supabase")
    def test_deferred_update_returns_early(
        self, mock_get_sb, mock_next_billing, mock_prorata, mock_stripe_update, mock_redis
    ):
        sb = _mock_sb()
        next_billing = datetime.now(timezone.utc) + timedelta(days=5)  # < 7 days

        sub_data = {
            "id": "sub-1",
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe_123",
            "expires_at": None,
        }
        plan_data = {
            "price_brl": 297.0,
            "stripe_price_id": "price_main",
            "stripe_price_id_monthly": "price_monthly",
            "stripe_price_id_annual": "price_annual",
        }
        sb.execute.side_effect = [
            Mock(data=[sub_data]),
            Mock(data=plan_data),
        ]
        mock_get_sb.return_value = sb

        mock_next_billing.return_value = next_billing

        from services.billing import ProRataResult
        mock_prorata.return_value = ProRataResult(
            prorated_credit=Decimal("0.00"),
            days_until_renewal=5,
            deferred=True,
            next_billing_date=next_billing,
            reason="Less than 7 days to renewal",
        )

        client = _create_client()
        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "annual",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["deferred"] is True
        assert body["prorated_credit"] == "0.00"
        # Stripe should NOT be called when deferred
        mock_stripe_update.assert_not_called()

    @patch("routes.subscriptions.update_stripe_subscription_billing_period")
    @patch("routes.subscriptions.calculate_prorata_credit")
    @patch("routes.subscriptions.get_next_billing_date")
    @patch("supabase_client.get_supabase")
    def test_stripe_failure_500(
        self, mock_get_sb, mock_next_billing, mock_prorata, mock_stripe_update
    ):
        sb = _mock_sb()
        next_billing = datetime.now(timezone.utc) + timedelta(days=20)

        sub_data = {
            "id": "sub-1",
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe_123",
            "expires_at": None,
        }
        plan_data = {
            "price_brl": 297.0,
            "stripe_price_id": "price_main",
            "stripe_price_id_monthly": "price_monthly",
            "stripe_price_id_annual": "price_annual",
        }
        sb.execute.side_effect = [
            Mock(data=[sub_data]),
            Mock(data=plan_data),
        ]
        mock_get_sb.return_value = sb

        mock_next_billing.return_value = next_billing

        from services.billing import ProRataResult
        mock_prorata.return_value = ProRataResult(
            prorated_credit=Decimal("45.00"),
            days_until_renewal=20,
            deferred=False,
            next_billing_date=next_billing,
        )

        mock_stripe_update.side_effect = Exception("Stripe API error")

        client = _create_client()
        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "annual",
        })

        assert resp.status_code == 500
        assert "stripe" in resp.json()["detail"].lower()

    @patch("routes.subscriptions.get_next_billing_date")
    @patch("supabase_client.get_supabase")
    def test_no_next_billing_date_400(self, mock_get_sb, mock_next_billing):
        sb = _mock_sb()
        sub_data = {
            "id": "sub-1",
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe_123",
            "expires_at": None,
        }
        plan_data = {
            "price_brl": 297.0,
            "stripe_price_id": "price_main",
            "stripe_price_id_monthly": None,
            "stripe_price_id_annual": None,
        }
        sb.execute.side_effect = [
            Mock(data=[sub_data]),
            Mock(data=plan_data),
        ]
        mock_get_sb.return_value = sb
        mock_next_billing.return_value = None  # Cannot determine billing date

        client = _create_client()
        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "annual",
        })

        assert resp.status_code == 400
        assert "data de cobran" in resp.json()["detail"].lower()

    def test_invalid_billing_period_422(self):
        client = _create_client()
        resp = client.post("/api/subscriptions/update-billing-period", json={
            "new_billing_period": "quarterly",
        })
        assert resp.status_code == 422
