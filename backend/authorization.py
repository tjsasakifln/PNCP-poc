"""Authorization helpers for BidIQ API.

Shared authorization logic used across multiple route modules.
Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import asyncio
import logging
import os

from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)


class ErrorCode:
    """Structured error codes for better frontend error handling"""
    DATE_RANGE_EXCEEDED = "DATE_RANGE_EXCEEDED"
    RATE_LIMIT = "RATE_LIMIT"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVALID_SECTOR = "INVALID_SECTOR"
    INVALID_UF = "INVALID_UF"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"


def get_admin_ids() -> set[str]:
    """Get admin user IDs from environment variable (fallback/override)."""
    raw = os.getenv("ADMIN_USER_IDS", "")
    return {uid.strip().lower() for uid in raw.split(",") if uid.strip()}


async def check_user_roles(user_id: str) -> tuple[bool, bool]:
    """
    Check user's admin and master status from Supabase.

    Returns:
        tuple: (is_admin, is_master)
        - is_admin: Can manage users via /admin/* endpoints
        - is_master: Has full feature access (Excel, unlimited quota)

    Hierarchy: admin > master > regular users
    Admins automatically get master privileges.
    """
    for attempt in range(2):
        try:
            from supabase_client import get_supabase
            sb = get_supabase()

            # Get profile - try with is_admin first, fallback to just plan_type
            try:
                profile = (
                    sb.table("profiles")
                    .select("is_admin, plan_type")
                    .eq("id", user_id)
                    .single()
                    .execute()
                )
            except Exception:
                # is_admin column might not exist yet - fallback
                profile = (
                    sb.table("profiles")
                    .select("plan_type")
                    .eq("id", user_id)
                    .single()
                    .execute()
                )

            if not profile.data:
                return (False, False)

            is_admin = profile.data.get("is_admin", False)
            plan_type = profile.data.get("plan_type", "")

            # Admin implies master access
            is_master = is_admin or plan_type == "master"

            if is_admin:
                logger.debug(f"User {mask_user_id(user_id)} is ADMIN (profiles.is_admin)")
            elif is_master:
                logger.debug(f"User {mask_user_id(user_id)} is MASTER (profiles.plan_type)")

            return (is_admin, is_master)

        except Exception as e:
            if attempt == 0:
                logger.debug(f"Retry user roles check for {mask_user_id(user_id)} after error: {type(e).__name__}")
                await asyncio.sleep(0.3)
                continue
            logger.warning(
                f"ROLE CHECK FAILED for user {mask_user_id(user_id)} after 2 attempts: {type(e).__name__}. "
                f"User will be treated as regular (non-admin/non-master)."
            )
            return (False, False)
    return (False, False)


async def is_admin(user_id: str) -> bool:
    """
    Check if user can access /admin/* endpoints.

    Sources (in order):
    1. ADMIN_USER_IDS env var (fallback/override)
    2. Supabase profiles.is_admin = true
    """
    # Fast path: check env var first (no DB call)
    admin_ids = get_admin_ids()
    if user_id.lower() in admin_ids:
        return True

    # Check Supabase
    is_admin_flag, _ = await check_user_roles(user_id)
    return is_admin_flag


async def has_master_access(user_id: str) -> bool:
    """
    Check if user has full feature access (master or admin).

    Sources:
    1. ADMIN_USER_IDS env var (admins get master access)
    2. Supabase profiles.is_admin = true (admins get master access)
    3. Supabase profiles.plan_type = 'master'
    """
    # Fast path: check env var first (no DB call)
    admin_ids = get_admin_ids()
    if user_id.lower() in admin_ids:
        return True

    # Check Supabase
    is_admin_flag, is_master = await check_user_roles(user_id)
    return is_admin_flag or is_master


def get_master_quota_info(is_admin: bool = False):
    """
    Get quota info for admin/master users - returns sala_guerra (highest tier).

    Admins/masters bypass all quota restrictions and have full access to all features.
    """
    from quota import QuotaInfo, PLAN_CAPABILITIES
    from datetime import datetime, timezone

    plan_name = "Sala de Guerra (Admin)" if is_admin else "Sala de Guerra (Master)"

    return QuotaInfo(
        allowed=True,
        plan_id="sala_guerra",
        plan_name=plan_name,
        capabilities=PLAN_CAPABILITIES["sala_guerra"],
        quota_used=0,
        quota_remaining=999999,  # Unlimited for admins/masters
        quota_reset_date=datetime.now(timezone.utc),
        trial_expires_at=None,
        error_message=None,
    )


# ---------------------------------------------------------------------------
# Backward-compatible aliases (STORY-226 AC8)
# These allow existing code that imports the underscore-prefixed names to
# continue working without modification.  New code should use the public names.
# ---------------------------------------------------------------------------
_get_admin_ids = get_admin_ids
_check_user_roles = check_user_roles
_is_admin = is_admin
_has_master_access = has_master_access
_get_master_quota_info = get_master_quota_info
