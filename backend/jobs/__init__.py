"""jobs package — DEBT-305 decomposition.

Provides organized import paths for job/cron-related modules:

  Queue management:
    - jobs.pool — ARQ connection pool lifecycle
    - jobs.result_store — Job result persistence, cancel flags, enqueue

  Job functions (ARQ worker):
    - jobs.llm_jobs — LLM summary, reclassification
    - jobs.excel_jobs — Excel generation
    - jobs.search_jobs — Search pipeline execution
    - jobs.cache_jobs — Cache refresh/warming
    - jobs.zero_match_jobs — Zero-match classification
    - jobs.notification_jobs — Email alerts, daily digest

  Cron tasks (lifespan background loops):
    - jobs.cron_health — PNCP health canary
    - jobs.cron_cache — Cache cleanup, refresh, warmup, coverage
    - jobs.cron_billing — Reconciliation, dunning, revenue share
    - jobs.cron_notifications — Alerts, trial sequence, SLA, volume

  Legacy re-exports (unchanged top-level modules):
    - jobs.queue → job_queue.*
    - jobs.cron → cron_jobs.*
    - jobs.worker_lifecycle → worker_lifecycle.*

All original import paths (``from job_queue import X``,
``from cron_jobs import Y``) continue to work unchanged.
"""
