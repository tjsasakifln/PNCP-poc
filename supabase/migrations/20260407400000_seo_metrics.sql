-- S14: SEO metrics table for Google Search Console snapshots.
-- Used by: backend/scripts/gsc_metrics.py (upsert), backend/routes/seo_admin.py (read).

CREATE TABLE IF NOT EXISTS public.seo_metrics (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date            DATE NOT NULL,
    source          TEXT NOT NULL DEFAULT 'gsc',
    impressions     INTEGER NOT NULL DEFAULT 0,
    clicks          INTEGER NOT NULL DEFAULT 0,
    ctr             NUMERIC(6,4) NOT NULL DEFAULT 0,
    avg_position    NUMERIC(6,2) NOT NULL DEFAULT 0,
    pages_indexed   INTEGER NOT NULL DEFAULT 0,
    top_queries     JSONB NOT NULL DEFAULT '[]'::jsonb,
    top_pages       JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_seo_metrics_date_source UNIQUE (date, source)
);

COMMENT ON TABLE public.seo_metrics IS 'Weekly GSC snapshots — populated by seo_snapshot cron job';

CREATE INDEX IF NOT EXISTS idx_seo_metrics_date_desc ON public.seo_metrics (date DESC);

-- RLS
ALTER TABLE public.seo_metrics ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read (admin check done at app layer)
CREATE POLICY seo_metrics_select ON public.seo_metrics
    FOR SELECT TO authenticated USING (true);

-- Service role can insert/update (cron job runs as service_role)
CREATE POLICY seo_metrics_service_write ON public.seo_metrics
    FOR ALL TO service_role USING (true) WITH CHECK (true);
