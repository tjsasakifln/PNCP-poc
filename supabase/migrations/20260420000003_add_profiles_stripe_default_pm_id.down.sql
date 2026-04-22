-- ============================================================================
-- Down migration: 20260420000003_add_profiles_stripe_default_pm_id
-- Story: STORY-CONV-003a
-- Date: 2026-04-20
--
-- Reverts addition of profiles.stripe_default_pm_id column and its index.
-- Safe to run: column is nullable, no foreign keys, no triggers depend on it.
-- ============================================================================

BEGIN;

DROP INDEX IF EXISTS public.idx_profiles_stripe_default_pm_id;

ALTER TABLE public.profiles
    DROP COLUMN IF EXISTS stripe_default_pm_id;

COMMIT;
