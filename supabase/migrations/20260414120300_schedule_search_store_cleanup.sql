-- STORY-1.4 (EPIC-TD-2026Q2 P0): Cron-based cleanup for search_results_store.
--
-- search_results_store.expires_at is set to now() + 24h on insert, but no
-- process deletes expired rows. Table grows linearly with searches and will
-- eventually pressure the 500 MB FREE-tier limit (same pattern as TD-DB-013).
--
-- Runs daily at 04:15 UTC — 15 minutes after cleanup-search-cache (STORY-1.3)
-- to spread DELETE load. DELETE on expires_at is idempotent and safe to rerun.

SET statement_timeout = 0;

CREATE EXTENSION IF NOT EXISTS pg_cron;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-search-store') THEN
        PERFORM cron.unschedule('cleanup-search-store');
    END IF;
END $$;

SELECT cron.schedule(
    'cleanup-search-store',
    '15 4 * * *',
    $$DELETE FROM public.search_results_store WHERE expires_at < now()$$
);
