-- GTM-FIX-010: Add sources_json and fetched_at to search_results_cache
-- sources_json tracks which data sources contributed to cached results
-- fetched_at records when the live fetch occurred (vs created_at = row creation)

-- Add sources tracking (AC1 revised, AC5 revised)
ALTER TABLE search_results_cache
    ADD COLUMN IF NOT EXISTS sources_json JSONB NOT NULL DEFAULT '["pncp"]'::jsonb;

-- Add explicit fetch timestamp (separate from row created_at)
ALTER TABLE search_results_cache
    ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ DEFAULT now() NOT NULL;

-- Index for TTL cleanup queries (find entries older than 24h)
CREATE INDEX IF NOT EXISTS idx_search_cache_fetched_at
    ON search_results_cache(fetched_at);

COMMENT ON COLUMN search_results_cache.sources_json IS 'GTM-FIX-010 AC5r: Which sources contributed to this cache entry (e.g. ["PNCP","PORTAL_COMPRAS"])';
COMMENT ON COLUMN search_results_cache.fetched_at IS 'GTM-FIX-010: When the live fetch was executed (for TTL calculations)';
