-- CRIT-004: Search Session Lifecycle Tracking (synced from backend/migrations/007)
-- Adds status, error, timing, and pipeline tracking columns to search_sessions.
-- Enables recording every search attempt (success, failure, timeout) so users
-- always see their search history even when processing fails mid-pipeline.
--
-- Idempotent: safe to run multiple times (ADD COLUMN IF NOT EXISTS).
-- Note: search_id column already exists via migration 20260220120000_add_search_id_to_search_sessions.sql

-- AC1: Lifecycle columns
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'created'
    CHECK (status IN ('created', 'processing', 'completed', 'failed', 'timed_out', 'cancelled'));

ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS error_code TEXT;
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS duration_ms INTEGER;
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS pipeline_stage TEXT;
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS raw_count INTEGER DEFAULT 0;
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS response_state TEXT;

-- AC3: Failed UFs tracking (new in CRIT-004)
ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS failed_ufs TEXT[];

-- AC3: Backfill existing sessions (all pre-existing records are successful completions)
UPDATE search_sessions
SET status = 'completed',
    started_at = COALESCE(created_at, now()),
    pipeline_stage = 'persist',
    response_state = 'live'
WHERE status = 'created'
  AND total_filtered > 0;

-- Also backfill zero-result sessions that were successfully completed
UPDATE search_sessions
SET status = 'completed',
    started_at = COALESCE(created_at, now()),
    pipeline_stage = 'persist',
    response_state = 'live'
WHERE status = 'created'
  AND total_raw >= 0
  AND resumo_executivo IS NOT NULL;

-- Index for efficient lookup of in-flight sessions (SIGTERM handler, monitoring)
CREATE INDEX IF NOT EXISTS idx_search_sessions_status
    ON search_sessions (status)
    WHERE status IN ('created', 'processing');

-- Index for SIGTERM cleanup query
CREATE INDEX IF NOT EXISTS idx_search_sessions_inflight
    ON search_sessions (status, started_at)
    WHERE status IN ('created', 'processing');

-- Note: idx_search_sessions_search_id already exists via migration 20260220120000

COMMENT ON COLUMN search_sessions.status IS 'Session lifecycle: created → processing → completed|failed|timed_out|cancelled';
COMMENT ON COLUMN search_sessions.error_message IS 'Human-readable error description (max 500 chars)';
COMMENT ON COLUMN search_sessions.error_code IS 'Machine-readable: sources_unavailable, timeout, filter_error, llm_error, db_error, quota_exceeded, unknown';
COMMENT ON COLUMN search_sessions.started_at IS 'When user initiated the search';
COMMENT ON COLUMN search_sessions.completed_at IS 'When processing finished (success or failure)';
COMMENT ON COLUMN search_sessions.duration_ms IS 'Total processing time in milliseconds';
COMMENT ON COLUMN search_sessions.pipeline_stage IS 'Last pipeline stage reached: validate, prepare, execute, filter, enrich, generate, persist';
COMMENT ON COLUMN search_sessions.raw_count IS 'Items fetched before filtering';
COMMENT ON COLUMN search_sessions.response_state IS 'Data quality: live, cached, degraded, empty_failure';
COMMENT ON COLUMN search_sessions.failed_ufs IS 'List of UF codes that failed to fetch (CRIT-004 AC3)';
