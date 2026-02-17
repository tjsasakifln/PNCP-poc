"""Tests for invoice.payment_failed webhook handler (GTM-FIX-007 Track 1).

Tests webhook event handling, status updates, email sending, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone


class TestInvoicePaymentFailedWebhook:
    """Test invoice.payment_failed webhook handling."""

    @patch("supabase_client.get_supabase")
    async def test_invoice_payment_failed_updates_status(self, mock_supabase):
        """
        Test that payment failure updates subscription_status to past_due (AC11).
        """
        from webhooks.stripe import _handle_invoice_payment_failed

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock subscription lookup
        subscription_data = {
            "id": "sub-123",
            "user_id": "user-456",
            "plan_id": "smartlic_pro",
        }
        sb_mock.table().select().eq().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock update operations
        update_mock = Mock()
        update_mock.eq().execute.return_value = Mock(data=[{"success": True}])
        sb_mock.table().update.return_value = update_mock

        # Create mock Stripe event
        event = Mock()
        event.data = Mock()
        event.data.object = {
            "customer": "cus_stripe123",
            "subscription": "sub_stripe123",
            "amount_due": 199900,  # R$ 1,999.00 in cents
            "attempt_count": 1,
        }

        # Handle event
        await _handle_invoice_payment_failed(sb_mock, event)

        # Verify subscription status updated to past_due
        # Check the update() calls - should have {"subscription_status": "past_due"}
        update_calls = sb_mock.table().update.call_args_list
        status_updates = [
            call for call in update_calls
            if call[0][0].get("subscription_status") == "past_due"
        ]
        assert len(status_updates) >= 1, "subscription_status should be updated to past_due"

    @patch("supabase_client.get_supabase")
    @patch("webhooks.stripe._send_payment_failed_email")
    async def test_invoice_payment_failed_sends_email(
        self, mock_send_email, mock_supabase
    ):
        """
        Test that payment failure triggers email notification (AC12).
        """
        from webhooks.stripe import _handle_invoice_payment_failed

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        subscription_data = {
            "id": "sub-123",
            "user_id": "user-456",
            "plan_id": "smartlic_pro",
        }
        sb_mock.table().select().eq().limit().execute.return_value = Mock(
            data=[subscription_data]
        )
        sb_mock.table().update().eq().execute.return_value = Mock(data=[{"success": True}])

        event = Mock()
        event.data = Mock()
        event.data.object = {
            "customer": "cus_stripe123",
            "subscription": "sub_stripe123",
            "amount_due": 199900,
            "attempt_count": 2,
        }

        await _handle_invoice_payment_failed(sb_mock, event)

        # Verify email send was called
        assert mock_send_email.called, "Payment failed email should be sent"
        call_args = mock_send_email.call_args
        assert call_args[0][1] == "user-456", "Email should be sent to correct user_id"
        assert call_args[0][2] == "smartlic_pro", "Email should include correct plan_id"

    @patch("supabase_client.get_supabase")
    async def test_invoice_payment_failed_no_subscription(self, mock_supabase):
        """
        Test graceful handling when no local subscription found.
        """
        from webhooks.stripe import _handle_invoice_payment_failed

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock empty subscription result
        sb_mock.table().select().eq().limit().execute.return_value = Mock(data=[])

        event = Mock()
        event.data = Mock()
        event.data.object = {
            "customer": "cus_unknown",
            "subscription": "sub_unknown",
            "amount_due": 199900,
            "attempt_count": 1,
        }

        # Should not raise exception
        await _handle_invoice_payment_failed(sb_mock, event)

        # Verify no update was attempted
        update_calls = [call for call in sb_mock.method_calls if "update" in str(call)]
        assert len(update_calls) == 0, "No updates should happen for unknown subscription"

    @patch("supabase_client.get_supabase")
    async def test_invoice_payment_failed_extracts_attempt_count(self, mock_supabase):
        """
        Test that attempt_count is correctly extracted from invoice data.
        """
        from webhooks.stripe import _handle_invoice_payment_failed

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        subscription_data = {
            "id": "sub-123",
            "user_id": "user-456",
            "plan_id": "smartlic_pro",
        }
        sb_mock.table().select().eq().limit().execute.return_value = Mock(
            data=[subscription_data]
        )
        sb_mock.table().update().eq().execute.return_value = Mock(data=[{"success": True}])

        event = Mock()
        event.data = Mock()
        event.data.object = {
            "customer": "cus_stripe123",
            "subscription": "sub_stripe123",
            "amount_due": 199900,
            "attempt_count": 3,  # 3rd retry attempt
        }

        # Mock logging to capture attempt_count
        with patch("webhooks.stripe.logger") as mock_logger:
            await _handle_invoice_payment_failed(sb_mock, event)

            # Check if attempt_count was logged
            info_calls = [
                call for call in mock_logger.info.call_args_list
                if "payment_failed_event" in str(call)
            ]
            assert len(info_calls) > 0, "Should log payment_failed_event"

            # Verify attempt_count in log extras
            log_call = info_calls[0]
            if len(log_call[1]) > 0 and "extra" in log_call[1]:
                extras = log_call[1]["extra"]
                assert extras.get("attempt_count") == 3, "Should log correct attempt_count"

    @patch("supabase_client.get_supabase")
    async def test_invoice_payment_failed_no_subscription_id(self, mock_supabase):
        """
        Test handling of invoice without subscription_id (one-time payment).
        """
        from webhooks.stripe import _handle_invoice_payment_failed

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        event = Mock()
        event.data = Mock()
        event.data.object = {
            "customer": "cus_stripe123",
            "subscription": None,  # No subscription
            "amount_due": 199900,
            "attempt_count": 1,
        }

        # Should exit early without errors
        await _handle_invoice_payment_failed(sb_mock, event)

        # Verify no DB operations were attempted
        select_calls = [call for call in sb_mock.method_calls if "select" in str(call)]
        assert len(select_calls) == 0, "Should exit early without DB queries"


class TestPaymentFailedEmailTemplate:
    """Test payment failed email template rendering."""

    def test_render_payment_failed_email(self):
        """Test payment failed email template includes all required elements."""
        from templates.emails.billing import render_payment_failed_email

        html = render_payment_failed_email(
            user_name="João Silva",
            plan_name="SmartLic Pro",
            amount="R$ 1.999,00",
            failure_reason="Cartão recusado",
            days_until_cancellation=11,
        )

        # Verify email contains key elements (AC5-AC6)
        assert "João Silva" in html
        assert "SmartLic Pro" in html
        assert "R$ 1.999,00" in html
        assert "Cartão recusado" in html
        assert "11 dias" in html
        assert "Atualizar Forma de Pagamento" in html
        assert "/api/billing-portal" in html

    def test_render_payment_failed_email_single_day(self):
        """Test email template with 1 day remaining."""
        from templates.emails.billing import render_payment_failed_email

        html = render_payment_failed_email(
            user_name="Maria Santos",
            plan_name="SmartLic Pro",
            amount="R$ 1.999,00",
            failure_reason="Saldo insuficiente",
            days_until_cancellation=1,
        )

        # Verify singular form
        assert "1 dia" in html
        assert "Maria Santos" in html


class TestBillingPortalEndpoint:
    """Test billing portal endpoint (AC6-AC7)."""

    @patch("os.getenv")
    @patch("supabase_client.get_supabase")
    async def test_create_billing_portal_session_success(
        self, mock_supabase, mock_getenv
    ):
        """Test successful billing portal session creation."""
        from routes.billing import create_billing_portal_session

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "STRIPE_SECRET_KEY":
                return "sk_test_fake"
            elif key == "FRONTEND_URL":
                return "https://smartlic.tech"
            return default

        mock_getenv.side_effect = getenv_side_effect

        user = {"id": "user-123", "email": "test@example.com"}

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock active subscription with stripe_customer_id
        subscription_data = {
            "stripe_customer_id": "cus_stripe123",
        }
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock Stripe billing portal session
        with patch("stripe.billing_portal.Session.create") as mock_create:
            mock_create.return_value = Mock(url="https://billing.stripe.com/session/xyz")

            # Call endpoint
            result = await create_billing_portal_session(user=user, db=sb_mock)

            # Verify response
            assert result["url"] == "https://billing.stripe.com/session/xyz"
            assert mock_create.called

    @patch("os.getenv")
    @patch("supabase_client.get_supabase")
    async def test_create_billing_portal_no_active_subscription(
        self, mock_supabase, mock_getenv
    ):
        """Test error when user has no active subscription."""
        from routes.billing import create_billing_portal_session
        from fastapi import HTTPException

        # Mock environment variables
        mock_getenv.return_value = "sk_test_fake"

        user = {"id": "user-123", "email": "test@example.com"}

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock no active subscription
        sb_mock.table().select().eq().eq().order().limit().execute.return_value = Mock(
            data=[]
        )

        # Should raise 404
        with pytest.raises(HTTPException) as exc_info:
            await create_billing_portal_session(user=user, db=sb_mock)

        assert exc_info.value.status_code == 404
        assert "assinatura ativa" in exc_info.value.detail.lower()
