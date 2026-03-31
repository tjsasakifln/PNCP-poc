"""jobs.cron.scheduler — Centralised cron task registration.

DEBT-204: Provides register_all_cron_tasks() as a single entry point.
"""
from cron_jobs import (  # noqa: F401
    start_health_canary_task,
    start_cache_cleanup_task,
    start_cache_refresh_task,
    start_warmup_task,
    start_coverage_check_task,
    start_session_cleanup_task,
    start_results_cleanup_task,
    start_reconciliation_task,
    start_pre_dunning_task,
    start_revenue_share_task,
    start_alerts_task,
    start_trial_sequence_task,
    start_sector_stats_task,
    start_support_sla_task,
    start_daily_volume_task,
    start_plan_reconciliation_task,
    start_stripe_events_purge_task,
)


def register_all_cron_tasks() -> list:
    """Return all cron task starter functions for programmatic registration."""
    return [
        start_health_canary_task,
        start_cache_cleanup_task,
        start_cache_refresh_task,
        start_warmup_task,
        start_coverage_check_task,
        start_session_cleanup_task,
        start_results_cleanup_task,
        start_reconciliation_task,
        start_pre_dunning_task,
        start_revenue_share_task,
        start_alerts_task,
        start_trial_sequence_task,
        start_sector_stats_task,
        start_support_sla_task,
        start_daily_volume_task,
        start_plan_reconciliation_task,
        start_stripe_events_purge_task,
    ]
