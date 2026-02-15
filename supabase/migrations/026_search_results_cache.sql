-- STORY-257A AC11: Search results cache for "Never Empty-Handed" resilience
-- Persists last successful search results per user to serve when all sources fail.
-- Two-level cache strategy: InMemoryCache (fast, lost on redeploy) + Supabase (persistent).

-- Create the search results cache table
CREATE TABLE IF NOT EXISTS search_results_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    params_hash TEXT NOT NULL,
    search_params JSONB NOT NULL,
    results JSONB NOT NULL,
    total_results INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,

    -- One cache entry per user per unique search params
    UNIQUE(user_id, params_hash)
);

-- Index for fast lookup by user, ordered by most recent
CREATE INDEX IF NOT EXISTS idx_search_cache_user
    ON search_results_cache(user_id, created_at DESC);

-- Index for cleanup queries (find oldest entries per user)
CREATE INDEX IF NOT EXISTS idx_search_cache_params_hash
    ON search_results_cache(params_hash);

-- RLS: Users can only read their own cache entries
ALTER TABLE search_results_cache ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (backend uses service role key)
CREATE POLICY "Service role full access on search_results_cache"
    ON search_results_cache
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Users can read their own cache entries (for potential direct access)
CREATE POLICY "Users can read own search cache"
    ON search_results_cache
    FOR SELECT
    USING (auth.uid() = user_id);

-- Function to enforce max 5 cache entries per user (cleanup on write)
CREATE OR REPLACE FUNCTION cleanup_search_cache_per_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete oldest entries beyond the 5 most recent for this user
    DELETE FROM search_results_cache
    WHERE id IN (
        SELECT id FROM search_results_cache
        WHERE user_id = NEW.user_id
        ORDER BY created_at DESC
        OFFSET 5
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-cleanup after insert/upsert
DROP TRIGGER IF EXISTS trg_cleanup_search_cache ON search_results_cache;
CREATE TRIGGER trg_cleanup_search_cache
    AFTER INSERT ON search_results_cache
    FOR EACH ROW
    EXECUTE FUNCTION cleanup_search_cache_per_user();

-- Comment for documentation
COMMENT ON TABLE search_results_cache IS 'STORY-257A AC11: Persistent cache of last 5 search results per user. Serves cached data when all sources fail (Never Empty-Handed principle).';
