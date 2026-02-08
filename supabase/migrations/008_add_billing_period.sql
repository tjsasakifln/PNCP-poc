-- ============================================================
-- SmartLic: Annual Subscriptions - Add billing_period
-- Migration: 008_add_billing_period
-- Date: 2026-02-07
-- Story: STORY-171
-- ============================================================

-- Add billing_period column to user_subscriptions (NOT subscriptions!)
-- Default to 'monthly' to maintain backward compatibility
ALTER TABLE public.user_subscriptions
  ADD COLUMN billing_period VARCHAR(10) NOT NULL DEFAULT 'monthly'
    CHECK (billing_period IN ('monthly', 'annual'));

COMMENT ON COLUMN public.user_subscriptions.billing_period IS 'Billing cycle: monthly or annual';

-- Add annual_benefits column to store annual-exclusive features
-- JSONB format: {"early_access": true, "proactive_search": true, ...}
ALTER TABLE public.user_subscriptions
  ADD COLUMN annual_benefits JSONB NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN public.user_subscriptions.annual_benefits IS 'JSON object storing annual-exclusive benefits';

-- Backfill existing annual plans
-- Identify annual subscriptions by plan_id = 'annual' (legacy)
UPDATE public.user_subscriptions
SET billing_period = 'annual'
WHERE plan_id = 'annual' AND is_active = true;

-- Performance index for common query pattern
-- Covers: SELECT ... WHERE user_id = ? AND billing_period = ? AND is_active = true
CREATE INDEX idx_user_subscriptions_billing
  ON public.user_subscriptions(user_id, billing_period, is_active)
  WHERE is_active = true;

COMMENT ON INDEX idx_user_subscriptions_billing IS 'Optimize queries filtering by user_id, billing_period, and active status';

-- Verify migration
-- Expected: All rows have valid billing_period ('monthly' or 'annual')
DO $$
DECLARE
  invalid_count INT;
BEGIN
  SELECT COUNT(*) INTO invalid_count
  FROM public.user_subscriptions
  WHERE billing_period NOT IN ('monthly', 'annual');

  IF invalid_count > 0 THEN
    RAISE EXCEPTION 'Migration validation failed: % rows have invalid billing_period', invalid_count;
  END IF;

  RAISE NOTICE 'Migration 008 completed successfully';
END $$;
