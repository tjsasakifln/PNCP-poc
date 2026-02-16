-- ============================================================================
-- Migration 028: Fix stripe_webhook_events RLS — Scope Policies to Correct Roles
-- STORY-TD-001: Post-deployment verification (V6) follow-up
-- Date: 2026-02-15
-- ============================================================================
-- Findings from V6 verification:
--   webhook_events_insert_service: roles={public}, WITH CHECK=true
--     → Any authenticated user can insert fake webhook events
--     → Should be service_role only (backend processes Stripe webhooks)
--   webhook_events_select_admin: roles={public}, USING=(is_admin check)
--     → Functional but unnecessarily broad role grant
--     → Should be scoped to authenticated role
-- ============================================================================

-- ============================================================
-- 1. Fix INSERT policy — restrict to service_role only
--    Current: FOR INSERT TO public WITH CHECK (true)
--    Risk: Any authenticated user can insert arbitrary webhook events
--    Fix: Only service_role (backend) can insert
-- ============================================================

DROP POLICY IF EXISTS "webhook_events_insert_service"
  ON public.stripe_webhook_events;

CREATE POLICY "webhook_events_insert_service"
  ON public.stripe_webhook_events
  FOR INSERT
  TO service_role
  WITH CHECK (true);

-- ============================================================
-- 2. Fix SELECT policy — scope to authenticated role
--    Current: FOR SELECT TO public USING (is_admin check)
--    The USING clause is correct but role should be authenticated
--    (anon users can never pass auth.uid() check anyway)
-- ============================================================

DROP POLICY IF EXISTS "webhook_events_select_admin"
  ON public.stripe_webhook_events;

CREATE POLICY "webhook_events_select_admin"
  ON public.stripe_webhook_events
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
        AND profiles.is_admin = true
    )
  );

-- ============================================================
-- 3. Add service_role SELECT for backend diagnostic access
--    Backend may need to query webhook events for retry/debug
-- ============================================================

CREATE POLICY "webhook_events_service_role_select"
  ON public.stripe_webhook_events
  FOR SELECT
  TO service_role
  USING (true);

-- ============================================================
-- Verification (run after applying):
-- ============================================================
-- SELECT policyname, roles, cmd
-- FROM pg_policies
-- WHERE tablename = 'stripe_webhook_events'
-- ORDER BY policyname;
--
-- Expected:
--   webhook_events_insert_service      | {service_role}  | INSERT
--   webhook_events_select_admin        | {authenticated} | SELECT
--   webhook_events_service_role_select | {service_role}  | SELECT
-- ============================================================
