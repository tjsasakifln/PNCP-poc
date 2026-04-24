-- STORY-1.3 (TD-DB-013 / TD-SYS-016): Schedule search_results_cache cleanup via pg_cron
--
-- Time: 4 UTC (1 AM BRT) — off-peak, before purge_old_bids (7 UTC).
--
-- Problem: trigger trg_cleanup_search_cache keeps max 5 entries/user on INSERT,
-- but only fires on INSERT. If a user never returns, old entries persist forever.
-- Storage estimate without cron: 500 users × 5 entries × 100KB ≈ 250MB in 6 months.
--
-- This cron deletes any row where created_at < 24h ago (the cache TTL).
-- Safe: concurrent trigger + cron DELETEs are idempotent.

SELECT cron.schedule(
  'cleanup-search-cache',
  '0 4 * * *',
  $$DELETE FROM public.search_results_cache WHERE created_at < now() - interval '24 hours'$$
);
