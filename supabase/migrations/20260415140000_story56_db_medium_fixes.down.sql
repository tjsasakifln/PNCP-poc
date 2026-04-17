-- ============================================================================
-- DOWN: story56_db_medium_fixes — reverses 20260415140000_story56_db_medium_fixes.sql
-- Date: 2026-04-16
-- Story: STORY-5.6 (TD-DB-012, TD-DB-015, TD-DB-020)
-- ============================================================================
-- Context:
--   Up migration:
--     AC1 (TD-DB-012): Added COMMENT on messages INSERT policy.
--     AC2 (TD-DB-015): Created idx_alert_preferences_digest_scan partial index.
--     AC3 (TD-DB-020): Added is_active BOOLEAN column to audit_events +
--                      partial index idx_audit_events_active.
-- ============================================================================

-- AC3: Drop partial index and column added to audit_events
DROP INDEX IF EXISTS public.idx_audit_events_active;

ALTER TABLE public.audit_events
  DROP COLUMN IF EXISTS is_active;

-- AC2: Drop digest-scan partial index on alert_preferences
DROP INDEX IF EXISTS public.idx_alert_preferences_digest_scan;

-- AC1: Remove COMMENT on messages INSERT policy (no structural change to revert)
-- Policy comment cannot be "dropped" — set to NULL to clear.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename  = 'messages'
      AND policyname = 'insert_messages_authenticated'
  ) THEN
    COMMENT ON POLICY insert_messages_authenticated ON public.messages IS NULL;
  END IF;
END
$$;
