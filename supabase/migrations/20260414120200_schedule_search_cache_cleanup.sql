-- STORY-1.3 (EPIC-TD-2026Q2 P0): Cron-based cleanup for search_results_cache.
--
-- Trigger trg_cleanup_search_cache only fires on INSERT (keeps max 5/user).
-- Churned / trial-expired users never trigger it, so their rows stay forever.
-- Estimated impact: ~250 MB of obsolete cache after 6 months without purge,
-- contributing materially toward the 500 MB FREE-tier ceiling.
--
-- Runs daily at 04:00 UTC (01:00 BRT) — off-peak, separate window from
-- purge-old-bids (07 UTC) and search_results_store cleanup (04:15 UTC).
-- 24h retention matches the SWR hard-expire threshold in backend/search_cache.py.

SET statement_timeout = 0;

CREATE EXTENSION IF NOT EXISTS pg_cron;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-search-cache') THEN
        PERFORM cron.unschedule('cleanup-search-cache');
    END IF;
END $$;

SELECT cron.schedule(
    'cleanup-search-cache',
    '0 4 * * *',
    $$DELETE FROM public.search_results_cache WHERE created_at < now() - interval '24 hours'$$
);
