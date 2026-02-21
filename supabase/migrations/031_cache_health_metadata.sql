-- GTM-RESILIENCE-B03: Cache health metadata per key
-- Adds 6 fields for per-key health tracking + degraded index
-- Prerequisite for B-01 (background revalidation) and B-02 (hot/warm/cold)

-- AC1: Add 6 health metadata fields
ALTER TABLE search_results_cache
    ADD COLUMN IF NOT EXISTS last_success_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_attempt_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS fail_streak INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS degraded_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS coverage JSONB,
    ADD COLUMN IF NOT EXISTS fetch_duration_ms INTEGER;

-- AC10: Index for efficient "which keys are degraded" queries
CREATE INDEX IF NOT EXISTS idx_search_cache_degraded
    ON search_results_cache (degraded_until)
    WHERE degraded_until IS NOT NULL;

-- Backfill existing rows: set last_success_at = fetched_at for rows that have data
-- Note: fetched_at may not exist yet (027b skipped), migration 033 re-runs this backfill
DO $$
BEGIN
    UPDATE search_results_cache
    SET last_success_at = fetched_at,
        last_attempt_at = fetched_at
    WHERE last_success_at IS NULL AND fetched_at IS NOT NULL;
EXCEPTION WHEN undefined_column THEN
    RAISE NOTICE 'Column fetched_at not yet available, migration 033 will handle backfill';
END $$;
