"""STORY-3.1 (EPIC-TD-2026Q2): Search state, background results, persistence.

Thin re-export of routes.search_state for the new routes/search/ package.
The flat module remains the canonical implementation so existing
``@patch("routes.search_state.X")`` and ``@patch("routes.search.X")`` patches
keep working unchanged.
"""

from routes.search_state import (  # noqa: F401
    _background_results,
    _RESULTS_TTL,
    _active_background_tasks,
    _MAX_BACKGROUND_TASKS,
    _MAX_BACKGROUND_RESULTS,
    _RESULTS_REDIS_PREFIX,
    _ASYNC_SEARCH_TIMEOUT,
    get_background_results_count,
    _cleanup_stale_results,
    store_background_results,
    _persist_results_to_redis,
    _persist_results_to_supabase,
    _safe_persist_results,
    _persist_done_callback,
    _get_results_from_supabase,
    _get_results_from_redis,
    get_background_results,
    get_background_results_async,
    _update_session_on_error,
    _update_session_on_complete,
    _apply_trial_paywall,
    _execute_background_fetch,
    _run_async_search,
)
