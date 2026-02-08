-- ============================================================
-- STORY-171: Stripe Webhook Events (Idempotency)
-- ============================================================
-- Purpose:
--   Store Stripe webhook events to prevent duplicate processing.
--   Stripe may retry webhooks, so we need idempotency checks.
--
-- Features:
--   - Primary key on Stripe event ID (evt_xxx)
--   - JSONB payload for full event debugging
--   - Index for analytics queries
--
-- Usage:
--   Before processing webhook, check if event_id exists:
--     SELECT id FROM stripe_webhook_events WHERE id = 'evt_xxx';
--   If found, return "already_processed" (HTTP 200)
--
-- Retention:
--   Keep events for 90 days for compliance/debugging
--   Archive to S3 after 90 days (future enhancement)
-- ============================================================

-- Create stripe_webhook_events table
CREATE TABLE IF NOT EXISTS public.stripe_webhook_events (
  id VARCHAR(255) PRIMARY KEY,  -- Stripe event ID (evt_xxxxxxxxxxxxx)
  type VARCHAR(100) NOT NULL,   -- Event type (customer.subscription.updated, etc.)
  processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload JSONB,                -- Full Stripe event object for debugging

  CONSTRAINT check_event_id_format CHECK (id ~ '^evt_')
);

-- Index for analytics queries (group by event type, time-series)
CREATE INDEX idx_webhook_events_type ON public.stripe_webhook_events(type, processed_at);

-- Index for recent events lookup (troubleshooting)
CREATE INDEX idx_webhook_events_recent ON public.stripe_webhook_events(processed_at DESC);

-- Comments for documentation
COMMENT ON TABLE public.stripe_webhook_events IS
  'Stores Stripe webhook events for idempotency and audit trail. Prevents duplicate processing.';

COMMENT ON COLUMN public.stripe_webhook_events.id IS
  'Stripe event ID (evt_xxx). Primary key for idempotency.';

COMMENT ON COLUMN public.stripe_webhook_events.type IS
  'Stripe event type (e.g., customer.subscription.updated, invoice.payment_succeeded)';

COMMENT ON COLUMN public.stripe_webhook_events.payload IS
  'Full Stripe event object (JSONB). Used for debugging and compliance.';

-- Row Level Security (public read for admin dashboard)
ALTER TABLE public.stripe_webhook_events ENABLE ROW LEVEL SECURITY;

-- Policy: Only service role can insert (webhooks run with service role)
CREATE POLICY "webhook_events_insert_service" ON public.stripe_webhook_events
  FOR INSERT
  WITH CHECK (true);  -- Service role bypasses RLS

-- Policy: Admins can view for debugging
CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.plan_type = 'master'
    )
  );

-- Grant permissions
GRANT SELECT ON public.stripe_webhook_events TO authenticated;
GRANT INSERT ON public.stripe_webhook_events TO service_role;

-- ============================================================
-- Rollback Script
-- ============================================================
-- To rollback this migration:
--   DROP TABLE IF EXISTS public.stripe_webhook_events CASCADE;
-- ============================================================
