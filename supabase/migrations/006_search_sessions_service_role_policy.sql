-- ============================================================================
-- Migration 006: Add Service Role Policy for search_sessions
-- ============================================================================
-- Date: 2026-02-10
-- Priority: P0-CRITICAL
-- Issue: Backend writes to search_sessions blocked by RLS
--
-- Problem:
-- - search_sessions table has RLS enabled
-- - Only has user-level policies (auth.uid() = user_id)
-- - Backend uses SUPABASE_SERVICE_ROLE_KEY (admin client)
-- - Service role context has auth.uid() = NULL
-- - Result: INSERT operations blocked by RLS
--
-- Solution:
-- - Add explicit service role policy with USING (true)
-- - Matches pattern from monthly_quota table (working correctly)
-- - Allows backend to insert/manage search history
--
-- Impact:
-- - Fixes search history save failures (all users affected)
-- - Enables /historico page to show search history
-- - No schema changes, only policy addition
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

-- Verification query (run after migration)
-- SELECT
--   schemaname,
--   tablename,
--   policyname,
--   roles,
--   cmd,
--   qual,
--   with_check
-- FROM pg_policies
-- WHERE tablename = 'search_sessions'
-- ORDER BY policyname;
--
-- Expected output:
-- | policyname                                   | cmd    | qual                    |
-- |----------------------------------------------|--------|-------------------------|
-- | Service role can manage search sessions      | ALL    | true                    |
-- | sessions_insert_own                          | INSERT | (auth.uid() = user_id)  |
-- | sessions_select_own                          | SELECT | (auth.uid() = user_id)  |
