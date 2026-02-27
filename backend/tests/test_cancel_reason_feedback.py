"""Tests for cancel reason + feedback endpoints (UX-308)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


@pytest.fixture
def test_user():
    return {"id": "test-user-ux308-001", "email": "ux308@test.com"}


@pytest.fixture
def client(test_user):
    """Create test client with auth override."""
    from main import app
    from auth import require_auth

    app.dependency_overrides[require_auth] = lambda: test_user
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def _mock_active_subscription(sb_mock):
    """Setup mock for an active subscription query."""
    subscription_data = {
        "id": "sub-local-ux308",
        "plan_id": "smartlic_pro",
        "billing_period": "monthly",
        "stripe_subscription_id": "sub_stripe_ux308",
        "is_active": True,
    }
    sb_mock.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
        data=[subscription_data]
    )
    return subscription_data


def _mock_stripe_modify():
    """Return a mock Stripe subscription with period end."""
    period_end_ts = int((datetime.now(timezone.utc) + timedelta(days=25)).timestamp())
    mock_sub = Mock()
    mock_sub.current_period_end = period_end_ts
    mock_sub.cancel_at_period_end = True
    return mock_sub


class TestCancelWithReason:
    """AC1: Cancel endpoint accepts reason field."""

    @patch("routes.subscriptions.os.getenv", return_value="sk_test_fake")
    @patch("supabase_client.get_supabase")
    def test_cancel_with_reason_too_expensive(self, mock_get_supabase, mock_getenv, client):
        """Cancel with reason='too_expensive' succeeds and logs reason."""
        import stripe as stripe_lib

        sb_mock = MagicMock()
        mock_get_supabase.return_value = sb_mock
        _mock_active_subscription(sb_mock)
        sb_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{}])

        with patch.object(stripe_lib.Subscription, "modify", return_value=_mock_stripe_modify()):
            with patch("routes.subscriptions.log_user_action") as mock_log:
                response = client.post(
                    "/v1/api/subscriptions/cancel",
                    json={"reason": "too_expensive"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ends_at" in data

        # Verify reason is logged
        mock_log.assert_called_once()
        log_details = mock_log.call_args[1].get("details") or mock_log.call_args[0][3]
        assert log_details["reason"] == "too_expensive"

    @patch("routes.subscriptions.os.getenv", return_value="sk_test_fake")
    @patch("supabase_client.get_supabase")
    def test_cancel_with_reason_not_using(self, mock_get_supabase, mock_getenv, client):
        """Cancel with reason='not_using' succeeds."""
        import stripe as stripe_lib

        sb_mock = MagicMock()
        mock_get_supabase.return_value = sb_mock
        _mock_active_subscription(sb_mock)
        sb_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{}])

        with patch.object(stripe_lib.Subscription, "modify", return_value=_mock_stripe_modify()):
            response = client.post(
                "/v1/api/subscriptions/cancel",
                json={"reason": "not_using"},
            )

        assert response.status_code == 200
        assert response.json()["success"] is True

    @patch("routes.subscriptions.os.getenv", return_value="sk_test_fake")
    @patch("supabase_client.get_supabase")
    def test_cancel_without_reason_backward_compat(self, mock_get_supabase, mock_getenv, client):
        """Cancel without body still works (backward compatibility)."""
        import stripe as stripe_lib

        sb_mock = MagicMock()
        mock_get_supabase.return_value = sb_mock
        _mock_active_subscription(sb_mock)
        sb_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{}])

        with patch.object(stripe_lib.Subscription, "modify", return_value=_mock_stripe_modify()):
            with patch("routes.subscriptions.log_user_action") as mock_log:
                response = client.post("/v1/api/subscriptions/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # reason should be None when not provided
        mock_log.assert_called_once()
        log_details = mock_log.call_args[1].get("details") or mock_log.call_args[0][3]
        assert log_details["reason"] is None

    @patch("routes.subscriptions.os.getenv", return_value="sk_test_fake")
    @patch("supabase_client.get_supabase")
    def test_cancel_with_invalid_reason_normalizes_to_other(self, mock_get_supabase, mock_getenv, client):
        """Invalid reason values are normalized to 'other'."""
        import stripe as stripe_lib

        sb_mock = MagicMock()
        mock_get_supabase.return_value = sb_mock
        _mock_active_subscription(sb_mock)
        sb_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{}])

        with patch.object(stripe_lib.Subscription, "modify", return_value=_mock_stripe_modify()):
            with patch("routes.subscriptions.log_user_action") as mock_log:
                response = client.post(
                    "/v1/api/subscriptions/cancel",
                    json={"reason": "invalid_reason_xyz"},
                )

        assert response.status_code == 200
        mock_log.assert_called_once()
        log_details = mock_log.call_args[1].get("details") or mock_log.call_args[0][3]
        assert log_details["reason"] == "other"

    @patch("routes.subscriptions.os.getenv", return_value="sk_test_fake")
    @patch("supabase_client.get_supabase")
    def test_cancel_with_all_valid_reasons(self, mock_get_supabase, mock_getenv, client):
        """All 5 valid reason values are accepted."""
        import stripe as stripe_lib

        valid_reasons = ["too_expensive", "not_using", "missing_features", "found_alternative", "other"]

        for reason in valid_reasons:
            sb_mock = MagicMock()
            mock_get_supabase.return_value = sb_mock
            _mock_active_subscription(sb_mock)
            sb_mock.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(data=[{}])

            with patch.object(stripe_lib.Subscription, "modify", return_value=_mock_stripe_modify()):
                with patch("routes.subscriptions.log_user_action") as mock_log:
                    response = client.post(
                        "/v1/api/subscriptions/cancel",
                        json={"reason": reason},
                    )

            assert response.status_code == 200, f"Failed for reason={reason}"
            log_details = mock_log.call_args[1].get("details") or mock_log.call_args[0][3]
            assert log_details["reason"] == reason


class TestCancelFeedback:
    """AC6: Post-cancellation feedback endpoint."""

    def test_submit_feedback_success(self, client):
        """Feedback is accepted and logged."""
        with patch("routes.subscriptions.log_user_action") as mock_log:
            response = client.post(
                "/v1/api/subscriptions/cancel-feedback",
                json={"feedback": "O preço não cabe no meu orçamento atual."},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Obrigado pelo feedback!"

        mock_log.assert_called_once()
        assert mock_log.call_args[0][1] == "subscription-cancel-feedback"

    def test_submit_feedback_empty_rejected(self, client):
        """Empty feedback is rejected by validation."""
        response = client.post(
            "/v1/api/subscriptions/cancel-feedback",
            json={"feedback": ""},
        )

        assert response.status_code == 422  # Pydantic validation

    def test_submit_feedback_missing_field(self, client):
        """Missing feedback field is rejected."""
        response = client.post(
            "/v1/api/subscriptions/cancel-feedback",
            json={},
        )

        assert response.status_code == 422

    def test_submit_feedback_truncated_at_2000(self, client):
        """Long feedback is accepted (max_length enforced by Pydantic)."""
        long_feedback = "x" * 2000
        with patch("routes.subscriptions.log_user_action"):
            response = client.post(
                "/v1/api/subscriptions/cancel-feedback",
                json={"feedback": long_feedback},
            )

        assert response.status_code == 200

    def test_submit_feedback_over_2000_rejected(self, client):
        """Feedback over 2000 chars is rejected."""
        response = client.post(
            "/v1/api/subscriptions/cancel-feedback",
            json={"feedback": "x" * 2001},
        )

        assert response.status_code == 422
