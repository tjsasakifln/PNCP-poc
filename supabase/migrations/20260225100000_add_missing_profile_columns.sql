-- ============================================================================
-- Migration: 20260225100000_add_missing_profile_columns.sql
-- Story: STORY-261 — Database Schema Integrity — Missing Columns
-- Date: 2026-02-25
-- Author: AIOS Development Team
--
-- Summary:
-- 5 columns exist in production (added via Supabase Dashboard) but have no
-- migration. In a disaster-recovery scenario (DB recreation from migrations),
-- Stripe billing, analytics, trial status, subscription cancel, and email
-- opt-out would break. This migration codifies them for enterprise-grade
-- reliability.
--
-- All operations are idempotent:
--   - ADD COLUMN IF NOT EXISTS for columns
--   - DROP CONSTRAINT IF EXISTS + ADD CONSTRAINT for checks
--   - CREATE INDEX IF NOT EXISTS for indexes
-- ============================================================================

BEGIN;

-- ============================================================
-- 1. profiles.subscription_status (T1-01)
--    Tracks current subscription state for billing & analytics
-- ============================================================

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'trial';

-- Idempotent constraint: drop then recreate
ALTER TABLE public.profiles
    DROP CONSTRAINT IF EXISTS chk_profiles_subscription_status;
ALTER TABLE public.profiles
    ADD CONSTRAINT chk_profiles_subscription_status
    CHECK (subscription_status IN ('trial', 'active', 'canceling', 'past_due', 'expired'));

-- Partial index for non-default values (faster billing queries)
CREATE INDEX IF NOT EXISTS idx_profiles_subscription_status
    ON public.profiles (subscription_status)
    WHERE subscription_status != 'trial';

-- ============================================================
-- 2. profiles.trial_expires_at (T1-02)
--    When the user's trial period expires
-- ============================================================

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ;

-- ============================================================
-- 3. profiles.subscription_end_date (T1-05)
--    When a canceled subscription actually ends
-- ============================================================

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMPTZ;

-- ============================================================
-- 4. profiles.email_unsubscribed + email_unsubscribed_at (T1-06)
--    LGPD compliance — user email opt-out
-- ============================================================

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS email_unsubscribed BOOLEAN DEFAULT FALSE;

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS email_unsubscribed_at TIMESTAMPTZ;

-- ============================================================
-- 5. user_subscriptions.subscription_status (T1-03)
--    Subscription-level status (mirrors Stripe subscription state)
-- ============================================================

ALTER TABLE public.user_subscriptions
    ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'active';

-- Idempotent constraint: drop then recreate
ALTER TABLE public.user_subscriptions
    DROP CONSTRAINT IF EXISTS chk_user_subs_subscription_status;
ALTER TABLE public.user_subscriptions
    ADD CONSTRAINT chk_user_subs_subscription_status
    CHECK (subscription_status IN ('active', 'trialing', 'past_due', 'canceled', 'expired'));

COMMIT;

-- ============================================================================
-- Verification queries (run after applying):
-- ============================================================================
-- 1. Check profiles columns:
--    SELECT column_name, data_type, column_default
--    FROM information_schema.columns
--    WHERE table_name = 'profiles'
--      AND column_name IN ('subscription_status', 'trial_expires_at',
--                          'subscription_end_date', 'email_unsubscribed',
--                          'email_unsubscribed_at');
--
-- 2. Check user_subscriptions column:
--    SELECT column_name, data_type, column_default
--    FROM information_schema.columns
--    WHERE table_name = 'user_subscriptions'
--      AND column_name = 'subscription_status';
--
-- 3. Check constraints:
--    SELECT conname, pg_get_constraintdef(oid)
--    FROM pg_constraint
--    WHERE conname IN ('chk_profiles_subscription_status',
--                      'chk_user_subs_subscription_status');
--
-- 4. Check index:
--    SELECT indexname, indexdef FROM pg_indexes
--    WHERE indexname = 'idx_profiles_subscription_status';
-- ============================================================================
