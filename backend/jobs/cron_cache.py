"""jobs.cron_cache — Cache cleanup cron task (shim).

Cache warming/refresh proactive jobs deprecated 2026-04-18
(STORY-CIG-BE-cache-warming-deprecate). Only cleanup remains.
"""
from cron.cache import start_cache_cleanup_task  # noqa: F401
