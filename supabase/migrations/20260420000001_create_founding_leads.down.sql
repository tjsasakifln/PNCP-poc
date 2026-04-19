-- ============================================================================
-- Rollback for 20260420000001_create_founding_leads
-- ============================================================================

BEGIN;

DROP POLICY IF EXISTS "founding_leads_service_write" ON public.founding_leads;
DROP POLICY IF EXISTS "founding_leads_admin_read" ON public.founding_leads;
DROP INDEX IF EXISTS idx_founding_leads_session_id;
DROP INDEX IF EXISTS idx_founding_leads_status;
DROP INDEX IF EXISTS idx_founding_leads_email;
DROP TABLE IF EXISTS public.founding_leads;

COMMIT;
