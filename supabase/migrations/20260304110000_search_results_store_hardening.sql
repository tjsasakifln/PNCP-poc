-- TD-001 AC7-AC11: search_results_store hardening
-- Composite index for cleanup queries + pg_cron daily cleanup + row size CHECK

-- ══════════════════════════════════════════════════════════════════
-- AC7/L-06: Composite index (user_id, expires_at) for cleanup queries
-- ══════════════════════════════════════════════════════════════════
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_results_store_user_expires
  ON public.search_results_store (user_id, expires_at);

-- ══════════════════════════════════════════════════════════════════
-- AC10: CHECK constraint for 2MB max row size
-- ══════════════════════════════════════════════════════════════════
ALTER TABLE public.search_results_store
  ADD CONSTRAINT chk_result_data_size
  CHECK (octet_length(results::text) < 2097152);

-- ══════════════════════════════════════════════════════════════════
-- AC8-AC9/H-03: pg_cron daily cleanup at 4am UTC
-- Deletes rows expired more than 7 days ago
-- AC11: pg_cron is enabled by default on Supabase Cloud
-- ══════════════════════════════════════════════════════════════════
SELECT cron.schedule(
  'cleanup-expired-search-results',
  '0 4 * * *',
  $$DELETE FROM public.search_results_store WHERE expires_at < NOW() - INTERVAL '7 days'$$
);
