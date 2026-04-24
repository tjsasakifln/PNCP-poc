-- STORY-415: Fix prevent_privilege_escalation trigger referencing non-existent is_master column.
--
-- Incident (2026-04-10, Sentry issue 7388075442, 6+ events):
--   Migration 20260404000000_security_hardening_rpc_rls.sql created a trigger
--   that referenced `NEW.is_master IS DISTINCT FROM OLD.is_master`, but
--   `is_master` is NOT a column on `profiles`. It is derived at runtime in
--   backend/authorization.py:81 as `is_master = is_admin or plan_type == "master"`.
--
-- Impact:
--   Every UPDATE on `profiles` raised `record "new" has no field "is_master"`
--   (SQLSTATE 42703), blocking:
--     - stripe_reconciliation cron (profile sync for subscription changes)
--     - /admin/users/{id}/assign-plan endpoint
--     - any code path that UPDATEs profiles row
--
-- Decision (@pm 2026-04-10): Option B — remove `is_master` from the trigger
-- body. Protecting `is_admin` and `plan_type` is sufficient because:
--   - `is_master` is derived exclusively from (is_admin, plan_type) in the
--     backend authorization layer (see authorization.py:81).
--   - Mutating either source field already triggers the escalation guard, so
--     the derived value is protected by transitivity.
--   - There is no storage of `is_master` to protect independently.
--
-- See also: STORY-414 for the schema contract gate hardening that will detect
-- this class of drift on startup.

CREATE OR REPLACE FUNCTION public.prevent_privilege_escalation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
BEGIN
    -- STORY-415: `is_master` is DERIVED from (is_admin, plan_type) at the
    -- application layer (backend/authorization.py:81). Protecting those two
    -- columns protects the derived value by transitivity.
    IF (NEW.is_admin IS DISTINCT FROM OLD.is_admin) OR
       (NEW.plan_type IS DISTINCT FROM OLD.plan_type) THEN

        -- Allow service_role (backend) to modify these fields
        v_role := coalesce(
            current_setting('request.jwt.claim.role', true),
            current_setting('role', true)
        );

        IF v_role IS DISTINCT FROM 'service_role' THEN
            RAISE EXCEPTION
                'Cannot modify protected fields (is_admin, plan_type). Use the application API.'
                USING ERRCODE = '42501';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.prevent_privilege_escalation() IS
    'STORY-415 (2026-04-10): protects is_admin and plan_type from direct PATCH. '
    'is_master is derived (not stored) so it is NOT checked here — see '
    'backend/authorization.py:81. Superseded from 20260404000000 which '
    'referenced NEW.is_master and caused 42703 errors in production.';

-- No need to DROP/CREATE the trigger — CREATE OR REPLACE FUNCTION reuses
-- the existing `protect_profiles_escalation` binding (which itself was
-- created by 20260404000000 as `BEFORE UPDATE ON profiles FOR EACH ROW`).
