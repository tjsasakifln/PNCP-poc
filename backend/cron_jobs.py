"""cron_jobs.py — Backward-compatibility facade.

All implementation has moved to jobs/cron/ sub-package (DEBT-v3-S3 Phase 2.2).
Import from this module continues to work unchanged.

NOTE: Mutable canary state (_pncp_cron_status, _pncp_cron_status_lock,
_pncp_recovery_epoch) lives HERE so that test fixtures that do
``cron_jobs._pncp_recovery_epoch = 0`` keep working.  jobs.cron.canary
reads/writes this state via a lazy ``import cron_jobs`` reference.
"""
import threading

# ── Canary state (canonical home — DO NOT move to canary.py) ──────────────
_pncp_cron_status_lock = threading.Lock()
_pncp_cron_status: dict = {"status": "unknown", "latency_ms": None, "updated_at": None}
_pncp_recovery_epoch: int = 0

# ── Canary functions ───────────────────────────────────────────────────────
from jobs.cron.canary import (  # noqa: F401
    get_pncp_cron_status,
    get_pncp_recovery_epoch,
    _update_pncp_cron_status,
    _is_cb_or_connection_error,
    run_health_canary,
    _health_canary_loop,
    start_health_canary_task,
    HEALTH_CANARY_INTERVAL_SECONDS,
)

# Cache ops — warming/refresh deprecated 2026-04-18 (STORY-CIG-BE-cache-warming-deprecate).
# Only passive cleanup remains.
from cron.cache import (  # noqa: F401
    CLEANUP_INTERVAL_SECONDS,
    start_cache_cleanup_task,
)

# Session / results cleanup
from jobs.cron.session_cleanup import (  # noqa: F401
    SESSION_STALE_HOURS,
    SESSION_OLD_DAYS,
    RESULTS_CLEANUP_INTERVAL_SECONDS,
    cleanup_stale_sessions,
    cleanup_expired_results,
    _session_cleanup_loop,
    _results_cleanup_loop,
    start_session_cleanup_task,
    start_results_cleanup_task,
)

# Notifications
from jobs.cron.notifications import (  # noqa: F401
    TRIAL_SEQUENCE_INTERVAL_SECONDS,
    TRIAL_SEQUENCE_BATCH_SIZE,
    ALERTS_LOCK_KEY,
    ALERTS_LOCK_TTL,
    run_search_alerts,
    _alerts_loop,
    _trial_sequence_loop,
    check_unanswered_messages,
    _support_sla_loop,
    record_daily_volume,
    _daily_volume_loop,
    _sector_stats_loop,
    start_alerts_task,
    start_trial_sequence_task,
    start_support_sla_task,
    start_daily_volume_task,
    start_sector_stats_task,
)

# Billing
from jobs.cron.billing import (  # noqa: F401
    RECONCILIATION_LOCK_KEY,
    RECONCILIATION_LOCK_TTL,
    PRE_DUNNING_INTERVAL_SECONDS,
    REVENUE_SHARE_LOCK_KEY,
    REVENUE_SHARE_LOCK_TTL,
    PLAN_RECONCILIATION_LOCK_KEY,
    PLAN_RECONCILIATION_LOCK_TTL,
    PLAN_RECONCILIATION_INTERVAL,
    STRIPE_EVENTS_RETENTION_DAYS,
    STRIPE_PURGE_INTERVAL_SECONDS,
    run_reconciliation,
    _reconciliation_loop,
    check_pre_dunning_cards,
    _pre_dunning_loop,
    run_revenue_share_report,
    _revenue_share_loop,
    run_plan_reconciliation,
    update_table_size_metrics,
    _plan_reconciliation_loop,
    purge_old_stripe_events,
    _stripe_events_purge_loop,
    start_reconciliation_task,
    start_pre_dunning_task,
    start_revenue_share_task,
    start_plan_reconciliation_task,
    start_stripe_events_purge_task,
)

# Trial risk detection
from jobs.cron.trial_risk_detection import (  # noqa: F401
    detect_at_risk_trials,
    start_trial_risk_task,
)

# Índice Municipal — quarterly recalc
from jobs.cron.indice_municipal import (  # noqa: F401
    run_indice_municipal_recalc,
    start_indice_municipal_task,
)

# New bids notifier — daily in-app badge
from jobs.cron.new_bids_notifier import (  # noqa: F401
    run_new_bids_notifier,
    start_new_bids_notifier_task,
)
