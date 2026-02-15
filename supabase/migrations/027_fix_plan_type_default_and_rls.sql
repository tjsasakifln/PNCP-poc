-- ============================================================================
-- Migration 027: Fix plan_type Column Default + RLS Security Hardening
-- STORY-TD-001: Verificacao de Producao e Migration 027
-- Date: 2026-02-15
-- ============================================================================
-- Fixes:
--   DB-02 (CRITICAL): Column default 'free' violates CHECK constraint from migration 020
--   DB-03 (HIGH/SAFETY): pipeline_items RLS overly permissive — cross-user access
--   DB-04 (HIGH/SAFETY): search_results_cache RLS overly permissive — cross-user access
-- ============================================================================

-- ============================================================
-- 1. DB-02: Fix profiles.plan_type column default
--    Migration 001 set default 'free', but migration 020 removed 'free'
--    from the CHECK constraint. New users would fail INSERT.
-- ============================================================

ALTER TABLE public.profiles
  ALTER COLUMN plan_type SET DEFAULT 'free_trial';

-- ============================================================
-- 2. DB-02: Recreate handle_new_user() trigger with correct default
--    Based on migration 024 version, but ensures plan_type = 'free_trial'
--    is explicitly set (not relying on column default alone)
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id, email, full_name, company, sector,
    phone_whatsapp, whatsapp_consent, plan_type, context_data
  )
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', ''),
    COALESCE(new.raw_user_meta_data->>'company', ''),
    COALESCE(new.raw_user_meta_data->>'sector', ''),
    COALESCE(new.raw_user_meta_data->>'phone_whatsapp', ''),
    COALESCE((new.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    'free_trial',
    '{}'::jsonb
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- 3. DB-03: Fix pipeline_items RLS — scope service role policy
--    Current: FOR ALL USING(true) — ANY authenticated user bypasses
--    per-operation policies because FOR ALL matches all operations.
--    Fix: Restrict service role policy to service_role only.
-- ============================================================

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "Service role full access on pipeline_items"
  ON public.pipeline_items;

-- Recreate scoped to service_role only
CREATE POLICY "Service role full access on pipeline_items"
  ON public.pipeline_items
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- 4. DB-04: Fix search_results_cache RLS — same pattern
--    Current: FOR ALL USING(true) WITH CHECK(true) — any role
--    Fix: Restrict to service_role only.
-- ============================================================

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "Service role full access on search_results_cache"
  ON search_results_cache;

-- Recreate scoped to service_role only
CREATE POLICY "Service role full access on search_results_cache"
  ON search_results_cache
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ============================================================
-- Verification queries (run after applying):
-- ============================================================
-- V6: Verify RLS policies are role-scoped:
--   SELECT policyname, roles, cmd, qual
--   FROM pg_policies
--   WHERE tablename IN ('pipeline_items', 'search_results_cache')
--   ORDER BY tablename, policyname;
--
-- V7: Verify column default is 'free_trial':
--   SELECT column_default
--   FROM information_schema.columns
--   WHERE table_name = 'profiles' AND column_name = 'plan_type';
--
-- V8: Test new user creation:
--   SELECT plan_type FROM profiles ORDER BY created_at DESC LIMIT 1;
-- ============================================================
