"""Tests for log_sanitizer module (Issue #168).

Tests cover:
- Email masking
- API key masking
- JWT/token masking
- User ID partial masking
- IP address masking
- Password redaction
- Phone number masking
- Dictionary sanitization
- String pattern sanitization
- Production environment detection
"""

import logging
import os
import pytest
from unittest.mock import patch

from log_sanitizer import (
    mask_email,
    mask_api_key,
    mask_token,
    mask_user_id,
    mask_ip_address,
    mask_password,
    mask_phone,
    sanitize_value,
    sanitize_dict,
    sanitize_string,
    sanitize,
    is_production,
    get_log_level,
    SanitizedLogAdapter,
    get_sanitized_logger,
    log_user_action,
    log_admin_action,
    log_auth_event,
)


class TestMaskEmail:
    """Tests for email masking."""

    def test_mask_normal_email(self):
        assert mask_email("user@example.com") == "u***@example.com"

    def test_mask_short_local_part(self):
        # Single character local part results in just "***"
        assert mask_email("a@test.org") == "***@test.org"

    def test_mask_long_email(self):
        assert mask_email("john.doe.smith@company.co.uk") == "j***@company.co.uk"

    def test_mask_none(self):
        assert mask_email(None) == "[no-email]"

    def test_mask_empty_string(self):
        assert mask_email("") == "[no-email]"

    def test_mask_invalid_email(self):
        assert mask_email("not-an-email") == "[invalid-email]"


class TestMaskApiKey:
    """Tests for API key masking."""

    def test_mask_openai_key(self):
        result = mask_api_key("sk-1234567890abcdefghijklmnopqrstuvwxyz1234")
        assert result == "sk-***1234"
        assert "1234567890" not in result

    def test_mask_supabase_key(self):
        # Supabase keys are JWT-like
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.abcd1234"
        result = mask_api_key(key)
        assert "***" in result
        assert len(result) < len(key)

    def test_mask_short_key(self):
        assert mask_api_key("short") == "[key-hidden]"

    def test_mask_none(self):
        assert mask_api_key(None) == "[no-key]"

    def test_mask_with_custom_visible_chars(self):
        result = mask_api_key("sk-1234567890abcdef", visible_chars=6)
        assert result.endswith("bcdef") or "***" in result


class TestMaskToken:
    """Tests for JWT/token masking."""

    def test_mask_jwt(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = mask_token(jwt)
        assert result == "eyJ***[JWT]"
        assert "sub" not in result

    def test_mask_bearer_token(self):
        assert mask_token("Bearer abc123xyz789") == "Bearer ***[TOKEN]"

    def test_mask_generic_long_token(self):
        result = mask_token("some_long_random_token_value")
        assert "***[TOKEN]" in result

    def test_mask_none(self):
        assert mask_token(None) == "[no-token]"

    def test_mask_short_token(self):
        assert mask_token("short") == "[token-hidden]"


class TestMaskUserId:
    """Tests for user ID partial masking."""

    def test_mask_uuid(self):
        result = mask_user_id("550e8400-e29b-41d4-a716-446655440000")
        assert result == "550e8400-***"
        assert "446655440000" not in result

    def test_mask_short_id(self):
        assert mask_user_id("user123") == "user***"

    def test_mask_very_short_id(self):
        assert mask_user_id("abc") == "[id-hidden]"

    def test_mask_none(self):
        assert mask_user_id(None) == "[no-id]"


class TestMaskIpAddress:
    """Tests for IP address masking."""

    def test_mask_ipv4(self):
        assert mask_ip_address("192.168.1.100") == "192.168.x.x"

    def test_mask_public_ipv4(self):
        assert mask_ip_address("8.8.8.8") == "8.8.x.x"

    def test_mask_ipv6(self):
        result = mask_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        assert "2001:0db8" in result
        assert "*" in result

    def test_mask_none(self):
        assert mask_ip_address(None) == "[no-ip]"


class TestMaskPassword:
    """Tests for password masking."""

    def test_always_redacts(self):
        assert mask_password("secretpassword123") == "[PASSWORD_REDACTED]"

    def test_redacts_none(self):
        assert mask_password(None) == "[PASSWORD_REDACTED]"

    def test_redacts_empty(self):
        assert mask_password("") == "[PASSWORD_REDACTED]"


class TestMaskPhone:
    """Tests for phone number masking."""

    def test_mask_brazilian_phone(self):
        assert mask_phone("+55 11 99999-1234") == "***-1234"

    def test_mask_us_phone(self):
        assert mask_phone("(555) 123-4567") == "***-4567"

    def test_mask_short_number(self):
        result = mask_phone("123")
        assert "[phone-hidden]" in result

    def test_mask_none(self):
        assert mask_phone(None) == "[no-phone]"


class TestSanitizeValue:
    """Tests for context-aware value sanitization."""

    def test_sanitize_password_field(self):
        assert sanitize_value("password", "secret123") == "[PASSWORD_REDACTED]"
        assert sanitize_value("new_password", "secret123") == "[PASSWORD_REDACTED]"

    def test_sanitize_email_field(self):
        result = sanitize_value("user_email", "user@test.com")
        assert "@test.com" in result
        assert "user" not in result or result.startswith("u***")

    def test_sanitize_api_key_field(self):
        result = sanitize_value("api_key", "sk-1234567890abcdef")
        assert "***" in result

    def test_sanitize_token_field(self):
        result = sanitize_value("access_token", "Bearer abc123")
        assert "***" in result or "[TOKEN]" in result

    def test_non_sensitive_field_unchanged(self):
        assert sanitize_value("name", "John Doe") == "John Doe"
        assert sanitize_value("count", 42) == 42


class TestSanitizeDict:
    """Tests for dictionary sanitization."""

    def test_sanitize_flat_dict(self):
        data = {
            "email": "user@test.com",
            "password": "secret123",
            "name": "John",
        }
        result = sanitize_dict(data)
        assert result["name"] == "John"
        assert result["password"] == "[PASSWORD_REDACTED]"
        assert "@test.com" in result["email"]

    def test_sanitize_nested_dict(self):
        data = {
            "user": {
                "email": "user@test.com",
                "credentials": {
                    "password": "secret"
                }
            }
        }
        result = sanitize_dict(data, deep=True)
        assert result["user"]["credentials"]["password"] == "[PASSWORD_REDACTED]"

    def test_sanitize_list_in_dict(self):
        data = {
            "users": [
                {"email": "alice@test.com"},
                {"email": "bob@test.com"},
            ]
        }
        result = sanitize_dict(data, deep=True)
        for user in result["users"]:
            assert "@test.com" in user["email"]
            # First char + *** pattern (alice -> a***@, bob -> b***@)
            assert user["email"].startswith("a***") or user["email"].startswith("b***")


class TestSanitizeString:
    """Tests for string pattern sanitization."""

    def test_sanitize_email_in_text(self):
        text = "User logged in: user@example.com at 10:00"
        result = sanitize_string(text)
        assert "user@example.com" not in result
        assert "@example.com" in result

    def test_sanitize_jwt_in_text(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig"
        text = f"Token: {jwt}"
        result = sanitize_string(text)
        assert jwt not in result
        assert "[JWT]" in result or "***" in result

    def test_sanitize_openai_key_in_text(self):
        text = "Using key: sk-1234567890abcdefghijklmnopqrstuvwxyz1234"
        result = sanitize_string(text)
        assert "1234567890abcdef" not in result

    def test_plain_text_unchanged(self):
        text = "This is a normal log message"
        assert sanitize_string(text) == text


class TestSanitizeUniversal:
    """Tests for the universal sanitize() function."""

    def test_sanitize_dict(self):
        data = {"password": "secret"}
        result = sanitize(data)
        assert result["password"] == "[PASSWORD_REDACTED]"

    def test_sanitize_string(self):
        text = "Email: user@test.com"
        result = sanitize(text)
        assert "user@test.com" not in result

    def test_sanitize_with_context(self):
        result = sanitize("sk-12345678901234567890", context="api_key")
        assert "***" in result


class TestEnvironmentConfig:
    """Tests for environment-based configuration."""

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_is_production_true(self):
        # Clear the cache
        is_production.cache_clear()
        assert is_production() == True

    @patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True)
    def test_is_production_false(self):
        is_production.cache_clear()
        assert is_production() == False

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_get_log_level(self):
        get_log_level.cache_clear()
        assert get_log_level() == "DEBUG"


class TestSanitizedLogAdapter:
    """Tests for the SanitizedLogAdapter."""

    def test_adapter_sanitizes_message(self, caplog):
        logger = logging.getLogger("test_adapter")
        logger.setLevel(logging.INFO)
        safe_logger = SanitizedLogAdapter(logger)

        with caplog.at_level(logging.INFO, logger="test_adapter"):
            safe_logger.info("User email: user@test.com logged in")

        # The email should be masked in the log output
        assert "user@test.com" not in caplog.text

    def test_get_sanitized_logger(self, caplog):
        logger = get_sanitized_logger("test_helper")
        assert isinstance(logger, SanitizedLogAdapter)


class TestLogHelperFunctions:
    """Tests for helper logging functions."""

    def test_log_user_action(self, caplog):
        logger = logging.getLogger("test_user_action")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO, logger="test_user_action"):
            log_user_action(logger, "login", "550e8400-e29b-41d4-a716-446655440000")

        # Should contain masked user ID
        assert "550e8400-***" in caplog.text
        assert "446655440000" not in caplog.text

    def test_log_admin_action(self, caplog):
        logger = logging.getLogger("test_admin_action")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO, logger="test_admin_action"):
            log_admin_action(
                logger,
                admin_id="550e8400-e29b-41d4-a716-446655440000",
                action="delete-user",
                target_user_id="661f9511-f3ac-52e5-b827-557766551111",
            )

        # Should contain masked UUIDs (first 8 chars + -***)
        assert "550e8400-***" in caplog.text
        assert "446655440000" not in caplog.text
        assert "557766551111" not in caplog.text

    def test_log_auth_event_success(self, caplog):
        logger = logging.getLogger("test_auth_success")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO, logger="test_auth_success"):
            log_auth_event(
                logger,
                event="login",
                success=True,
                email="user@test.com"
            )

        # Should log at INFO level and mask email
        assert "login" in caplog.text
        assert "success=True" in caplog.text
        assert "user@test.com" not in caplog.text

    def test_log_auth_event_failure(self, caplog):
        logger = logging.getLogger("test_auth_failure")
        logger.setLevel(logging.WARNING)

        with caplog.at_level(logging.WARNING, logger="test_auth_failure"):
            log_auth_event(
                logger,
                event="login",
                success=False,
                email="user@test.com",
                reason="invalid password"
            )

        # Should log at WARNING level
        assert "success=False" in caplog.text


class TestIntegration:
    """Integration tests for real-world scenarios."""

    def test_sanitize_pncp_api_error_response(self):
        """Test sanitizing a typical API error response."""
        error_response = {
            "error": "Authentication failed",
            "user_email": "admin@company.com",
            "api_key": "sk-12345678901234567890123456789012",
            "request_id": "req_abc123",
        }
        result = sanitize_dict(error_response)

        assert result["request_id"] == "req_abc123"  # Safe field unchanged
        assert "admin@company.com" not in str(result)
        assert "12345678901234567890" not in str(result)

    def test_sanitize_supabase_user_data(self):
        """Test sanitizing Supabase user profile data."""
        user_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "phone": "+55 11 98765-4321",
            "created_at": "2026-01-01T00:00:00Z",
        }
        result = sanitize_dict(user_data)

        assert result["created_at"] == user_data["created_at"]  # Safe field
        assert "user@example.com" not in str(result)
        assert "98765-4321" not in str(result) or "***-4321" in str(result)

    def test_sanitize_stripe_webhook_payload(self):
        """Test sanitizing Stripe webhook data."""
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer_email": "customer@test.com",
                    "client_reference_id": "user-uuid-here",
                    "payment_intent": "pi_123456789",
                }
            }
        }
        result = sanitize_dict(payload)

        assert "customer@test.com" not in str(result)
        assert result["data"]["object"]["payment_intent"] == "pi_123456789"
