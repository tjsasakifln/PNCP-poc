"""
Tests for GTM-FIX-009: Email confirmation recovery endpoints.

AC13: test_resend_confirmation_rate_limit
AC14: test_auth_status_returns_confirmation_state
"""

import time
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with auth_email router."""
    from fastapi import FastAPI
    from routes.auth_email import router, _resend_timestamps

    app = FastAPI()
    app.include_router(router, prefix="/v1")

    # Clear rate limit state between tests
    _resend_timestamps.clear()

    yield TestClient(app)

    _resend_timestamps.clear()


class TestResendConfirmation:
    """AC13: test_resend_confirmation_rate_limit."""

    @patch("supabase_client.get_supabase")
    def test_resend_success(self, mock_get_supabase, client):
        """First resend should succeed."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        response = client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reenviado" in data["message"].lower()
        mock_supabase.auth.resend.assert_called_once_with({
            "type": "signup",
            "email": "test@example.com"
        })

    @patch("supabase_client.get_supabase")
    def test_resend_rate_limited_within_60s(self, mock_get_supabase, client):
        """Second resend within 60s should be blocked (429)."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # First request succeeds
        client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "test@example.com"}
        )

        # Second request within 60s should be rate limited
        response = client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 429
        assert "aguarde" in response.json()["detail"].lower()

    @patch("supabase_client.get_supabase")
    def test_resend_allowed_after_cooldown(self, mock_get_supabase, client):
        """Resend should work again after 60s cooldown."""
        from routes.auth_email import _resend_timestamps

        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # Simulate a resend 61 seconds ago
        _resend_timestamps["test@example.com"] = time.time() - 61

        response = client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    @patch("supabase_client.get_supabase")
    def test_resend_case_insensitive(self, mock_get_supabase, client):
        """Rate limiting should be case-insensitive."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # First request with lowercase
        client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "Test@Example.COM"}
        )

        # Same email different case should be rate limited
        response = client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 429

    def test_resend_invalid_email(self, client):
        """Invalid email should return 422."""
        response = client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "not-an-email"}
        )

        assert response.status_code == 422

    @patch("supabase_client.get_supabase")
    def test_resend_supabase_error(self, mock_get_supabase, client):
        """Supabase failure should return 500."""
        mock_supabase = MagicMock()
        mock_supabase.auth.resend.side_effect = Exception("Network error")
        mock_get_supabase.return_value = mock_supabase

        response = client.post(
            "/v1/auth/resend-confirmation",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 500


class TestAuthStatus:
    """AC14: test_auth_status_returns_confirmation_state."""

    @patch("supabase_client.get_supabase")
    def test_status_confirmed(self, mock_get_supabase, client):
        """Should return confirmed=True for confirmed users."""
        mock_user = MagicMock()
        mock_user.email = "confirmed@example.com"
        mock_user.email_confirmed_at = "2026-01-01T00:00:00Z"
        mock_user.id = "user-123"

        mock_supabase = MagicMock()
        mock_supabase.auth.admin.list_users.return_value = [mock_user]
        mock_get_supabase.return_value = mock_supabase

        response = client.get("/v1/auth/status?email=confirmed@example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["confirmed"] is True
        assert data["user_id"] == "user-123"

    @patch("supabase_client.get_supabase")
    def test_status_not_confirmed(self, mock_get_supabase, client):
        """Should return confirmed=False for unconfirmed users."""
        mock_user = MagicMock()
        mock_user.email = "unconfirmed@example.com"
        mock_user.email_confirmed_at = None
        mock_user.id = "user-456"

        mock_supabase = MagicMock()
        mock_supabase.auth.admin.list_users.return_value = [mock_user]
        mock_get_supabase.return_value = mock_supabase

        response = client.get("/v1/auth/status?email=unconfirmed@example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["confirmed"] is False

    @patch("supabase_client.get_supabase")
    def test_status_user_not_found(self, mock_get_supabase, client):
        """Should return confirmed=False for unknown emails."""
        mock_supabase = MagicMock()
        mock_supabase.auth.admin.list_users.return_value = []
        mock_get_supabase.return_value = mock_supabase

        response = client.get("/v1/auth/status?email=unknown@example.com")

        assert response.status_code == 200
        assert response.json()["confirmed"] is False

    def test_status_missing_email(self, client):
        """Should return 422 when email param is missing."""
        response = client.get("/v1/auth/status")
        assert response.status_code == 422

    @patch("supabase_client.get_supabase")
    def test_status_supabase_error(self, mock_get_supabase, client):
        """Supabase failure should gracefully return confirmed=False."""
        mock_supabase = MagicMock()
        mock_supabase.auth.admin.list_users.side_effect = Exception("DB down")
        mock_get_supabase.return_value = mock_supabase

        response = client.get("/v1/auth/status?email=test@example.com")

        assert response.status_code == 200
        assert response.json()["confirmed"] is False

    @patch("supabase_client.get_supabase")
    def test_status_case_insensitive(self, mock_get_supabase, client):
        """Email matching should be case-insensitive."""
        mock_user = MagicMock()
        mock_user.email = "User@Example.COM"
        mock_user.email_confirmed_at = "2026-01-01T00:00:00Z"
        mock_user.id = "user-789"

        mock_supabase = MagicMock()
        mock_supabase.auth.admin.list_users.return_value = [mock_user]
        mock_get_supabase.return_value = mock_supabase

        response = client.get("/v1/auth/status?email=user@example.com")

        assert response.status_code == 200
        assert response.json()["confirmed"] is True
