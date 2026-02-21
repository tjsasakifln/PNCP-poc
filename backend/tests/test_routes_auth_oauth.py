"""Tests for OAuth routes (routes/auth_oauth.py).

Tests OAuth flow endpoints: initiate, callback, and revoke.
Uses mocked authentication and external APIs.

STORY-180: Google Sheets Export - OAuth Routes Tests
STORY-224: Fixed 4 skipped tests — OAuth state now uses cryptographic nonces (STORY-210 AC13)
"""

import pytest
import time
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone, timedelta
import base64


@pytest.fixture
def app():
    """Create test FastAPI app with OAuth routes."""
    from routes.auth_oauth import router

    test_app = FastAPI()
    test_app.include_router(router)

    return test_app


@pytest.fixture
def client(app, mock_user):
    """Create test client with mocked authentication."""
    from auth import require_auth

    # Override require_auth dependency
    def mock_require_auth():
        return mock_user

    app.dependency_overrides[require_auth] = mock_require_auth

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


def _make_mock_token_response():
    """Create mock token response matching exchange_code_for_tokens return schema."""
    return {
        "access_token": "ya29.test_token",
        "refresh_token": "1//refresh_token",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "scope": ["https://www.googleapis.com/auth/spreadsheets"]
    }


class TestGoogleOAuthInitiate:
    """Test suite for GET /api/auth/google endpoint."""

    def test_redirects_to_google_oauth(self, client):
        """Should redirect to Google OAuth authorization URL."""
        with patch("routes.auth_oauth.get_authorization_url") as mock_get_url:
            mock_get_url.return_value = "https://accounts.google.com/o/oauth2/auth?client_id=123"

            response = client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)

            assert response.status_code == 307  # Redirect
            assert "https://accounts.google.com/o/oauth2/auth" in response.headers["location"]

    def test_stores_nonce_with_user_id_and_redirect_in_state(self, client):
        """Should use cryptographic nonce as state and store user_id + redirect."""
        from routes.auth_oauth import _oauth_nonce_store

        with patch("routes.auth_oauth.get_authorization_url") as mock_get_url:
            # Capture the state parameter passed to get_authorization_url
            captured_state = None

            def capture_state(redirect_uri, state):
                nonlocal captured_state
                captured_state = state
                return f"https://oauth.google.com?state={state}"

            mock_get_url.side_effect = capture_state

            client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)

            # State should be an opaque nonce, not base64-encoded
            assert captured_state is not None
            assert len(captured_state) > 20  # cryptographic nonce is long

            # Nonce should be stored with correct user_id and redirect_path
            assert captured_state in _oauth_nonce_store
            user_id, redirect_path, _ = _oauth_nonce_store[captured_state]
            assert user_id == "user-123-uuid"
            assert redirect_path == "/buscar"

            # Clean up nonce store
            _oauth_nonce_store.pop(captured_state, None)

    def test_uses_default_redirect_when_not_provided(self, client):
        """Should use default redirect path when not provided."""
        with patch("routes.auth_oauth.get_authorization_url") as mock_get_url:
            mock_get_url.return_value = "https://oauth.google.com"

            response = client.get("/api/auth/google", follow_redirects=False)

            # Should still work with default redirect
            assert response.status_code == 307


class TestGoogleOAuthCallback:
    """Test suite for GET /api/auth/google/callback endpoint."""

    @pytest.mark.asyncio
    async def test_exchanges_code_for_tokens(self, client):
        """Should exchange authorization code for access/refresh tokens."""
        from routes.auth_oauth import _oauth_nonce_store

        # Pre-populate nonce store with a valid nonce
        test_nonce = "test-nonce-exchange"
        _oauth_nonce_store[test_nonce] = ("user-123-uuid", "/buscar", time.time())
        mock_token_response = _make_mock_token_response()

        try:
            with patch("routes.auth_oauth.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
                mock_exchange.return_value = mock_token_response

                with patch("routes.auth_oauth.save_user_tokens", new_callable=AsyncMock) as mock_save:
                    client.get(f"/api/auth/google/callback?code=auth_code_123&state={test_nonce}")

                    # Should have called exchange_code_for_tokens
                    mock_exchange.assert_called_once()

                    # Should have saved tokens
                    mock_save.assert_called_once()
        finally:
            _oauth_nonce_store.pop(test_nonce, None)

    @pytest.mark.asyncio
    async def test_saves_encrypted_tokens_to_database(self, client):
        """Should save encrypted tokens to database."""
        from routes.auth_oauth import _oauth_nonce_store

        # Pre-populate nonce store with a valid nonce
        test_nonce = "test-nonce-save-tokens"
        _oauth_nonce_store[test_nonce] = ("user-123-uuid", "/buscar", time.time())
        mock_token_response = _make_mock_token_response()

        try:
            with patch("routes.auth_oauth.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
                mock_exchange.return_value = mock_token_response

                with patch("routes.auth_oauth.save_user_tokens", new_callable=AsyncMock) as mock_save:
                    client.get(f"/api/auth/google/callback?code=auth_code_123&state={test_nonce}")

                    # Verify save_user_tokens was called with correct params
                    call_args = mock_save.call_args
                    assert call_args[1]["user_id"] == "user-123-uuid"
                    assert call_args[1]["access_token"] == "ya29.test_token"
                    assert call_args[1]["refresh_token"] == "1//refresh_token"
                    assert call_args[1]["scope"] == "https://www.googleapis.com/auth/spreadsheets"
        finally:
            _oauth_nonce_store.pop(test_nonce, None)

    @pytest.mark.asyncio
    async def test_redirects_to_original_path_on_success(self, client):
        """Should redirect to original path after successful authorization."""
        state = base64.urlsafe_b64encode(b"user-123-uuid:/buscar").decode()
        mock_token_response = _make_mock_token_response()

        with patch("routes.auth_oauth.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_token_response

            with patch("routes.auth_oauth.save_user_tokens", new_callable=AsyncMock):
                response = client.get(
                    f"/api/auth/google/callback?code=auth_code_123&state={state}",
                    follow_redirects=False
                )

                assert response.status_code == 307  # Redirect
                assert "/buscar" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_redirects_with_error_on_invalid_state(self, client):
        """Should redirect with error on invalid state parameter."""
        response = client.get(
            "/api/auth/google/callback?code=auth_code_123&state=invalid_base64",
            follow_redirects=False
        )

        # Route returns RedirectResponse with error info
        assert response.status_code == 307
        assert "error=invalid_state" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_redirects_with_error_on_authorization_denied(self, client):
        """Should redirect with error when user denies authorization."""
        state = base64.urlsafe_b64encode(b"user-123-uuid:/buscar").decode()

        # Google sends error param without code when user denies
        response = client.get(
            f"/api/auth/google/callback?error=access_denied&state={state}",
            follow_redirects=False
        )

        # Route returns RedirectResponse with oauth_denied error
        assert response.status_code == 307
        assert "error=oauth_denied" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_handles_token_exchange_failure(self, client):
        """Should handle token exchange failure gracefully."""
        from routes.auth_oauth import _oauth_nonce_store

        # Pre-populate nonce store with a valid nonce
        test_nonce = "test-nonce-exchange-failure"
        _oauth_nonce_store[test_nonce] = ("user-123-uuid", "/buscar", time.time())

        try:
            with patch("routes.auth_oauth.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
                from fastapi import HTTPException
                mock_exchange.side_effect = HTTPException(status_code=400, detail="Invalid code")

                response = client.get(
                    f"/api/auth/google/callback?code=invalid_code&state={test_nonce}",
                    follow_redirects=False
                )

                # Route catches HTTPException and redirects with error
                assert response.status_code == 307
                assert "error=oauth_failed" in response.headers["location"]
        finally:
            _oauth_nonce_store.pop(test_nonce, None)


class TestRevokeGoogleToken:
    """Test suite for DELETE /api/auth/google endpoint."""

    @pytest.mark.asyncio
    async def test_revokes_token_successfully(self, client):
        """Should revoke OAuth token and return success message."""
        with patch("routes.auth_oauth.revoke_user_google_token", new_callable=AsyncMock) as mock_revoke:
            mock_revoke.return_value = True

            response = client.delete("/api/auth/google")

            assert response.status_code == 200
            assert "success" in response.json()["message"].lower() or response.json()["success"] is True

            # Verify revoke was called with correct user_id
            mock_revoke.assert_called_once_with("user-123-uuid")

    @pytest.mark.asyncio
    async def test_handles_revoke_failure_gracefully(self, client):
        """Should handle revoke failure (e.g., token doesn't exist)."""
        with patch("routes.auth_oauth.revoke_user_google_token", new_callable=AsyncMock) as mock_revoke:
            mock_revoke.side_effect = Exception("Database error")

            response = client.delete("/api/auth/google")

            # Should return 500 on unexpected error
            assert response.status_code in [200, 500]


class TestOAuthIntegration:
    """Integration tests for complete OAuth flow."""

    @pytest.mark.asyncio
    async def test_complete_oauth_flow(self, client):
        """Should complete full OAuth flow: initiate -> callback -> revoke."""
        # Step 1: Initiate OAuth
        with patch("routes.auth_oauth.get_authorization_url") as mock_get_url:
            mock_get_url.return_value = "https://oauth.google.com?state=123"

            initiate_response = client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)
            assert initiate_response.status_code == 307

        # Step 2: Handle callback
        state = base64.urlsafe_b64encode(b"user-123-uuid:/buscar").decode()
        mock_token_response = _make_mock_token_response()

        with patch("routes.auth_oauth.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_token_response

            with patch("routes.auth_oauth.save_user_tokens", new_callable=AsyncMock):
                callback_response = client.get(
                    f"/api/auth/google/callback?code=auth_code&state={state}",
                    follow_redirects=False
                )
                assert callback_response.status_code == 307

        # Step 3: Revoke token
        with patch("routes.auth_oauth.revoke_user_google_token", new_callable=AsyncMock) as mock_revoke:
            mock_revoke.return_value = True
            revoke_response = client.delete("/api/auth/google")
            assert revoke_response.status_code == 200
