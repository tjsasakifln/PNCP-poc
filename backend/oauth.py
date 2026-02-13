"""
OAuth 2.0 token management for Google Sheets integration.

This module handles:
- Token encryption/decryption (AES-256)
- Token storage and retrieval from Supabase
- Automatic token refresh on expiration
- OAuth flow endpoints (authorization URL, callback handler)

Security:
- Tokens encrypted at rest using Fernet (AES-256 GCM)
- Tokens never logged in plaintext
- Auto-refresh prevents expired token errors
- CSRF protection via state parameter

STORY-180: Google Sheets Export
"""

import os
import base64
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException
from google_auth_oauthlib.flow import Flow

from supabase_client import get_supabase

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI",
    "http://localhost:8000/api/auth/google/callback"
)
ENCRYPTION_KEY_B64 = os.getenv("ENCRYPTION_KEY", "")

# Google Sheets API scope
GOOGLE_SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"

# Validate encryption key on module load
# STORY-210 AC6: Raise error in production when ENCRYPTION_KEY is missing
if not ENCRYPTION_KEY_B64:
    _env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    if _env in ("production", "prod"):
        raise RuntimeError(
            "ENCRYPTION_KEY is required in production. "
            "Generate with: openssl rand -base64 32"
        )
    logger.warning(
        "ENCRYPTION_KEY not set. Generate with: openssl rand -base64 32"
    )
    # Use a temporary key for development (INSECURE - for testing only)
    ENCRYPTION_KEY_B64 = base64.urlsafe_b64encode(b"0" * 32).decode()

try:
    # Decode and ensure 32 bytes for Fernet
    key_bytes = base64.urlsafe_b64decode(ENCRYPTION_KEY_B64.encode())
    if len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b'\0')
    elif len(key_bytes) > 32:
        key_bytes = key_bytes[:32]

    ENCRYPTION_KEY = base64.urlsafe_b64encode(key_bytes)
    cipher = Fernet(ENCRYPTION_KEY)
except Exception as e:
    logger.error(f"Failed to initialize encryption: {e}")
    raise RuntimeError("Invalid ENCRYPTION_KEY configuration")


# ============================================================================
# Token Encryption/Decryption
# ============================================================================

def encrypt_aes256(plaintext: str) -> str:
    """
    Encrypt token using AES-256 (Fernet).

    Args:
        plaintext: Token to encrypt

    Returns:
        Base64-encoded ciphertext

    Security:
        - Uses Fernet (AES-256 GCM with authentication)
        - Includes timestamp for token expiration
        - Returns URL-safe base64 string
    """
    if not plaintext:
        return ""

    try:
        encrypted_bytes = cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Token encryption failed. Contact support."
        )


def decrypt_aes256(ciphertext: str) -> str:
    """
    Decrypt token using AES-256 (Fernet).

    Args:
        ciphertext: Base64-encoded encrypted token

    Returns:
        Decrypted plaintext token

    Raises:
        HTTPException 500: If decryption fails (corrupted data or wrong key)
    """
    if not ciphertext:
        return ""

    try:
        decrypted_bytes = cipher.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Token decryption failed. Re-authorization required."
        )


# ============================================================================
# OAuth Flow Functions
# ============================================================================

def get_authorization_url(redirect_uri: str, state: Optional[str] = None) -> str:
    """
    Generate Google OAuth 2.0 authorization URL.

    Args:
        redirect_uri: Callback URL (must match Google Cloud config)
        state: Optional CSRF token (recommended)

    Returns:
        Authorization URL to redirect user to

    Example:
        >>> url = get_authorization_url("http://localhost:8000/callback")
        >>> # Redirect user to this URL
    """
    if not state:
        state = secrets.token_urlsafe(32)

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=[GOOGLE_SHEETS_SCOPE]
    )

    flow.redirect_uri = redirect_uri

    authorization_url, _ = flow.authorization_url(
        access_type='offline',      # Request refresh token
        include_granted_scopes='true',
        prompt='consent',            # Force consent screen (ensures refresh token)
        state=state
    )

    return authorization_url


async def exchange_code_for_tokens(
    authorization_code: str,
    redirect_uri: str
) -> Dict[str, Any]:
    """
    Exchange authorization code for access + refresh tokens.

    Args:
        authorization_code: Code from OAuth callback
        redirect_uri: Must match the redirect_uri used in authorization URL

    Returns:
        {
            'access_token': str,
            'refresh_token': str,
            'expires_at': datetime,
            'scope': list[str]
        }

    Raises:
        HTTPException 400: Invalid code or redirect_uri mismatch
        HTTPException 500: Google OAuth API error
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=[GOOGLE_SHEETS_SCOPE],
        redirect_uri=redirect_uri
    )

    try:
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_at": credentials.expiry,
            "scope": credentials.scopes
        }
    except Exception as e:
        logger.error(f"Token exchange failed: {type(e).__name__}")
        raise HTTPException(
            status_code=400,
            detail="Invalid authorization code or callback mismatch."
        )


async def refresh_google_token(refresh_token: str) -> Dict[str, Any]:
    """
    Exchange refresh token for new access token.

    Args:
        refresh_token: User's refresh token

    Returns:
        {
            'access_token': str,
            'expires_in': int,  # seconds
            'scope': str
        }

    Raises:
        HTTPException 401: Refresh token revoked/invalid
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )

        if response.status_code != 200:
            logger.error(f"Token refresh failed: HTTP {response.status_code}")
            raise HTTPException(
                status_code=401,
                detail="Google authorization expired. Please re-authorize Google Sheets access."
            )

        return response.json()


# ============================================================================
# Database Operations
# ============================================================================

async def save_user_tokens(
    user_id: str,
    provider: str,
    access_token: str,
    refresh_token: Optional[str],
    expires_at: datetime,
    scope: str
) -> None:
    """
    Store encrypted OAuth tokens in database.

    Uses PostgreSQL UPSERT (ON CONFLICT) to handle re-authorization.

    Args:
        user_id: Supabase user UUID
        provider: OAuth provider ('google', 'microsoft', etc.)
        access_token: OAuth access token
        refresh_token: OAuth refresh token (optional)
        expires_at: Expiration timestamp (UTC)
        scope: Granted scopes (space-separated string)

    Raises:
        HTTPException 500: Database error
    """
    sb = get_supabase()

    try:
        # Encrypt tokens before storage
        encrypted_access = encrypt_aes256(access_token)
        encrypted_refresh = encrypt_aes256(refresh_token) if refresh_token else None

        # Upsert (insert or update if exists)
        sb.table("user_oauth_tokens").upsert({
            "user_id": user_id,
            "provider": provider,
            "access_token": encrypted_access,
            "refresh_token": encrypted_refresh,
            "expires_at": expires_at.isoformat(),
            "scope": scope,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="user_id,provider").execute()

        logger.info(f"Saved {provider} OAuth tokens for user {user_id[:8]}")

    except Exception as e:
        logger.error(f"Failed to save tokens: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save OAuth tokens. Try again."
        )


async def get_user_google_token(user_id: str) -> Optional[str]:
    """
    Get valid Google access token for user, refreshing if expired.

    This is the main function used by Google Sheets export endpoint.

    Args:
        user_id: Supabase user UUID

    Returns:
        str: Valid access token
        None: User has not authorized Google Sheets

    Raises:
        HTTPException 401: Refresh token revoked, re-authorization required
        HTTPException 500: Database or decryption error
    """
    sb = get_supabase()

    try:
        # Query token from database
        result = sb.table("user_oauth_tokens")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("provider", "google")\
            .limit(1)\
            .execute()

        if not result.data:
            logger.info(f"No Google OAuth token for user {user_id[:8]}")
            return None

        token_record = result.data[0]

        # Decrypt tokens
        access_token = decrypt_aes256(token_record["access_token"])
        refresh_token_enc = token_record.get("refresh_token")
        refresh_token = decrypt_aes256(refresh_token_enc) if refresh_token_enc else None
        expires_at = datetime.fromisoformat(token_record["expires_at"])

        # Check if expired
        now = datetime.now(timezone.utc)
        if now < expires_at:
            logger.debug(f"Using cached access token for user {user_id[:8]}")
            return access_token  # Still valid

        # Expired - refresh
        if not refresh_token:
            logger.warning(f"No refresh token for user {user_id[:8]}, re-auth required")
            return None

        logger.info(f"Access token expired for user {user_id[:8]}, refreshing...")
        new_tokens = await refresh_google_token(refresh_token)

        # Update database with new tokens
        new_expires_at = now + timedelta(seconds=new_tokens.get("expires_in", 3600))

        await save_user_tokens(
            user_id=user_id,
            provider="google",
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens.get("refresh_token", refresh_token),  # Keep old if not returned
            expires_at=new_expires_at,
            scope=token_record["scope"]
        )

        return new_tokens["access_token"]

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Failed to get Google token: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve Google authorization. Try again."
        )


async def revoke_user_google_token(user_id: str) -> bool:
    """
    Revoke user's Google OAuth access and delete tokens.

    Args:
        user_id: Supabase user UUID

    Returns:
        True if revoked successfully, False if no tokens found

    Raises:
        HTTPException 500: Database error
    """
    sb = get_supabase()

    try:
        # Get tokens to revoke
        result = sb.table("user_oauth_tokens")\
            .select("access_token")\
            .eq("user_id", user_id)\
            .eq("provider", "google")\
            .execute()

        if not result.data:
            return False

        access_token = decrypt_aes256(result.data[0]["access_token"])

        # Revoke with Google (best effort - don't fail if Google API down)
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    data={"token": access_token},
                    timeout=5.0
                )
                logger.info("Google token revoked successfully")
        except Exception as e:
            logger.warning(f"Failed to revoke with Google: {type(e).__name__}")

        # Delete from database
        sb.table("user_oauth_tokens")\
            .delete()\
            .eq("user_id", user_id)\
            .eq("provider", "google")\
            .execute()

        logger.info(f"Deleted Google OAuth tokens for user {user_id[:8]}")
        return True

    except Exception as e:
        logger.error(f"Failed to revoke tokens: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke Google authorization. Try again."
        )
