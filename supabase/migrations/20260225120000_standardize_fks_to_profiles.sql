-- STORY-264 AC1-AC3: Standardize FK references to profiles(id)
-- Repoints user_id FKs from auth.users(id) to profiles(id) ON DELETE CASCADE
-- for: pipeline_items, classification_feedback, trial_email_log.
-- Uses NOT VALID + VALIDATE for non-blocking production application.

-- ============================================================
-- 1. pipeline_items (AC1)
-- ============================================================
DO $$
BEGIN
    -- Drop old FK referencing auth.users
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'pipeline_items_user_id_fkey'
        AND table_name = 'pipeline_items'
    ) THEN
        ALTER TABLE pipeline_items DROP CONSTRAINT pipeline_items_user_id_fkey;
    END IF;

    -- Add new FK referencing profiles(id) — NOT VALID for fast lock release
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'pipeline_items_user_id_profiles_fkey'
        AND table_name = 'pipeline_items'
    ) THEN
        ALTER TABLE pipeline_items
            ADD CONSTRAINT pipeline_items_user_id_profiles_fkey
            FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
    END IF;
END $$;

-- Validate in a separate statement (full scan, but doesn't block writes)
ALTER TABLE pipeline_items VALIDATE CONSTRAINT pipeline_items_user_id_profiles_fkey;

-- ============================================================
-- 2. classification_feedback (AC2)
-- ============================================================
DO $$
BEGIN
    -- Only proceed if the table exists (created via backend migration 006)
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'classification_feedback'
    ) THEN
        -- Drop old FK referencing auth.users
        IF EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'classification_feedback_user_id_fkey'
            AND table_name = 'classification_feedback'
        ) THEN
            ALTER TABLE classification_feedback DROP CONSTRAINT classification_feedback_user_id_fkey;
        END IF;

        -- Add new FK referencing profiles(id) — NOT VALID for fast lock release
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'classification_feedback_user_id_profiles_fkey'
            AND table_name = 'classification_feedback'
        ) THEN
            ALTER TABLE classification_feedback
                ADD CONSTRAINT classification_feedback_user_id_profiles_fkey
                FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
        END IF;

        -- Validate (full scan, doesn't block writes)
        ALTER TABLE classification_feedback
            VALIDATE CONSTRAINT classification_feedback_user_id_profiles_fkey;
    END IF;
END $$;

-- ============================================================
-- 3. trial_email_log (AC3)
-- ============================================================
DO $$
BEGIN
    -- Drop old FK referencing auth.users
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'trial_email_log_user_id_fkey'
        AND table_name = 'trial_email_log'
    ) THEN
        ALTER TABLE trial_email_log DROP CONSTRAINT trial_email_log_user_id_fkey;
    END IF;

    -- Add new FK referencing profiles(id) — NOT VALID for fast lock release
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'trial_email_log_user_id_profiles_fkey'
        AND table_name = 'trial_email_log'
    ) THEN
        ALTER TABLE trial_email_log
            ADD CONSTRAINT trial_email_log_user_id_profiles_fkey
            FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
    END IF;
END $$;

-- Validate in a separate statement
ALTER TABLE trial_email_log VALIDATE CONSTRAINT trial_email_log_user_id_profiles_fkey;

-- ============================================================
-- Documentation
-- ============================================================
COMMENT ON CONSTRAINT pipeline_items_user_id_profiles_fkey ON pipeline_items IS
    'STORY-264 AC1: FK standardized to profiles(id) ON DELETE CASCADE';

COMMENT ON CONSTRAINT trial_email_log_user_id_profiles_fkey ON trial_email_log IS
    'STORY-264 AC3: FK standardized to profiles(id) ON DELETE CASCADE';

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
