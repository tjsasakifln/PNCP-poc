-- STORY-1.4 (TD-DB-014): Schedule search_results_store cleanup via pg_cron
--
-- Time: 4:15 UTC — 15 min after search_cache cleanup (4:00 UTC) to avoid
-- concurrent large DELETE load on the same worker.
--
-- Problem: search_results_store.expires_at defines a soft TTL (24h) but no
-- scheduled job deletes expired rows. Table grows linearly with search volume.
--
-- This cron deletes any row where expires_at < now().
-- Safe: DELETE idempotent; app handles 404 if result deleted between access.

SELECT cron.schedule(
  'cleanup-search-store',
  '15 4 * * *',
  $$DELETE FROM public.search_results_store WHERE expires_at < now()$$
);
