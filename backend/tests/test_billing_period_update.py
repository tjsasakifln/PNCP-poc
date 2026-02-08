"""Tests for billing period update functionality (STORY-171).

Tests successful billing period updates (monthly → annual) with pro-rata
credit calculations, Stripe integration mocking, and database updates.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal


class TestBillingPeriodUpdateSuccess:
    """Test successful billing period updates."""

    @patch("routes.subscriptions.get_supabase")
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

        # Mock user
        user = {"id": "test-user-123", "email": "test@example.com"}

        # Mock Supabase responses
        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock subscription fetch
        subscription_data = {
            "id": "sub-123",
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe123",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
        }
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock plan pricing fetch
        plan_data = {
            "price_brl": 297.00,
            "stripe_price_id": "price_monthly123",
        }
        sb_mock.table().select().eq().single().execute.return_value = Mock(data=plan_data)

        # Mock next billing date
        next_billing = datetime.now(timezone.utc) + timedelta(days=15)
        mock_get_next_billing.return_value = next_billing

        # Mock Stripe update
        mock_update_stripe.return_value = {"id": "sub_stripe123", "status": "active"}

        # Mock database update
        sb_mock.table().update().eq().execute.return_value = Mock(data=[{"success": True}])

        # Execute request
        request = UpdateBillingPeriodRequest(
            new_billing_period="annual",
            user_timezone="America/Sao_Paulo"
        )

        with patch("routes.subscriptions.require_auth", return_value=user):
            # Import the function that uses the dependency
            import asyncio
            response = asyncio.run(update_billing_period(request, user))

        # Assertions
        assert response.success is True
        assert response.new_billing_period == "annual"
        assert response.deferred is False
        assert Decimal(response.prorated_credit) > 0  # Should have credit for 15 days

    @patch("routes.subscriptions.get_supabase")
    @patch("routes.subscriptions.get_next_billing_date")
    def test_update_deferred_when_less_than_7_days(
        self,
        mock_get_next_billing,
        mock_supabase
    ):
        """Test that update is deferred when < 7 days until renewal."""
        from routes.subscriptions import update_billing_period, UpdateBillingPeriodRequest

        user = {"id": "test-user-123", "email": "test@example.com"}

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock subscription with 5 days until renewal
        subscription_data = {
            "id": "sub-123",
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe123",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        }
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock plan pricing
        plan_data = {"price_brl": 297.00, "stripe_price_id": "price_monthly123"}
        sb_mock.table().select().eq().single().execute.return_value = Mock(data=plan_data)

        # Mock next billing date (5 days from now)
        next_billing = datetime.now(timezone.utc) + timedelta(days=5)
        mock_get_next_billing.return_value = next_billing

        request = UpdateBillingPeriodRequest(
            new_billing_period="annual",
            user_timezone="America/Sao_Paulo"
        )

        import asyncio
        response = asyncio.run(update_billing_period(request, user))

        # Should be deferred
        assert response.success is True
        assert response.deferred is True
        assert response.prorated_credit == "0.00"
        assert "próximo ciclo" in response.message.lower()

    @patch("routes.subscriptions.get_supabase")
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

    @patch("routes.subscriptions.get_supabase")
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
