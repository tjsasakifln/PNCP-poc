"""jobs.result_store — Job result persistence (Redis/cancel flags).

Re-exports result store functions from job_queue.
"""
from job_queue import (  # noqa: F401
    persist_job_result,
    get_job_result,
    set_cancel_flag,
    check_cancel_flag,
    clear_cancel_flag,
    enqueue_job,
)
