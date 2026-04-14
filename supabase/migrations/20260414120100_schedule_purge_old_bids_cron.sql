-- STORY-1.2 (EPIC-TD-2026Q2 P0): Schedule purge_old_bids via pg_cron.
--
-- Runs daily at 07:00 UTC (04:00 BRT) — 2 hours after the full PNCP crawl
-- (05 UTC) to guarantee ingestion has consolidated active data before purge.
-- Matches INGESTION_FULL_CRAWL_HOUR_UTC + 2 from backend/jobs/queue/config.py.
--
-- Architecture: dual mechanism (ARQ worker + pg_cron) is intentional — pg_cron
-- acts as a Supabase-native backup if the Railway worker is offline or restarting.
-- purge_old_bids(12) retains 12 days = 10-day search window + 2-day buffer.
--
-- Storage rationale: pncp_raw_bids grows ~3-5K rows/day. Without purge the
-- table reaches the 500 MB FREE-tier cap in 3-4 weeks → table locks → search
-- downtime. Highest ROI debt in the epic (~30 min work → avoids 10-30k BRL loss).

SET statement_timeout = 0;

CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Idempotent: unschedule any existing job with the same name before creating.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'purge-old-bids') THEN
        PERFORM cron.unschedule('purge-old-bids');
    END IF;
END $$;

SELECT cron.schedule(
    'purge-old-bids',
    '0 7 * * *',
    $$SELECT public.purge_old_bids(12)$$
);
