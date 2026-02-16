"""Tests for ES256 JWT support in auth.py (STORY-227 Track 2).

Tests ES256 token validation, JWKS caching, backward compatibility with HS256,
and full round-trip integration with real cryptographic key pairs.

AC11: ES256 token validation (unit tests)
AC12: HS256 backward compatibility
AC13: JWKS key caching behavior
AC14: ES256 integration round-trip (no mocking jwt.decode)
"""

import hashlib
import os
import time
import pytest
import jwt as pyjwt
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, FastAPI, Depends
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


# ── Shared constants ──────────────────────────────────────────────────────────

TEST_SUPABASE_URL = "https://test.supabase.co"
TEST_HS256_SECRET = "test-hs256-secret-key-at-least-32-chars-long!"

# Standard valid JWT claims
VALID_CLAIMS = {
    "sub": "user-es256-uuid",
    "email": "es256@example.com",
    "role": "authenticated",
    "aud": "authenticated",
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_auth_cache():
    """Clear auth token cache before each test to prevent cache poisoning."""
    from auth import _token_cache
    _token_cache.clear()
    yield
    _token_cache.clear()


@pytest.fixture(autouse=True)
def reset_jwks_state():
    """Reset the module-level JWKS client state before each test.

    auth.py has a lazy-initialized _jwks_client and a _jwks_init_attempted
    guard that prevents re-initialization after the first attempt. Both must
    be reset between tests to avoid state leakage.

    Uses auth.reset_jwks_client() if available; falls back to direct
    attribute manipulation.
    """
    import auth
    if hasattr(auth, "reset_jwks_client"):
        auth.reset_jwks_client()
    else:
        if hasattr(auth, "_jwks_client"):
            auth._jwks_client = None
        if hasattr(auth, "_jwks_init_attempted"):
            auth._jwks_init_attempted = False
    yield
    if hasattr(auth, "reset_jwks_client"):
        auth.reset_jwks_client()
    else:
        if hasattr(auth, "_jwks_client"):
            auth._jwks_client = None
        if hasattr(auth, "_jwks_init_attempted"):
            auth._jwks_init_attempted = False


@pytest.fixture
def ec_key_pair():
    """Generate a fresh EC P-256 key pair for ES256 JWT signing/verification.

    Returns:
        dict with keys:
            - private_key: EC private key object
            - public_key: EC public key object
            - private_pem: PEM-encoded private key (bytes)
            - public_pem: PEM-encoded public key (bytes)
            - public_pem_str: PEM-encoded public key (str, for env vars)
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return {
        "private_key": private_key,
        "public_key": public_key,
        "private_pem": private_pem,
        "public_pem": public_pem,
        "public_pem_str": public_pem.decode("utf-8"),
    }


@pytest.fixture
def second_ec_key_pair():
    """Generate a second, independent EC P-256 key pair.

    Used for testing wrong-key scenarios where a token signed by one key
    is verified against a different key.
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return {
        "private_key": private_key,
        "public_key": public_key,
        "private_pem": private_pem,
        "public_pem": public_pem,
        "public_pem_str": public_pem.decode("utf-8"),
    }


@pytest.fixture
def app_with_protected_route():
    """Create a FastAPI app with public and protected routes for integration tests."""
    from auth import require_auth, get_current_user

    app = FastAPI()

    @app.get("/public")
    async def public_endpoint(user=Depends(get_current_user)):
        return {"user": user}

    @app.get("/protected")
    async def protected_endpoint(user=Depends(require_auth)):
        return {"user_id": user["id"], "email": user["email"], "role": user["role"]}

    return app


def _make_credentials(token: str) -> Mock:
    """Helper: create mock HTTPAuthorizationCredentials with a specific token."""
    mock = Mock()
    mock.credentials = token
    return mock


def _encode_es256_token(claims: dict, private_pem: bytes) -> str:
    """Helper: create a real ES256 JWT from claims and a PEM private key."""
    return pyjwt.encode(claims, private_pem, algorithm="ES256")


def _encode_hs256_token(claims: dict, secret: str) -> str:
    """Helper: create a real HS256 JWT from claims and a symmetric secret."""
    return pyjwt.encode(claims, secret, algorithm="HS256")


def _valid_claims_with_exp(**overrides) -> dict:
    """Helper: return valid claims with a future expiry, merged with overrides."""
    base = {
        "sub": "user-es256-uuid",
        "email": "es256@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    base.update(overrides)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# AC11: Unit tests for ES256 token validation
# ══════════════════════════════════════════════════════════════════════════════


class TestES256Validation:
    """AC11: Unit tests for ES256 token validation via PEM public key."""

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_es256_token_returns_correct_user_data(self, mock_jwt_decode, ec_key_pair):
        """AC11: ES256 token validated with PEM public key returns correct user data."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",  # Empty to prevent JWKS auto-construction
        }
        mock_jwt_decode.return_value = {
            "sub": "es256-user-id",
            "email": "alice@es256.com",
            "role": "authenticated",
            "aud": "authenticated",
        }

        token = _encode_es256_token(
            _valid_claims_with_exp(sub="es256-user-id", email="alice@es256.com"),
            ec_key_pair["private_pem"],
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            result = await get_current_user(credentials=creds)

        assert result is not None
        assert result["id"] == "es256-user-id"
        assert result["email"] == "alice@es256.com"
        assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    async def test_pem_key_detected_uses_es256_algorithm(self, ec_key_pair):
        """AC11: When SUPABASE_JWT_SECRET starts with '-----BEGIN', ES256 algorithm is used.

        Directly tests _get_jwt_key_and_algorithms to verify PEM detection
        returns the correct key and ["ES256"] algorithms.
        """
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",  # Empty to prevent JWKS auto-construction
        }

        with patch.dict(os.environ, env, clear=False):
            key, algorithms = auth._get_jwt_key_and_algorithms("fake-es256-token")

        assert algorithms == ["ES256"]
        # Key is the PEM string (not bytes) from env var
        assert "-----BEGIN" in str(key)

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_es256_token_with_service_role(self, mock_jwt_decode, ec_key_pair):
        """AC11: ES256 token with service_role is handled correctly."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.return_value = {
            "sub": "service-es256-id",
            "email": "svc@internal.com",
            "role": "service_role",
            "aud": "authenticated",
        }

        token = _encode_es256_token(
            _valid_claims_with_exp(sub="service-es256-id", email="svc@internal.com", role="service_role"),
            ec_key_pair["private_pem"],
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            result = await get_current_user(credentials=creds)

        assert result["id"] == "service-es256-id"
        assert result["role"] == "service_role"

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_es256_token_missing_sub_raises_401(self, mock_jwt_decode, ec_key_pair):
        """AC11: ES256 token without 'sub' claim raises 401."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.return_value = {
            "email": "nosub@es256.com",
            "role": "authenticated",
            "aud": "authenticated",
        }

        token = "fake-es256-no-sub"
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "user ID" in exc_info.value.detail or "sem" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_es256_token_missing_email_defaults_to_unknown(self, mock_jwt_decode, ec_key_pair):
        """AC11: ES256 token without email defaults to 'unknown'."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.return_value = {
            "sub": "es256-no-email",
            "role": "authenticated",
            "aud": "authenticated",
        }

        token = "fake-es256-no-email"
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            result = await get_current_user(credentials=creds)

        assert result["email"] == "unknown"

    @pytest.mark.asyncio
    async def test_es256_token_with_mocked_key_resolution(self, ec_key_pair):
        """AC11: ES256 validation via mocked _get_jwt_key_and_algorithms.

        Mocks the key resolution helper to return an ES256 public key (as bytes),
        then verifies auth.py correctly passes it to jwt.decode and returns user data.
        """
        from auth import get_current_user
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        token = _encode_es256_token(
            _valid_claims_with_exp(sub="mock-key-user", email="mockkey@test.com"),
            ec_key_pair["private_pem"],
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            with patch.object(
                auth, "_get_jwt_key_and_algorithms",
                return_value=(ec_key_pair["public_pem"], ["ES256"]),
            ):
                result = await get_current_user(credentials=creds)

        assert result is not None
        assert result["id"] == "mock-key-user"
        assert result["email"] == "mockkey@test.com"

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_es256_expired_token_raises_401(self, mock_jwt_decode, ec_key_pair):
        """AC11: Expired ES256 token raises 401 'Token expirado'."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.side_effect = pyjwt.ExpiredSignatureError()

        token = _encode_es256_token(
            _valid_claims_with_exp(exp=int(time.time()) - 3600),
            ec_key_pair["private_pem"],
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token expirado"

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_es256_invalid_signature_raises_401(self, mock_jwt_decode, ec_key_pair):
        """AC11: ES256 token with invalid signature raises 401."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.side_effect = pyjwt.InvalidSignatureError("Signature verification failed")

        token = "fake-bad-sig-token"
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        # Could be "Token invalido" or "Token invalido ou expirado" depending on
        # whether fallback decode also fails
        assert "invalido" in exc_info.value.detail.lower()


# ══════════════════════════════════════════════════════════════════════════════
# AC12: HS256 backward compatibility
# ══════════════════════════════════════════════════════════════════════════════


class TestHS256BackwardCompatibility:
    """AC12: Confirm HS256 tokens are still accepted after ES256 support is added."""

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_hs256_token_still_validated_with_symmetric_secret(self, mock_jwt_decode):
        """AC12: HS256 token validated when SUPABASE_JWT_SECRET is a plain string."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": TEST_HS256_SECRET,
            "SUPABASE_URL": "",  # Empty to prevent JWKS
        }
        mock_jwt_decode.return_value = {
            "sub": "hs256-user",
            "email": "hs256@example.com",
            "role": "authenticated",
            "aud": "authenticated",
        }

        token = _encode_hs256_token(
            _valid_claims_with_exp(sub="hs256-user", email="hs256@example.com"),
            TEST_HS256_SECRET,
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            result = await get_current_user(credentials=creds)

        assert result is not None
        assert result["id"] == "hs256-user"
        assert result["email"] == "hs256@example.com"

    @pytest.mark.asyncio
    async def test_symmetric_secret_uses_hs256_algorithm(self):
        """AC12: Non-PEM secret (no '-----BEGIN') selects HS256 algorithm.

        Directly tests _get_jwt_key_and_algorithms to verify non-PEM keys
        produce HS256 strategy.
        """
        import auth

        env = {
            "SUPABASE_JWT_SECRET": TEST_HS256_SECRET,
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            key, algorithms = auth._get_jwt_key_and_algorithms("fake-hs256-token")

        assert algorithms == ["HS256"]
        assert key == TEST_HS256_SECRET

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_es256_token_rejected_when_using_hs256_secret(self, mock_jwt_decode, ec_key_pair):
        """AC12: ES256 token with wrong key type (HS256 secret) is rejected."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": TEST_HS256_SECRET,  # Symmetric, not PEM
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.side_effect = pyjwt.InvalidTokenError(
            "Algorithm mismatch or invalid signature"
        )

        # Token is ES256-signed but secret is HS256
        token = _encode_es256_token(
            _valid_claims_with_exp(),
            ec_key_pair["private_pem"],
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "invalido" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_hs256_expired_token_still_raises_401(self, mock_jwt_decode):
        """AC12: Expired HS256 token still raises 401 after ES256 support added."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": TEST_HS256_SECRET,
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.side_effect = pyjwt.ExpiredSignatureError()

        token = _encode_hs256_token(
            _valid_claims_with_exp(exp=int(time.time()) - 3600),
            TEST_HS256_SECRET,
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token expirado"

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_hs256_wrong_secret_raises_401(self, mock_jwt_decode):
        """AC12: HS256 token signed with wrong secret is rejected."""
        from auth import get_current_user

        env = {
            "SUPABASE_JWT_SECRET": TEST_HS256_SECRET,
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.side_effect = pyjwt.InvalidSignatureError()

        token = _encode_hs256_token(
            _valid_claims_with_exp(),
            "completely-wrong-secret-32-chars-long!!!!!",
        )
        creds = _make_credentials(token)

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "invalido" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("auth.jwt.decode")
    async def test_cache_works_for_both_hs256_and_es256(self, mock_jwt_decode, ec_key_pair):
        """AC12: Token cache correctly stores both HS256 and ES256 tokens separately."""
        from auth import get_current_user, _token_cache

        env = {
            "SUPABASE_JWT_SECRET": TEST_HS256_SECRET,
            "SUPABASE_URL": "",
        }
        mock_jwt_decode.return_value = dict(VALID_CLAIMS)

        hs256_token = _encode_hs256_token(
            _valid_claims_with_exp(sub="cache-hs256"),
            TEST_HS256_SECRET,
        )
        es256_token = _encode_es256_token(
            _valid_claims_with_exp(sub="cache-es256"),
            ec_key_pair["private_pem"],
        )

        creds_hs256 = _make_credentials(hs256_token)
        creds_es256 = _make_credentials(es256_token)

        with patch.dict(os.environ, env, clear=False):
            await get_current_user(credentials=creds_hs256)
            await get_current_user(credentials=creds_es256)

        # Both tokens should have separate cache entries
        assert len(_token_cache) == 2

        hs256_hash = hashlib.sha256(hs256_token.encode("utf-8")).hexdigest()
        es256_hash = hashlib.sha256(es256_token.encode("utf-8")).hexdigest()
        assert hs256_hash in _token_cache
        assert es256_hash in _token_cache
        assert hs256_hash != es256_hash


# ══════════════════════════════════════════════════════════════════════════════
# AC13: JWKS key caching behavior
# ══════════════════════════════════════════════════════════════════════════════


class TestJWKSCaching:
    """AC13: Tests for JWKS key resolution and PyJWKClient caching.

    These tests verify that when a JWKS URL is configured, the auth module:
    1. Creates a PyJWKClient with the correct URL and lifespan=300
    2. Calls get_signing_key_from_jwt with the raw token
    3. Passes the signing key to jwt.decode with ES256 algorithm
    4. Reuses the PyJWKClient instance across calls (lazy singleton)

    Implementation note: auth.py uses _get_jwks_client() which has a
    _jwks_init_attempted guard. We must reset both _jwks_client and
    _jwks_init_attempted before each test (handled by reset_jwks_state fixture).
    We also patch PyJWKClient at the auth module level since auth.py imports
    it as `from jwt import PyJWKClient`.
    """

    JWKS_URL = "https://test.supabase.co/auth/v1/.well-known/jwks.json"

    def _make_mock_signing_key(self, public_pem: bytes) -> MagicMock:
        """Create a mock signing key that mimics PyJWKClient's return."""
        mock_key = MagicMock()
        mock_key.key = public_pem
        return mock_key

    @pytest.mark.asyncio
    async def test_jwks_client_created_with_correct_url_and_lifespan(self, ec_key_pair):
        """AC13: PyJWKClient is created with correct JWKS URL, cache_jwk_set=True, lifespan=300."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_JWKS_URL": self.JWKS_URL,
            "SUPABASE_URL": "",
        }

        mock_signing_key = self._make_mock_signing_key(ec_key_pair["public_pem"])

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                mock_client_instance = MagicMock()
                mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
                mock_client_class.return_value = mock_client_instance

                key, algorithms = auth._get_jwt_key_and_algorithms("fake-token")

                mock_client_class.assert_called_once_with(
                    self.JWKS_URL,
                    cache_jwk_set=True,
                    lifespan=300,
                )

    @pytest.mark.asyncio
    async def test_jwks_get_signing_key_called_with_token(self, ec_key_pair):
        """AC13: get_signing_key_from_jwt is called with the raw JWT token."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_JWKS_URL": self.JWKS_URL,
            "SUPABASE_URL": "",
        }

        test_token = _encode_es256_token(
            _valid_claims_with_exp(),
            ec_key_pair["private_pem"],
        )
        mock_signing_key = self._make_mock_signing_key(ec_key_pair["public_pem"])

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                mock_client_instance = MagicMock()
                mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
                mock_client_class.return_value = mock_client_instance

                key, algorithms = auth._get_jwt_key_and_algorithms(test_token)

                mock_client_instance.get_signing_key_from_jwt.assert_called_once_with(test_token)

    @pytest.mark.asyncio
    async def test_jwks_signing_key_returned_with_es256(self, ec_key_pair):
        """AC13: The signing key from JWKS is returned with ["ES256"] algorithms."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_JWKS_URL": self.JWKS_URL,
            "SUPABASE_URL": "",
        }

        mock_signing_key = self._make_mock_signing_key(ec_key_pair["public_pem"])

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                mock_client_instance = MagicMock()
                mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
                mock_client_class.return_value = mock_client_instance

                key, algorithms = auth._get_jwt_key_and_algorithms("test-token")

                assert key == ec_key_pair["public_pem"]
                assert algorithms == ["ES256"]

    @pytest.mark.asyncio
    async def test_jwks_client_is_reused_across_calls(self, ec_key_pair):
        """AC13: PyJWKClient is lazy-initialized and reused (not re-created per call)."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_JWKS_URL": self.JWKS_URL,
            "SUPABASE_URL": "",
        }

        mock_signing_key = self._make_mock_signing_key(ec_key_pair["public_pem"])

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                mock_client_instance = MagicMock()
                mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
                mock_client_class.return_value = mock_client_instance

                # Call twice with different tokens
                auth._get_jwt_key_and_algorithms("token-1")
                auth._get_jwt_key_and_algorithms("token-2")

                # PyJWKClient constructor should be called only once (lazy init)
                assert mock_client_class.call_count == 1
                # But get_signing_key_from_jwt called once per token
                assert mock_client_instance.get_signing_key_from_jwt.call_count == 2

    @pytest.mark.asyncio
    async def test_jwks_auto_constructed_from_supabase_url(self, ec_key_pair):
        """AC13: When SUPABASE_JWKS_URL is not set, JWKS URL is auto-constructed from SUPABASE_URL."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "https://myproject.supabase.co",
            # No explicit SUPABASE_JWKS_URL
        }

        mock_signing_key = self._make_mock_signing_key(ec_key_pair["public_pem"])

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                mock_client_instance = MagicMock()
                mock_client_instance.get_signing_key_from_jwt.return_value = mock_signing_key
                mock_client_class.return_value = mock_client_instance

                key, algorithms = auth._get_jwt_key_and_algorithms("token")

                # Should auto-construct JWKS URL from SUPABASE_URL
                mock_client_class.assert_called_once_with(
                    "https://myproject.supabase.co/auth/v1/.well-known/jwks.json",
                    cache_jwk_set=True,
                    lifespan=300,
                )

    @pytest.mark.asyncio
    async def test_jwks_not_used_when_no_url_available(self, ec_key_pair):
        """AC13: When neither SUPABASE_JWKS_URL nor SUPABASE_URL is set, falls through to PEM."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",  # Empty prevents auto-construction
            # No SUPABASE_JWKS_URL
        }

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                key, algorithms = auth._get_jwt_key_and_algorithms("any-token")

                # PyJWKClient should not be instantiated
                mock_client_class.assert_not_called()
                # Falls through to PEM detection (strategy 2)
                assert algorithms == ["ES256"]
                assert "-----BEGIN" in str(key)

    @pytest.mark.asyncio
    async def test_jwks_fallback_to_pem_on_client_error(self, ec_key_pair):
        """AC13: If PyJWKClient.get_signing_key_from_jwt fails, falls back to PEM key."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_JWKS_URL": self.JWKS_URL,
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                mock_client_instance = MagicMock()
                mock_client_instance.get_signing_key_from_jwt.side_effect = \
                    pyjwt.exceptions.PyJWKClientError("JWKS fetch failed")
                mock_client_class.return_value = mock_client_instance

                key, algorithms = auth._get_jwt_key_and_algorithms("token-fail")

                # Should fall back to PEM key (strategy 2)
                assert algorithms == ["ES256"]
                assert "-----BEGIN" in str(key)

    @pytest.mark.asyncio
    async def test_jwks_init_only_attempted_once(self, ec_key_pair):
        """AC13: _get_jwks_client only attempts initialization once to avoid repeated failures."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_JWKS_URL": self.JWKS_URL,
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with patch.object(auth, "PyJWKClient") as mock_client_class:
                # First call: initialization fails
                mock_client_class.side_effect = Exception("Network error")

                result1 = auth._get_jwks_client()
                assert result1 is None  # Failed
                assert mock_client_class.call_count == 1

                # Second call: should not retry (init already attempted)
                result2 = auth._get_jwks_client()
                assert result2 is None
                assert mock_client_class.call_count == 1  # Still 1, not retried


# ══════════════════════════════════════════════════════════════════════════════
# AC14: Integration tests with real ES256 JWT encode/decode round-trip
# ══════════════════════════════════════════════════════════════════════════════


class TestES256Integration:
    """AC14: Integration tests using real ES256 JWT encode + decode.

    These tests create actual EC P-256 key pairs, sign real JWTs,
    and run the full validation path in auth.py with NO mocking of jwt.decode.
    Only environment variables are patched.
    """

    @pytest.mark.asyncio
    async def test_es256_real_round_trip_direct(self, ec_key_pair):
        """AC14: Real ES256 JWT encode -> get_current_user decode -> correct user returned.

        Calls get_current_user directly (no HTTP layer). No jwt.decode mock.
        """
        from auth import get_current_user

        claims = _valid_claims_with_exp(
            sub="real-es256-user",
            email="real-es256@example.com",
        )
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])
        creds = _make_credentials(token)

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",  # Empty to prevent JWKS
        }

        with patch.dict(os.environ, env, clear=False):
            result = await get_current_user(credentials=creds)

        assert result is not None
        assert result["id"] == "real-es256-user"
        assert result["email"] == "real-es256@example.com"
        assert result["role"] == "authenticated"

    def test_es256_real_round_trip_via_http(self, ec_key_pair, app_with_protected_route):
        """AC14: Real ES256 JWT round-trip via HTTP TestClient."""
        claims = _valid_claims_with_exp(
            sub="http-es256-user",
            email="http-es256@example.com",
        )
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            client = TestClient(app_with_protected_route)
            response = client.get(
                "/protected",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["user_id"] == "http-es256-user"
        assert body["email"] == "http-es256@example.com"
        assert body["role"] == "authenticated"

    @pytest.mark.asyncio
    async def test_es256_expired_token_raises_401(self, ec_key_pair):
        """AC14: Real expired ES256 token is rejected with 401."""
        from auth import get_current_user

        claims = _valid_claims_with_exp(
            sub="expired-es256-user",
            exp=int(time.time()) - 3600,  # Expired 1 hour ago
            iat=int(time.time()) - 7200,
        )
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])
        creds = _make_credentials(token)

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "expirado" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_es256_wrong_key_raises_401(self, ec_key_pair, second_ec_key_pair):
        """AC14: ES256 token signed with wrong key is rejected with 401."""
        from auth import get_current_user

        # Sign token with first key pair
        claims = _valid_claims_with_exp(sub="wrong-key-user")
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])
        creds = _make_credentials(token)

        # But configure auth with SECOND key pair's public key
        env = {
            "SUPABASE_JWT_SECRET": second_ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401
        assert "invalido" in exc_info.value.detail.lower()

    def test_es256_wrong_key_via_http(
        self, ec_key_pair, second_ec_key_pair, app_with_protected_route
    ):
        """AC14: ES256 token with wrong key returns 401 via HTTP."""
        claims = _valid_claims_with_exp(sub="http-wrong-key")
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])

        # Configure with wrong public key
        env = {
            "SUPABASE_JWT_SECRET": second_ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            client = TestClient(app_with_protected_route)
            response = client.get(
                "/protected",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    def test_es256_expired_via_http(self, ec_key_pair, app_with_protected_route):
        """AC14: Expired ES256 token returns 401 via HTTP."""
        claims = _valid_claims_with_exp(
            sub="http-expired-es256",
            exp=int(time.time()) - 3600,
            iat=int(time.time()) - 7200,
        )
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            client = TestClient(app_with_protected_route)
            response = client.get(
                "/protected",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_es256_token_cached_after_validation(self, ec_key_pair):
        """AC14: Validated ES256 token is stored in cache."""
        from auth import get_current_user, _token_cache

        claims = _valid_claims_with_exp(sub="cache-es256-user")
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])
        creds = _make_credentials(token)

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            await get_current_user(credentials=creds)

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert token_hash in _token_cache
        cached_user, cached_time = _token_cache[token_hash]
        assert cached_user["id"] == "cache-es256-user"

    @pytest.mark.asyncio
    async def test_es256_cached_token_served_on_second_call(self, ec_key_pair):
        """AC14: Second call for same ES256 token is served from cache (no re-decode)."""
        from auth import get_current_user

        claims = _valid_claims_with_exp(sub="cached-twice-user")
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])
        creds = _make_credentials(token)

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with patch("auth.jwt.decode", wraps=pyjwt.decode) as spy_decode:
                result1 = await get_current_user(credentials=creds)
                result2 = await get_current_user(credentials=creds)

                # jwt.decode called only once (second call served from cache)
                assert spy_decode.call_count == 1
                assert result1["id"] == result2["id"] == "cached-twice-user"

    @pytest.mark.asyncio
    async def test_es256_wrong_audience_raises_401(self, ec_key_pair):
        """AC14: ES256 token with wrong audience is rejected."""
        from auth import get_current_user

        claims = _valid_claims_with_exp(sub="wrong-aud", aud="wrong-audience")
        token = _encode_es256_token(claims, ec_key_pair["private_pem"])
        creds = _make_credentials(token)

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_es256_malformed_token_raises_401(self, ec_key_pair):
        """AC14: Completely malformed token string is rejected."""
        from auth import get_current_user

        creds = _make_credentials("not.a.valid.jwt.at.all")

        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

        assert exc_info.value.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# Additional: _is_pem_key helper + _get_jwt_key_and_algorithms direct tests
# ══════════════════════════════════════════════════════════════════════════════


class TestKeyDetection:
    """Direct tests for key type detection helpers in auth.py."""

    def test_is_pem_key_detects_public_key(self, ec_key_pair):
        """_is_pem_key returns True for PEM public key."""
        import auth
        assert auth._is_pem_key(ec_key_pair["public_pem_str"]) is True

    def test_is_pem_key_rejects_symmetric_secret(self):
        """_is_pem_key returns False for plain symmetric secret."""
        import auth
        assert auth._is_pem_key(TEST_HS256_SECRET) is False

    def test_is_pem_key_handles_whitespace(self, ec_key_pair):
        """_is_pem_key handles leading whitespace in PEM keys."""
        import auth
        padded_pem = "  \n" + ec_key_pair["public_pem_str"]
        assert auth._is_pem_key(padded_pem) is True

    def test_is_pem_key_empty_string(self):
        """_is_pem_key returns False for empty string."""
        import auth
        assert auth._is_pem_key("") is False

    def test_get_jwt_key_raises_500_when_no_secret(self):
        """_get_jwt_key_and_algorithms raises 500 when no secret configured."""
        import auth

        env = {
            "SUPABASE_JWT_SECRET": "",
            "SUPABASE_URL": "",
        }

        with patch.dict(os.environ, env, clear=False):
            with pytest.raises(HTTPException) as exc_info:
                auth._get_jwt_key_and_algorithms("any-token")

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Auth not configured"

    def test_get_jwt_key_priority_order(self, ec_key_pair):
        """Key detection priority: JWKS > PEM > HS256 symmetric."""
        import auth

        # With PEM key and no JWKS -> ES256
        env = {
            "SUPABASE_JWT_SECRET": ec_key_pair["public_pem_str"],
            "SUPABASE_URL": "",
        }
        with patch.dict(os.environ, env, clear=False):
            _, algorithms = auth._get_jwt_key_and_algorithms("token")
            assert algorithms == ["ES256"]

        # Reset JWKS state for next test
        auth.reset_jwks_client()

        # With symmetric secret and no JWKS -> HS256
        env2 = {
            "SUPABASE_JWT_SECRET": TEST_HS256_SECRET,
            "SUPABASE_URL": "",
        }
        with patch.dict(os.environ, env2, clear=False):
            _, algorithms = auth._get_jwt_key_and_algorithms("token")
            assert algorithms == ["HS256"]


# ══════════════════════════════════════════════════════════════════════════════
# Additional: Crypto key generation validation
# ══════════════════════════════════════════════════════════════════════════════


class TestCryptoKeyGeneration:
    """Sanity tests to verify our test infrastructure (key generation) works correctly.

    These tests do NOT test auth.py directly. They validate that the EC key
    pairs generated in fixtures produce valid ES256 JWTs that PyJWT can
    encode and decode independently.
    """

    def test_ec_key_pair_produces_valid_pem(self, ec_key_pair):
        """Fixture produces valid PEM-encoded keys."""
        assert ec_key_pair["public_pem_str"].startswith("-----BEGIN PUBLIC KEY-----")
        assert ec_key_pair["private_pem"].startswith(b"-----BEGIN PRIVATE KEY-----")

    def test_es256_jwt_encode_decode_round_trip(self, ec_key_pair):
        """ES256 JWT can be encoded with private key and decoded with public key."""
        claims = {
            "sub": "roundtrip-user",
            "email": "roundtrip@test.com",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(claims, ec_key_pair["private_pem"], algorithm="ES256")
        decoded = pyjwt.decode(
            token,
            ec_key_pair["public_pem"],
            algorithms=["ES256"],
            audience="authenticated",
        )
        assert decoded["sub"] == "roundtrip-user"
        assert decoded["email"] == "roundtrip@test.com"

    def test_es256_wrong_key_raises_invalid_signature(self, ec_key_pair, second_ec_key_pair):
        """ES256 JWT signed with key A cannot be decoded with key B."""
        claims = {
            "sub": "wrong-key-user",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(claims, ec_key_pair["private_pem"], algorithm="ES256")

        with pytest.raises(pyjwt.InvalidSignatureError):
            pyjwt.decode(
                token,
                second_ec_key_pair["public_pem"],
                algorithms=["ES256"],
                audience="authenticated",
            )

    def test_es256_expired_token_raises_expired_error(self, ec_key_pair):
        """Expired ES256 JWT raises ExpiredSignatureError."""
        claims = {
            "sub": "expired-user",
            "aud": "authenticated",
            "exp": int(time.time()) - 100,
        }
        token = pyjwt.encode(claims, ec_key_pair["private_pem"], algorithm="ES256")

        with pytest.raises(pyjwt.ExpiredSignatureError):
            pyjwt.decode(
                token,
                ec_key_pair["public_pem"],
                algorithms=["ES256"],
                audience="authenticated",
            )

    def test_two_key_pairs_are_independent(self, ec_key_pair, second_ec_key_pair):
        """Two generated key pairs have different public keys."""
        assert ec_key_pair["public_pem"] != second_ec_key_pair["public_pem"]
        assert ec_key_pair["private_pem"] != second_ec_key_pair["private_pem"]

    def test_pem_detection_logic(self, ec_key_pair):
        """Verify the PEM prefix detection that auth.py uses."""
        pem_str = ec_key_pair["public_pem_str"]
        symmetric_secret = "not-a-pem-key-just-a-plain-secret"

        assert pem_str.startswith("-----BEGIN")
        assert not symmetric_secret.startswith("-----BEGIN")
