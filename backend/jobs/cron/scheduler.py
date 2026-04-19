"""jobs.cron.scheduler — Centralised cron task registration."""
from jobs.cron.canary import start_health_canary_task  # noqa: F401
from cron.cache import start_cache_cleanup_task  # noqa: F401
from jobs.cron.session_cleanup import start_session_cleanup_task, start_results_cleanup_task  # noqa: F401
from jobs.cron.notifications import (  # noqa: F401
    start_alerts_task, start_trial_sequence_task,
    start_support_sla_task, start_daily_volume_task, start_sector_stats_task,
)
from jobs.cron.billing import (  # noqa: F401
    start_reconciliation_task, start_pre_dunning_task, start_revenue_share_task,
    start_plan_reconciliation_task, start_stripe_events_purge_task,
)
from jobs.cron.seo_snapshot import start_seo_snapshot_task  # noqa: F401
from jobs.cron.indice_municipal import start_indice_municipal_task  # noqa: F401
from jobs.cron.new_bids_notifier import start_new_bids_notifier_task  # noqa: F401
from jobs.cron.pncp_canary import start_pncp_canary_task  # noqa: F401
from jobs.cron.llm_batch_poll import start_llm_batch_poll_task  # noqa: F401


def register_all_cron_tasks() -> list:
    return [
        start_health_canary_task,
        start_cache_cleanup_task,
        start_session_cleanup_task, start_results_cleanup_task,
        start_reconciliation_task, start_pre_dunning_task, start_revenue_share_task,
        start_alerts_task, start_trial_sequence_task,
        start_sector_stats_task, start_support_sla_task, start_daily_volume_task,
        start_plan_reconciliation_task, start_stripe_events_purge_task,
        start_seo_snapshot_task,
        start_indice_municipal_task,
        start_new_bids_notifier_task,
        start_pncp_canary_task,
        start_llm_batch_poll_task,
    ]
