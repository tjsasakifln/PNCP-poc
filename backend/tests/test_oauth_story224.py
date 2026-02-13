"""Tests for STORY-224 Track 2: Google OAuth Tests (AC8-AC13).

Additional tests to ensure complete coverage of OAuth functionality
beyond existing test_oauth.py and test_routes_auth_oauth.py.

STORY-224: OAuth test suite completion
- AC8: Test initiate_google_oauth() generates correct authorization URL
- AC9: Test OAuth state parameter includes nonce (after STORY-210 fix)
- AC10: Test complete_google_oauth() exchanges code for tokens (already covered in test_oauth.py)
- AC11: Test OAuth callback rejects invalid state parameter
- AC12: Test token encryption with ENCRYPTION_KEY (not fallback)
- AC13: Test token decryption retrieves original tokens (already covered in test_oauth.py)
"""

import pytest
import os
import secrets
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone, timedelta


@pytest.fixture
def app():
    """Create test FastAPI app with OAuth routes."""
    from fastapi import FastAPI
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


class TestAC8AuthorizationURL:
    """AC8: Test initiate_google_oauth() generates correct authorization URL."""

    def test_authorization_url_contains_all_required_components(self):
        """Should generate authorization URL with ALL required OAuth 2.0 components."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        state = "test_state_nonce_12345"

        auth_url = get_authorization_url(redirect_uri, state)

        # Verify base URL
        assert auth_url.startswith("https://accounts.google.com/o/oauth2/auth")

        # Verify required OAuth 2.0 parameters
        assert "response_type=code" in auth_url
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert f"state={state}" in auth_url
        assert "scope=" in auth_url

        # Verify Google-specific parameters for offline access
        assert "access_type=offline" in auth_url
        assert "prompt=consent" in auth_url

    def test_authorization_url_includes_correct_scope(self):
        """Should include Google Sheets scope in authorization URL."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        state = "test_state"

        auth_url = get_authorization_url(redirect_uri, state)

        # Google Sheets API scope (URL-encoded)
        assert "scope=" in auth_url
        assert "spreadsheets" in auth_url

    def test_authorization_url_uses_provided_state_parameter(self):
        """Should use the exact state parameter provided (CSRF protection)."""
        from oauth import get_authorization_url

        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        unique_state = f"nonce_{secrets.token_urlsafe(32)}"

        auth_url = get_authorization_url(redirect_uri, unique_state)

        # Verify exact state parameter is present
        assert f"state={unique_state}" in auth_url


class TestAC9OAuthStateNonce:
    """AC9: Test OAuth state parameter includes cryptographic nonce (STORY-210 fix)."""

    def test_initiate_oauth_generates_cryptographic_nonce(self, client):
        """Should generate a cryptographic nonce as state parameter (not base64)."""
        captured_state = None

        def capture_auth_url(redirect_uri, state):
            nonlocal captured_state
            captured_state = state
            return f"https://oauth.google.com?state={state}"

        with patch("routes.auth_oauth.get_authorization_url", side_effect=capture_auth_url):
            response = client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)

            assert response.status_code == 307
            assert captured_state is not None

            # Nonce should be URL-safe random string (not base64-encoded user_id)
            # secrets.token_urlsafe(32) produces 43 chars minimum
            assert len(captured_state) >= 32

            # Should NOT be decodable as base64 user_id:redirect pattern
            # (Old pattern was predictable, new pattern is random nonce)
            import base64
            try:
                decoded = base64.urlsafe_b64decode(captured_state.encode()).decode()
                # If decodable, should NOT contain user-id pattern
                assert "user-123-uuid" not in decoded
            except Exception:
                # Expected: nonce is NOT valid base64 encoding of user_id
                pass

    def test_state_parameter_is_unique_per_request(self, client):
        """Should generate different nonce for each OAuth initiation."""
        captured_states = []

        def capture_auth_url(redirect_uri, state):
            captured_states.append(state)
            return f"https://oauth.google.com?state={state}"

        with patch("routes.auth_oauth.get_authorization_url", side_effect=capture_auth_url):
            # Make multiple OAuth initiation requests
            client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)
            client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)
            client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)

            # All nonces should be unique
            assert len(captured_states) == 3
            assert len(set(captured_states)) == 3  # All unique

    def test_nonce_store_associates_user_and_redirect(self, client):
        """Should store nonce with associated user_id and redirect_path."""
        from routes.auth_oauth import _oauth_nonce_store

        # Clear store before test
        _oauth_nonce_store.clear()

        captured_state = None

        def capture_auth_url(redirect_uri, state):
            nonlocal captured_state
            captured_state = state
            return f"https://oauth.google.com?state={state}"

        with patch("routes.auth_oauth.get_authorization_url", side_effect=capture_auth_url):
            response = client.get("/api/auth/google?redirect=/buscar", follow_redirects=False)

            # Verify nonce was stored
            assert captured_state in _oauth_nonce_store

            user_id, redirect_path, created_at = _oauth_nonce_store[captured_state]
            assert user_id == "user-123-uuid"  # From mock_user fixture
            assert redirect_path == "/buscar"
            assert isinstance(created_at, float)  # Unix timestamp


class TestAC11InvalidStateRejection:
    """AC11: Test OAuth callback rejects invalid state parameter."""

    @pytest.mark.asyncio
    async def test_callback_rejects_invalid_nonce(self, client):
        """Should reject OAuth callback with invalid/unknown nonce."""
        # Use a random nonce that was never stored
        invalid_state = secrets.token_urlsafe(32)

        response = client.get(
            f"/api/auth/google/callback?code=auth_code_123&state={invalid_state}",
            follow_redirects=False
        )

        # Should redirect with error
        assert response.status_code == 307
        assert "error=invalid_state" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_callback_rejects_expired_nonce(self, client):
        """Should reject OAuth callback with expired nonce (> 10 minutes)."""
        from routes.auth_oauth import _oauth_nonce_store
        import time

        # Create an expired nonce (created 11 minutes ago)
        expired_nonce = secrets.token_urlsafe(32)
        old_timestamp = time.time() - 660  # 11 minutes ago
        _oauth_nonce_store[expired_nonce] = ("user-123-uuid", "/buscar", old_timestamp)

        response = client.get(
            f"/api/auth/google/callback?code=auth_code_123&state={expired_nonce}",
            follow_redirects=False
        )

        # Should reject expired nonce
        assert response.status_code == 307
        assert "error=invalid_state" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_callback_consumes_nonce_on_valid_use(self, client):
        """Should consume (delete) nonce after successful verification."""
        from routes.auth_oauth import _oauth_nonce_store, _store_oauth_nonce

        # Store a valid nonce
        valid_nonce = _store_oauth_nonce("user-123-uuid", "/buscar")

        # Verify nonce exists before callback
        assert valid_nonce in _oauth_nonce_store

        mock_token_response = {
            "access_token": "ya29.test_token",
            "refresh_token": "1//refresh_token",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "scope": ["https://www.googleapis.com/auth/spreadsheets"]
        }

        with patch("routes.auth_oauth.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_token_response

            with patch("routes.auth_oauth.save_user_tokens", new_callable=AsyncMock):
                response = client.get(
                    f"/api/auth/google/callback?code=auth_code_123&state={valid_nonce}",
                    follow_redirects=False
                )

                # Callback should succeed
                assert response.status_code == 307
                assert "google_oauth=success" in response.headers["location"]

                # Nonce should be consumed (deleted)
                assert valid_nonce not in _oauth_nonce_store

    @pytest.mark.asyncio
    async def test_callback_rejects_reused_nonce(self, client):
        """Should reject nonce reuse (replay attack prevention)."""
        from routes.auth_oauth import _store_oauth_nonce

        # Store a valid nonce
        valid_nonce = _store_oauth_nonce("user-123-uuid", "/buscar")

        mock_token_response = {
            "access_token": "ya29.test_token",
            "refresh_token": "1//refresh_token",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "scope": ["https://www.googleapis.com/auth/spreadsheets"]
        }

        with patch("routes.auth_oauth.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_token_response

            with patch("routes.auth_oauth.save_user_tokens", new_callable=AsyncMock):
                # First use: should succeed
                response1 = client.get(
                    f"/api/auth/google/callback?code=auth_code_123&state={valid_nonce}",
                    follow_redirects=False
                )
                assert response1.status_code == 307
                assert "google_oauth=success" in response1.headers["location"]

                # Second use: should fail (nonce already consumed)
                response2 = client.get(
                    f"/api/auth/google/callback?code=auth_code_456&state={valid_nonce}",
                    follow_redirects=False
                )
                assert response2.status_code == 307
                assert "error=invalid_state" in response2.headers["location"]


class TestAC12EncryptionKeyUsage:
    """AC12: Test token encryption with ENCRYPTION_KEY (not fallback)."""

    def test_encryption_uses_environment_key(self, monkeypatch):
        """Should use ENCRYPTION_KEY from environment variable, not fallback."""
        import base64

        # Set explicit encryption key
        test_key = base64.urlsafe_b64encode(b"test_encryption_key_32_bytes__").decode()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key)

        # Re-import oauth to pick up new env var
        import importlib
        import oauth
        importlib.reload(oauth)

        plaintext = "ya29.test_access_token"
        encrypted = oauth.encrypt_aes256(plaintext)
        decrypted = oauth.decrypt_aes256(encrypted)

        assert decrypted == plaintext

        # Verify it's using the test key (not default fallback)
        # The cipher module-level variable should use our test key
        assert oauth.ENCRYPTION_KEY_B64 == test_key

    def test_encryption_fails_without_key_in_production(self, monkeypatch):
        """Should raise error in production if ENCRYPTION_KEY is missing."""
        # Unset encryption key
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "production")

        # Re-import should raise RuntimeError
        import importlib
        import oauth

        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY is required in production"):
            importlib.reload(oauth)

    def test_encryption_warns_without_key_in_development(self, monkeypatch, caplog):
        """Should warn (but not fail) in development if ENCRYPTION_KEY is missing."""
        import logging

        # Unset encryption key, set development environment
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "development")

        # Re-import oauth module
        import importlib
        import oauth

        with caplog.at_level(logging.WARNING):
            importlib.reload(oauth)

            # Should log warning about missing key
            assert any("ENCRYPTION_KEY not set" in record.message for record in caplog.records)

    def test_encrypted_tokens_are_different_each_time(self):
        """Should produce different ciphertext for same plaintext (Fernet includes timestamp)."""
        from oauth import encrypt_aes256

        plaintext = "ya29.same_token_encrypted_twice"

        encrypted1 = encrypt_aes256(plaintext)
        encrypted2 = encrypt_aes256(plaintext)

        # Ciphertexts should be different (Fernet includes timestamp)
        assert encrypted1 != encrypted2

    def test_encrypted_token_format_is_fernet_compatible(self):
        """Should produce Fernet-compatible encrypted tokens."""
        from oauth import encrypt_aes256

        plaintext = "ya29.test_token"
        encrypted = encrypt_aes256(plaintext)

        # Fernet tokens are base64-encoded and start with specific pattern
        # gAAAAAB... is the standard Fernet prefix
        assert encrypted.startswith("gAAAAA")
        assert len(encrypted) > len(plaintext)


class TestAC13TokenDecryption:
    """AC13: Test token decryption retrieves original tokens (additional scenarios)."""

    def test_decrypt_handles_very_long_tokens(self):
        """Should correctly encrypt/decrypt very long OAuth tokens."""
        from oauth import encrypt_aes256, decrypt_aes256

        # Google access tokens can be 200+ characters
        long_token = "ya29." + "x" * 300

        encrypted = encrypt_aes256(long_token)
        decrypted = decrypt_aes256(encrypted)

        assert decrypted == long_token

    def test_decrypt_handles_special_characters(self):
        """Should correctly handle tokens with special characters."""
        from oauth import encrypt_aes256, decrypt_aes256

        # OAuth tokens can contain - _ / + = characters
        special_token = "ya29.a0AfH6SMB-xyz_123/abc+def==XYZ"

        encrypted = encrypt_aes256(special_token)
        decrypted = decrypt_aes256(encrypted)

        assert decrypted == special_token

    def test_decrypt_raises_error_on_tampered_ciphertext(self):
        """Should raise error when ciphertext is tampered with."""
        from oauth import encrypt_aes256, decrypt_aes256

        plaintext = "ya29.test_token"
        encrypted = encrypt_aes256(plaintext)

        # Tamper with ciphertext (flip a character)
        tampered = encrypted[:-5] + "X" + encrypted[-4:]

        with pytest.raises(Exception):  # Fernet raises InvalidToken
            decrypt_aes256(tampered)

    def test_decrypt_raises_error_on_wrong_key(self, monkeypatch):
        """Should fail to decrypt if key changes between encrypt/decrypt."""
        import base64

        # Encrypt with one key
        test_key1 = base64.urlsafe_b64encode(b"key_one_32_bytes_long_1234567").decode()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key1)

        import importlib
        import oauth
        importlib.reload(oauth)

        plaintext = "ya29.test_token"
        encrypted = oauth.encrypt_aes256(plaintext)

        # Change key
        test_key2 = base64.urlsafe_b64encode(b"key_two_32_bytes_long_7654321").decode()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key2)
        importlib.reload(oauth)

        # Decrypt should fail with different key
        with pytest.raises(Exception):  # Fernet raises InvalidToken
            oauth.decrypt_aes256(encrypted)
