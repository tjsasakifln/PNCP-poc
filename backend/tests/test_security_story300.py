"""
STORY-300: Security Hardening — Backend Tests

AC5: Backend NEVER returns stack traces in production responses
AC6: Excel export errors return generic message + correlation_id
AC7: Sentry captures the full exception
AC8: log_sanitizer covers new endpoints
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    from main import app
    from auth import require_auth
    from database import get_db

    async def mock_auth():
        return {"id": "test-user-id", "email": "test@test.com", "role": "authenticated"}

    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    app.dependency_overrides[require_auth] = mock_auth
    app.dependency_overrides[get_db] = lambda: mock_db

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(get_db, None)


class TestAC5NeverLeakStackTraces:
    """AC5: Backend NEVER returns stack traces in production responses."""

    def test_global_handler_returns_generic_message(self, client):
        """AC5: Unhandled exceptions return generic PT message, not stack trace."""
        # Trigger an unhandled error by requesting a route that will fail
        # The global exception handler should catch it
        with patch("routes.user.check_user_roles", side_effect=RuntimeError("Internal DB connection pool exhausted")):
            response = client.get("/v1/me")

        assert response.status_code == 500
        body = response.json()
        detail = body.get("detail", "")

        # Must NOT contain stack trace fragments
        assert "Traceback" not in detail
        assert "RuntimeError" not in detail
        assert "pool exhausted" not in detail
        assert "File " not in detail  # No file paths

        # Must be generic PT message
        assert "erro" in detail.lower()

    def test_global_handler_includes_correlation_id(self, client):
        """AC6: Error responses include correlation_id for support tracing."""
        with patch("routes.user.check_user_roles", side_effect=RuntimeError("boom")):
            response = client.get("/v1/me")

        assert response.status_code == 500
        body = response.json()
        # Must include correlation_id field
        assert "correlation_id" in body

    def test_global_handler_includes_request_id(self, client):
        """AC5: Error responses include request_id for log correlation."""
        with patch("routes.user.check_user_roles", side_effect=RuntimeError("boom")):
            response = client.get("/v1/me")

        assert response.status_code == 500
        body = response.json()
        assert "request_id" in body

    def test_global_handler_sends_to_sentry(self, client):
        """AC7: Sentry captures the full exception with stack trace."""
        with (
            patch("routes.user.check_user_roles", side_effect=RuntimeError("sentry test")),
            patch("sentry_sdk.capture_exception") as mock_sentry,
        ):
            response = client.get("/v1/me")

        assert response.status_code == 500
        # Sentry must have been called with the exception
        mock_sentry.assert_called_once()
        captured_exc = mock_sentry.call_args[0][0]
        assert isinstance(captured_exc, RuntimeError)
        assert "sentry test" in str(captured_exc)

    def test_rls_error_returns_403_with_correlation_id(self, client):
        """AC5: RLS errors return 403 with correlation_id, no internal details."""
        with (
            patch("routes.user.check_user_roles", side_effect=Exception("new row violates row-level security policy")),
            patch("sentry_sdk.capture_exception"),
        ):
            response = client.get("/v1/me")

        assert response.status_code == 403
        body = response.json()
        assert "correlation_id" in body
        assert "row-level" not in body.get("detail", "").lower()

    def test_stripe_error_returns_500_with_correlation_id(self, client):
        """AC5: Stripe errors return 500 with correlation_id, no internal details."""
        with (
            patch("routes.user.check_user_roles", side_effect=Exception("Stripe API error: card_declined")),
            patch("sentry_sdk.capture_exception"),
        ):
            response = client.get("/v1/me")

        assert response.status_code == 500
        body = response.json()
        assert "correlation_id" in body
        assert "card_declined" not in body.get("detail", "").lower()
        assert "pagamento" in body.get("detail", "").lower()

    def test_error_response_never_contains_python_paths(self, client):
        """AC5: Error responses never contain Python file paths or module names."""
        with (
            patch("routes.user.check_user_roles", side_effect=ValueError("at /app/backend/routes/user.py line 42")),
            patch("sentry_sdk.capture_exception"),
        ):
            response = client.get("/v1/me")

        assert response.status_code == 500
        body_str = json.dumps(response.json())
        assert "/app/" not in body_str
        assert ".py" not in body_str
        assert "line 42" not in body_str


class TestAC6ExcelErrorSanitization:
    """AC6: Excel export errors return generic message + correlation_id."""

    def test_excel_error_in_pipeline_returns_generic_message(self):
        """AC6: Excel generation failure shows generic error, not stack trace."""
        # The search pipeline already handles this — verify the error message pattern
        from search_pipeline import SearchPipeline
        import inspect
        source = inspect.getsource(SearchPipeline)

        # The pipeline must contain the generic error message for Excel failures
        assert "Erro temporário ao gerar Excel" in source

    def test_excel_error_never_exposes_openpyxl_traceback(self):
        """AC6: openpyxl errors are caught, not exposed to users."""
        from excel import create_excel

        # Trigger an error with invalid input
        try:
            create_excel("not a list")  # type: ignore
        except ValueError as e:
            # Must be our custom ValueError, not openpyxl internal
            assert "lista" in str(e).lower()
        except Exception:
            pytest.fail("Unexpected exception type from create_excel")


class TestAC8LogSanitizerCoverage:
    """AC8: log_sanitizer.py covers new endpoints and patterns."""

    def test_sanitize_correlation_id_not_masked(self):
        """AC8: correlation_id is NOT masked (it's for support tracing)."""
        from log_sanitizer import sanitize_value
        corr_id = "abc-123-def-456"
        # correlation_id should pass through unmolested
        result = sanitize_value("correlation_id", corr_id)
        assert result == corr_id

    def test_sanitize_request_id_not_masked(self):
        """AC8: request_id is NOT masked (it's for log correlation)."""
        from log_sanitizer import sanitize_value
        req_id = "550e8400-e29b-41d4-a716-446655440000"
        # request_id should not be treated as a user_id
        result = sanitize_value("request_id", req_id)
        assert result == req_id

    def test_log_sanitizer_masks_user_email_in_error_context(self):
        """AC8: Emails in error context are masked."""
        from log_sanitizer import sanitize_string
        msg = "Failed to process for user@example.com"
        result = sanitize_string(msg)
        assert "user@example.com" not in result
        assert "u***@example.com" in result

    def test_log_sanitizer_masks_jwt_in_error_context(self):
        """AC8: JWTs in error context are masked."""
        from log_sanitizer import sanitize_string
        msg = "Auth failed: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
        result = sanitize_string(msg)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result

    def test_sanitize_dict_covers_new_error_fields(self):
        """AC8: New error response fields are properly handled."""
        from log_sanitizer import sanitize_dict
        error_context = {
            "correlation_id": "abc-123",
            "request_id": "req-456",
            "user_email": "admin@smartlic.tech",
            "password": "secret123",
        }
        result = sanitize_dict(error_context)
        assert result["correlation_id"] == "abc-123"  # Not masked
        assert result["request_id"] == "req-456"  # Not masked
        assert "admin@smartlic.tech" not in result["user_email"]  # Masked
        assert result["password"] == "[PASSWORD_REDACTED]"  # Masked


class TestSecurityHeadersBackend:
    """Verify backend SecurityHeadersMiddleware still works after changes."""

    def test_security_headers_present(self, client):
        """Backend responses include security headers."""
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in response.headers.get("Permissions-Policy", "")
        assert "max-age=31536000" in response.headers.get("Strict-Transport-Security", "")

    def test_x_request_id_in_response(self, client):
        """Backend responses include X-Request-ID for correlation."""
        response = client.get("/health")
        assert response.headers.get("x-request-id") is not None
