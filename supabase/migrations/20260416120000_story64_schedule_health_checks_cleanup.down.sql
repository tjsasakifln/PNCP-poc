-- ============================================================================
-- DOWN: story64_schedule_health_checks_cleanup — reverses
--       20260416120000_story64_schedule_health_checks_cleanup.sql
-- Date: 2026-04-16
-- Story: STORY-6.4 AC1 (TD-DB-023)
-- ============================================================================
-- Context:
--   Up migration re-scheduled 'cleanup-health-checks' to '0 3 * * *' (3am UTC).
--   Previous schedule was '10 4 * * *' (from 20260308310000_debt009_retention_pgcron_jobs.sql).
--
--   Down: unschedule the job. The original job from debt009 migration is NOT
--   automatically restored — re-apply 20260308310000 manually if needed.
-- ============================================================================

SELECT cron.unschedule('cleanup-health-checks')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-health-checks');
