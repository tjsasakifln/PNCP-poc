"""
OAuth 2.0 authentication routes for Google Sheets integration.

Endpoints:
- GET /api/auth/google - Initiate OAuth flow
- GET /api/auth/google/callback - Handle OAuth callback
- DELETE /api/auth/google - Revoke access

STORY-180: Google Sheets Export
STORY-210 AC13: Cryptographic nonce for OAuth CSRF protection
"""

import logging
import os
import secrets
import time
from typing import Optional, Dict, Tuple

from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from auth import require_auth
from oauth import (
    get_authorization_url,
    exchange_code_for_tokens,
    save_user_tokens,
    revoke_user_google_token
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["oauth"])

# Frontend URL for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# STORY-210 AC13: In-memory OAuth nonce store with TTL
# Key: nonce string, Value: (user_id, redirect_path, created_at)
_OAUTH_NONCE_TTL = 600  # 10 minutes
_oauth_nonce_store: Dict[str, Tuple[str, str, float]] = {}

# Allowed redirect paths (whitelist)
_ALLOWED_REDIRECT_PATHS = {"/buscar", "/configuracoes", "/dashboard", "/"}


def _store_oauth_nonce(user_id: str, redirect_path: str) -> str:
    """Generate and store a cryptographic nonce for OAuth CSRF protection."""
    # Prune expired nonces (keep store clean)
    now = time.time()
    expired = [k for k, v in _oauth_nonce_store.items() if now - v[2] > _OAUTH_NONCE_TTL]
    for k in expired:
        del _oauth_nonce_store[k]

    nonce = secrets.token_urlsafe(32)
    _oauth_nonce_store[nonce] = (user_id, redirect_path, now)
    return nonce


def _verify_oauth_nonce(nonce: str) -> Optional[Tuple[str, str]]:
    """Verify and consume a nonce. Returns (user_id, redirect_path) or None."""
    entry = _oauth_nonce_store.pop(nonce, None)
    if entry is None:
        return None

    user_id, redirect_path, created_at = entry
    if time.time() - created_at > _OAUTH_NONCE_TTL:
        return None  # Expired

    return user_id, redirect_path


# ============================================================================
# Request/Response Models
# ============================================================================

class RevokeResponse(BaseModel):
    """Response for revoke endpoint."""
    success: bool
    message: str


# ============================================================================
# OAuth Flow Endpoints
# ============================================================================

@router.get("/google")
async def google_oauth_initiate(
    redirect: str = Query(default="/buscar", description="Page to return to after auth"),
    user: dict = Depends(require_auth)
):
    """
    Initiate Google OAuth 2.0 flow.

    Redirects user to Google consent screen to authorize Google Sheets access.

    Query Parameters:
        redirect: Frontend path to return to after authorization

    Returns:
        302 Redirect to Google OAuth consent screen

    Security:
        - CSRF protection via state parameter
        - State encodes user_id + redirect path
        - Validates state on callback

    Example:
        GET /api/auth/google?redirect=/buscar
        → Redirects to https://accounts.google.com/o/oauth2/auth?...
    """
    try:
        # Build redirect URI
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        redirect_uri = f"{backend_url}/api/auth/google/callback"

        # STORY-210 AC13: Validate redirect path against whitelist
        if redirect not in _ALLOWED_REDIRECT_PATHS:
            logger.warning(f"OAuth redirect path not in whitelist: {redirect}")
            redirect = "/buscar"

        # STORY-210 AC13: Cryptographic nonce for CSRF protection
        # Replaces predictable base64(user_id:redirect) with random nonce
        state = _store_oauth_nonce(user["id"], redirect)

        # Generate authorization URL
        authorization_url = get_authorization_url(redirect_uri, state)

        logger.info(f"Initiating Google OAuth for user {user['id'][:8]}")

        return RedirectResponse(authorization_url)

    except Exception as e:
        logger.error(f"Failed to initiate OAuth: {type(e).__name__}")
        return RedirectResponse(
            f"{FRONTEND_URL}{redirect}?error=oauth_init_failed"
        )


@router.get("/google/callback")
async def google_oauth_callback(
    code: Optional[str] = Query(default=None, description="Authorization code from Google"),
    state: str = Query(..., description="CSRF state token"),
    error: Optional[str] = Query(default=None, description="OAuth error (if any)")
):
    """
    Handle OAuth callback from Google.

    This endpoint is called by Google after user authorizes access.

    Query Parameters:
        code: Authorization code (exchanged for tokens), absent on error
        state: CSRF state token (contains user_id + redirect path)
        error: OAuth error code (if authorization failed)

    Returns:
        302 Redirect to frontend with success/error status

    Flow:
        1. Decode state param to get user_id and redirect path
        2. Exchange code for tokens (access + refresh)
        3. Encrypt and save tokens to database
        4. Redirect to frontend with success flag

    Error Handling:
        - Invalid state → Redirect with error=invalid_state
        - Code exchange failed → Redirect with error=oauth_failed
        - Database error → Redirect with error=storage_failed
    """
    # Handle OAuth error (Google sends error without code when user denies)
    if error:
        logger.warning(f"OAuth callback error: {error}")
        return RedirectResponse(
            f"{FRONTEND_URL}/buscar?error=oauth_denied&detail={error}"
        )

    # code is required for token exchange (absent only on error)
    if not code:
        logger.warning("OAuth callback missing authorization code")
        return RedirectResponse(
            f"{FRONTEND_URL}/buscar?error=missing_code"
        )

    try:
        # STORY-210 AC13: Verify cryptographic nonce (replaces base64 decode)
        nonce_result = _verify_oauth_nonce(state)
        if nonce_result is None:
            logger.error("Invalid or expired OAuth state nonce")
            return RedirectResponse(
                f"{FRONTEND_URL}/buscar?error=invalid_state"
            )
        user_id, redirect_path = nonce_result

        # Build redirect URI (must match authorization request)
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        redirect_uri = f"{backend_url}/api/auth/google/callback"

        # Exchange code for tokens
        tokens = await exchange_code_for_tokens(code, redirect_uri)

        # Save encrypted tokens to database
        await save_user_tokens(
            user_id=user_id,
            provider="google",
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_at=tokens["expires_at"],
            scope=" ".join(tokens["scope"])
        )

        logger.info(f"Google OAuth completed successfully for user {user_id[:8]}")

        # Redirect to frontend with success flag
        return RedirectResponse(
            f"{FRONTEND_URL}{redirect_path}?google_oauth=success"
        )

    except HTTPException as e:
        # Re-raise FastAPI exceptions
        logger.error(f"OAuth callback failed: {e.detail}")
        return RedirectResponse(
            f"{FRONTEND_URL}/buscar?error=oauth_failed&detail={e.detail}"
        )

    except Exception as e:
        logger.error(f"Unexpected OAuth callback error: {type(e).__name__}")
        return RedirectResponse(
            f"{FRONTEND_URL}/buscar?error=oauth_failed"
        )


@router.delete("/google")
async def google_oauth_revoke(
    user: dict = Depends(require_auth)
) -> RevokeResponse:
    """
    Revoke Google OAuth access and delete tokens.

    Deletes user's OAuth tokens from database and revokes access with Google.

    Returns:
        {
            "success": true,
            "message": "Google Sheets access revoked successfully"
        }

    Security:
        - Requires authentication
        - Only deletes tokens for authenticated user
        - Revokes with Google API (best effort)

    Note:
        Revoking access does NOT delete existing spreadsheets.
        Spreadsheets remain in user's Google Drive.
    """
    try:
        success = await revoke_user_google_token(user["id"])

        if success:
            logger.info(f"Google OAuth revoked for user {user['id'][:8]}")
            return RevokeResponse(
                success=True,
                message="Google Sheets access revoked successfully"
            )
        else:
            logger.info(f"No Google OAuth tokens to revoke for user {user['id'][:8]}")
            return RevokeResponse(
                success=True,
                message="No Google Sheets access to revoke"
            )

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Failed to revoke OAuth: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke Google Sheets access. Try again."
        )
