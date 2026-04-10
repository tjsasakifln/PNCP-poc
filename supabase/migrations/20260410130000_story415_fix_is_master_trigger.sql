-- STORY-415: Fix prevent_privilege_escalation trigger referencing non-existent is_master column.
--
-- Context:
--   Migration 20260404000000_security_hardening_rpc_rls.sql introduced a
--   trigger that guards profiles.is_admin, profiles.is_master and
--   profiles.plan_type against direct PostgREST PATCH. However,
--   profiles.is_master never existed as a column — is_master is derived
--   in the backend (backend/authorization.py:81) from
--       is_master = is_admin OR plan_type == 'master'
--   so every UPDATE on profiles failed with:
--       record "new" has no field "is_master"  (SQLSTATE 42703)
--
--   This blocked stripe_reconciliation.py + admin.assign_plan() flows,
--   generating Sentry issue 7388075442 (6+ events on 2026-04-10).
--
-- Decision (@pm 2026-04-10, Opção B):
--   Remove the NEW.is_master reference entirely. The guard still covers
--   both primary privilege knobs:
--     - is_admin (the real admin flag)
--     - plan_type (the "master" plan is derived from this)
--   No backend refactor needed because is_master is already derived.
--
-- This migration replaces the function body only; the trigger itself is
-- already attached to the profiles table by the earlier migration.
--
-- Rollback: `DROP FUNCTION public.prevent_privilege_escalation()` followed
-- by re-running 20260404000000 would restore the broken version — but
-- rolling back is NOT recommended because it reintroduces the crash.

CREATE OR REPLACE FUNCTION public.prevent_privilege_escalation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
BEGIN
    -- STORY-415: Removed NEW.is_master / OLD.is_master references.
    -- is_master is a DERIVED field (see backend/authorization.py:81),
    -- not a real column on profiles. Including it here raised
    --     42703: record "new" has no field "is_master"
    -- on every profiles UPDATE, blocking Stripe reconciliation and the
    -- admin plan assignment UI. The guard still protects is_admin and
    -- plan_type, which together determine is_master transitively.
    IF (NEW.is_admin IS DISTINCT FROM OLD.is_admin) OR
       (NEW.plan_type IS DISTINCT FROM OLD.plan_type) THEN

        -- Allow service_role (backend) to modify these fields
        v_role := coalesce(
            current_setting('request.jwt.claim.role', true),
            current_setting('role', true)
        );

        IF v_role IS DISTINCT FROM 'service_role' THEN
            RAISE EXCEPTION 'Cannot modify protected fields (is_admin, plan_type). Use the application API.'
                USING ERRCODE = '42501';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

-- The trigger was created by 20260404000000 and is already attached to
-- the profiles table — a CREATE OR REPLACE FUNCTION picks up the new body
-- without re-binding the trigger. But re-bind it idempotently as a
-- defensive measure in case the earlier migration never reached the
-- target environment for any reason.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'protect_profiles_escalation'
    ) THEN
        CREATE TRIGGER protect_profiles_escalation
            BEFORE UPDATE ON public.profiles
            FOR EACH ROW
            EXECUTE FUNCTION public.prevent_privilege_escalation();
    END IF;
END $$;
