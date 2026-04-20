-- ============================================================================
-- Migration: 20260420000003_add_profiles_stripe_default_pm_id
-- Story: STORY-CONV-003a — Backend Signup + Stripe Customer + Subscription
-- Date: 2026-04-20
--
-- Purpose:
--   Adds `stripe_default_pm_id` column to profiles so the signup+card flow
--   (CONV-003a AC2) can persist the Stripe PaymentMethod ID that was attached
--   to the Customer and set as the subscription's default PM.
--
--   `profiles.stripe_customer_id` and `profiles.stripe_subscription_id` already
--   exist (migration 001). This migration only adds the PM reference so trial
--   expiry can charge the card without round-tripping Stripe's Customer API.
--
--   Column is nullable because (a) legacy profiles have no card, and (b) the
--   cartão-obrigatório flow is rolled out gradually via feature flag
--   TRIAL_REQUIRE_CARD_ROLLOUT_PCT (introduced in CONV-003b).
--
-- Scaffolding-only migration: CONV-003a full Stripe integration (AC1/AC4) is
-- deferred to the next session. This migration is safe to ship now because
-- the column is nullable and unused until backend writes to it.
-- ============================================================================

BEGIN;

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS stripe_default_pm_id TEXT;

COMMENT ON COLUMN public.profiles.stripe_default_pm_id IS
    'STORY-CONV-003a: Stripe PaymentMethod ID attached to the Customer and '
    'used as the subscription default payment method. Set at signup when '
    'TRIAL_REQUIRE_CARD_ROLLOUT_PCT is active; null for legacy users and '
    'users who signed up before the feature flag was enabled.';

-- Partial index for billing reconciliation (most profiles won't have a PM
-- during rollout ramp-up).
CREATE INDEX IF NOT EXISTS idx_profiles_stripe_default_pm_id
    ON public.profiles (stripe_default_pm_id)
    WHERE stripe_default_pm_id IS NOT NULL;

COMMIT;
