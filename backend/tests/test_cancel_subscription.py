"""Tests for subscription cancellation endpoint (GTM-FIX-006)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


@pytest.fixture
def test_user():
    return {"id": "test-user-cancel-123", "email": "cancel@test.com"}


@pytest.fixture
def client(test_user):
    """Create test client with auth override."""
    from main import app
    from auth import require_auth

    app.dependency_overrides[require_auth] = lambda: test_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestCancelSubscriptionSuccess:
    """AC14: test_cancel_subscription_success"""

    @patch("routes.subscriptions.os.getenv")
    @patch("supabase_client.get_supabase")
    def test_cancel_subscription_success(self, mock_get_supabase, mock_getenv, client):
        """Successful cancellation sets cancel_at_period_end and updates profile."""
        import stripe as stripe_lib

        mock_getenv.return_value = "sk_test_fake"

        sb_mock = MagicMock()
        mock_get_supabase.return_value = sb_mock

        # Mock: active subscription found
        subscription_data = {
            "id": "sub-local-123",
            "plan_id": "smartlic_pro",
            "billing_period": "monthly",
            "stripe_subscription_id": "sub_stripe_cancel_123",
            "is_active": True,
        }
        sb_mock.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock: Stripe modify returns subscription with current_period_end
        period_end_ts = int((datetime.now(timezone.utc) + timedelta(days=25)).timestamp())
        mock_stripe_sub = Mock()
        mock_stripe_sub.current_period_end = period_end_ts
        mock_stripe_sub.cancel_at_period_end = True

        with patch.object(stripe_lib.Subscription, "modify", return_value=mock_stripe_sub) as mock_modify:
            # Mock profile update (chained calls for 2nd .table() call)
            sb_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{}])

            response = client.post("/v1/api/subscriptions/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ends_at" in data
        assert data["ends_at"] != ""

        # Verify Stripe was called with cancel_at_period_end=True
        mock_modify.assert_called_once()
        call_kwargs = mock_modify.call_args
        assert call_kwargs[1].get("cancel_at_period_end") is True or \
               (len(call_kwargs[0]) > 0 and call_kwargs[1].get("cancel_at_period_end") is True)


class TestCancelSubscriptionNoActive:
    """AC15: test_cancel_subscription_no_active_subscription"""

    @patch("supabase_client.get_supabase")
    def test_cancel_no_active_subscription(self, mock_get_supabase, client):
        """Returns 404 when user has no active subscription."""
        sb_mock = MagicMock()
        mock_get_supabase.return_value = sb_mock

        # Mock: no active subscription
        sb_mock.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=[]
        )

        response = client.post("/v1/api/subscriptions/cancel")

        assert response.status_code == 404
        assert "ativa" in response.json()["detail"].lower() or "assinatura" in response.json()["detail"].lower()

    @patch("supabase_client.get_supabase")
    def test_cancel_no_stripe_subscription_id(self, mock_get_supabase, client):
        """Returns 400 when subscription has no Stripe ID."""
        sb_mock = MagicMock()
        mock_get_supabase.return_value = sb_mock

        subscription_data = {
            "id": "sub-local-456",
            "plan_id": "smartlic_pro",
            "billing_period": "monthly",
            "stripe_subscription_id": None,
            "is_active": True,
        }
        sb_mock.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=[subscription_data]
        )

        response = client.post("/v1/api/subscriptions/cancel")

        assert response.status_code == 400
