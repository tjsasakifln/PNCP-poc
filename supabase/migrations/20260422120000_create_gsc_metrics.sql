-- STORY-SEO-005: Google Search Console metrics cache
-- Weekly ARQ job (backend/jobs/cron/gsc_sync.py) populates this table from GSC API
-- Dashboard at /admin/seo reads for data-driven SEO decisions

CREATE TABLE IF NOT EXISTS gsc_metrics (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  query TEXT,
  page TEXT,
  country TEXT DEFAULT 'BRA',
  device TEXT,
  clicks INTEGER NOT NULL DEFAULT 0,
  impressions INTEGER NOT NULL DEFAULT 0,
  ctr NUMERIC(6,5) NOT NULL DEFAULT 0,
  position NUMERIC(8,3) NOT NULL DEFAULT 0,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT gsc_metrics_uniq UNIQUE (date, query, page, country, device)
);

CREATE INDEX IF NOT EXISTS idx_gsc_metrics_date ON gsc_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_gsc_metrics_page ON gsc_metrics(page);
CREATE INDEX IF NOT EXISTS idx_gsc_metrics_query_gin
  ON gsc_metrics USING GIN (to_tsvector('portuguese', query));
CREATE INDEX IF NOT EXISTS idx_gsc_metrics_impressions ON gsc_metrics(impressions DESC);

ALTER TABLE gsc_metrics ENABLE ROW LEVEL SECURITY;

-- Admin-only read (no public exposure of GSC data)
DROP POLICY IF EXISTS "admin_read_gsc_metrics" ON gsc_metrics;
CREATE POLICY "admin_read_gsc_metrics" ON gsc_metrics
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
        AND (profiles.is_admin = true OR profiles.is_master = true)
    )
  );

-- Service role writes (ARQ job uses service_role_key)
DROP POLICY IF EXISTS "service_write_gsc_metrics" ON gsc_metrics;
CREATE POLICY "service_write_gsc_metrics" ON gsc_metrics
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

COMMENT ON TABLE gsc_metrics IS
  'STORY-SEO-005: Google Search Console query/page performance cache. Populated weekly by ARQ cron gsc_sync_job. Admin-only read via RLS.';
