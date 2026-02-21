-- GTM-RESILIENCE-B02: Hot/Warm/Cold cache priority system
-- Adds priority classification, access tracking, and smart eviction
-- Depends on: 026_search_results_cache.sql, 031_cache_health_metadata.sql

-- AC3: Add priority classification and access tracking fields
ALTER TABLE search_results_cache
    ADD COLUMN IF NOT EXISTS priority TEXT NOT NULL DEFAULT 'cold',
    ADD COLUMN IF NOT EXISTS access_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ;

-- Index for priority-based eviction queries (AC7)
CREATE INDEX IF NOT EXISTS idx_search_cache_priority
    ON search_results_cache (user_id, priority, last_accessed_at);

-- AC7: Smart eviction — replaces FIFO with priority-aware cleanup
-- Limit increased from 5 to 10 entries per user
-- Eviction order: cold first → warm → hot (oldest within each class)
CREATE OR REPLACE FUNCTION cleanup_search_cache_per_user()
RETURNS TRIGGER AS $$
DECLARE
    entry_count INTEGER;
BEGIN
    -- Count entries for this user
    SELECT COUNT(*) INTO entry_count
    FROM search_results_cache
    WHERE user_id = NEW.user_id;

    -- Only evict if over 10 entries
    IF entry_count > 10 THEN
        -- Delete oldest entries beyond limit, prioritizing cold → warm → hot
        DELETE FROM search_results_cache
        WHERE id IN (
            SELECT id FROM search_results_cache
            WHERE user_id = NEW.user_id
            ORDER BY
                CASE priority
                    WHEN 'cold' THEN 0
                    WHEN 'warm' THEN 1
                    WHEN 'hot'  THEN 2
                    ELSE 0
                END ASC,
                COALESCE(last_accessed_at, created_at) ASC
            LIMIT (entry_count - 10)
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Backfill: set last_accessed_at for existing rows that don't have it
-- Note: fetched_at may not exist yet (027b skipped), migration 033 re-runs this backfill
DO $$
BEGIN
    UPDATE search_results_cache
    SET last_accessed_at = COALESCE(last_success_at, fetched_at, created_at)
    WHERE last_accessed_at IS NULL;
EXCEPTION WHEN undefined_column THEN
    RAISE NOTICE 'Column fetched_at not yet available, migration 033 will handle backfill';
END $$;
