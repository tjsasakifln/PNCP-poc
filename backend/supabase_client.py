"""Supabase client singleton for backend operations."""

import asyncio
import os
import logging
import time

logger = logging.getLogger(__name__)

# Lazy import to avoid breaking existing tests that don't have supabase installed
_supabase_client = None


def _get_config():
    """Get Supabase configuration from environment."""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
            "Get these from your Supabase project settings."
        )
    return url, service_key


def get_supabase():
    """Get or create Supabase admin client (uses service role key).

    Returns:
        supabase.Client: Authenticated Supabase client with admin privileges.

    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set.
    """
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url, key = _get_config()
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized")
    return _supabase_client


def get_supabase_url() -> str:
    """Get Supabase project URL."""
    return os.getenv("SUPABASE_URL", "")


def get_supabase_anon_key() -> str:
    """Get Supabase anon key (for frontend JWT verification)."""
    return os.getenv("SUPABASE_ANON_KEY", "")


async def sb_execute(query):
    """Non-blocking Supabase query execution (STORY-290).

    Offloads synchronous postgrest-py .execute() to the default
    thread pool executor, preventing event loop blocking.

    Each call that previously blocked the event loop for ~5-50ms
    now runs in a background thread while the event loop stays free.

    Usage:
        # Before (blocks event loop):
        result = db.table("profiles").select("*").eq("id", uid).execute()

        # After (non-blocking):
        result = await sb_execute(db.table("profiles").select("*").eq("id", uid))
    """
    from metrics import SUPABASE_EXECUTE_DURATION
    start = time.monotonic()
    result = await asyncio.to_thread(query.execute)
    SUPABASE_EXECUTE_DURATION.observe(time.monotonic() - start)
    return result
