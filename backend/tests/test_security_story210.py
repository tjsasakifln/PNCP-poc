"""Security tests for STORY-210: Security Hardening.

AC15: Full-token cache key collision test
AC16: Encryption key production error test
AC17: Download route validation test (frontend — tested via import)
AC18: OAuth nonce CSRF test
AC19: JWT audience verification test
"""

import hashlib
import os
import time
from unittest.mock import patch, Mock

import jwt as pyjwt
import pytest
from fastapi import HTTPException


# ============================================================================
# AC15: Full-token cache key — different tokens produce different keys
# ============================================================================

class TestTokenCacheKey:
    """Verify that different JWTs produce different cache keys (AC15)."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        from auth import _token_cache
        _token_cache.clear()
        yield
        _token_cache.clear()

    def test_different_tokens_produce_different_cache_keys(self):
        """Two different JWTs must hash to different cache keys.

        Previously, only the first 16 chars were hashed, which is the same
        for all Supabase HS256 JWTs (eyJhbGciOiJIUzI1).
        """
        token_a = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIn0.fake_sig_a"
        token_b = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWIiLCJhdWQiOiJhdXRoZW50aWNhdGVkIn0.fake_sig_b"

        # Same first 16 chars
        assert token_a[:16] == token_b[:16], "Tokens should share the same prefix"

        # Full hash MUST differ
        hash_a = hashlib.sha256(token_a.encode('utf-8')).hexdigest()
        hash_b = hashlib.sha256(token_b.encode('utf-8')).hexdigest()
        assert hash_a != hash_b, "Full-token hashes must differ"

    def test_prefix_only_hash_would_collide(self):
        """Demonstrate the bug: prefix-only hash causes collision."""
        token_a = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.USER_A_PAYLOAD"
        token_b = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.USER_B_PAYLOAD"

        # With prefix-only (the OLD bug)
        prefix_hash_a = hashlib.sha256(token_a[:16].encode('utf-8')).hexdigest()
        prefix_hash_b = hashlib.sha256(token_b[:16].encode('utf-8')).hexdigest()
        assert prefix_hash_a == prefix_hash_b, "Prefix-only hash SHOULD collide (this was the bug)"

        # With full token (the FIX)
        full_hash_a = hashlib.sha256(token_a.encode('utf-8')).hexdigest()
        full_hash_b = hashlib.sha256(token_b.encode('utf-8')).hexdigest()
        assert full_hash_a != full_hash_b, "Full-token hash should NOT collide"

    @pytest.mark.asyncio
    async def test_auth_cache_uses_full_token_hash(self):
        """get_current_user should use full token hash, preventing collision."""
        from auth import get_current_user, _token_cache

        secret = "test-secret-key-for-testing-12345678"
        token_a = pyjwt.encode(
            {"sub": "user-a", "email": "a@test.com", "role": "authenticated", "aud": "authenticated"},
            secret,
            algorithm="HS256",
        )
        token_b = pyjwt.encode(
            {"sub": "user-b", "email": "b@test.com", "role": "authenticated", "aud": "authenticated"},
            secret,
            algorithm="HS256",
        )

        creds_a = Mock()
        creds_a.credentials = token_a
        creds_b = Mock()
        creds_b.credentials = token_b

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": secret}):
            user_a = await get_current_user(creds_a)
            user_b = await get_current_user(creds_b)

        assert user_a["id"] == "user-a"
        assert user_b["id"] == "user-b"
        assert user_a["id"] != user_b["id"], "Different tokens must resolve to different users"
        assert len(_token_cache) == 2, "Both tokens should be cached separately"


# ============================================================================
# AC16: Encryption key production error
# ============================================================================

class TestEncryptionKeyProduction:
    """Verify ENCRYPTION_KEY raises RuntimeError in production when missing (AC16)."""

    def test_missing_encryption_key_raises_in_production(self):
        """When ENCRYPTION_KEY is empty and ENVIRONMENT=production, must raise RuntimeError."""
        import importlib

        env = {
            "ENCRYPTION_KEY": "",
            "ENVIRONMENT": "production",
            "GOOGLE_OAUTH_CLIENT_ID": "",
            "GOOGLE_OAUTH_CLIENT_SECRET": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(RuntimeError, match="ENCRYPTION_KEY is required"):
                import oauth
                importlib.reload(oauth)

    def test_missing_encryption_key_warns_in_development(self):
        """When ENCRYPTION_KEY is empty in dev, should warn but not crash."""
        import importlib

        env = {
            "ENCRYPTION_KEY": "",
            "ENVIRONMENT": "development",
            "GOOGLE_OAUTH_CLIENT_ID": "",
            "GOOGLE_OAUTH_CLIENT_SECRET": "",
        }

        with patch.dict(os.environ, env, clear=False):
            import oauth
            # Should not raise — just use temporary key
            importlib.reload(oauth)
            assert oauth.cipher is not None


# ============================================================================
# AC18: OAuth state nonce — cryptographically random, callback rejects forged
# ============================================================================

class TestOAuthNonce:
    """Verify OAuth CSRF uses cryptographic nonce, not predictable state (AC18)."""

    def test_nonce_is_cryptographically_random(self):
        """Each nonce should be unique and unpredictable."""
        from routes.auth_oauth import _store_oauth_nonce

        nonces = set()
        for _ in range(100):
            nonce = _store_oauth_nonce("user-123", "/buscar")
            nonces.add(nonce)

        assert len(nonces) == 100, "100 nonces should all be unique"

    def test_nonce_length_provides_sufficient_entropy(self):
        """Nonce should have at least 32 bytes of entropy (256 bits)."""
        from routes.auth_oauth import _store_oauth_nonce

        nonce = _store_oauth_nonce("user-123", "/buscar")
        # secrets.token_urlsafe(32) produces ~43 chars
        assert len(nonce) >= 40, f"Nonce too short: {len(nonce)} chars"

    def test_verify_valid_nonce(self):
        """Valid nonce should return (user_id, redirect_path)."""
        from routes.auth_oauth import _store_oauth_nonce, _verify_oauth_nonce

        nonce = _store_oauth_nonce("user-abc", "/dashboard")
        result = _verify_oauth_nonce(nonce)

        assert result is not None
        user_id, redirect_path = result
        assert user_id == "user-abc"
        assert redirect_path == "/dashboard"

    def test_nonce_consumed_on_verify(self):
        """Nonce should be consumed (one-time use) — replay attack prevention."""
        from routes.auth_oauth import _store_oauth_nonce, _verify_oauth_nonce

        nonce = _store_oauth_nonce("user-abc", "/buscar")

        # First verification succeeds
        result = _verify_oauth_nonce(nonce)
        assert result is not None

        # Second verification fails (nonce consumed)
        result = _verify_oauth_nonce(nonce)
        assert result is None

    def test_forged_nonce_rejected(self):
        """Forged/unknown nonce should be rejected."""
        from routes.auth_oauth import _verify_oauth_nonce

        result = _verify_oauth_nonce("forged-nonce-value-abc123")
        assert result is None

    def test_expired_nonce_rejected(self):
        """Nonce older than TTL should be rejected."""
        from routes.auth_oauth import (
            _store_oauth_nonce,
            _verify_oauth_nonce,
            _oauth_nonce_store,
            _OAUTH_NONCE_TTL,
        )

        nonce = _store_oauth_nonce("user-abc", "/buscar")

        # Manually expire the nonce
        user_id, redirect_path, _ = _oauth_nonce_store[nonce]
        _oauth_nonce_store[nonce] = (user_id, redirect_path, time.time() - _OAUTH_NONCE_TTL - 1)

        result = _verify_oauth_nonce(nonce)
        assert result is None

    def test_redirect_path_whitelist(self):
        """Only whitelisted redirect paths should be accepted."""
        from routes.auth_oauth import _ALLOWED_REDIRECT_PATHS

        assert "/buscar" in _ALLOWED_REDIRECT_PATHS
        assert "/dashboard" in _ALLOWED_REDIRECT_PATHS
        assert "https://evil.com" not in _ALLOWED_REDIRECT_PATHS


# ============================================================================
# AC19: JWT audience verification
# ============================================================================

class TestJWTAudienceVerification:
    """Verify JWT with wrong audience is rejected (AC19)."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        from auth import _token_cache
        _token_cache.clear()
        yield
        _token_cache.clear()

    @pytest.mark.asyncio
    async def test_jwt_wrong_audience_rejected(self):
        """JWT with wrong audience claim should be rejected with 401."""
        from auth import get_current_user

        secret = "test-secret-key-for-testing-12345678"

        # Token with wrong audience
        token = pyjwt.encode(
            {"sub": "user-x", "aud": "wrong-audience", "role": "authenticated"},
            secret,
            algorithm="HS256",
        )

        creds = Mock()
        creds.credentials = token

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": secret}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(creds)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_jwt_correct_audience_accepted(self):
        """JWT with 'authenticated' audience should be accepted."""
        from auth import get_current_user

        secret = "test-secret-key-for-testing-12345678"

        token = pyjwt.encode(
            {
                "sub": "user-y",
                "email": "y@test.com",
                "aud": "authenticated",
                "role": "authenticated",
            },
            secret,
            algorithm="HS256",
        )

        creds = Mock()
        creds.credentials = token

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": secret}):
            user = await get_current_user(creds)

        assert user["id"] == "user-y"
        assert user["email"] == "y@test.com"

    @pytest.mark.asyncio
    async def test_jwt_missing_audience_rejected(self):
        """JWT without audience claim should be rejected."""
        from auth import get_current_user

        secret = "test-secret-key-for-testing-12345678"

        token = pyjwt.encode(
            {"sub": "user-z", "role": "authenticated"},
            secret,
            algorithm="HS256",
        )

        creds = Mock()
        creds.credentials = token

        with patch.dict(os.environ, {"SUPABASE_JWT_SECRET": secret}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(creds)

        assert exc_info.value.status_code == 401


# ============================================================================
# Rate limiting tests for /change-password (AC12)
# ============================================================================

class TestChangePasswordRateLimit:
    """Verify rate limiting on /change-password endpoint."""

    @pytest.fixture(autouse=True)
    def reset_rate_limiter(self):
        from routes.user import _change_password_attempts
        _change_password_attempts.clear()
        yield
        _change_password_attempts.clear()

    def test_allows_up_to_5_attempts(self):
        """Should allow 5 attempts within the window."""
        from routes.user import _check_change_password_rate_limit

        for _ in range(5):
            _check_change_password_rate_limit("user-test-123")
        # No exception = pass

    def test_blocks_6th_attempt(self):
        """Should block the 6th attempt within 15 minutes."""
        from routes.user import _check_change_password_rate_limit

        for _ in range(5):
            _check_change_password_rate_limit("user-test-123")

        with pytest.raises(HTTPException) as exc_info:
            _check_change_password_rate_limit("user-test-123")

        assert exc_info.value.status_code == 429

    def test_different_users_have_separate_limits(self):
        """Rate limit should be per-user, not global."""
        from routes.user import _check_change_password_rate_limit

        for _ in range(5):
            _check_change_password_rate_limit("user-a")

        # User B should still be allowed
        _check_change_password_rate_limit("user-b")


# ============================================================================
# Security headers middleware test (AC10)
# ============================================================================

class TestSecurityHeaders:
    """Verify security headers are added to responses."""

    def test_security_headers_applied(self):
        """All required security headers should be present in response."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from middleware import SecurityHeadersMiddleware

        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/test")

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in response.headers["Permissions-Policy"]


# ============================================================================
# Plans endpoint no longer leaks Stripe Price IDs (AC11)
# ============================================================================

class TestPlansStripePriceIds:
    """Verify Stripe Price IDs are stripped from /api/plans response."""

    def test_plan_details_model_has_no_stripe_fields(self):
        """PlanDetails model should NOT have stripe_price_id fields."""
        from routes.plans import PlanDetails

        field_names = set(PlanDetails.model_fields.keys())
        assert "stripe_price_id_monthly" not in field_names
        assert "stripe_price_id_annual" not in field_names
