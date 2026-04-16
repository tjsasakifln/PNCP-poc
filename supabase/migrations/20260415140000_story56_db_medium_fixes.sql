-- ============================================================================
-- Migration: STORY-5.6 DB Medium Fixes Bundle (EPIC-TD-2026Q2 P2)
-- Date: 2026-04-15
-- ACs: AC1 (TD-DB-012), AC2 (TD-DB-015), AC3 (TD-DB-020)
-- ============================================================================

-- ============================================================
-- AC1 (TD-DB-012): COMMENT on messages INSERT policy
-- Explains the triple-nested EXISTS pattern for future maintainers.
-- Policy was renamed from 'messages_insert_user' to
-- 'insert_messages_authenticated' in migration 20260331200000.
-- ============================================================

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename  = 'messages'
      AND policyname = 'insert_messages_authenticated'
  ) THEN
    COMMENT ON POLICY insert_messages_authenticated ON public.messages IS
      'INSERT guard: sender must be auth.uid(). '
      'Triple-nested EXISTS validates that the target conversation belongs to '
      'the sender (c.user_id = auth.uid()) OR the sender is an admin '
      '(profiles.is_admin = true). This prevents users from injecting messages '
      'into conversations they do not own.';
  END IF;
END
$$;

-- ============================================================
-- AC2 (TD-DB-015): Digest scan index on alert_preferences
-- Optimized for the cron job that scans users due for digest:
--   SELECT ... WHERE enabled AND frequency != 'off'
--     AND last_digest_sent_at < now() - interval ...
-- Puts last_digest_sent_at first for efficient range scans.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_alert_preferences_digest_scan
  ON public.alert_preferences (last_digest_sent_at, frequency)
  WHERE enabled = true AND frequency != 'off';

-- ============================================================
-- AC3 (TD-DB-020): Soft-delete flag on audit_events (LGPD)
-- Allows marking records as inactive instead of hard-deleting,
-- preserving audit trail integrity while honoring erasure requests.
-- ============================================================

ALTER TABLE public.audit_events
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

COMMENT ON COLUMN public.audit_events.is_active IS
  'Soft-delete flag for LGPD/GDPR erasure requests. '
  'When false, the row is logically deleted but preserved for audit integrity. '
  'Queries should filter WHERE is_active = true unless reviewing full history.';

-- Partial index for active-only queries (most common access pattern)
CREATE INDEX IF NOT EXISTS idx_audit_events_active
  ON public.audit_events (timestamp DESC)
  WHERE is_active = true;

-- ============================================================
-- Verification queries
-- ============================================================
-- 1. Check policy comment:
--    SELECT obj_description(p.oid) FROM pg_policy p
--    JOIN pg_class c ON p.polrelid = c.oid
--    WHERE c.relname = 'messages' AND p.polname = 'insert_messages_authenticated';
--
-- 2. Check digest_scan index:
--    SELECT indexname FROM pg_indexes WHERE indexname = 'idx_alert_preferences_digest_scan';
--
-- 3. Check is_active column:
--    SELECT column_name, data_type, column_default
--    FROM information_schema.columns
--    WHERE table_name = 'audit_events' AND column_name = 'is_active';
-- ============================================================
