-- STORY-318: Split from 20260227120000_concurrency_safety.sql (Fix 1)
-- Stripe Webhook Atomicity — status + received_at columns

-- Add status column for tracking processing state
ALTER TABLE stripe_webhook_events
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'completed' NOT NULL;

-- Add received_at for stuck event detection
ALTER TABLE stripe_webhook_events
  ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ DEFAULT NOW();

-- Backfill received_at from processed_at for existing rows
UPDATE stripe_webhook_events
SET received_at = processed_at
WHERE received_at IS NULL OR received_at = NOW();

-- GRANT UPDATE (required for status transitions: processing -> completed/failed)
GRANT UPDATE ON stripe_webhook_events TO service_role;
