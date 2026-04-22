-- Rollback STORY-SEO-005 gsc_metrics table

DROP POLICY IF EXISTS "admin_read_gsc_metrics" ON gsc_metrics;
DROP POLICY IF EXISTS "service_write_gsc_metrics" ON gsc_metrics;
DROP INDEX IF EXISTS idx_gsc_metrics_impressions;
DROP INDEX IF EXISTS idx_gsc_metrics_query_gin;
DROP INDEX IF EXISTS idx_gsc_metrics_page;
DROP INDEX IF EXISTS idx_gsc_metrics_date;
DROP TABLE IF EXISTS gsc_metrics;
