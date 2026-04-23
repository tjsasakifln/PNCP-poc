DROP INDEX IF EXISTS idx_health_checks_api_status_checked_at;
ALTER TABLE health_checks DROP COLUMN IF EXISTS api_status;
