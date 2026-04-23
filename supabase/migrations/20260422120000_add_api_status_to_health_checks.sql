-- Separate API availability from upstream (PNCP/Portal) availability.
-- Before: overall_status mixed SmartLic components with government APIs,
--   producing ~88% uptime dominated by PNCP timeouts (>10s) even though
--   the product serves from DataLake locally (DATALAKE_QUERY_ENABLED=true).
-- After: api_status = own components only (Redis, Supabase, ARQ). Uptime
--   SLO is computed from this column; overall_status is kept for the
--   public status page (sources + components combined view).

ALTER TABLE health_checks
  ADD COLUMN IF NOT EXISTS api_status TEXT
  CHECK (api_status IN ('healthy', 'degraded', 'unhealthy'));

UPDATE health_checks
SET api_status = CASE
  WHEN components_json::jsonb @> '{"supabase": "unhealthy"}' THEN 'unhealthy'
  WHEN components_json::jsonb @> '{"redis": "unhealthy"}' THEN 'unhealthy'
  WHEN components_json::jsonb @> '{"arq_worker": "unhealthy"}' THEN 'degraded'
  ELSE 'healthy'
END
WHERE api_status IS NULL;

CREATE INDEX IF NOT EXISTS idx_health_checks_api_status_checked_at
  ON health_checks (api_status, checked_at DESC);

COMMENT ON COLUMN health_checks.api_status IS
  'SmartLic API availability (own components only). Used for SLO/uptime calc. Excludes PNCP/Portal upstreams.';
