"""jobs.queue.definitions — Backward-compat shim. Use jobs.queue sub-modules directly."""
from jobs.queue.pool import enqueue_job, get_queue_health, is_queue_available  # noqa: F401
from jobs.queue.result_store import (  # noqa: F401
    set_cancel_flag, check_cancel_flag, clear_cancel_flag,
    persist_job_result, get_job_result,
    acquire_search_slot, release_search_slot,
    store_pending_review_bids, store_zero_match_results, get_zero_match_results,
    _update_results_excel_url,
)
from jobs.queue.jobs import (  # noqa: F401
    llm_summary_job, excel_generation_job, bid_analysis_job,
    cache_refresh_job, cache_warming_job, daily_digest_job, email_alerts_job,
    reclassify_pending_bids_job, classify_zero_match_job,
)
from jobs.queue.search import search_job  # noqa: F401
