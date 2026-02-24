"""Tests for STORY-258 AC20-AC21: Pre-signup validation endpoints.

Endpoints:
- GET /v1/auth/check-email — disposable check, corporate detection
- GET /v1/auth/check-phone — phone uniqueness check

Rate limiting: 10 req/min/IP (per-IP, in-memory).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear per-IP rate limit state between tests."""
    import routes.auth_check as auth_check_module
    auth_check_module._rate_limits.clear()
    yield
    auth_check_module._rate_limits.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# GET /v1/auth/check-email
# ============================================================================

class TestCheckEmailEndpoint:
    """Tests for GET /v1/auth/check-email."""

    def test_disposable_email_returns_disposable_true(self, client):
        """AC15: Disposable domain returns disposable=true, available=true."""
        response = client.get("/v1/auth/check-email?email=user@tempmail.com")
        assert response.status_code == 200
        data = response.json()
        assert data["disposable"] is True
        assert data["available"] is True  # Never reveal block to prevent enumeration
        assert data["corporate"] is False

    def test_gmail_returns_disposable_false_corporate_false(self, client):
        """Personal email (Gmail) is not disposable and not corporate."""
        response = client.get("/v1/auth/check-email?email=user@gmail.com")
        assert response.status_code == 200
        data = response.json()
        assert data["disposable"] is False
        assert data["available"] is True
        assert data["corporate"] is False

    def test_outlook_is_personal_not_corporate(self, client):
        """Outlook is a personal provider — corporate=false."""
        response = client.get("/v1/auth/check-email?email=user@outlook.com")
        assert response.status_code == 200
        data = response.json()
        assert data["disposable"] is False
        assert data["corporate"] is False

    def test_hotmail_is_personal_not_corporate(self, client):
        """Hotmail is a personal provider — corporate=false."""
        response = client.get("/v1/auth/check-email?email=user@hotmail.com")
        assert response.status_code == 200
        data = response.json()
        assert data["disposable"] is False
        assert data["corporate"] is False

    def test_corporate_email_returns_corporate_true(self, client):
        """Corporate domain (not personal, not disposable) → corporate=true."""
        response = client.get("/v1/auth/check-email?email=contato@empresa.com.br")
        assert response.status_code == 200
        data = response.json()
        assert data["disposable"] is False
        assert data["corporate"] is True
        assert data["available"] is True

    def test_mailinator_returns_disposable_true(self, client):
        """Mailinator is disposable."""
        response = client.get("/v1/auth/check-email?email=test@mailinator.com")
        assert response.status_code == 200
        data = response.json()
        assert data["disposable"] is True

    def test_guerrillamail_returns_disposable_true(self, client):
        """Guerrillamail is disposable."""
        response = client.get("/v1/auth/check-email?email=test@guerrillamail.com")
        assert response.status_code == 200
        data = response.json()
        assert data["disposable"] is True

    def test_missing_email_param_returns_422(self, client):
        """Missing required email parameter returns 422."""
        response = client.get("/v1/auth/check-email")
        assert response.status_code == 422

    def test_email_too_short_returns_422(self, client):
        """Email shorter than min_length=5 returns 422."""
        response = client.get("/v1/auth/check-email?email=a@b")
        assert response.status_code == 422

    def test_rate_limit_enforced(self, client):
        """After 10 requests from same IP, 11th is rejected with 429."""
        import routes.auth_check as auth_check_module

        # Directly inject 10 timestamps within the last minute to simulate limit reached
        import time
        now = time.time()
        auth_check_module._rate_limits["testclient"] = [now] * 10

        response = client.get("/v1/auth/check-email?email=user@gmail.com")
        assert response.status_code == 429
        assert "Muitas" in response.json()["detail"]

    def test_response_shape_has_required_keys(self, client):
        """Response always contains available, disposable, corporate."""
        response = client.get("/v1/auth/check-email?email=user@gmail.com")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "disposable" in data
        assert "corporate" in data


# ============================================================================
# GET /v1/auth/check-phone
# ============================================================================

class TestCheckPhoneEndpoint:
    """Tests for GET /v1/auth/check-phone."""

    def test_available_phone_returns_true(self, client):
        """Phone not found in DB → available=true."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []  # No rows found
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute.return_value
        ) = mock_result

        with patch("supabase_client.get_supabase", return_value=mock_db):
            response = client.get("/v1/auth/check-phone?phone=(11) 99999-1234")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    def test_taken_phone_returns_false(self, client):
        """Phone found in DB → available=false."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": "some-user-id"}]  # Row found
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute.return_value
        ) = mock_result

        with patch("supabase_client.get_supabase", return_value=mock_db):
            response = client.get("/v1/auth/check-phone?phone=11999991234")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    def test_invalid_phone_format_returns_available_true(self, client):
        """Invalid phone format (normalization returns None) → available=true (fail open).

        Note: Query param min_length=8 means we need at least 8 chars; the phone
        "12345678" passes FastAPI validation but normalizes to None (8 digits is
        neither 10 nor 11 → invalid → available=true).
        """
        response = client.get("/v1/auth/check-phone?phone=12345678")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    def test_db_error_fails_open(self, client):
        """DB errors return available=true to not block signup."""
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
            response = client.get("/v1/auth/check-phone?phone=(11) 99999-1234")

        assert response.status_code == 200
        assert response.json()["available"] is True

    def test_missing_phone_param_returns_422(self, client):
        """Missing required phone parameter returns 422."""
        response = client.get("/v1/auth/check-phone")
        assert response.status_code == 422

    def test_phone_too_short_returns_422(self, client):
        """Phone shorter than min_length=8 returns 422."""
        response = client.get("/v1/auth/check-phone?phone=1234567")
        assert response.status_code == 422

    def test_rate_limit_phone_enforced(self, client):
        """Rate limit applies to check-phone as well (10 req/min/IP)."""
        import routes.auth_check as auth_check_module
        import time

        now = time.time()
        auth_check_module._rate_limits["testclient"] = [now] * 10

        response = client.get("/v1/auth/check-phone?phone=11999991234")
        assert response.status_code == 429

    def test_response_shape_has_available_key(self, client):
        """Response contains only available key (no data leakage)."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute.return_value
        ) = mock_result

        with patch("supabase_client.get_supabase", return_value=mock_db):
            response = client.get("/v1/auth/check-phone?phone=11999991234")

        assert response.status_code == 200
        data = response.json()
        # Only 'available' — no user data leaked
        assert "available" in data
        assert "user_id" not in data
        assert "email" not in data

    def test_phone_normalization_applied(self, client):
        """Phone is normalized before DB lookup — +55 prefix stripped."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        eq_mock = MagicMock()
        eq_mock.limit.return_value.execute.return_value = mock_result
        select_mock = MagicMock()
        select_mock.eq.return_value = eq_mock
        mock_db.table.return_value.select.return_value = select_mock

        with patch("supabase_client.get_supabase", return_value=mock_db):
            response = client.get("/v1/auth/check-phone?phone=%2B55+11+99999-1234")

        assert response.status_code == 200
        # Verify .eq was called with the normalized phone (11999991234), not raw
        call_args = select_mock.eq.call_args
        assert call_args is not None
        _, normalized_phone = call_args[0]
        assert normalized_phone == "11999991234"

    def test_check_phone_accepts_optional_company_param(self, client):
        """AC13: Optional company param is accepted without breaking the endpoint."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute.return_value
        ) = mock_result

        with patch("supabase_client.get_supabase", return_value=mock_db):
            response = client.get(
                "/v1/auth/check-phone?phone=11999991234&company=Empresa+ABC"
            )

        assert response.status_code == 200
        assert response.json()["available"] is True


# ============================================================================
# AC20 — Integration tests: disposable email detection
# ============================================================================

class TestSignupDisposableEmailIntegration:
    """AC20: Integration tests — disposable email detection via check-email endpoint."""

    def test_check_email_returns_disposable_true_for_known_domains(self, client):
        """AC20: Known disposable domains return disposable=true."""
        for domain in ["tempmail.com", "mailinator.com", "guerrillamail.com", "yopmail.com"]:
            response = client.get(f"/v1/auth/check-email?email=test@{domain}")
            assert response.status_code == 200, f"Expected 200 for {domain}"
            data = response.json()
            assert data["disposable"] is True, f"Expected disposable=true for {domain}"
            # AC15: available is always true to prevent enumeration
            assert data["available"] is True, f"Expected available=true for disposable domain {domain}"

    def test_check_email_returns_disposable_false_for_legitimate(self, client):
        """AC20: Legitimate email providers return disposable=false."""
        legitimate_emails = [
            "user@gmail.com",
            "user@outlook.com",
            "contato@empresa.com.br",
            "hello@minhafirma.net",
        ]
        for email in legitimate_emails:
            response = client.get(f"/v1/auth/check-email?email={email}")
            assert response.status_code == 200, f"Expected 200 for {email}"
            data = response.json()
            assert data["disposable"] is False, f"Expected disposable=false for {email}"

    def test_check_email_response_shape_complete(self, client):
        """AC20: Response always includes available, disposable, corporate."""
        response = client.get("/v1/auth/check-email?email=user@gmail.com")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) >= {"available", "disposable", "corporate"}

    def test_check_email_corporate_flag_set_for_business_domain(self, client):
        """AC20: Custom business domain sets corporate=true."""
        response = client.get("/v1/auth/check-email?email=contato@empresa.com.br")
        assert response.status_code == 200
        data = response.json()
        assert data["corporate"] is True

    def test_check_email_gmail_is_not_corporate(self, client):
        """AC20: Gmail is personal — corporate=false."""
        response = client.get("/v1/auth/check-email?email=user@gmail.com")
        assert response.status_code == 200
        data = response.json()
        assert data["corporate"] is False


# ============================================================================
# AC21 — Integration test: duplicate phone → available=false
# ============================================================================

class TestSignupDuplicatePhoneIntegration:
    """AC21: Integration tests — duplicate phone returns available=false."""

    def test_check_phone_returns_unavailable_for_existing(self, client):
        """AC21: When a profile with the phone exists, available=false is returned."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        # Simulate an existing profile row with that phone
        mock_result.data = [{"id": "existing-user-uuid"}]
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute.return_value
        ) = mock_result

        with patch("supabase_client.get_supabase", return_value=mock_db):
            response = client.get("/v1/auth/check-phone?phone=(11) 98765-4321")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False, "Phone already in use must return available=false"
        # Ensure no user data is leaked
        assert "id" not in data
        assert "email" not in data

    def test_check_phone_returns_available_for_new_number(self, client):
        """AC21: When no profile with the phone exists, available=true is returned."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []  # No rows — phone is free
        (
            mock_db.table.return_value
            .select.return_value
            .eq.return_value
            .limit.return_value
            .execute.return_value
        ) = mock_result

        with patch("supabase_client.get_supabase", return_value=mock_db):
            response = client.get("/v1/auth/check-phone?phone=11987654321")

        assert response.status_code == 200
        assert response.json()["available"] is True
