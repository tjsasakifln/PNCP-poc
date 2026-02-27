-- STORY-307: Concurrency Safety — Atomic Operations in Critical Paths
-- AC16: Add status column to stripe_webhook_events
-- AC17: Add received_at column to stripe_webhook_events
-- AC18: Add version column to pipeline_items
-- AC19: GRANT UPDATE on stripe_webhook_events to service_role
-- AC20: Validate PK index on stripe_webhook_events(id)

-- ============================================================================
-- Fix 1: Stripe Webhook Atomicity
-- ============================================================================

-- AC16: Add status column for tracking processing state
-- Existing rows are already processed, so default to 'completed'
ALTER TABLE stripe_webhook_events
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'completed' NOT NULL;

-- AC17: Add received_at for stuck event detection
-- Existing rows use processed_at as best approximation
ALTER TABLE stripe_webhook_events
  ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ DEFAULT NOW();

-- Backfill received_at from processed_at for existing rows
UPDATE stripe_webhook_events
SET received_at = processed_at
WHERE received_at IS NULL OR received_at = NOW();

-- AC19: GRANT UPDATE (currently only INSERT and SELECT)
-- Required for status transitions: processing → completed/failed
GRANT UPDATE ON stripe_webhook_events TO service_role;

-- AC20: Validate PK index — id is already PRIMARY KEY, which creates a unique index.
-- No action needed, but add a comment for auditability.
-- VERIFY: SELECT indexname FROM pg_indexes WHERE tablename = 'stripe_webhook_events';

-- ============================================================================
-- Fix 2: Pipeline Optimistic Locking
-- ============================================================================

-- AC18: Add version column for optimistic locking
ALTER TABLE pipeline_items
  ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;

-- ============================================================================
-- Fix 3: Quota Atomicity — Atomic Fallback RPC
-- ============================================================================

-- AC13-AC15: Atomic increment with ON CONFLICT for the fallback path
-- Eliminates read-modify-write race condition
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

-- Grant execute to service_role
GRANT EXECUTE ON FUNCTION increment_quota_fallback_atomic(UUID, TEXT, INTEGER) TO service_role;
