"""jobs.search_jobs — Search pipeline async jobs.

Re-exports search job functions from job_queue.
"""
from job_queue import (  # noqa: F401
    search_job,
    acquire_search_slot,
    release_search_slot,
    _persist_search_results_to_redis,
    _persist_search_results_to_supabase,
    _update_search_session,
    _get_active_search_count,
)
