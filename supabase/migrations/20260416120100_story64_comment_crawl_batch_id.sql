-- ============================================================================
-- STORY-6.4 AC2 (TD-DB-032): Document soft FK rationale for
-- pncp_raw_bids.crawl_batch_id.
-- Date: 2026-04-16
-- ============================================================================
-- Context:
--   pncp_raw_bids.crawl_batch_id (TEXT) references ingestion_runs.crawl_batch_id
--   but intentionally has NO hard FK constraint. The original migration
--   (20260326000000_datalake_raw_bids.sql) added a basic COMMENT; this
--   migration replaces it with an expanded rationale for future maintainers.
-- ============================================================================

COMMENT ON COLUMN public.pncp_raw_bids.crawl_batch_id IS
    'Soft reference to ingestion_runs.crawl_batch_id. '
    'Intentionally NOT a hard FK to allow batch deletion and historic data '
    'retention without cascade constraints: when a crawl_batch is purged from '
    'ingestion_runs for housekeeping, its raw bid rows can remain in '
    'pncp_raw_bids with the original crawl_batch_id for audit traceability. '
    'A hard FK with ON DELETE CASCADE would silently wipe bid data on batch '
    'cleanup; ON DELETE SET NULL would lose the audit trail. '
    'See STORY-6.4 TD-DB-032.';
