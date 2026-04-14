-- ============================================================================
-- STORY-2.7 (TD-DB-010) EPIC-TD-2026Q2: Stripe webhook RLS admin policy fix
-- Date: 2026-04-14
-- ============================================================================
-- Context:
--   Migration 010_stripe_webhook_events.sql originally created a SELECT policy
--   checking profiles.plan_type = 'master'. Migration 028 later scoped it to
--   the 'authenticated' role but kept the is_admin check only.
--
--   STORY-415 (2026-04-10) documented that profiles.is_master is NOT a real
--   column — it's a derived value (is_admin OR plan_type = 'master'), see
--   backend/authorization.py:81.
--
--   STORY-2.7 ensures the webhook_events_select_admin policy aligns with the
--   backend "is_master" derivation so both admins (is_admin=true) AND master-
--   plan users (plan_type='master') can read webhook events for debugging
--   payment failures.
--
-- Effect:
--   Replaces webhook_events_select_admin USING clause to accept either
--   is_admin = true OR plan_type = 'master'.
-- ============================================================================

BEGIN;

DROP POLICY IF EXISTS "webhook_events_select_admin" ON public.stripe_webhook_events;

CREATE POLICY "webhook_events_select_admin"
  ON public.stripe_webhook_events
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid()
        AND (profiles.is_admin = true OR profiles.plan_type = 'master')
    )
  );

COMMENT ON POLICY "webhook_events_select_admin" ON public.stripe_webhook_events IS
  'STORY-2.7 (TD-DB-010): admins (is_admin = true) OR master-plan users '
  '(plan_type = ''master'') can read webhook events for payment-failure debug. '
  'Mirrors backend authorization.py derivation: is_master = is_admin OR plan_type = ''master''.';

COMMIT;

-- ============================================================================
-- Verification:
--   SELECT policyname, roles, qual
--   FROM pg_policies
--   WHERE tablename = 'stripe_webhook_events' AND policyname = 'webhook_events_select_admin';
-- ============================================================================
