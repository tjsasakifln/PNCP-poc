-- DEBT-120: DB Optimization — Index Analysis, Traceability, Cleanup
-- Tracks: Index Analysis (AC1-AC4), Pipeline Traceability (AC5-AC6)

-- ============================================================================
-- TRACK 1: Index Analysis — search_results_cache (AC1-AC4)
-- ============================================================================
--
-- AC1: pg_stat_user_indexes executed 2026-03-10 against production.
-- AC2: Results (ordered by idx_scan ASC):
--
-- | Index                                       | idx_scan | idx_tup_read | index_size | Verdict      |
-- |---------------------------------------------|----------|--------------|------------|--------------|
-- | idx_search_cache_fetched_at                 | 0        | 0            | 16 kB      | DROP         |
-- | search_results_cache_pkey                   | 96       | 100          | 16 kB      | KEEP (PK)    |
-- | search_results_cache_user_id_params_hash_key| 118      | 57           | 16 kB      | KEEP (UNIQUE)|
-- | idx_search_cache_priority                   | 172      | 2273         | 16 kB      | KEEP         |
-- | idx_search_cache_params_hash                | 236      | 3            | 16 kB      | KEEP         |
-- | idx_search_cache_user                       | 982      | 41           | 16 kB      | KEEP         |
-- | idx_search_cache_global_hash                | 1114     | 10           | 16 kB      | KEEP         |
-- | idx_search_cache_degraded                   | 2563     | 0            | 8192 bytes | KEEP         |
--
-- AC3: idx_search_cache_params_hash is NOT redundant with UNIQUE(user_id, params_hash).
--   The UNIQUE constraint has user_id as leading column — queries filtering by
--   params_hash alone (e.g., cross-user cleanup) cannot use it efficiently.
--   Production confirms 236 scans on the standalone index.
--
-- AC4: Decision per index:
--   - idx_search_cache_fetched_at: DROP — 0 scans ever. All fetched_at queries
--     use composite indexes (idx_search_cache_user or idx_search_cache_priority)
--     first, then filter fetched_at in-memory. The pg_cron cleanup job uses
--     created_at, not fetched_at. No query path benefits from this index.
--   - idx_search_cache_degraded: KEEP despite 0 tup_read — it's a small partial
--     index (8kB) used by background revalidation queries. The 2563 scans with
--     0 tuples read means "scanned frequently, found nothing" which is correct
--     (degraded_until IS NOT NULL is rare).
--   - All other indexes: KEEP — actively used with significant scan counts.

-- AC3: Drop unused index
DROP INDEX IF EXISTS idx_search_cache_fetched_at;

-- ============================================================================
-- TRACK 2: Pipeline Traceability — search_id on pipeline_items (AC5)
-- ============================================================================

-- AC5: Add search_id column for search-to-pipeline traceability
ALTER TABLE public.pipeline_items
    ADD COLUMN IF NOT EXISTS search_id TEXT;

-- Index for querying pipeline items by search origin
CREATE INDEX IF NOT EXISTS idx_pipeline_items_search_id
    ON public.pipeline_items(search_id)
    WHERE search_id IS NOT NULL;

COMMENT ON COLUMN public.pipeline_items.search_id IS
    'DEBT-120 AC5: Links pipeline item to the search session that discovered it';
