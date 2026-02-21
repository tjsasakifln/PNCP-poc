-- CRIT-013: Search State Transitions Audit Trail
-- Source: backend/migrations/008_search_state_transitions.sql
-- Records every state transition for deterministic, auditable search lifecycle.
-- Fire-and-forget inserts — never blocks the pipeline.
--
-- Idempotent: safe to run multiple times.

-- AC5: Audit trail table
CREATE TABLE IF NOT EXISTS search_state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_id UUID NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    stage TEXT,
    details JSONB DEFAULT '{}',
    duration_since_previous_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for timeline lookups by search_id (AC7)
CREATE INDEX IF NOT EXISTS idx_state_transitions_search_id
    ON search_state_transitions (search_id, created_at ASC);

-- Index for observability queries (state duration histograms)
CREATE INDEX IF NOT EXISTS idx_state_transitions_to_state
    ON search_state_transitions (to_state, created_at);

-- RLS: Only authenticated users can read their own transitions
ALTER TABLE search_state_transitions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read transitions for their own searches
-- (join through search_sessions to verify ownership)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'search_state_transitions'
        AND policyname = 'Users can read own transitions'
    ) THEN
        CREATE POLICY "Users can read own transitions"
            ON search_state_transitions
            FOR SELECT
            USING (
                search_id IN (
                    SELECT search_id FROM search_sessions
                    WHERE user_id = auth.uid()
                    AND search_id IS NOT NULL
                )
            );
    END IF;
END $$;

-- Service role can insert (backend writes)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'search_state_transitions'
        AND policyname = 'Service role can insert transitions'
    ) THEN
        CREATE POLICY "Service role can insert transitions"
            ON search_state_transitions
            FOR INSERT
            WITH CHECK (true);
    END IF;
END $$;

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';

COMMENT ON TABLE search_state_transitions IS 'CRIT-013: Audit trail for search state machine transitions';
COMMENT ON COLUMN search_state_transitions.search_id IS 'UUID correlating with search_sessions.search_id';
COMMENT ON COLUMN search_state_transitions.from_state IS 'Previous state (NULL for initial CREATED)';
COMMENT ON COLUMN search_state_transitions.to_state IS 'New state after transition';
COMMENT ON COLUMN search_state_transitions.stage IS 'Pipeline stage that triggered the transition';
COMMENT ON COLUMN search_state_transitions.details IS 'Arbitrary metadata (JSON) for the transition';
COMMENT ON COLUMN search_state_transitions.duration_since_previous_ms IS 'Milliseconds since previous transition';
