"""Authentication middleware for FastAPI using Supabase JWT."""

import os
import logging
from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
        logger.warning(f"JWT verification failed: {e}")
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
