"""Redis connection manager for distributed progress tracking.

Provides a singleton Redis client with graceful fallback to None if Redis is unavailable.
Used by progress.py for pub/sub-based SSE state sharing across backend instances.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded Redis client singleton
_redis_client: Optional[any] = None
_redis_available = False


def get_redis() -> Optional[any]:
    """Get Redis client instance or None if unavailable.

    Returns:
        redis.asyncio.Redis instance if REDIS_URL is set and connection succeeds.
        None if Redis is unavailable (graceful degradation to in-memory mode).
    """
    global _redis_client, _redis_available

    # Already attempted connection
    if _redis_client is not None:
        return _redis_client

    # No REDIS_URL = in-memory mode
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        if not _redis_available:  # Log once
            logger.warning(
                "REDIS_URL not set. Progress tracking will use in-memory mode "
                "(not suitable for horizontal scaling)."
            )
            _redis_available = True  # Prevent repeated logs
        return None

    # Try to connect to Redis
    try:
        import redis.asyncio as aioredis

        _redis_client = aioredis.from_url(
            redis_url,
            decode_responses=True,  # Automatically decode bytes to strings
            socket_connect_timeout=3,
            socket_timeout=3,
        )

        # Test connection (sync check during startup is acceptable)
        import asyncio
        try:
            asyncio.run(_redis_client.ping())
            logger.info(f"Redis connected successfully: {redis_url.split('@')[-1]}")  # Hide credentials
            _redis_available = True
        except Exception as ping_error:
            logger.warning(
                f"Redis connection test failed: {ping_error}. "
                "Falling back to in-memory progress tracking."
            )
            _redis_client = None
            _redis_available = False

        return _redis_client

    except ImportError:
        logger.warning(
            "redis package not installed. Install with 'pip install redis[hiredis]' "
            "for distributed progress tracking support. Using in-memory mode."
        )
        _redis_available = False
        return None

    except Exception as e:
        logger.warning(
            f"Failed to initialize Redis client: {e}. "
            "Progress tracking will use in-memory mode."
        )
        _redis_available = False
        return None


async def is_redis_available() -> bool:
    """Check if Redis is available for pub/sub.

    Returns:
        True if Redis client is connected, False otherwise.
    """
    redis = get_redis()
    if redis is None:
        return False

    try:
        await redis.ping()
        return True
    except Exception:
        return False
