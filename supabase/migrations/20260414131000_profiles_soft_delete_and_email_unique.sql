-- ============================================================================
-- STORY-2.8 (TD-DB-011) EPIC-TD-2026Q2: profiles soft-delete + email uniqueness
-- Date: 2026-04-14
-- ============================================================================
-- Context:
--   TD-DB-011 requires:
--     AC1: Dedup script idempotente (DRY-RUN default) — see
--          backend/scripts/dedup_profiles_email.py
--     AC2: Audit log via audit_events (event_type='profile_dedup_merged')
--     AC3: UNIQUE on profiles.email enforced at DB layer
--     AC4: Frontend defensive check on signup (already implemented by
--          STORY-258 /auth/check-email + disposable-only design to avoid
--          enumeration). This migration adds the missing soft-delete columns
--          used by the dedup script so loser profiles are archived — not
--          physically removed — preserving auth.users referential integrity.
--
--   20260224000000_phone_email_unique.sql already created a partial unique
--   index (idx_profiles_email_unique) scoped to WHERE email IS NOT NULL.
--   That satisfies AC3 for all non-NULL emails. This migration complements
--   it with:
--     - deleted_at / deleted_reason columns (soft-delete support)
--     - a migrated_to column (pointer back to the winner after dedup)
--     - an INDEX on deleted_at to speed up "active profiles" queries
--
--   NOTE: we deliberately do NOT add a second UNIQUE CONSTRAINT on email,
--         because:
--           * The existing partial unique index already enforces uniqueness
--             on non-NULL rows.
--           * Supabase auth.users is the source of truth for emails; profiles
--             is a 1:1 mirror guarded by handle_new_user() + idx_profiles_email_unique.
--           * A plain UNIQUE constraint on a nullable column behaves like the
--             existing partial index anyway (multiple NULLs allowed in PG).
-- ============================================================================

BEGIN;

-- 1. Soft-delete columns (idempotent)
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS deleted_at     timestamptz,
  ADD COLUMN IF NOT EXISTS deleted_reason text,
  ADD COLUMN IF NOT EXISTS migrated_to    uuid REFERENCES public.profiles(id) ON DELETE SET NULL;

COMMENT ON COLUMN public.profiles.deleted_at IS
  'STORY-2.8: soft-delete timestamp. NULL = active profile. '
  'Physical deletion is avoided to preserve auth.users referential integrity.';

COMMENT ON COLUMN public.profiles.deleted_reason IS
  'STORY-2.8: free-text reason for soft-delete '
  '(e.g. ''dedup_merged_to_<uuid>''). Read by audit tooling.';

COMMENT ON COLUMN public.profiles.migrated_to IS
  'STORY-2.8: when a profile is merged into another (dedup), this points '
  'to the winner id. NULL otherwise. ON DELETE SET NULL keeps history '
  'readable even if the winner is later deleted.';

-- 2. Index for fast "active users" lookups (partial, only non-deleted rows)
CREATE INDEX IF NOT EXISTS idx_profiles_active
  ON public.profiles (id)
  WHERE deleted_at IS NULL;

-- 3. Ensure idx_profiles_email_unique exists (defence-in-depth; migration
--    20260224000000 may not have run on every environment yet).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes WHERE indexname = 'idx_profiles_email_unique'
  ) THEN
    CREATE UNIQUE INDEX idx_profiles_email_unique
      ON public.profiles (email)
      WHERE email IS NOT NULL;
  END IF;
END $$;

COMMENT ON INDEX public.idx_profiles_email_unique IS
  'STORY-258 AC5 / STORY-2.8 AC3: defence-in-depth UNIQUE on profiles.email '
  '(auth.users is source of truth). Partial index — NULLs allowed but very '
  'rare in practice since handle_new_user() always copies auth.users.email.';

COMMIT;

-- ============================================================================
-- Verification:
--   SELECT column_name, is_nullable FROM information_schema.columns
--   WHERE table_name = 'profiles'
--     AND column_name IN ('deleted_at', 'deleted_reason', 'migrated_to');
--
--   SELECT indexname FROM pg_indexes WHERE tablename = 'profiles'
--   AND indexname IN ('idx_profiles_email_unique', 'idx_profiles_active');
-- ============================================================================
