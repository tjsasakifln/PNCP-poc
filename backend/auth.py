"""Authentication middleware for FastAPI using Supabase JWT.

Security hardened in Issue #168:
- JWT errors sanitized (no token content in logs)
- Auth events logged with proper masking

Performance optimization:
- Token validation cache (60s TTL) to reduce Supabase Auth API calls
- Eliminates intermittent auth failures from remote validation timeouts

CRITICAL FIX (2026-02-11): Use local JWT validation instead of Supabase API
- Fixes: token_verification success=False AuthApiError
- Source: https://github.com/orgs/supabase/discussions/20763
- Much faster (no API call) and more reliable

STORY-203 SYS-M02: Use hashlib.sha256 for deterministic cache keys
- Python's hash() is not deterministic across process restarts
- hashlib.sha256() provides collision-resistant, deterministic hashing

STORY-227 Track 1: ES256+JWKS support
- Supabase rotated JWT signing from HS256 to ES256 (Feb 2026)
- Supports JWKS endpoint for dynamic public key fetching (5-min cache)
- Supports PEM public key via SUPABASE_JWT_SECRET env var
- Backward compatible: accepts both HS256 and ES256 during transition
- Key detection order: JWKS endpoint > PEM key > HS256 symmetric secret
"""

import time
import os
import hashlib
import jwt
from jwt import PyJWKClient
from typing import Any, Optional, Dict, Tuple

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from log_sanitizer import log_auth_event, get_sanitized_logger

logger = get_sanitized_logger(__name__)

security = HTTPBearer(auto_error=False)

# Token validation cache - reduces Supabase Auth API calls by ~95%
# Key: SHA256 hash of FULL token, Value: (user_data, timestamp)
# STORY-210 AC3: MUST hash full token. Hashing only a prefix (e.g. [:16])
# causes identity collision — all Supabase HS256 JWTs share the same prefix.
_token_cache: Dict[str, Tuple[dict, float]] = {}
CACHE_TTL = 60  # seconds - balances security (short-lived) vs performance

# ---------------------------------------------------------------------------
# JWKS client — lazily initialized on first use to avoid startup failures
# when SUPABASE_URL is not yet configured or network is unavailable.
# ---------------------------------------------------------------------------
_jwks_client: Optional[PyJWKClient] = None
_jwks_init_attempted: bool = False


def _get_jwks_client() -> Optional[PyJWKClient]:
    """Return the cached PyJWKClient instance, creating it on first call.

    The client is only created if a JWKS URL can be determined from either:
      1. SUPABASE_JWKS_URL env var (explicit override), or
      2. SUPABASE_URL env var (auto-constructed).

    Returns None if neither is available or if initialization fails.
    The 5-minute cache is handled internally by PyJWKClient (lifespan=300).
    """
    global _jwks_client, _jwks_init_attempted

    if _jwks_client is not None:
        return _jwks_client

    # Only attempt init once to avoid repeated failures on every request
    if _jwks_init_attempted:
        return None
    _jwks_init_attempted = True

    jwks_url = os.getenv("SUPABASE_JWKS_URL")
    if not jwks_url:
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        if supabase_url:
            jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"

    if not jwks_url:
        logger.debug("No JWKS URL available — JWKS client not initialized")
        return None

    try:
        _jwks_client = PyJWKClient(
            jwks_url,
            cache_jwk_set=True,
            lifespan=300,  # AC3: 5-minute JWKS cache TTL
        )
        logger.info(f"JWKS client initialized: {jwks_url}")
        return _jwks_client
    except Exception as e:
        logger.warning(f"Failed to initialize JWKS client: {type(e).__name__}")
        return None


def _is_pem_key(secret: str) -> bool:
    """Check whether SUPABASE_JWT_SECRET contains a PEM-encoded public key."""
    return secret.strip().startswith("-----BEGIN")


def _get_jwt_key_and_algorithms(token: str) -> Tuple[Any, list[str]]:
    """Determine the correct key and algorithm(s) for JWT verification.

    Strategy (AC4 — backward compatible during HS256→ES256 transition):
      1. JWKS endpoint (preferred): fetch signing key by token's ``kid`` header.
         Returns the EC public key with ``["ES256"]``.
      2. PEM public key: if SUPABASE_JWT_SECRET starts with ``-----BEGIN``,
         treat it as an EC/RSA PEM key. Returns the PEM string with
         ``["ES256"]`` (AC5).
      3. HS256 symmetric secret (legacy): plain string used directly with
         ``["HS256"]``.

    Returns:
        (key, algorithms): tuple of the verification key and list of
        algorithm strings to pass to ``jwt.decode``.

    Raises:
        HTTPException 500: if no JWT secret is configured at all.
    """
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")

    # --- Strategy 1: JWKS endpoint (dynamic key rotation support) ----------
    jwks = _get_jwks_client()
    if jwks is not None:
        try:
            signing_key = jwks.get_signing_key_from_jwt(token)
            logger.debug("Using JWKS-derived signing key (ES256)")
            return signing_key.key, ["ES256"]
        except jwt.exceptions.PyJWKClientError as e:
            # JWKS fetch/match failed — fall through to other strategies
            logger.debug(f"JWKS key lookup failed ({type(e).__name__}), trying fallbacks")
        except Exception as e:
            logger.debug(f"JWKS unexpected error ({type(e).__name__}), trying fallbacks")

    # --- Strategy 2: PEM public key in env var (AC5) -----------------------
    if jwt_secret and _is_pem_key(jwt_secret):
        logger.debug("Using PEM public key from SUPABASE_JWT_SECRET (ES256)")
        return jwt_secret, ["ES256"]

    # --- Strategy 3: HS256 symmetric secret (legacy) -----------------------
    if jwt_secret:
        logger.debug("Using symmetric secret from SUPABASE_JWT_SECRET (HS256)")
        return jwt_secret, ["HS256"]

    # No key available at all
    logger.error("SUPABASE_JWT_SECRET not configured and no JWKS URL available!")
    raise HTTPException(status_code=500, detail="Auth not configured")


def reset_jwks_client() -> None:
    """Reset the JWKS client so it will be re-initialized on next use.

    Useful for testing or when rotating JWKS endpoints at runtime.
    """
    global _jwks_client, _jwks_init_attempted
    _jwks_client = None
    _jwks_init_attempted = False
    logger.info("JWKS client reset — will re-initialize on next request")


def _decode_with_fallback(token: str, primary_key: Any, primary_algorithms: list[str]) -> dict:
    """Attempt JWT decode with the alternate algorithm for backward compatibility.

    During the HS256→ES256 transition (AC4), tokens may be signed with either
    algorithm. If the primary decode (based on key detection) fails, this
    function tries the other algorithm using the symmetric secret.

    This handles the case where:
      - Server is configured for ES256 (JWKS/PEM) but receives an old HS256 token
      - Server is configured for HS256 but receives a new ES256 token (limited —
        requires JWKS or PEM key to be available for ES256 verification)

    Raises the original exception if the fallback also fails.
    """
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")

    if "HS256" in primary_algorithms and jwt_secret and not _is_pem_key(jwt_secret):
        # Primary was HS256 — try ES256 via JWKS if available
        jwks = _get_jwks_client()
        if jwks is not None:
            try:
                signing_key = jwks.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["ES256"],
                    audience="authenticated",
                )
                logger.info("JWT fallback: decoded with ES256 (JWKS) after HS256 failed")
                return payload
            except Exception:
                pass
        # No JWKS available or JWKS also failed — cannot try ES256 without a key
        raise jwt.InvalidTokenError("Fallback ES256 decode not possible without JWKS")

    elif "ES256" in primary_algorithms and jwt_secret and not _is_pem_key(jwt_secret):
        # Primary was ES256 — try HS256 with the symmetric secret
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            logger.info("JWT fallback: decoded with HS256 after ES256 failed")
            return payload
        except Exception:
            raise jwt.InvalidTokenError("Fallback HS256 decode also failed")

    elif "ES256" in primary_algorithms and jwt_secret and _is_pem_key(jwt_secret):
        # Primary was ES256 with PEM key — no HS256 fallback possible (no symmetric secret)
        raise jwt.InvalidTokenError("ES256 PEM decode failed, no HS256 secret available")

    # No meaningful fallback available
    raise jwt.InvalidTokenError("No fallback algorithm available")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Extract and verify user from Supabase JWT token.

    Supports ES256 (via JWKS or PEM key) and HS256 (symmetric secret) with
    automatic fallback between algorithms during the transition period (AC4).
    Key detection order: JWKS endpoint > PEM key > HS256 symmetric secret.

    Uses local cache (60s TTL) to reduce validation overhead by ~95% and
    eliminate intermittent validation failures from remote timeouts.

    Returns None if no token provided (allows anonymous access where needed).
    Raises HTTPException 401 if token is invalid.
    Raises HTTPException 500 if auth is not configured (no key available).
    """
    if credentials is None:
        return None

    token = credentials.credentials
    # STORY-210 AC3: Hash FULL token to prevent identity collision (CVSS 9.1)
    # Previously hashed only first 16 chars, which are identical for all Supabase JWTs.
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

    # FAST PATH: Check cache first (avoids remote Supabase call)
    if token_hash in _token_cache:
        user_data, cached_at = _token_cache[token_hash]
        age = time.time() - cached_at
        if age < CACHE_TTL:
            logger.debug(f"Auth cache HIT (age={age:.1f}s, user={user_data['id'][:8]})")
            return user_data
        else:
            # Expired - remove from cache
            del _token_cache[token_hash]
            logger.debug(f"Auth cache EXPIRED (age={age:.1f}s)")

    # SLOW PATH: Cache miss or expired - validate locally with JWT
    logger.debug("Auth cache MISS - validating JWT locally")
    try:
        # Determine key and algorithm(s) based on configuration
        # (raises HTTPException 500 if completely unconfigured)
        key, algorithms = _get_jwt_key_and_algorithms(token)

        try:
            # STORY-210 AC7: Enable audience verification (removed verify_aud: False)
            payload = jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience="authenticated",  # Supabase default audience
            )
        except jwt.InvalidAlgorithmError:
            # AC4: Backward compatibility — if primary algorithm fails,
            # retry with the alternate algorithm during HS256→ES256 transition.
            # e.g. token signed with HS256 but we tried ES256, or vice versa.
            payload = _decode_with_fallback(token, key, algorithms)
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError as e:
            # Primary decode failed — attempt fallback before giving up (AC4)
            try:
                payload = _decode_with_fallback(token, key, algorithms)
            except Exception:
                logger.warning(f"Invalid JWT token: {type(e).__name__}")
                raise HTTPException(status_code=401, detail="Token invalido")

        # Extract user data from JWT claims
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "authenticated")

        if not user_id:
            raise HTTPException(status_code=401, detail="Token sem user ID")

        # Build user data from JWT claims (no API call needed!)
        user_data = {
            "id": user_id,
            "email": email or "unknown",
            "role": role,
        }

        # Cache validated token
        _token_cache[token_hash] = (user_data, time.time())
        logger.debug(f"Auth cache STORED for user {user_data['id'][:8]}")
        logger.info(f"JWT validation SUCCESS for user {user_data['id'][:8]} ({email})")

        return user_data

    except HTTPException:
        raise
    except Exception as e:
        # SECURITY: Sanitize error message to avoid token leakage (Issue #168)
        # Only log generic error type, never the actual exception details
        # which may contain token fragments
        log_auth_event(
            logger,
            event="token_verification",
            success=False,
            reason=type(e).__name__,  # Only log exception type, not message
        )
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")


async def require_auth(
    user: Optional[dict] = Depends(get_current_user),
) -> dict:
    """Require authenticated user. Returns user dict or raises 401."""
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Autenticacao necessaria. Faca login para continuar.",
        )
    return user


def clear_token_cache() -> int:
    """Clear all cached tokens. Useful for testing or security incidents.

    Returns:
        Number of cache entries cleared
    """
    global _token_cache
    count = len(_token_cache)
    _token_cache.clear()
    logger.info(f"Auth cache cleared - removed {count} entries")
    return count
