"""Tests for GTM-CRIT-003: Auth failures return HTTP 401 (not 500).

Tests that when all JWT authentication mechanisms fail (JWKS, PEM, HS256),
the system returns HTTP 401 with proper WWW-Authenticate header and
user-friendly error message, without leaking internal stack traces.

AC4: When _resolve_signing_key() raises, response is 401 with WWW-Authenticate header
AC5: logger.error is called with the config message
AC7: Response body does NOT contain stack trace information
"""

import os
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def auth_misconfigured_env():
    """Environment with no JWT secret and no JWKS URL."""
    return {
        # No SUPABASE_JWT_SECRET
        # No SUPABASE_URL (so no auto-JWKS URL)
        # No SUPABASE_JWKS_URL
        "REDIS_HOST": "localhost",  # Keep other vars to avoid unrelated errors
    }


@pytest.fixture
def test_app():
    """Create a minimal FastAPI app with a protected endpoint for testing."""
    from fastapi import FastAPI, Depends
    from auth import require_auth

    app = FastAPI()

    @app.get("/protected")
    async def protected_endpoint(user: dict = Depends(require_auth)):
        return {"user_id": user["id"]}

    return app


class TestAuthConfigFailureReturns401:
    """Test suite for AC4, AC5, AC7: Auth config failure returns 401."""

    def test_auth_failure_returns_401_with_www_authenticate_header(
        self, test_app, auth_misconfigured_env
    ):
        """AC4: When JWT signing key cannot be resolved, returns 401 with WWW-Authenticate header."""
        # Clear any cached JWKS client state from previous tests
        from auth import reset_jwks_client
        reset_jwks_client()

        with patch.dict(os.environ, auth_misconfigured_env, clear=True):
            client = TestClient(test_app)

            # GET /protected requires auth
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer fake-token-123"},
            )

        # Should be 401, not 500
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

        # Should have WWW-Authenticate header
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

        # Should have user-friendly Portuguese message
        assert "detail" in response.json()
        detail = response.json()["detail"]
        assert "Autenticação indisponível" in detail or "indisponível" in detail.lower()

    def test_auth_failure_logs_error_message(
        self, test_app, auth_misconfigured_env, caplog
    ):
        """AC5: logger.error is called with the config message."""
        # Clear any cached JWKS client state from previous tests
        from auth import reset_jwks_client
        reset_jwks_client()

        with patch.dict(os.environ, auth_misconfigured_env, clear=True):
            client = TestClient(test_app)

            with caplog.at_level("ERROR"):
                response = client.get(
                    "/protected",
                    headers={"Authorization": "Bearer fake-token-456"},
                )

        # Verify error was logged
        assert any(
            "SUPABASE_JWT_SECRET not configured" in record.message
            for record in caplog.records
        ), "Expected error log message about JWT secret not found"

    def test_auth_failure_does_not_leak_stack_trace(
        self, test_app, auth_misconfigured_env
    ):
        """AC7: Response body does NOT contain Traceback or internal file paths."""
        # Clear any cached JWKS client state from previous tests
        from auth import reset_jwks_client
        reset_jwks_client()

        with patch.dict(os.environ, auth_misconfigured_env, clear=True):
            client = TestClient(test_app)

            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer fake-token-789"},
            )

        response_text = response.text.lower()

        # Should NOT contain stack trace indicators
        assert "traceback" not in response_text, "Response contains 'Traceback'"
        assert 'file "' not in response_text, "Response contains 'File \"'"
        assert "auth.py" not in response_text, "Response contains 'auth.py'"
        assert "main.py" not in response_text, "Response contains 'main.py'"

        # Should contain user-friendly message
        assert "autenticação" in response_text or "indisponível" in response_text


class TestAuthConfigFailureWithDirectCall:
    """Test suite for direct function call to _get_jwt_key_and_algorithms."""

    def test_resolve_signing_key_raises_401_when_no_config(self):
        """Direct test: _get_jwt_key_and_algorithms raises 401 when unconfigured."""
        from fastapi import HTTPException

        # Clear any cached JWKS client state
        from auth import reset_jwks_client, _get_jwt_key_and_algorithms
        reset_jwks_client()

        env_no_auth = {
            # No JWT secret, no JWKS, no Supabase URL
        }

        with patch.dict(os.environ, env_no_auth, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                _get_jwt_key_and_algorithms("fake-token")

        assert exc_info.value.status_code == 401
        assert "Autenticação indisponível" in exc_info.value.detail
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"

    def test_resolve_signing_key_logs_error_when_no_config(self, caplog):
        """Direct test: _get_jwt_key_and_algorithms logs error message."""
        from fastapi import HTTPException

        # Clear any cached JWKS client state
        from auth import reset_jwks_client, _get_jwt_key_and_algorithms
        reset_jwks_client()

        env_no_auth = {}

        with patch.dict(os.environ, env_no_auth, clear=True):
            with caplog.at_level("ERROR"):
                try:
                    _get_jwt_key_and_algorithms("fake-token")
                except HTTPException:
                    pass

        # Verify the specific error message was logged
        assert any(
            "SUPABASE_JWT_SECRET not configured" in record.message
            and "no JWKS URL available" in record.message
            for record in caplog.records
        ), "Expected error log about missing JWT secret and JWKS URL"
