"""Tests for authentication middleware (auth.py).

Tests JWT verification, require_auth dependency, and error handling.
Uses mocked Supabase client to avoid external API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    @pytest.fixture
    def mock_user_response(self):
        """Create a mock Supabase user response."""
        mock = Mock()
        mock.user = Mock()
        mock.user.id = "user-123-uuid"
        mock.user.email = "test@example.com"
        mock.user.role = "authenticated"
        return mock

    @pytest.fixture
    def mock_credentials(self):
        """Create mock HTTP Authorization credentials."""
        mock = Mock()
        mock.credentials = "valid-jwt-token-123"
        return mock

    @pytest.mark.asyncio
    async def test_returns_none_when_no_credentials(self):
        """Should return None when no credentials provided (allows anonymous access)."""
        from auth import get_current_user

        result = await get_current_user(credentials=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_user_dict_on_valid_token(self, mock_credentials, mock_user_response):
        """Should return user dict when token is valid."""
        from auth import get_current_user

        mock_supabase = Mock()
        mock_supabase.auth.get_user.return_value = mock_user_response

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = await get_current_user(credentials=mock_credentials)

        assert result is not None
        assert result["id"] == "user-123-uuid"
        assert result["email"] == "test@example.com"
        assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    async def test_raises_401_when_token_invalid(self, mock_credentials):
        """Should raise HTTPException 401 when token is invalid."""
        from auth import get_current_user

        mock_supabase = Mock()
        # Return None to simulate invalid token
        mock_supabase.auth.get_user.return_value = None

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert "invalido" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_raises_401_when_user_response_has_no_user(self, mock_credentials):
        """Should raise HTTPException 401 when response has no user object."""
        from auth import get_current_user

        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.user = None  # No user in response
        mock_supabase.auth.get_user.return_value = mock_response

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_on_supabase_exception(self, mock_credentials):
        """Should raise HTTPException 401 when Supabase raises an exception."""
        from auth import get_current_user

        mock_supabase = Mock()
        mock_supabase.auth.get_user.side_effect = Exception("Network error")

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert "expirado" in exc_info.value.detail.lower() or "invalido" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_logs_warning_on_verification_failure(self, mock_credentials, caplog):
        """Should log warning when JWT verification fails."""
        from auth import get_current_user
        import logging

        mock_supabase = Mock()
        mock_supabase.auth.get_user.side_effect = Exception("Token expired")

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with caplog.at_level(logging.WARNING):
                with pytest.raises(HTTPException):
                    await get_current_user(credentials=mock_credentials)

        # SECURITY (Issue #168): Log format changed to sanitized auth events
        # Format: "Auth: token_verification success=False reason=ExceptionType"
        assert any("token_verification" in record.message and "success=False" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_extracts_token_from_credentials(self, mock_user_response):
        """Should extract token string from credentials object."""
        from auth import get_current_user

        mock_credentials = Mock()
        mock_credentials.credentials = "my-specific-token-abc123"

        mock_supabase = Mock()
        mock_supabase.auth.get_user.return_value = mock_user_response

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            await get_current_user(credentials=mock_credentials)

        # Verify the token was passed to Supabase
        mock_supabase.auth.get_user.assert_called_once_with("my-specific-token-abc123")

    @pytest.mark.asyncio
    async def test_reraises_http_exception(self, mock_credentials):
        """Should re-raise HTTPException if already an HTTPException."""
        from auth import get_current_user

        mock_supabase = Mock()
        # Simulate case where get_user raises HTTPException (e.g., from internal code)
        mock_response = Mock()
        mock_response.user = None
        mock_supabase.auth.get_user.return_value = mock_response

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=mock_credentials)

        # The 401 from "Token invalido" should be raised
        assert exc_info.value.status_code == 401


class TestRequireAuth:
    """Test suite for require_auth dependency."""

    @pytest.mark.asyncio
    async def test_returns_user_when_authenticated(self):
        """Should return user dict when user is authenticated."""
        from auth import require_auth

        mock_user = {
            "id": "user-456",
            "email": "authenticated@example.com",
            "role": "authenticated",
        }

        result = await require_auth(user=mock_user)

        assert result == mock_user
        assert result["id"] == "user-456"
        assert result["email"] == "authenticated@example.com"

    @pytest.mark.asyncio
    async def test_raises_401_when_user_is_none(self):
        """Should raise HTTPException 401 when user is None (not authenticated)."""
        from auth import require_auth

        with pytest.raises(HTTPException) as exc_info:
            await require_auth(user=None)

        assert exc_info.value.status_code == 401
        assert "autenticacao" in exc_info.value.detail.lower()
        assert "login" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_error_message_is_user_friendly(self):
        """Should return user-friendly error message in Portuguese."""
        from auth import require_auth

        with pytest.raises(HTTPException) as exc_info:
            await require_auth(user=None)

        detail = exc_info.value.detail
        assert "Autenticacao necessaria" in detail
        assert "Faca login" in detail


class TestHTTPBearerSecurity:
    """Test suite for HTTP Bearer security scheme configuration."""

    def test_security_auto_error_is_false(self):
        """Security scheme should have auto_error=False to allow optional auth."""
        from auth import security

        # auto_error=False allows endpoints to work without token
        assert security.auto_error is False


class TestAuthIntegration:
    """Integration tests for auth middleware with FastAPI TestClient."""

    @pytest.fixture
    def app_with_protected_route(self):
        """Create a FastAPI app with a protected route."""
        from fastapi import FastAPI, Depends
        from auth import require_auth, get_current_user

        app = FastAPI()

        @app.get("/public")
        async def public_endpoint(user=Depends(get_current_user)):
            return {"user": user}

        @app.get("/protected")
        async def protected_endpoint(user=Depends(require_auth)):
            return {"user_id": user["id"]}

        return app

    def test_public_endpoint_works_without_token(self, app_with_protected_route):
        """Public endpoint should work without authentication token."""
        client = TestClient(app_with_protected_route)

        response = client.get("/public")

        assert response.status_code == 200
        assert response.json()["user"] is None

    def test_protected_endpoint_requires_token(self, app_with_protected_route):
        """Protected endpoint should return 401 without token."""
        client = TestClient(app_with_protected_route)

        response = client.get("/protected")

        assert response.status_code == 401

    def test_protected_endpoint_accepts_valid_token(self, app_with_protected_route):
        """Protected endpoint should accept valid token."""
        from unittest.mock import patch, Mock

        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = "test-user-id"
        mock_user_response.user.email = "test@example.com"
        mock_user_response.user.role = "authenticated"

        mock_supabase = Mock()
        mock_supabase.auth.get_user.return_value = mock_user_response

        client = TestClient(app_with_protected_route)

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer valid-token"}
            )

        assert response.status_code == 200
        assert response.json()["user_id"] == "test-user-id"

    def test_protected_endpoint_rejects_invalid_token(self, app_with_protected_route):
        """Protected endpoint should return 401 for invalid token."""
        from unittest.mock import patch, Mock

        mock_supabase = Mock()
        mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

        client = TestClient(app_with_protected_route)

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer invalid-token"}
            )

        assert response.status_code == 401


class TestAuthEdgeCases:
    """Test edge cases and boundary conditions for auth module."""

    @pytest.mark.asyncio
    async def test_handles_user_with_missing_email(self):
        """Should handle user response with missing email gracefully."""
        from auth import get_current_user

        mock_credentials = Mock()
        mock_credentials.credentials = "token"

        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = "user-id"
        mock_user_response.user.email = None  # Missing email
        mock_user_response.user.role = "authenticated"

        mock_supabase = Mock()
        mock_supabase.auth.get_user.return_value = mock_user_response

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = await get_current_user(credentials=mock_credentials)

        assert result["id"] == "user-id"
        assert result["email"] is None
        assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    async def test_converts_user_id_to_string(self):
        """Should convert user ID to string (UUID to str)."""
        from auth import get_current_user
        import uuid

        mock_credentials = Mock()
        mock_credentials.credentials = "token"

        user_uuid = uuid.uuid4()

        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = user_uuid  # UUID object
        mock_user_response.user.email = "test@example.com"
        mock_user_response.user.role = "authenticated"

        mock_supabase = Mock()
        mock_supabase.auth.get_user.return_value = mock_user_response

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = await get_current_user(credentials=mock_credentials)

        assert isinstance(result["id"], str)
        assert result["id"] == str(user_uuid)
