-- ============================================================================
-- COPY AND PASTE THIS SQL INTO SUPABASE DASHBOARD SQL EDITOR
-- ============================================================================
-- Migration 006: Add Service Role Policy for search_sessions
-- Date: 2026-02-10
-- Priority: P0-CRITICAL
-- Deployment Time: ~2 minutes
-- ============================================================================

-- Add service role policy for all operations
DROP POLICY IF EXISTS "Service role can manage search sessions" ON public.search_sessions;
CREATE POLICY "Service role can manage search sessions" ON public.search_sessions
    FOR ALL
    USING (true);

-- Document the policy purpose
COMMENT ON POLICY "Service role can manage search sessions" ON public.search_sessions IS
  'Allows backend service role to insert/update search session history. '
  'Required because backend uses SUPABASE_SERVICE_ROLE_KEY for admin operations. '
  'Without this policy, RLS blocks backend writes even though service role has admin privileges. '
  'Pattern matches monthly_quota table which works correctly with the same policy structure.';

-- ============================================================================
-- VERIFICATION QUERY (run this after to confirm)
-- ============================================================================

SELECT
  schemaname,
  tablename,
  policyname,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename = 'search_sessions'
ORDER BY policyname;

-- Expected output: 3 policies
-- 1. Service role can manage search sessions (NEW) | ALL    | true
-- 2. sessions_insert_own                           | INSERT | (auth.uid() = user_id)
-- 3. sessions_select_own                           | SELECT | (auth.uid() = user_id)

-- ============================================================================
-- ✅ If you see 3 policies above, migration was successful!
-- ============================================================================
