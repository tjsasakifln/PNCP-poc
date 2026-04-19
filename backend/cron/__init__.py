"""cron package — DEBT-v3-S3 decomposition of cron_jobs.py.

Re-exports all public names so ``from cron_jobs import X`` works unchanged.
"""

# __all__ needed so ``from cron import *`` exports underscore-prefixed names.
__all__ = [
    "_is_cb_or_connection_error",
    "get_pncp_cron_status", "get_pncp_recovery_epoch", "_update_pncp_cron_status",
    "_pncp_cron_status_lock", "_pncp_cron_status", "_pncp_recovery_epoch",
    "CLEANUP_INTERVAL_SECONDS", "start_cache_cleanup_task",
    "HEALTH_CANARY_INTERVAL_SECONDS", "run_health_canary", "start_health_canary_task",
    "RECONCILIATION_LOCK_KEY", "RECONCILIATION_LOCK_TTL",
    "REVENUE_SHARE_LOCK_KEY", "REVENUE_SHARE_LOCK_TTL",
    "PLAN_RECONCILIATION_LOCK_KEY", "PLAN_RECONCILIATION_LOCK_TTL", "PLAN_RECONCILIATION_INTERVAL",
    "PRE_DUNNING_INTERVAL_SECONDS", "STRIPE_EVENTS_RETENTION_DAYS", "STRIPE_PURGE_INTERVAL_SECONDS",
    "_MONITORED_TABLES", "run_reconciliation", "start_reconciliation_task",
    "check_pre_dunning_cards", "start_pre_dunning_task",
    "run_revenue_share_report", "start_revenue_share_task",
    "run_plan_reconciliation", "update_table_size_metrics", "start_plan_reconciliation_task",
    "purge_old_stripe_events", "start_stripe_events_purge_task",
    "SESSION_STALE_HOURS", "SESSION_OLD_DAYS",
    "TRIAL_SEQUENCE_INTERVAL_SECONDS", "TRIAL_SEQUENCE_BATCH_SIZE",
    "RESULTS_CLEANUP_INTERVAL_SECONDS", "ALERTS_LOCK_KEY", "ALERTS_LOCK_TTL",
    "SECTOR_STATS_INTERVAL_SECONDS", "SECTOR_STATS_HOUR_UTC",
    "DAILY_VOLUME_INTERVAL_SECONDS", "DAILY_VOLUME_HOUR_UTC",
    "cleanup_stale_sessions", "start_session_cleanup_task",
    "run_search_alerts", "_alerts_loop", "start_alerts_task",
    "start_trial_sequence_task", "start_sector_stats_task",
    "check_unanswered_messages", "start_support_sla_task",
    "record_daily_volume", "start_daily_volume_task",
    "cleanup_expired_results", "start_results_cleanup_task",
]

from cron._loop import is_cb_or_connection_error as _is_cb_or_connection_error  # noqa: F401
from cron.pncp_status import (get_pncp_cron_status, get_pncp_recovery_epoch,  # noqa: F401
    update_pncp_cron_status as _update_pncp_cron_status,
    _pncp_cron_status_lock, _pncp_cron_status, _pncp_recovery_epoch)
from cron.cache import CLEANUP_INTERVAL_SECONDS, start_cache_cleanup_task  # noqa: F401
from cron.health import (HEALTH_CANARY_INTERVAL_SECONDS, run_health_canary,  # noqa: F401
    start_health_canary_task)
from cron.billing import (RECONCILIATION_LOCK_KEY, RECONCILIATION_LOCK_TTL,  # noqa: F401
    REVENUE_SHARE_LOCK_KEY, REVENUE_SHARE_LOCK_TTL,
    PLAN_RECONCILIATION_LOCK_KEY, PLAN_RECONCILIATION_LOCK_TTL, PLAN_RECONCILIATION_INTERVAL,
    PRE_DUNNING_INTERVAL_SECONDS, STRIPE_EVENTS_RETENTION_DAYS, STRIPE_PURGE_INTERVAL_SECONDS,
    _MONITORED_TABLES, run_reconciliation, start_reconciliation_task,
    check_pre_dunning_cards, start_pre_dunning_task,
    run_revenue_share_report, start_revenue_share_task,
    run_plan_reconciliation, update_table_size_metrics, start_plan_reconciliation_task,
    purge_old_stripe_events, start_stripe_events_purge_task)
# P0 zero-churn: Unified cron imports — use jobs/cron/ (active) for trial_sequence
# to eliminate dual-cron conflict (CRIT-044). Legacy cron.notifications still
# provides non-trial functions (session cleanup, alerts, etc.)
from cron.notifications import (SESSION_STALE_HOURS, SESSION_OLD_DAYS,  # noqa: F401
    TRIAL_SEQUENCE_INTERVAL_SECONDS, TRIAL_SEQUENCE_BATCH_SIZE,
    RESULTS_CLEANUP_INTERVAL_SECONDS, ALERTS_LOCK_KEY, ALERTS_LOCK_TTL,
    SECTOR_STATS_INTERVAL_SECONDS, SECTOR_STATS_HOUR_UTC,
    DAILY_VOLUME_INTERVAL_SECONDS, DAILY_VOLUME_HOUR_UTC,
    cleanup_stale_sessions, start_session_cleanup_task,
    run_search_alerts, _alerts_loop, start_alerts_task,
    start_sector_stats_task,
    check_unanswered_messages, start_support_sla_task,
    record_daily_volume, start_daily_volume_task,
    cleanup_expired_results, start_results_cleanup_task)
from jobs.cron.notifications import (  # noqa: F401
    start_trial_sequence_task,  # CRIT-044: canonical source for trial emails
)
