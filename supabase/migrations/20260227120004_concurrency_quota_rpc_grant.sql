-- STORY-318: Split from 20260227120000_concurrency_safety.sql (Fix 3b)
-- GRANT EXECUTE on increment_quota_fallback_atomic to service_role

GRANT EXECUTE ON FUNCTION increment_quota_fallback_atomic(UUID, TEXT, INTEGER) TO service_role;
