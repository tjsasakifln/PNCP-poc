"""jobs.excel_jobs — Excel generation async jobs.

Re-exports Excel job functions from job_queue.
"""
from job_queue import (  # noqa: F401
    excel_generation_job,
    _update_results_excel_url,
)
