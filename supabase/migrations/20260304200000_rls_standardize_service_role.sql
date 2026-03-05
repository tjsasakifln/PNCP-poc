-- TD-003: RLS Policy Standardization — replace auth.role() with TO service_role
-- Affects 8 tables: alert_preferences, reconciliation_log, organizations,
-- organization_members, classification_feedback, partners, partner_referrals,
-- search_results_store
--
-- Pattern: DROP old policy using auth.role() → CREATE new policy with TO service_role
-- User-facing policies (auth.uid()) are NOT touched.

BEGIN;

-- ══════════════════════════════════════════════════════════════════
-- 1. alert_preferences (H-04)
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Service role full access to alert preferences" ON alert_preferences;

CREATE POLICY "service_role_all" ON alert_preferences
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ══════════════════════════════════════════════════════════════════
-- 2. reconciliation_log (H-05)
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Service role full access reconciliation_log" ON reconciliation_log;

CREATE POLICY "service_role_all" ON reconciliation_log
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ══════════════════════════════════════════════════════════════════
-- 3. organizations (H-06)
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Service role full access on organizations" ON organizations;

CREATE POLICY "service_role_all" ON organizations
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ══════════════════════════════════════════════════════════════════
-- 4. organization_members (H-06)
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Service role full access on organization_members" ON organization_members;

CREATE POLICY "service_role_all" ON organization_members
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ══════════════════════════════════════════════════════════════════
-- 5. classification_feedback (M-09)
-- Note: user-facing policies (feedback_insert_own, feedback_select_own,
-- feedback_update_own, feedback_delete_own) are NOT touched.
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "feedback_admin_all" ON classification_feedback;

CREATE POLICY "service_role_all" ON classification_feedback
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ══════════════════════════════════════════════════════════════════
-- 6. partners (DA-01)
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "partners_service_role" ON partners;

CREATE POLICY "service_role_all" ON partners
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ══════════════════════════════════════════════════════════════════
-- 7. partner_referrals (DA-01)
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "partner_referrals_service_role" ON partner_referrals;

CREATE POLICY "service_role_all" ON partner_referrals
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ══════════════════════════════════════════════════════════════════
-- 8. search_results_store (DA-02)
-- ══════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Service role full access" ON search_results_store;

CREATE POLICY "service_role_all" ON search_results_store
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

COMMIT;

-- ══════════════════════════════════════════════════════════════════
-- Verification queries (run manually after push):
--
-- Should return 0 rows:
-- SELECT schemaname, tablename, policyname, qual
-- FROM pg_policies
-- WHERE schemaname = 'public' AND qual LIKE '%auth.role()%';
--
-- Should return 8+ rows:
-- SELECT tablename, policyname FROM pg_policies
-- WHERE schemaname = 'public' AND roles @> ARRAY['service_role']::name[];
-- ══════════════════════════════════════════════════════════════════
