-- ============================================================================
-- DOWN: backfill_pncp_raw_bids_dates — reverses
--       20260414132000_backfill_pncp_raw_bids_dates.sql
-- Date: 2026-04-16
-- Story: STORY-2.12 AC2 (TD-DB-015)
-- ============================================================================

-- NO AUTOMATIC ROLLBACK: manual restore from backup required.
--
-- This migration performed bulk DML (UPDATE) on public.pncp_raw_bids:
--   1. SET data_publicacao = (ingested_at - 1 day) WHERE data_publicacao IS NULL
--   2. SET data_abertura   = data_publicacao        WHERE data_abertura IS NULL
--
-- There is no safe, deterministic way to reverse these updates because:
--   - We do not know which rows had NULL before the migration ran.
--   - Setting them back to NULL would affect rows that genuinely had values.
--
-- To rollback:
--   1. Identify a backup taken immediately before this migration was applied.
--   2. Restore public.pncp_raw_bids from that backup (pg_restore or
--      Supabase point-in-time recovery).
--   3. Validate row counts and NULL distribution post-restore:
--        SELECT
--          COUNT(*) FILTER (WHERE data_publicacao IS NULL) AS pub_null,
--          COUNT(*) FILTER (WHERE data_abertura IS NULL)   AS abr_null,
--          COUNT(*)                                        AS total
--        FROM public.pncp_raw_bids WHERE is_active = true;
--
-- See STORY-6.2 TD-DB-030 for the full irreversible DML rollback policy.

-- COMMENT ON changes: reset to pre-migration state (no STORY-2.12 annotation)
COMMENT ON COLUMN public.pncp_raw_bids.data_publicacao IS NULL;
COMMENT ON COLUMN public.pncp_raw_bids.data_abertura   IS NULL;
