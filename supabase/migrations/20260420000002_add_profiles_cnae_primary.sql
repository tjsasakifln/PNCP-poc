-- ============================================================================
-- Migration: 20260420000002_add_profiles_cnae_primary
-- Story: STORY-BIZ-002 — Upsell Consultoria Plano (CNAEs 70.2/74.9/82.9)
-- Date: 2026-04-20
--
-- Purpose:
--   Adds a nullable `cnae_primary` text column to profiles so the plan
--   recommendation service can detect consultancy profiles (divisions
--   70.2, 74.9, 82.9) and surface the higher-ARPU Consultoria plan.
--
--   Column is nullable on purpose: legacy profiles don't have CNAE and
--   the recommender defaults to Pro when null. A follow-up story will
--   make the onboarding wizard persist CNAE into this column.
-- ============================================================================

BEGIN;

ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS cnae_primary TEXT;

COMMENT ON COLUMN public.profiles.cnae_primary IS
    'STORY-BIZ-002: primary CNAE of the profile company, in XX.YY-Z/NN or '
    'XX.YY format. Used by services/plan_recommender.py to detect '
    'consultancies. Nullable — null means "no recommendation signal yet".';

-- Partial index for consultancy detection (most profiles are not consultancies).
-- Index only the rows where CNAE starts with a prefix we care about.
CREATE INDEX IF NOT EXISTS idx_profiles_cnae_consultoria
    ON public.profiles (cnae_primary)
    WHERE cnae_primary LIKE '70.2%'
       OR cnae_primary LIKE '74.9%'
       OR cnae_primary LIKE '82.9%';

COMMIT;
