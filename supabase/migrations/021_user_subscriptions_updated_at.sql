-- ============================================================================
-- Migration 021: user_subscriptions updated_at + Stripe Price ID Documentation
-- STORY-203 Track 1: Database Cleanup
-- Date: 2026-02-12
-- ============================================================================
-- This migration combines:
--   DB-M03: Add updated_at column to user_subscriptions table
--   DB-M05: Document that Stripe price IDs should be environment-aware
-- ============================================================================

-- ============================================================
-- 1. DB-M03: Add updated_at to user_subscriptions
--    Tracks when subscription metadata changes (plan_id, credits, etc.)
--    Essential for audit trails and debugging subscription issues
-- ============================================================

ALTER TABLE public.user_subscriptions
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Create trigger to auto-update updated_at on changes
DROP TRIGGER IF EXISTS user_subscriptions_updated_at ON public.user_subscriptions;
CREATE TRIGGER user_subscriptions_updated_at
  BEFORE UPDATE ON public.user_subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

COMMENT ON COLUMN public.user_subscriptions.updated_at IS
  'Timestamp of last subscription update. Critical for audit trails and debugging.';

-- ============================================================
-- 2. DB-M05: Document Stripe Price ID environment awareness
--    IMPORTANT: Migration 015 hardcodes production Stripe price IDs.
--    For staging/development environments, these should be replaced
--    with test mode price IDs from Stripe Dashboard.
-- ============================================================

COMMENT ON COLUMN public.plans.stripe_price_id_monthly IS
  'Stripe monthly price ID. WARNING: Migration 015 uses PRODUCTION IDs (price_1Sy...). For staging/dev, manually update with TEST mode price IDs from Stripe Dashboard.';

COMMENT ON COLUMN public.plans.stripe_price_id_annual IS
  'Stripe annual price ID. WARNING: Migration 015 uses PRODUCTION IDs (price_1Sz...). For staging/dev, manually update with TEST mode price IDs from Stripe Dashboard.';

COMMENT ON COLUMN public.plans.stripe_price_id IS
  'Legacy Stripe price ID column (defaults to monthly). WARNING: Migration 015 uses PRODUCTION IDs. For staging/dev, manually update with TEST mode price IDs.';

-- ============================================================================
-- Environment-Specific Price ID Setup Instructions
-- ============================================================================
--
-- PRODUCTION (already configured in migration 015):
--   consultor_agil: price_1Syir09FhmvPslGYOCbOvWVB (monthly), price_1SzRAC9FhmvPslGYLBuYTaSa (annual)
--   maquina:        price_1Syirk9FhmvPslGY1kbNWxaz (monthly), price_1SzR8F9FhmvPslGYDW84AzYA (annual)
--   sala_guerra:    price_1Syise9FhmvPslGYAR8Fbf5E (monthly), price_1SzR5c9FhmvPslGYQym74G6K (annual)
--
-- STAGING/DEVELOPMENT:
--   1. Create test mode prices in Stripe Dashboard (https://dashboard.stripe.com/test/prices)
--   2. Copy price IDs (they start with "price_" in test mode too)
--   3. Run manual UPDATE to replace production price IDs:
--
--   UPDATE public.plans SET
--     stripe_price_id_monthly = 'price_TEST_consultor_agil_monthly',
--     stripe_price_id_annual  = 'price_TEST_consultor_agil_annual',
--     stripe_price_id         = 'price_TEST_consultor_agil_monthly'
--   WHERE id = 'consultor_agil';
--
--   (Repeat for 'maquina' and 'sala_guerra')
--
-- RECOMMENDATION:
--   Future enhancement: Store price IDs in environment variables or a separate
--   config table (plans_stripe_config) to avoid hardcoding in migrations.
--
-- ============================================================================

-- ============================================================================
-- Verification queries (run after applying):
-- ============================================================================
-- 1. Verify updated_at column exists with trigger:
--    SELECT column_name, data_type, column_default
--    FROM information_schema.columns
--    WHERE table_name = 'user_subscriptions' AND column_name = 'updated_at';
--
--    SELECT tgname FROM pg_trigger
--    WHERE tgrelid = 'public.user_subscriptions'::regclass;
--
-- 2. Check Stripe price ID comments were added:
--    SELECT col_description('public.plans'::regclass, attnum) AS comment
--    FROM pg_attribute
--    WHERE attrelid = 'public.plans'::regclass
--      AND attname IN ('stripe_price_id', 'stripe_price_id_monthly', 'stripe_price_id_annual');
-- ============================================================================
