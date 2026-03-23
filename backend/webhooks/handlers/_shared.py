"""
Shared utilities for Stripe webhook handlers.

Extracted from webhooks/stripe.py during DEBT-307 decomposition.

NOTE ON TEST COMPATIBILITY:
Many existing tests patch `webhooks.stripe.redis_cache` and
`webhooks.stripe.invalidate_plan_status_cache` etc.
To maintain compatibility, this module imports those symbols from the same
source modules and re-exports them. Tests that patch at the handler module
level (`webhooks.handlers._shared.redis_cache`) will also work.
"""

import stripe
from cache import redis_cache
from log_sanitizer import get_sanitized_logger
from quota import invalidate_plan_status_cache, clear_plan_capabilities_cache

logger = get_sanitized_logger(__name__)


def resolve_user_id(sb, session_data: dict) -> str | None:
    """Resolve Supabase user_id from checkout session.

    Checks client_reference_id first (programmatic checkout).
    Falls back to customer_details.email lookup (Payment Links).

    MAYDAY-A2: Payment Links don't set client_reference_id,
    so we match by email in auth.users via profiles table.
    """
    user_id = session_data.get("client_reference_id")
    if user_id:
        return user_id

    # Fallback: look up user by email from checkout session
    customer_details = session_data.get("customer_details") or {}
    email = customer_details.get("email")
    if not email:
        # Also try customer_email (older Stripe API versions)
        email = session_data.get("customer_email")
    if not email:
        return None

    try:
        result = (
            sb.table("profiles")
            .select("id")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        if result.data:
            logger.info(f"Resolved user_id from email {email}: {result.data[0]['id']}")
            return result.data[0]["id"]

        logger.warning(f"No profile found for email {email} — user must sign up first")
        return None
    except Exception as e:
        logger.error(f"Failed to resolve user_id from email {email}: {e}")
        return None


async def invalidate_user_caches(user_id: str, context: str = "") -> None:
    """Invalidate Redis + in-memory plan caches for a user.

    Uses module-level redis_cache reference so test patches at this module work.
    Never raises.
    """
    cache_key = f"features:{user_id}"
    try:
        await redis_cache.delete(cache_key)
        logger.info(f"{context}: user_id={user_id}, cache invalidated")
    except Exception as e:
        logger.warning(f"Cache invalidation failed ({context}, non-fatal): {e}")
        logger.info(f"{context}: user_id={user_id}")

    # HARDEN-008: Invalidate in-memory plan caches to prevent stale quota
    invalidate_plan_status_cache(user_id)
    clear_plan_capabilities_cache()
