-- STORY-316 AC5: Health checks history table
-- Stores periodic health check results for uptime calculation
CREATE TABLE IF NOT EXISTS health_checks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    overall_status TEXT NOT NULL CHECK (overall_status IN ('healthy', 'degraded', 'unhealthy')),
    sources_json JSONB NOT NULL DEFAULT '{}',
    components_json JSONB NOT NULL DEFAULT '{}',
    latency_ms INTEGER
);

-- Index for uptime queries (last 24h, 7d, 30d)
CREATE INDEX idx_health_checks_checked_at ON health_checks (checked_at DESC);

-- Retention: auto-delete after 30 days via pg_cron or app-level cleanup
COMMENT ON TABLE health_checks IS 'STORY-316 AC5: Periodic health check results (30-day retention)';
