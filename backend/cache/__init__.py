"""cache package — SYS-004 backend package grouping.

Re-exports from cache_module (renamed from cache.py) so that
``from cache import redis_cache`` continues to work.

Also provides new import paths:
  - cache.redis_pool (from redis_pool)
"""

from cache_module import *  # noqa: F401,F403
