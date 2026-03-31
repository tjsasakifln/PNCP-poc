"""jobs.queue.worker — WorkerSettings re-export.

DEBT-204: Thin shim. Implementation lives in job_queue.
"""
from job_queue import WorkerSettings  # noqa: F401
