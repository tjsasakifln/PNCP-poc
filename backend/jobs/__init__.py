"""jobs package — SYS-004 backend package grouping.

Provides a new import path for job/cron-related modules:
  - jobs.queue (from job_queue)
  - jobs.cron (from cron_jobs)
  - jobs.worker_lifecycle (from worker_lifecycle)

All original import paths continue to work via the unchanged top-level modules.
"""
