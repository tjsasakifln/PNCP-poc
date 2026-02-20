-- Migration: Add search_id column to search_sessions table
-- Story: CRIT-011
-- Reason: CRIT-003 startup recovery requires search_id for correlation
-- Related: GTM-FIX-031 (search_id added to BuscaRequest schema)

ALTER TABLE search_sessions
  ADD COLUMN IF NOT EXISTS search_id UUID DEFAULT NULL;

-- Index for startup recovery query (find stale sessions by search_id)
CREATE INDEX IF NOT EXISTS idx_search_sessions_search_id
  ON search_sessions (search_id)
  WHERE search_id IS NOT NULL;

-- Index for cleanup of old sessions
CREATE INDEX IF NOT EXISTS idx_search_sessions_status_created
  ON search_sessions (status, created_at)
  WHERE status = 'in_progress';

COMMENT ON COLUMN search_sessions.search_id IS
  'UUID linking session to SSE progress tracker, ARQ jobs, and cache entries. Optional for backward compatibility.';
