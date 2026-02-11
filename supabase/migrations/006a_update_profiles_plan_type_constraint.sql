-- ============================================================
-- SmartLic: Update profiles plan_type CHECK constraint
-- Migration: 006_update_profiles_plan_type_constraint
-- Date: 2026-02-06
-- Issue: Admin assign-plan fails because profiles.plan_type_check
--        does not include new plan IDs (consultor_agil, maquina, sala_guerra)
-- ============================================================

-- Drop the old constraint
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_plan_type_check;

-- Add the new constraint with all valid plan types
-- Includes: legacy plans (for backwards compatibility) + new pricing tiers + free_trial
ALTER TABLE public.profiles ADD CONSTRAINT profiles_plan_type_check
  CHECK (plan_type IN (
    -- Legacy plans (backwards compatibility)
    'free',
    'avulso',
    'pack',
    'monthly',
    'annual',
    'master',
    -- New pricing tiers (STORY-165)
    'free_trial',
    'consultor_agil',
    'maquina',
    'sala_guerra'
  ));

-- Migrate existing 'free' users to 'free_trial' (optional - for consistency)
-- Uncomment if you want to standardize on new naming
-- UPDATE public.profiles SET plan_type = 'free_trial' WHERE plan_type = 'free';

-- Verify the constraint was updated correctly
-- SELECT conname, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'public.profiles'::regclass AND conname LIKE '%plan_type%';
