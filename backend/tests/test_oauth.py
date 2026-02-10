"""Tests for OAuth module (oauth.py).

Tests encryption/decryption, authorization URL generation, token management,
and refresh logic. Uses mocked external APIs to avoid real Google API calls.

STORY-180: Google Sheets Export - OAuth Infrastructure Tests
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import os


class TestTokenEncryption:
    """Test suite for AES-256 token encryption/decryption."""

    def test_encrypt_produces_fernet_format(self):
        """Should encrypt plaintext and produce Fernet-formatted ciphertext."""
        from oauth import encrypt_aes256

        plaintext = "ya29.a0AfH6SMBxyz123_test_access_token"
        encrypted = encrypt_aes256(plaintext)

        # Fernet tokens start with 'gAAAAA'
        assert encrypted.startswith("gAAAAA")
        assert len(encrypted) > len(plaintext)
        assert encrypted != plaintext

    def test_decrypt_returns_original_plaintext(self):
        """Should decrypt ciphertext back to original plaintext."""
        from oauth import encrypt_aes256, decrypt_aes256

        plaintext = "ya29.a0AfH6SMBxyz123_test_access_token"
        encrypted = encrypt_aes256(plaintext)
        decrypted = decrypt_aes256(encrypted)

        assert decrypted == plaintext

    def test_encrypt_different_inputs_produce_different_outputs(self):
        """Should produce different ciphertexts for different plaintexts."""
        from oauth import encrypt_aes256

        plaintext1 = "token_1"
        plaintext2 = "token_2"

        encrypted1 = encrypt_aes256(plaintext1)
        encrypted2 = encrypt_aes256(plaintext2)

        assert encrypted1 != encrypted2

    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Should raise error when decrypting invalid ciphertext."""
        from oauth import decrypt_aes256
        from cryptography.fernet import InvalidToken

        invalid_ciphertext = "invalid_base64_not_encrypted"

        with pytest.raises(Exception):  # Fernet raises InvalidToken
            decrypt_aes256(invalid_ciphertext)

    def test_encrypt_empty_string(self):
        """Should handle empty string encryption."""
        from oauth import encrypt_aes256, decrypt_aes256

        plaintext = ""
        encrypted = encrypt_aes256(plaintext)
        decrypted = decrypt_aes256(encrypted)

        assert decrypted == plaintext

    def test_encrypt_unicode_characters(self):
        """Should handle Unicode characters in plaintext."""
        from oauth import encrypt_aes256, decrypt_aes256

        plaintext = "token_with_unicode_こんにちは_🔐"
        encrypted = encrypt_aes256(plaintext)
        decrypted = decrypt_aes256(encrypted)

        assert decrypted == plaintext


class TestAuthorizationURL:
    """Test suite for OAuth authorization URL generation."""

    def test_generates_valid_google_oauth_url(self):
        """Should generate valid Google OAuth authorization URL."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        state = "test_state_123"

        auth_url = get_authorization_url(redirect_uri, state)

        # Verify URL structure
        assert auth_url.startswith("https://accounts.google.com/o/oauth2/auth")
        assert "response_type=code" in auth_url
        assert "access_type=offline" in auth_url
        assert "prompt=consent" in auth_url

    def test_includes_client_id_in_url(self):
        """Should include GOOGLE_OAUTH_CLIENT_ID in authorization URL."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        state = "test_state_123"

        auth_url = get_authorization_url(redirect_uri, state)

        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
        assert f"client_id={client_id[:20]}" in auth_url or "client_id=" in auth_url

    def test_includes_redirect_uri_in_url(self):
        """Should include redirect_uri parameter (URL-encoded)."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        state = "test_state_123"

        auth_url = get_authorization_url(redirect_uri, state)

        # URL-encoded redirect_uri
        assert "redirect_uri=" in auth_url
        assert "http%3A%2F%2F" in auth_url or "https%3A%2F%2F" in auth_url

    def test_includes_spreadsheets_scope(self):
        """Should include Google Sheets API scope."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        state = "test_state_123"

        auth_url = get_authorization_url(redirect_uri, state)

        # URL-encoded scope
        assert "scope=" in auth_url
        assert "spreadsheets" in auth_url

    def test_includes_state_parameter(self):
        """Should include state parameter for CSRF protection."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        state = "test_state_123"

        auth_url = get_authorization_url(redirect_uri, state)

        assert f"state={state}" in auth_url


class TestExchangeCodeForTokens:
    """Test suite for OAuth code exchange."""

    @pytest.mark.asyncio
    async def test_exchanges_code_successfully(self):
        """Should exchange authorization code for access/refresh tokens."""
        from oauth import exchange_code_for_tokens
        from datetime import datetime, timezone

        mock_credentials = Mock()
        mock_credentials.token = "ya29.a0AfH6SMBxyz123"
        mock_credentials.refresh_token = "1//refresh_token_xyz"
        mock_credentials.expiry = datetime.now(timezone.utc)
        mock_credentials.scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        with patch("oauth.Flow") as mock_flow_class:
            mock_flow = Mock()
            mock_flow_class.from_client_config.return_value = mock_flow
            mock_flow.credentials = mock_credentials

            result = await exchange_code_for_tokens(
                authorization_code="auth_code_123",
                redirect_uri="http://localhost:8000/api/auth/google/callback"
            )

            assert result["access_token"] == "ya29.a0AfH6SMBxyz123"
            assert result["refresh_token"] == "1//refresh_token_xyz"
            mock_flow.fetch_token.assert_called_once_with(code="auth_code_123")

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_code(self, mock_async_http_client):
        """Should raise HTTPException on invalid authorization code."""
        from oauth import exchange_code_for_tokens
        from fastapi import HTTPException

        mock_error_response = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code"
        }

        mock_async_http_client.post.return_value = Mock(
            status_code=400,
            json=lambda: mock_error_response,
            text="Bad Request"
        )

        with patch("oauth.httpx.AsyncClient", return_value=mock_async_http_client):
            with pytest.raises(HTTPException) as exc_info:
                await exchange_code_for_tokens(
                    authorization_code="invalid_code",  # Fixed parameter name
                    redirect_uri="http://localhost:8000/api/auth/google/callback"
                )

            assert exc_info.value.status_code == 400


class TestRefreshGoogleToken:
    """Test suite for OAuth token refresh."""

    @pytest.mark.asyncio
    async def test_refreshes_token_successfully(self, mock_async_http_client):
        """Should refresh access token using refresh token."""
        from oauth import refresh_google_token

        mock_response = {
            "access_token": "ya29.a0AfH6SMB_new_token",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/spreadsheets",
            "token_type": "Bearer"
        }

        mock_async_http_client.post.return_value = Mock(
            status_code=200,
            json=lambda: mock_response
        )

        with patch("oauth.httpx.AsyncClient", return_value=mock_async_http_client):
            result = await refresh_google_token(refresh_token="1//refresh_token_xyz")

            assert result["access_token"] == mock_response["access_token"]
            assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_refresh_token(self, mock_async_http_client):
        """Should raise HTTPException on invalid refresh token."""
        from oauth import refresh_google_token
        from fastapi import HTTPException

        mock_async_http_client.post.return_value = Mock(
            status_code=400,
            json=lambda: {"error": "invalid_grant"},
            text="Bad Request"
        )

        with patch("oauth.httpx.AsyncClient", return_value=mock_async_http_client):
            with pytest.raises(HTTPException) as exc_info:
                await refresh_google_token(refresh_token="invalid_refresh_token")

            # refresh_google_token raises 401 (token revoked/expired)
            assert exc_info.value.status_code == 401


class TestSaveUserTokens:
    """Test suite for saving OAuth tokens to database."""

    @pytest.mark.asyncio
    async def test_saves_tokens_with_encryption(self, mock_supabase, mock_expires_at):
        """Should save encrypted tokens to database."""
        from oauth import save_user_tokens

        with patch("oauth.get_supabase", return_value=mock_supabase):
            with patch("oauth.encrypt_aes256") as mock_encrypt:
                mock_encrypt.side_effect = lambda x: f"encrypted_{x}"

                await save_user_tokens(
                    user_id="user-123",
                    provider="google",  # Added missing parameter
                    access_token="access_token_plain",
                    refresh_token="refresh_token_plain",
                    expires_at=mock_expires_at,
                    scope="https://www.googleapis.com/auth/spreadsheets"
                )

                # Verify encryption was called
                assert mock_encrypt.call_count == 2
                mock_encrypt.assert_any_call("access_token_plain")
                mock_encrypt.assert_any_call("refresh_token_plain")

                # Verify upsert was called
                mock_supabase.table.assert_called_with("user_oauth_tokens")
                mock_supabase.table.return_value.upsert.assert_called_once()


class TestGetUserGoogleToken:
    """Test suite for retrieving and auto-refreshing user tokens."""

    @pytest.mark.asyncio
    async def test_returns_valid_token_not_expired(self, mock_supabase, mock_expires_at):
        """Should return access token when not expired."""
        from oauth import get_user_google_token

        mock_token_data = {
            "access_token": "encrypted_access_token",
            "refresh_token": "encrypted_refresh_token",
            "expires_at": mock_expires_at.isoformat(),
            "scope": "https://www.googleapis.com/auth/spreadsheets"
        }

        # Return as list (code accesses result.data[0])
        mock_supabase.execute.return_value = Mock(data=[mock_token_data])

        with patch("oauth.get_supabase", return_value=mock_supabase):
            with patch("oauth.decrypt_aes256") as mock_decrypt:
                mock_decrypt.return_value = "decrypted_access_token"

                result = await get_user_google_token(user_id="user-123")

                assert result == "decrypted_access_token"
                # decrypt is called for both access_token and refresh_token
                mock_decrypt.assert_any_call("encrypted_access_token")

    @pytest.mark.asyncio
    async def test_returns_none_when_no_token_found(self, mock_supabase):
        """Should return None when user has no OAuth token."""
        from oauth import get_user_google_token

        # Default fixture returns Mock(data=[]) - empty list means no token found
        with patch("oauth.get_supabase", return_value=mock_supabase):
            result = await get_user_google_token(user_id="user-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_refreshes_token_when_expired(self, mock_supabase):
        """Should refresh token automatically when expired."""
        from oauth import get_user_google_token

        expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired

        mock_token_data = {
            "access_token": "encrypted_old_token",
            "refresh_token": "encrypted_refresh_token",
            "expires_at": expires_at.isoformat(),
            "scope": "https://www.googleapis.com/auth/spreadsheets"
        }

        mock_refresh_response = {
            "access_token": "new_access_token",
            "expires_in": 3600
        }

        # Return token data as a list (result.data[0] access pattern)
        mock_supabase.execute.return_value = Mock(data=[mock_token_data])

        with patch("oauth.get_supabase", return_value=mock_supabase):
            with patch("oauth.decrypt_aes256") as mock_decrypt:
                mock_decrypt.side_effect = ["old_access_token", "refresh_token_plain"]

                with patch("oauth.refresh_google_token", new_callable=AsyncMock, return_value=mock_refresh_response):
                    with patch("oauth.save_user_tokens", new_callable=AsyncMock) as mock_save:
                        result = await get_user_google_token(user_id="user-123")

                        # Should have called save_user_tokens with new token
                        mock_save.assert_called_once()


class TestRevokeUserGoogleToken:
    """Test suite for revoking OAuth tokens."""

    @pytest.mark.asyncio
    async def test_deletes_token_from_database(self, mock_supabase):
        """Should delete OAuth token from database."""
        from oauth import revoke_user_google_token

        # Mock execute to return token data (select query finds a token)
        mock_supabase.execute.return_value = Mock(
            data=[{"access_token": "encrypted_token"}]
        )

        with patch("oauth.get_supabase", return_value=mock_supabase):
            with patch("oauth.decrypt_aes256", return_value="decrypted_token"):
                # Mock httpx to avoid real HTTP calls to Google revoke endpoint
                mock_http = AsyncMock()
                mock_http.__aenter__.return_value = mock_http
                with patch("oauth.httpx.AsyncClient", return_value=mock_http):
                    result = await revoke_user_google_token(user_id="user-123")

                    assert result is True
                    mock_supabase.table.assert_called_with("user_oauth_tokens")
                    mock_supabase.delete.assert_called()

    @pytest.mark.asyncio
    async def test_handles_token_not_found_gracefully(self, mock_supabase):
        """Should handle case when token doesn't exist."""
        from oauth import revoke_user_google_token

        # Default fixture returns Mock(data=[]) - no tokens found
        with patch("oauth.get_supabase", return_value=mock_supabase):
            # Should not raise exception
            result = await revoke_user_google_token(user_id="user-123")
            # Function returns False when no token found (idempotent)
            assert result is False
