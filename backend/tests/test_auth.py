"""Tests for authentication middleware (auth.py).

Tests local JWT verification, require_auth dependency, caching, and error handling.
Mocks jwt.decode and os.environ instead of the old Supabase client.

Rewritten for STORY-214 Frente 1: auth.py now does local JWT validation
using PyJWT instead of calling Supabase Auth API.
"""

import hashlib
import os
import time
import pytest
import jwt as pyjwt
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient


# ── Shared constants ────────────────────────────────────────────────────────

TEST_JWT_SECRET = "test-secret-key-at-least-32-chars-long!"
TEST_SUPABASE_URL = "https://test.supabase.co"

# Standard valid JWT claims
VALID_CLAIMS = {
    "sub": "user-123-uuid",
    "email": "test@example.com",
    "role": "authenticated",
    "aud": "authenticated",
}

# Env vars needed by auth.py
TEST_ENV = {
    "SUPABASE_JWT_SECRET": TEST_JWT_SECRET,
    "SUPABASE_URL": TEST_SUPABASE_URL,
}


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_auth_cache():
    """Clear auth token cache before each test to prevent cache poisoning."""
    from auth import _token_cache
    _token_cache.clear()
    yield
    _token_cache.clear()


@pytest.fixture
def mock_credentials():
    """Create mock HTTP Authorization credentials."""
    mock = Mock()
    mock.credentials = "valid-jwt-token-123"
    return mock


def _make_credentials(token: str) -> Mock:
    """Helper: create mock credentials with a specific token string."""
    mock = Mock()
    mock.credentials = token
    return mock


# ══════════════════════════════════════════════════════════════════════════════
# AC1-AC9: Unit tests (mock jwt.decode)
# ══════════════════════════════════════════════════════════════════════════════


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_credentials(self):
        """Should return None when no credentials provided (allows anonymous access)."""
        from auth import get_current_user

        result = await get_current_user(credentials=None)

        assert result is None

    # ── AC2: Valid JWT returns correct user data ────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_returns_user_dict_on_valid_token(self, mock_jwt_decode, mock_credentials):
        """AC2: Valid HS256 JWT returns correct user_id, email, role."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "user-123-uuid",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
        }

        result = await get_current_user(credentials=mock_credentials)

        assert result is not None
        assert result["id"] == "user-123-uuid"
        assert result["email"] == "test@example.com"
        assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_jwt_decode_called_with_correct_params(self, mock_jwt_decode, mock_credentials):
        """AC1: jwt.decode is called with token, secret, HS256, and audience."""
        from auth import get_current_user

        mock_jwt_decode.return_value = dict(VALID_CLAIMS)

        await get_current_user(credentials=mock_credentials)

        mock_jwt_decode.assert_called_once_with(
            mock_credentials.credentials,
            TEST_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )

    # ── AC3: Expired JWT → 401 ─────────────────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_raises_401_when_token_expired(self, mock_jwt_decode, mock_credentials):
        """AC3: Expired JWT raises 401 'Token expirado'."""
        from auth import get_current_user

        mock_jwt_decode.side_effect = pyjwt.ExpiredSignatureError()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token expirado"

    # ── AC4: Invalid/malformed JWT → 401 ───────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_raises_401_when_token_invalid(self, mock_jwt_decode, mock_credentials):
        """AC4: Invalid JWT raises 401 'Token invalido'."""
        from auth import get_current_user

        mock_jwt_decode.side_effect = pyjwt.InvalidTokenError("bad token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token invalido"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_raises_401_when_token_decode_error(self, mock_jwt_decode, mock_credentials):
        """AC4: DecodeError (subclass of InvalidTokenError) also raises 401."""
        from auth import get_current_user

        mock_jwt_decode.side_effect = pyjwt.DecodeError("Not enough segments")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token invalido"

    # ── AC5: Missing JWT secret → 401 (GTM-CRIT-003) ──────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"SUPABASE_URL": TEST_SUPABASE_URL}, clear=False)
    async def test_raises_401_when_jwt_secret_missing(self, mock_credentials):
        """AC5: Missing SUPABASE_JWT_SECRET raises 401 'Autenticação indisponível' (GTM-CRIT-003)."""
        from auth import get_current_user, reset_jwks_client

        # Clear JWKS client state to force re-initialization
        reset_jwks_client()

        # Ensure the key is NOT in environment
        env_copy = os.environ.copy()
        env_copy.pop("SUPABASE_JWT_SECRET", None)

        with patch.dict(os.environ, env_copy, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Autenticação indisponível" in exc_info.value.detail
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"

    # ── AC6: JWT without sub claim → 401 ──────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_raises_401_when_jwt_has_no_sub(self, mock_jwt_decode, mock_credentials):
        """AC6: JWT without 'sub' claim raises 401 'Token sem user ID'."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "email": "no-sub@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            # no "sub" key
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token sem user ID"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_raises_401_when_sub_is_empty_string(self, mock_jwt_decode, mock_credentials):
        """AC6: JWT with empty string 'sub' raises 401 'Token sem user ID'."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "",
            "email": "empty-sub@example.com",
            "role": "authenticated",
            "aud": "authenticated",
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token sem user ID"

    # ── AC7: Missing email defaults to "unknown" ──────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_defaults_email_to_unknown_when_missing(self, mock_jwt_decode, mock_credentials):
        """AC7: JWT with missing email defaults to 'unknown'."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "user-no-email",
            "role": "authenticated",
            "aud": "authenticated",
            # no "email" key
        }

        result = await get_current_user(credentials=mock_credentials)

        assert result["id"] == "user-no-email"
        assert result["email"] == "unknown"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_defaults_email_to_unknown_when_none(self, mock_jwt_decode, mock_credentials):
        """AC7: JWT with email=None also defaults to 'unknown'."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "user-null-email",
            "email": None,
            "role": "authenticated",
            "aud": "authenticated",
        }

        result = await get_current_user(credentials=mock_credentials)

        assert result["id"] == "user-null-email"
        assert result["email"] == "unknown"

    # ── AC8: role = "authenticated" ───────────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_role_authenticated(self, mock_jwt_decode, mock_credentials):
        """AC8: JWT with role='authenticated' is returned correctly."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "user-auth-role",
            "email": "auth@example.com",
            "role": "authenticated",
            "aud": "authenticated",
        }

        result = await get_current_user(credentials=mock_credentials)

        assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_role_defaults_to_authenticated(self, mock_jwt_decode, mock_credentials):
        """AC8: JWT without explicit role defaults to 'authenticated'."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "user-no-role",
            "email": "norole@example.com",
            "aud": "authenticated",
            # no "role" key
        }

        result = await get_current_user(credentials=mock_credentials)

        assert result["role"] == "authenticated"

    # ── AC9: role = "service_role" ────────────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_role_service_role(self, mock_jwt_decode, mock_credentials):
        """AC9: JWT with role='service_role' is returned correctly."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "service-account-id",
            "email": "service@internal.com",
            "role": "service_role",
            "aud": "authenticated",
        }

        result = await get_current_user(credentials=mock_credentials)

        assert result["role"] == "service_role"
        assert result["id"] == "service-account-id"
        assert result["email"] == "service@internal.com"

    # ── General exception handling ────────────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_general_exception_raises_401(self, mock_jwt_decode, mock_credentials):
        """General exception during validation raises 401 'Token invalido ou expirado'."""
        from auth import get_current_user

        mock_jwt_decode.side_effect = RuntimeError("Unexpected failure")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token invalido ou expirado"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_general_exception_logs_auth_event(self, mock_jwt_decode, mock_credentials):
        """General exception should invoke log_auth_event with event type name."""
        from auth import get_current_user

        mock_jwt_decode.side_effect = ValueError("something weird")

        with patch("auth.log_auth_event") as mock_log:
            with pytest.raises(HTTPException):
                await get_current_user(credentials=mock_credentials)

            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args
            # Positional or keyword args
            assert call_kwargs[1]["event"] == "token_verification" or call_kwargs[0][1] == "token_verification"
            assert call_kwargs[1].get("success") is False or (len(call_kwargs[0]) > 2 and call_kwargs[0][2] is False)

    # ── Cache behavior ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_caches_validated_token(self, mock_jwt_decode, mock_credentials):
        """Validated token is cached; second call does not invoke jwt.decode again."""
        from auth import get_current_user, _token_cache

        mock_jwt_decode.return_value = dict(VALID_CLAIMS)

        # First call: populates cache
        result1 = await get_current_user(credentials=mock_credentials)
        assert mock_jwt_decode.call_count == 1
        assert len(_token_cache) == 1

        # Second call: served from cache
        result2 = await get_current_user(credentials=mock_credentials)
        assert mock_jwt_decode.call_count == 1  # NOT called again
        assert result2["id"] == result1["id"]

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_cache_expires_after_ttl(self, mock_jwt_decode, mock_credentials):
        """Cached token expires after CACHE_TTL seconds."""
        from auth import get_current_user, _token_cache, CACHE_TTL

        mock_jwt_decode.return_value = dict(VALID_CLAIMS)

        # First call: populates cache
        await get_current_user(credentials=mock_credentials)
        assert mock_jwt_decode.call_count == 1

        # Manually expire the cache entry
        token_hash = hashlib.sha256(
            mock_credentials.credentials.encode("utf-8")
        ).hexdigest()
        user_data, _ = _token_cache[token_hash]
        _token_cache[token_hash] = (user_data, time.time() - CACHE_TTL - 1)

        # Third call: cache expired, jwt.decode called again
        await get_current_user(credentials=mock_credentials)
        assert mock_jwt_decode.call_count == 2

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_cache_uses_sha256_of_full_token(self, mock_jwt_decode, mock_credentials):
        """Cache key is SHA256 hash of the full token (STORY-210 AC3)."""
        from auth import get_current_user, _token_cache

        mock_jwt_decode.return_value = dict(VALID_CLAIMS)

        await get_current_user(credentials=mock_credentials)

        expected_hash = hashlib.sha256(
            mock_credentials.credentials.encode("utf-8")
        ).hexdigest()
        assert expected_hash in _token_cache

    # ── HTTPException re-raise path ───────────────────────────────────────

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_reraises_http_exception_directly(self, mock_jwt_decode, mock_credentials):
        """HTTPException raised during validation is re-raised unchanged."""
        from auth import get_current_user

        # Missing sub triggers HTTPException 401 internally
        mock_jwt_decode.return_value = {
            "aud": "authenticated",
            "role": "authenticated",
            # no "sub"
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token sem user ID"


# ══════════════════════════════════════════════════════════════════════════════
# TestRequireAuth
# ══════════════════════════════════════════════════════════════════════════════


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


# ══════════════════════════════════════════════════════════════════════════════
# TestHTTPBearerSecurity
# ══════════════════════════════════════════════════════════════════════════════


class TestHTTPBearerSecurity:
    """Test suite for HTTP Bearer security scheme configuration."""

    def test_security_auto_error_is_false(self):
        """Security scheme should have auto_error=False to allow optional auth."""
        from auth import security

        assert security.auto_error is False


# ══════════════════════════════════════════════════════════════════════════════
# AC10: Integration tests with REAL JWT tokens (jwt.encode + jwt.decode)
# ══════════════════════════════════════════════════════════════════════════════


class TestAuthIntegration:
    """Integration tests using real PyJWT encode/decode — no jwt.decode mock.

    These tests create actual HS256 JWT tokens and only patch environment
    variables, so the full JWT validation path in auth.py runs for real.
    """

    INTEGRATION_SECRET = "integration-test-secret-must-be-32-chars!!"

    INTEGRATION_ENV = {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    }

    def _encode_token(self, claims: dict, secret: str | None = None) -> str:
        """Create a real HS256 JWT from claims."""
        return pyjwt.encode(
            claims,
            secret or self.INTEGRATION_SECRET,
            algorithm="HS256",
        )

    @pytest.fixture
    def app_with_protected_route(self):
        """Create a FastAPI app with public and protected routes."""
        from fastapi import FastAPI, Depends
        from auth import require_auth, get_current_user

        app = FastAPI()

        @app.get("/public")
        async def public_endpoint(user=Depends(get_current_user)):
            return {"user": user}

        @app.get("/protected")
        async def protected_endpoint(user=Depends(require_auth)):
            return {"user_id": user["id"], "email": user["email"], "role": user["role"]}

        return app

    # ── AC10: Real JWT round-trip ─────────────────────────────────────────

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_round_trip_protected_endpoint(self, app_with_protected_route):
        """AC10: Real JWT encode -> auth.py decode -> correct user returned."""
        token = self._encode_token({
            "sub": "real-user-id-abc",
            "email": "real@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        })

        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["user_id"] == "real-user-id-abc"
        assert body["email"] == "real@example.com"
        assert body["role"] == "authenticated"

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_service_role(self, app_with_protected_route):
        """AC10+AC9: Real JWT with service_role works end-to-end."""
        token = self._encode_token({
            "sub": "service-id-xyz",
            "email": "svc@internal.com",
            "role": "service_role",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        })

        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["role"] == "service_role"
        assert body["user_id"] == "service-id-xyz"

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_expired_token(self, app_with_protected_route):
        """AC10+AC3: Real expired JWT returns 401 via real jwt.decode."""
        token = self._encode_token({
            "sub": "expired-user",
            "email": "expired@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(time.time()) - 3600,  # expired 1 hour ago
            "iat": int(time.time()) - 7200,
        })

        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "expirado" in response.json()["detail"].lower()

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_wrong_secret(self, app_with_protected_route):
        """AC10+AC4: JWT signed with wrong secret is rejected."""
        token = self._encode_token(
            {
                "sub": "wrong-secret-user",
                "email": "wrong@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
            },
            secret="completely-different-wrong-secret-key!!!!!",
        )

        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "invalido" in response.json()["detail"].lower()

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_malformed_token(self, app_with_protected_route):
        """AC10+AC4: Completely malformed token string is rejected."""
        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer not.a.valid.jwt.at.all"},
        )

        assert response.status_code == 401

    def test_public_endpoint_works_without_token(self, app_with_protected_route):
        """Public endpoint returns None user when no token provided."""
        client = TestClient(app_with_protected_route)

        response = client.get("/public")

        assert response.status_code == 200
        assert response.json()["user"] is None

    def test_protected_endpoint_requires_token(self, app_with_protected_route):
        """Protected endpoint returns 401 without any token."""
        client = TestClient(app_with_protected_route)

        response = client.get("/protected")

        assert response.status_code == 401

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_missing_email_defaults_to_unknown(self, app_with_protected_route):
        """AC10+AC7: Real JWT without email field defaults to 'unknown'."""
        token = self._encode_token({
            "sub": "user-no-email-real",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
            # no "email" key
        })

        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == "unknown"

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_missing_sub_returns_401(self, app_with_protected_route):
        """AC10+AC6: Real JWT without 'sub' claim returns 401."""
        token = self._encode_token({
            "email": "nosub@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
            # no "sub" key
        })

        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "user ID" in response.json()["detail"] or "sem" in response.json()["detail"].lower()

    @patch.dict(os.environ, {
        "SUPABASE_JWT_SECRET": "integration-test-secret-must-be-32-chars!!",
        "SUPABASE_URL": "https://integration.supabase.co",
    })
    def test_real_jwt_wrong_audience(self, app_with_protected_route):
        """AC10: JWT with wrong audience is rejected."""
        token = self._encode_token({
            "sub": "wrong-aud-user",
            "email": "aud@example.com",
            "role": "authenticated",
            "aud": "wrong-audience",
            "exp": int(time.time()) + 3600,
        })

        client = TestClient(app_with_protected_route)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# TestAuthEdgeCases
# ══════════════════════════════════════════════════════════════════════════════


class TestAuthEdgeCases:
    """Test edge cases and boundary conditions for auth module."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_handles_user_with_missing_email(self, mock_jwt_decode):
        """JWT with missing email defaults to 'unknown'."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "edge-user-id",
            "role": "authenticated",
            "aud": "authenticated",
            # no "email"
        }

        result = await get_current_user(credentials=_make_credentials("edge-token-1"))

        assert result["id"] == "edge-user-id"
        assert result["email"] == "unknown"
        assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_handles_user_with_empty_email(self, mock_jwt_decode):
        """JWT with empty string email defaults to 'unknown'."""
        from auth import get_current_user

        mock_jwt_decode.return_value = {
            "sub": "edge-user-empty-email",
            "email": "",
            "role": "authenticated",
            "aud": "authenticated",
        }

        result = await get_current_user(credentials=_make_credentials("edge-token-2"))

        assert result["id"] == "edge-user-empty-email"
        # empty string is falsy, so auth.py does `email or "unknown"`
        assert result["email"] == "unknown"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_uuid_style_user_id_preserved(self, mock_jwt_decode):
        """UUID-style sub claim is preserved as-is in the returned dict."""
        from auth import get_current_user

        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        mock_jwt_decode.return_value = {
            "sub": uuid_str,
            "email": "uuid@example.com",
            "role": "authenticated",
            "aud": "authenticated",
        }

        result = await get_current_user(credentials=_make_credentials("edge-token-3"))

        assert result["id"] == uuid_str
        assert isinstance(result["id"], str)

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_different_tokens_get_different_cache_entries(self, mock_jwt_decode):
        """Two different tokens produce separate cache entries."""
        from auth import get_current_user, _token_cache

        mock_jwt_decode.return_value = dict(VALID_CLAIMS)

        creds_a = _make_credentials("token-aaa")
        creds_b = _make_credentials("token-bbb")

        await get_current_user(credentials=creds_a)
        await get_current_user(credentials=creds_b)

        assert len(_token_cache) == 2
        assert mock_jwt_decode.call_count == 2

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_invalid_audience_raises_invalid_token(self, mock_jwt_decode):
        """InvalidAudienceError (subclass of InvalidTokenError) → 401."""
        from auth import get_current_user

        mock_jwt_decode.side_effect = pyjwt.InvalidAudienceError("wrong aud")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=_make_credentials("bad-aud-token"))

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token invalido"

    @pytest.mark.asyncio
    @patch.dict(os.environ, TEST_ENV)
    @patch("auth.jwt.decode")
    async def test_invalid_issuer_raises_invalid_token(self, mock_jwt_decode):
        """InvalidIssuerError (subclass of InvalidTokenError) → 401."""
        from auth import get_current_user

        mock_jwt_decode.side_effect = pyjwt.InvalidIssuerError("wrong iss")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=_make_credentials("bad-iss-token"))

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token invalido"

    def test_clear_token_cache_returns_count(self):
        """clear_token_cache returns the number of cleared entries."""
        from auth import clear_token_cache, _token_cache

        _token_cache["hash1"] = ({"id": "a"}, time.time())
        _token_cache["hash2"] = ({"id": "b"}, time.time())

        count = clear_token_cache()

        assert count == 2
        assert len(_token_cache) == 0

    def test_clear_token_cache_empty(self):
        """clear_token_cache on empty cache returns 0."""
        from auth import clear_token_cache

        count = clear_token_cache()

        assert count == 0
