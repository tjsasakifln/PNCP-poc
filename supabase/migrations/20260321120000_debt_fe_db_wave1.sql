-- DEBT Wave 1 PR1: Security & Accessibility database fixes
-- DEBT-DB-006: Add RLS SELECT policy for trial_email_log
-- DEBT-DB-020: Verify composite index on search_sessions (already exists as idx_search_sessions_created)
-- DEBT-DB-002: Ensure classification_feedback FK to profiles exists (idempotent)

-- ============================================================
-- DEBT-DB-006: trial_email_log RLS SELECT policy
-- Table has RLS enabled but NO user-facing policies.
-- Add SELECT so users can view their own trial email logs.
-- ============================================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'trial_email_log'
      AND policyname = 'Users can view own trial emails'
  ) THEN
    CREATE POLICY "Users can view own trial emails"
      ON public.trial_email_log
      FOR SELECT
      USING (auth.uid() = user_id);
  END IF;
END $$;

-- ============================================================
-- DEBT-DB-020: Composite index on search_sessions(user_id, created_at DESC)
-- NOTE: This index already exists as idx_search_sessions_created from migration 001.
-- Creating with the requested name as an alias for documentation clarity.
-- IF NOT EXISTS prevents errors if the index already covers this.
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_search_sessions_user_created
  ON public.search_sessions(user_id, created_at DESC);

-- ============================================================
-- DEBT-DB-002: Ensure classification_feedback FK references profiles(id)
-- The FK was standardized in 20260225120000_standardize_fks_to_profiles.sql
-- but only runs if the table existed at that time. This is a safety net.
-- ============================================================
DO $$
BEGIN
  -- Only proceed if the table exists
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'classification_feedback'
  ) THEN
    -- Check if the profiles FK already exists
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.table_constraints
      WHERE constraint_name = 'classification_feedback_user_id_profiles_fkey'
        AND table_name = 'classification_feedback'
    ) THEN
      -- Drop old auth.users FK if it exists
      IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'classification_feedback_user_id_fkey'
          AND table_name = 'classification_feedback'
      ) THEN
        ALTER TABLE public.classification_feedback
          DROP CONSTRAINT classification_feedback_user_id_fkey;
      END IF;

      -- Add FK to profiles(id) with CASCADE
      ALTER TABLE public.classification_feedback
        ADD CONSTRAINT classification_feedback_user_id_profiles_fkey
        FOREIGN KEY (user_id) REFERENCES public.profiles(id)
        ON DELETE CASCADE NOT VALID;

      -- Validate separately (non-blocking)
      ALTER TABLE public.classification_feedback
        VALIDATE CONSTRAINT classification_feedback_user_id_profiles_fkey;
    END IF;
  END IF;
END $$;
