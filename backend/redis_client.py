"""Redis client compatibility shim (DEPRECATED).

STORY-217: This module is deprecated. Use redis_pool instead:
    from redis_pool import get_redis_pool, is_redis_available

All functions redirect to the unified redis_pool module.
This shim exists only for backward compatibility during migration.
"""

import warnings
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_redis() -> Optional["redis.asyncio.Redis"]:
    """Get Redis client instance (DEPRECATED).

    Use ``from redis_pool import get_redis_pool`` instead.
    Returns the cached pool instance or None (does NOT initialize the pool).
    """
    warnings.warn(
        "redis_client.get_redis() is deprecated. "
        "Use 'from redis_pool import get_redis_pool' (async) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Return the already-initialized pool (set during startup_redis)
    import redis_pool
    return redis_pool._redis_pool


async def is_redis_available() -> bool:
    """Check if Redis is available (DEPRECATED).

    Use ``from redis_pool import is_redis_available`` instead.
    """
    from redis_pool import is_redis_available as _is_available
    return await _is_available()
