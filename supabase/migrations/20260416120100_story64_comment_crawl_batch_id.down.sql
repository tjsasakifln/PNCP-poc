-- ============================================================================
-- DOWN: story64_comment_crawl_batch_id — reverses
--       20260416120100_story64_comment_crawl_batch_id.sql
-- Date: 2026-04-16
-- Story: STORY-6.4 AC2 (TD-DB-032)
-- ============================================================================

COMMENT ON COLUMN public.pncp_raw_bids.crawl_batch_id IS
    'Links row to the ingestion_runs.crawl_batch_id that created/last-updated it.';
