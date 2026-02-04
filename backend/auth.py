"""Authentication middleware for FastAPI using Supabase JWT.

Security hardened in Issue #168:
- JWT errors sanitized (no token content in logs)
- Auth events logged with proper masking
"""

import os
import logging
from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from log_sanitizer import sanitize_string, log_auth_event

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Extract and verify user from Supabase JWT token.

    Returns None if no token provided (allows anonymous access where needed).
    Raises HTTPException 401 if token is invalid.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        user_response = sb.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token invalido")
        return {
            "id": str(user_response.user.id),
            "email": user_response.user.email,
            "role": user_response.user.role,
        }
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
