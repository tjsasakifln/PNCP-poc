"""Tests for billing period update functionality (GTM-002).

Tests successful billing period updates (monthly → annual/semiannual)
with Stripe integration mocking and database updates.
No pro-rata calculations — Stripe handles proration automatically.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta


class TestBillingPeriodUpdateSuccess:
    """Test successful billing period updates."""

    @patch("supabase_client.get_supabase")
    @patch("routes.subscriptions.update_stripe_subscription_billing_period")
    @patch("routes.subscriptions.get_next_billing_date")
    def test_update_monthly_to_annual_15_days_remaining(
        self,
        mock_get_next_billing,
        mock_update_stripe,
        mock_supabase
    ):
        """Test monthly → annual with 15 days until renewal."""
        from routes.subscriptions import update_billing_period, UpdateBillingPeriodRequest

        user = {"id": "test-user-123", "email": "test@example.com"}

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        subscription_data = {
            "id": "sub-123",
            "plan_id": "smartlic_pro",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe123",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
        }
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        plan_data = {
            "price_brl": 1999.00,
            "stripe_price_id_annual": "price_annual123",
        }
        sb_mock.table().select().eq().single().execute.return_value = Mock(data=plan_data)

        next_billing = datetime.now(timezone.utc) + timedelta(days=15)
        mock_get_next_billing.return_value = next_billing

        mock_update_stripe.return_value = {"id": "sub_stripe123", "status": "active"}

        sb_mock.table().update().eq().execute.return_value = Mock(data=[{"success": True}])

        request = UpdateBillingPeriodRequest(new_billing_period="annual")

        with patch("routes.subscriptions.require_auth", return_value=user):
            import asyncio
            response = asyncio.run(update_billing_period(request, user))

        assert response.success is True
        assert response.new_billing_period == "annual"
        assert response.next_billing_date is not None

    @patch("supabase_client.get_supabase")
    @patch("routes.subscriptions.update_stripe_subscription_billing_period")
    @patch("routes.subscriptions.get_next_billing_date")
    def test_update_monthly_to_semiannual(
        self,
        mock_get_next_billing,
        mock_update_stripe,
        mock_supabase
    ):
        """Test monthly → semiannual billing period update."""
        from routes.subscriptions import update_billing_period, UpdateBillingPeriodRequest

        user = {"id": "test-user-123", "email": "test@example.com"}

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        subscription_data = {
            "id": "sub-123",
            "plan_id": "smartlic_pro",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe123",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        }
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        plan_data = {"price_brl": 1999.00, "stripe_price_id_semiannual": "price_semi123"}
        sb_mock.table().select().eq().single().execute.return_value = Mock(data=plan_data)

        next_billing = datetime.now(timezone.utc) + timedelta(days=5)
        mock_get_next_billing.return_value = next_billing

        mock_update_stripe.return_value = {"id": "sub_stripe123", "status": "active"}

        sb_mock.table().update().eq().execute.return_value = Mock(data=[{"success": True}])

        request = UpdateBillingPeriodRequest(new_billing_period="semiannual")

        import asyncio
        response = asyncio.run(update_billing_period(request, user))

        assert response.success is True
        assert response.new_billing_period == "semiannual"

    @patch("supabase_client.get_supabase")
    def test_error_when_no_active_subscription(self, mock_supabase):
        """Test 404 error when user has no active subscription."""
        from routes.subscriptions import update_billing_period, UpdateBillingPeriodRequest
        from fastapi import HTTPException

        user = {"id": "test-user-123", "email": "test@example.com"}

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock empty subscription result
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(data=[])

        request = UpdateBillingPeriodRequest(new_billing_period="annual")

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_billing_period(request, user))

        assert exc_info.value.status_code == 404
        assert "assinatura ativa" in exc_info.value.detail.lower()

    @patch("supabase_client.get_supabase")
    def test_error_when_already_on_target_billing_period(self, mock_supabase):
        """Test 400 error when already on target billing period."""
        from routes.subscriptions import update_billing_period, UpdateBillingPeriodRequest
        from fastapi import HTTPException

        user = {"id": "test-user-123", "email": "test@example.com"}

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock subscription already on annual billing
        subscription_data = {
            "id": "sub-123",
            "plan_id": "consultor_agil",
            "billing_period": "annual",  # Already annual
            "stripe_subscription_id": "sub_stripe123",
        }
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        request = UpdateBillingPeriodRequest(new_billing_period="annual")

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_billing_period(request, user))

        assert exc_info.value.status_code == 400
        assert "já está" in exc_info.value.detail.lower()
