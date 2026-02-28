-- STORY-318: Split from 20260227120000_concurrency_safety.sql (Fix 3a)
-- Quota Atomicity — Atomic Fallback RPC function creation

CREATE OR REPLACE FUNCTION increment_quota_fallback_atomic(
  p_user_id UUID,
  p_month_year TEXT,
  p_max_quota INTEGER DEFAULT 999999
)
RETURNS TABLE(new_count INTEGER) AS $$
BEGIN
  RETURN QUERY
  INSERT INTO monthly_quota (user_id, month_year, searches_count, updated_at)
  VALUES (p_user_id, p_month_year, 1, NOW())
  ON CONFLICT (user_id, month_year)
  DO UPDATE SET
    searches_count = CASE
      WHEN monthly_quota.searches_count < p_max_quota
      THEN monthly_quota.searches_count + 1
      ELSE monthly_quota.searches_count
    END,
    updated_at = NOW()
  RETURNING monthly_quota.searches_count;
END;
$$ LANGUAGE plpgsql;
