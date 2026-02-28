-- STORY-316 AC9: Incidents table for status page
CREATE TABLE IF NOT EXISTS incidents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'ongoing' CHECK (status IN ('ongoing', 'resolved')),
    affected_sources TEXT[] NOT NULL DEFAULT '{}',
    description TEXT NOT NULL DEFAULT ''
);

-- Index for active incidents and recent history
CREATE INDEX idx_incidents_status ON incidents (status) WHERE status = 'ongoing';
CREATE INDEX idx_incidents_started_at ON incidents (started_at DESC);

COMMENT ON TABLE incidents IS 'STORY-316 AC9: System incidents for public status page';
