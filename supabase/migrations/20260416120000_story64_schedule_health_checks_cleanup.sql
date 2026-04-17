-- ============================================================================
-- STORY-6.4 AC1 (TD-DB-023): Schedule / confirm pg_cron job to delete
-- health_checks older than 30 days.
-- Date: 2026-04-16
-- ============================================================================
-- Context:
--   The health_checks table (20260228150000_add_health_checks_table.sql) uses
--   column `checked_at` (NOT `created_at`) as its temporal axis.
--
--   A cleanup job was first introduced in
--   20260308310000_debt009_retention_pgcron_jobs.sql at '10 4 * * *' (UTC).
--   STORY-6.4 re-registers it idempotently to:
--     1. Document the correct column name (checked_at) for future maintainers.
--     2. Move the schedule to 3am UTC (consistent with other retention jobs).
--     3. Ensure this cron is picked up by the existing STORY-1.1 pg_cron monitor
--        (cron_job_health view covers all jobs in cron.job by default).
--
--   Idempotent: unschedule first, then schedule.
-- ============================================================================

SELECT cron.unschedule('cleanup-health-checks')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-health-checks');

SELECT cron.schedule(
    'cleanup-health-checks',
    '0 3 * * *',
    $$DELETE FROM public.health_checks
      WHERE checked_at < now() - INTERVAL '30 days';$$
);

COMMENT ON TABLE public.health_checks IS
    'STORY-316 AC5 + STORY-6.4 TD-DB-023: Periodic health check results. '
    '30-day retention enforced by pg_cron job ''cleanup-health-checks'' '
    '(runs daily 03:00 UTC). Temporal axis: checked_at (NOT created_at). '
    'Monitored by STORY-1.1 cron_job_health view.';
