"""
OAuth 2.0 authentication routes for Google Sheets integration.

Endpoints:
- GET /api/auth/google - Initiate OAuth flow
- GET /api/auth/google/callback - Handle OAuth callback
- DELETE /api/auth/google - Revoke access

STORY-180: Google Sheets Export
"""

import logging
import base64
from typing import Optional

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
import os
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


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

        # CSRF protection: encode user_id + redirect path in state param
        state = base64.urlsafe_b64encode(
            f"{user['id']}:{redirect}".encode()
        ).decode()

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
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="CSRF state token"),
    error: Optional[str] = Query(default=None, description="OAuth error (if any)")
):
    """
    Handle OAuth callback from Google.

    This endpoint is called by Google after user authorizes access.

    Query Parameters:
        code: Authorization code (exchanged for tokens)
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
    # Handle OAuth error
    if error:
        logger.warning(f"OAuth callback error: {error}")
        return RedirectResponse(
            f"{FRONTEND_URL}/buscar?error=oauth_denied&detail={error}"
        )

    try:
        # Decode state to get user_id and redirect path
        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            user_id, redirect_path = decoded.split(":", 1)
        except Exception:
            logger.error("Invalid OAuth state parameter")
            return RedirectResponse(
                f"{FRONTEND_URL}/buscar?error=invalid_state"
            )

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
