-- STORY-1.2 (TD-DB-004): Schedule purge_old_bids via pg_cron
--
-- Time: 7 UTC (4 AM BRT) — 2h after full crawl (5 UTC).
-- Purging AFTER ingestion ensures we don't delete bids collected in the
-- current window (23-5 UTC). Aligned with INGESTION_FULL_CRAWL_HOUR_UTC + 2.
--
-- Retention: 12 days = 10-day search window + 2-day buffer.
-- Without this cron: ~3-5K new rows/day → 500MB FREE tier hit in 3-4 weeks.
--
-- ARQ worker also runs this job at 7 UTC (ingestion_purge_job).
-- pg_cron is the backup: guarantees purge even if Railway worker is offline.

SELECT cron.schedule(
  'purge-old-bids',
  '0 7 * * *',
  $$SELECT public.purge_old_bids(12)$$
);
