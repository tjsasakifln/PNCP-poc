-- DEBT-001: Database Integrity Critical Fixes
-- DB-013: Fix partner_referrals NOT NULL vs ON DELETE SET NULL conflict
-- DB-038: Fix wrong table names in index migration 20260307100000
-- DB-039: Add user_id index on classification_feedback for RLS
-- DB-012: Consolidate duplicate updated_at trigger functions

-- ══════════════════════════════════════════════════════════════════
-- DB-013: partner_referrals.referred_user_id — DROP NOT NULL
-- The FK was changed to ON DELETE SET NULL in 20260304100000 but the
-- column is still NOT NULL from 20260301200000, making profile
-- deletion fail with constraint violation.
-- ══════════════════════════════════════════════════════════════════
ALTER TABLE public.partner_referrals
  ALTER COLUMN referred_user_id DROP NOT NULL;

-- ══════════════════════════════════════════════════════════════════
-- DB-038: Drop indexes from 20260307100000 that reference wrong tables.
-- Original migration tried to create indexes on non-existent tables:
--   searches    → should be search_sessions
--   pipeline    → should be pipeline_items
--   feedback    → should be classification_feedback
-- The entire 20260307100000 may have failed as a transaction, so
-- these DROP IF EXISTS are defensive.
-- ══════════════════════════════════════════════════════════════════
DROP INDEX IF EXISTS idx_searches_user_id;
DROP INDEX IF EXISTS idx_pipeline_user_id;
DROP INDEX IF EXISTS idx_feedback_user_id;

-- Create correct indexes (IF NOT EXISTS for idempotency)
CREATE INDEX IF NOT EXISTS idx_search_sessions_user_id
  ON public.search_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_items_user_id
  ON public.pipeline_items(user_id);

-- DB-039: classification_feedback user_id index for RLS performance
-- Existing idx_feedback_user_created covers (user_id, created_at)
-- but RLS needs a standalone user_id index for auth.uid() = user_id
-- NOTE: Table may not exist yet in production; create index only if table exists
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'classification_feedback') THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_classification_feedback_user_id ON public.classification_feedback(user_id)';
  END IF;
END
$$;

-- Ensure search_results_store index exists (may have been lost with 20260307100000)
CREATE INDEX IF NOT EXISTS idx_search_results_store_user_id
  ON public.search_results_store(user_id);

-- ══════════════════════════════════════════════════════════════════
-- DB-012: Consolidate duplicate trigger functions
-- update_updated_at() (001_profiles_and_sessions.sql) and
-- set_updated_at() (20260304120000) are identical.
-- Migrate remaining 5 triggers to set_updated_at(), then drop the duplicate.
-- ══════════════════════════════════════════════════════════════════

-- Ensure canonical function exists
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Re-point profiles trigger (from 001_profiles_and_sessions.sql)
DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Re-point plan_features trigger (from 009_create_plan_features.sql)
DROP TRIGGER IF EXISTS plan_features_updated_at ON public.plan_features;
CREATE TRIGGER plan_features_updated_at
  BEFORE UPDATE ON public.plan_features
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Re-point plans trigger (from 020_tighten_plan_type_constraint.sql)
DROP TRIGGER IF EXISTS plans_updated_at ON public.plans;
CREATE TRIGGER plans_updated_at
  BEFORE UPDATE ON public.plans
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Re-point user_subscriptions trigger (from 021_user_subscriptions_updated_at.sql)
DROP TRIGGER IF EXISTS user_subscriptions_updated_at ON public.user_subscriptions;
CREATE TRIGGER user_subscriptions_updated_at
  BEFORE UPDATE ON public.user_subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Re-point organizations trigger (from 20260301100000_create_organizations.sql)
DROP TRIGGER IF EXISTS tr_organizations_updated_at ON public.organizations;
CREATE TRIGGER tr_organizations_updated_at
  BEFORE UPDATE ON public.organizations
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Drop the duplicate function (safe: no triggers reference it anymore)
DROP FUNCTION IF EXISTS public.update_updated_at();
