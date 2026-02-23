-- GTM-ARCH-002: Add params_hash_global for cross-user cache fallback
-- Allows trial users to benefit from cached results of any user
-- with the same search parameters (setor + ufs + dates).

-- AC2: Add params_hash_global column
ALTER TABLE search_results_cache
    ADD COLUMN IF NOT EXISTS params_hash_global TEXT;

-- Index for fast global fallback lookup (AC4)
CREATE INDEX IF NOT EXISTS idx_search_cache_global_hash
    ON search_results_cache (params_hash_global, created_at DESC);

-- Backfill: existing rows get params_hash as their global hash
-- (best approximation; new writes will compute the proper global hash)
UPDATE search_results_cache
SET params_hash_global = params_hash
WHERE params_hash_global IS NULL;

COMMENT ON COLUMN search_results_cache.params_hash_global
    IS 'GTM-ARCH-002: Hash of (setor, ufs, data_inicio, data_fim) for cross-user cache sharing';
