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

import json
import time
import os
import hashlib
import jwt
from collections import OrderedDict
from jwt import PyJWKClient
from typing import Any, Optional, Dict, Tuple

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from log_sanitizer import log_auth_event, get_sanitized_logger

logger = get_sanitized_logger(__name__)

security = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# DEBT-014 SYS-010 + SYS-018: Bounded LRU auth cache with Redis L2
# ---------------------------------------------------------------------------
# L1 (in-memory): OrderedDict with LRU eviction, 60s TTL, max 1000 entries
# L2 (Redis): shared between Gunicorn workers, 5min TTL
# Fallback: if Redis unavailable, L1 still works (per-worker only)
#
# Key: SHA256 hash of FULL token (STORY-210 AC3)
# Value: (user_data, timestamp)
# ---------------------------------------------------------------------------
_token_cache: OrderedDict[str, Tuple[dict, float]] = OrderedDict()
CACHE_TTL = 60  # L1 in-memory TTL (seconds)
REDIS_CACHE_TTL = 300  # L2 Redis TTL (5 minutes, shared between workers)
MAX_CACHE_ENTRIES = 1000  # Max L1 entries (LRU eviction when exceeded)
_REDIS_KEY_PREFIX = "smartlic:auth:"


def _cache_store_memory(token_hash: str, user_data: dict) -> None:
    """Store in L1 with LRU eviction."""
    _token_cache[token_hash] = (user_data, time.time())
    _token_cache.move_to_end(token_hash)
    # Evict oldest entries if over limit
    while len(_token_cache) > MAX_CACHE_ENTRIES:
        _token_cache.popitem(last=False)
        try:
            from metrics import AUTH_CACHE_EVICTIONS
            AUTH_CACHE_EVICTIONS.inc()
        except Exception:
            pass
    try:
        from metrics import AUTH_CACHE_SIZE
        AUTH_CACHE_SIZE.set(len(_token_cache))
    except Exception:
        pass


async def _redis_cache_get(token_hash: str) -> Optional[dict]:
    """Try to get user data from Redis L2 cache."""
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            data = await redis.get(f"{_REDIS_KEY_PREFIX}{token_hash}")
            if data:
                return json.loads(data)
    except Exception:
        pass
    return None


async def _redis_cache_set(token_hash: str, user_data: dict) -> None:
    """Store user data in Redis L2 cache with TTL (fire-and-forget)."""
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            await redis.setex(
                f"{_REDIS_KEY_PREFIX}{token_hash}",
                REDIS_CACHE_TTL,
                json.dumps(user_data),
            )
    except Exception:
        pass

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
        HTTPException 401: if no JWT secret is configured at all.
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
    raise HTTPException(
        status_code=401,
        detail="Autenticação indisponível. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )


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
    Raises HTTPException 401 if auth is not configured (no key available).
    """
    if credentials is None:
        return None

    token = credentials.credentials
    # STORY-210 AC3: Hash FULL token to prevent identity collision (CVSS 9.1)
    # Previously hashed only first 16 chars, which are identical for all Supabase JWTs.
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

    # FAST PATH 1: Check L1 in-memory cache (no I/O)
    if token_hash in _token_cache:
        user_data, cached_at = _token_cache[token_hash]
        age = time.time() - cached_at
        if age < CACHE_TTL:
            _token_cache.move_to_end(token_hash)  # LRU refresh
            logger.debug(f"Auth cache L1 HIT (age={age:.1f}s, user={user_data['id'][:8]})")
            try:
                from metrics import AUTH_CACHE_HITS
                AUTH_CACHE_HITS.labels(level="memory").inc()
            except Exception:
                pass
            return user_data
        else:
            # Expired - remove from cache
            del _token_cache[token_hash]
            logger.debug(f"Auth cache L1 EXPIRED (age={age:.1f}s)")

    # FAST PATH 2: Check L2 Redis cache (shared between workers)
    redis_data = await _redis_cache_get(token_hash)
    if redis_data:
        logger.debug(f"Auth cache L2 HIT (redis, user={redis_data.get('id', '?')[:8]})")
        _cache_store_memory(token_hash, redis_data)  # Promote to L1
        try:
            from metrics import AUTH_CACHE_HITS
            AUTH_CACHE_HITS.labels(level="redis").inc()
        except Exception:
            pass
        return redis_data

    # SLOW PATH: Cache miss — validate locally with JWT
    logger.debug("Auth cache MISS - validating JWT locally")
    try:
        from metrics import AUTH_CACHE_MISSES
        AUTH_CACHE_MISSES.inc()
    except Exception:
        pass
    try:
        # Determine key and algorithm(s) based on configuration
        # (raises HTTPException 401 if completely unconfigured)
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

        # STORY-317: Extract AAL (Authenticator Assurance Level) from JWT
        # aal1 = password only, aal2 = password + TOTP verified
        aal = payload.get("aal", "aal1")

        # Build user data from JWT claims (no API call needed!)
        user_data = {
            "id": user_id,
            "email": email or "unknown",
            "role": role,
            "aal": aal,
        }

        # Cache validated token in L1 + L2
        _cache_store_memory(token_hash, user_data)
        await _redis_cache_set(token_hash, user_data)
        logger.debug(f"Auth cache STORED (L1+L2) for user {user_data['id'][:8]}")
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


async def require_mfa(
    user: dict = Depends(require_auth),
) -> dict:
    """STORY-317 AC2/AC3: Require MFA (aal2) for sensitive endpoints.

    For admin/master roles: always requires aal2.
    For regular users with MFA enrolled: requires aal2.
    For regular users without MFA: allows aal1 (pass-through).

    Used on: /admin/*, /checkout, /billing-portal, /change-password
    """
    aal = user.get("aal", "aal1")
    user_id = user["id"]

    if aal == "aal2":
        return user

    # Check if user is admin/master (MFA mandatory for these roles)
    from authorization import check_user_roles
    is_admin, is_master = await check_user_roles(user_id)

    if is_admin or is_master:
        raise HTTPException(
            status_code=403,
            detail="MFA obrigatório para sua conta. Configure a autenticação em dois fatores.",
            headers={"X-MFA-Required": "true"},
        )

    # For regular users: check if they have MFA enrolled but haven't verified
    # If they have factors, they need to verify; if not, allow through
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        result = (
            sb.table("mfa_factors")
            .select("id, status")
            .eq("user_id", user_id)
            .eq("status", "verified")
            .execute()
        )
        if result.data and len(result.data) > 0:
            # User has MFA enrolled but session is aal1 — need to verify
            raise HTTPException(
                status_code=403,
                detail="Verificação MFA necessária. Use seu app autenticador.",
                headers={"X-MFA-Required": "true"},
            )
    except HTTPException:
        raise
    except Exception as e:
        # If we can't check factors, allow through (fail-open for non-admin)
        logger.warning(f"MFA factor check failed for user {user_id[:8]}: {type(e).__name__}")

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
