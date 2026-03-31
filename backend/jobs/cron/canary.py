"""jobs.cron.canary — PNCP health canary and status tracking.

DEBT-204: Logical grouping facade. Implementation lives in cron_jobs.
"""
from cron_jobs import (  # noqa: F401
    get_pncp_cron_status,
    get_pncp_recovery_epoch,
    _update_pncp_cron_status,
    _is_cb_or_connection_error,
    start_health_canary_task,
    run_health_canary,
    _health_canary_loop,
)
