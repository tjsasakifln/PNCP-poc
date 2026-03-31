-- DEBT-207: Trigger Naming Standardization
-- Standardize ALL triggers to use trg_ prefix.
-- PostgreSQL does not support ALTER TRIGGER RENAME, so we DROP + CREATE.
-- Logic is preserved exactly — only the name changes.

-- ══════════════════════════════════════════════════════════════════
-- 1. profiles_updated_at → trg_profiles_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 2. plan_features_updated_at → trg_plan_features_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS plan_features_updated_at ON public.plan_features;
CREATE TRIGGER trg_plan_features_updated_at
  BEFORE UPDATE ON public.plan_features
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 3. plans_updated_at → trg_plans_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS plans_updated_at ON public.plans;
CREATE TRIGGER trg_plans_updated_at
  BEFORE UPDATE ON public.plans
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 4. user_subscriptions_updated_at → trg_user_subscriptions_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS user_subscriptions_updated_at ON public.user_subscriptions;
CREATE TRIGGER trg_user_subscriptions_updated_at
  BEFORE UPDATE ON public.user_subscriptions
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 5. tr_organizations_updated_at → trg_organizations_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS tr_organizations_updated_at ON public.organizations;
CREATE TRIGGER trg_organizations_updated_at
  BEFORE UPDATE ON public.organizations
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 6. tr_pipeline_items_updated_at → trg_pipeline_items_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS tr_pipeline_items_updated_at ON public.pipeline_items;
CREATE TRIGGER trg_pipeline_items_updated_at
  BEFORE UPDATE ON public.pipeline_items
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 7. trigger_alert_preferences_updated_at → trg_alert_preferences_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS trigger_alert_preferences_updated_at ON public.alert_preferences;
CREATE TRIGGER trg_alert_preferences_updated_at
  BEFORE UPDATE ON public.alert_preferences
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 8. trigger_alerts_updated_at → trg_alerts_updated_at
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS trigger_alerts_updated_at ON public.alerts;
CREATE TRIGGER trg_alerts_updated_at
  BEFORE UPDATE ON public.alerts
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ══════════════════════════════════════════════════════════════════
-- 9. trigger_create_alert_preferences_on_profile → trg_create_alert_preferences_on_profile
-- ══════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS trigger_create_alert_preferences_on_profile ON public.profiles;
CREATE TRIGGER trg_create_alert_preferences_on_profile
  AFTER INSERT ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.create_default_alert_preferences();

-- ══════════════════════════════════════════════════════════════════
-- Verification: All triggers should now have trg_ prefix
-- SELECT tgname FROM pg_trigger
-- WHERE tgname !~ '^(trg_|pg_)' AND NOT tgisinternal;
-- Should return 0 rows.
-- ══════════════════════════════════════════════════════════════════

NOTIFY pgrst, 'reload schema';
