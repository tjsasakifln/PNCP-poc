-- ============================================================================
-- Migration 020: Tighten plan_type Constraint + Add profiles INSERT Policy
-- STORY-203 Track 1: Database Cleanup
-- Date: 2026-02-12
-- ============================================================================
-- This migration combines:
--   DB-M02: Remove legacy plan_type values from CHECK constraint
--   DB-H05: Add INSERT policy on profiles table for security hygiene
--   DB-L01: Add updated_at column to plans table
-- ============================================================================

-- ============================================================
-- 1. DB-M02: Tighten plan_type CHECK constraint
--    Remove legacy values: 'free', 'avulso', 'pack', 'monthly', 'annual'
--    Keep only: 'free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master'
-- ============================================================

-- CRITICAL: Migrate existing legacy plan_type values BEFORE dropping constraint
-- Map legacy values to current equivalents:
--   'free' → 'free_trial'
--   'monthly' → 'consultor_agil' (lowest paid tier)
--   'annual' → 'consultor_agil' (lowest paid tier)
--   'avulso', 'pack' → 'free_trial' (single purchase plans deprecated)

UPDATE public.profiles
SET plan_type = 'free_trial'
WHERE plan_type IN ('free', 'avulso', 'pack');

UPDATE public.profiles
SET plan_type = 'consultor_agil'
WHERE plan_type IN ('monthly', 'annual');

-- Drop the old constraint
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_plan_type_check;

-- Add the new constraint with ONLY current plan types
-- This removes legacy values for cleaner schema and prevents accidental usage
ALTER TABLE public.profiles ADD CONSTRAINT profiles_plan_type_check
  CHECK (plan_type IN (
    'free_trial',      -- Trial plan (default for new users)
    'consultor_agil',  -- Tier 1: 25 searches/month
    'maquina',         -- Tier 2: 100 searches/month
    'sala_guerra',     -- Tier 3: Unlimited searches
    'master'           -- Admin/internal accounts
  ));

COMMENT ON CONSTRAINT profiles_plan_type_check ON public.profiles IS
  'Only current plan types allowed. Legacy values (free, monthly, annual, avulso, pack) removed in migration 020.';

-- ============================================================
-- 2. DB-H05: Add INSERT policy on profiles table
--    Good security hygiene even though handle_new_user() runs
--    as SECURITY DEFINER (which bypasses RLS)
-- ============================================================

-- Allow authenticated users to insert their own profile
-- (In practice, handle_new_user trigger creates profiles, but this
-- provides defense-in-depth and allows manual profile creation if needed)
DROP POLICY IF EXISTS "profiles_insert_own" ON public.profiles;
CREATE POLICY "profiles_insert_own" ON public.profiles
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

-- Service role can insert any profile (admin operations, migrations, etc.)
DROP POLICY IF EXISTS "profiles_insert_service" ON public.profiles;
CREATE POLICY "profiles_insert_service" ON public.profiles
  FOR INSERT
  TO service_role
  WITH CHECK (true);

-- ============================================================
-- 3. DB-L01: Add updated_at to plans table
--    Tracks when plan metadata (price, limits, etc.) was last modified
-- ============================================================

ALTER TABLE public.plans
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- Create trigger to auto-update updated_at on changes
DROP TRIGGER IF EXISTS plans_updated_at ON public.plans;
CREATE TRIGGER plans_updated_at
  BEFORE UPDATE ON public.plans
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

COMMENT ON COLUMN public.plans.updated_at IS
  'Timestamp of last plan metadata update. Useful for cache invalidation and change tracking.';

-- ============================================================================
-- Verification queries (run after applying):
-- ============================================================================
-- 1. Check plan_type constraint only includes current values:
--    SELECT pg_get_constraintdef(oid) FROM pg_constraint
--    WHERE conname = 'profiles_plan_type_check' AND conrelid = 'public.profiles'::regclass;
--
-- 2. Verify no legacy plan_type values remain:
--    SELECT plan_type, COUNT(*) FROM public.profiles GROUP BY plan_type;
--
-- 3. Check INSERT policies exist:
--    SELECT policyname, roles, cmd FROM pg_policies WHERE tablename = 'profiles' AND cmd = 'INSERT';
--
-- 4. Verify plans.updated_at column exists with trigger:
--    SELECT column_name, data_type FROM information_schema.columns
--    WHERE table_name = 'plans' AND column_name = 'updated_at';
--
--    SELECT tgname FROM pg_trigger WHERE tgrelid = 'public.plans'::regclass;
-- ============================================================================
