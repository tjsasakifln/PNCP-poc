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
"""

import logging
import time
import os
import hashlib
import jwt
from typing import Optional, Dict, Tuple

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from log_sanitizer import log_auth_event

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Token validation cache - reduces Supabase Auth API calls by ~95%
# Key: SHA256 hash of FULL token, Value: (user_data, timestamp)
# STORY-210 AC3: MUST hash full token. Hashing only a prefix (e.g. [:16])
# causes identity collision — all Supabase HS256 JWTs share the same prefix.
_token_cache: Dict[str, Tuple[dict, float]] = {}
CACHE_TTL = 60  # seconds - balances security (short-lived) vs performance


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Extract and verify user from Supabase JWT token.

    Uses local cache (60s TTL) to reduce Supabase Auth API calls by ~95% and
    eliminate intermittent validation failures from remote timeouts.

    Returns None if no token provided (allows anonymous access where needed).
    Raises HTTPException 401 if token is invalid.
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
        # CRITICAL FIX: Validate JWT locally instead of calling Supabase API
        # This is MUCH faster and eliminates AuthApiError issues
        # Source: https://github.com/orgs/supabase/discussions/20763
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            logger.error("SUPABASE_JWT_SECRET not configured!")
            raise HTTPException(status_code=500, detail="Auth not configured")

        # Decode and verify JWT signature locally
        # audience is the Supabase project URL without protocol
        supabase_url = os.getenv("SUPABASE_URL", "")
        audience = supabase_url.replace("https://", "").replace("http://", "")

        try:
            # STORY-210 AC7: Enable audience verification (removed verify_aud: False)
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",  # Supabase default audience
            )
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError as e:
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
