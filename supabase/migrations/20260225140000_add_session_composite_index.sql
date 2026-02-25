-- STORY-264 AC8: Composite index for search_sessions frequent queries
-- Optimizes: SELECT ... WHERE user_id = X AND status = Y ORDER BY created_at DESC

CREATE INDEX IF NOT EXISTS idx_search_sessions_user_status_created
    ON search_sessions (user_id, status, created_at DESC);

COMMENT ON INDEX idx_search_sessions_user_status_created IS
    'STORY-264 AC8: Composite index for user+status+date queries';
