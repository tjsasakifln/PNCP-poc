-- STORY-202 DB-M01: Standardize all user-related FKs to reference profiles(id)
-- instead of auth.users(id) for consistency

-- 1. monthly_quota: Change FK from auth.users(id) to profiles(id)
-- First check if the constraint exists, drop it, then add new one

DO $$
BEGIN
    -- Drop existing FK on monthly_quota if it references auth.users
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'monthly_quota_user_id_fkey'
        AND table_name = 'monthly_quota'
    ) THEN
        ALTER TABLE monthly_quota DROP CONSTRAINT monthly_quota_user_id_fkey;
    END IF;

    -- Add new FK referencing profiles(id)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'monthly_quota_user_id_profiles_fkey'
        AND table_name = 'monthly_quota'
    ) THEN
        ALTER TABLE monthly_quota
            ADD CONSTRAINT monthly_quota_user_id_profiles_fkey
            FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    -- user_oauth_tokens
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'user_oauth_tokens_user_id_fkey'
        AND table_name = 'user_oauth_tokens'
    ) THEN
        ALTER TABLE user_oauth_tokens DROP CONSTRAINT user_oauth_tokens_user_id_fkey;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'user_oauth_tokens_user_id_profiles_fkey'
        AND table_name = 'user_oauth_tokens'
    ) THEN
        ALTER TABLE user_oauth_tokens
            ADD CONSTRAINT user_oauth_tokens_user_id_profiles_fkey
            FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    -- google_sheets_exports
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'google_sheets_exports_user_id_fkey'
        AND table_name = 'google_sheets_exports'
    ) THEN
        ALTER TABLE google_sheets_exports DROP CONSTRAINT google_sheets_exports_user_id_fkey;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'google_sheets_exports_user_id_profiles_fkey'
        AND table_name = 'google_sheets_exports'
    ) THEN
        ALTER TABLE google_sheets_exports
            ADD CONSTRAINT google_sheets_exports_user_id_profiles_fkey
            FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
    END IF;
END $$;

COMMENT ON CONSTRAINT monthly_quota_user_id_profiles_fkey ON monthly_quota IS
    'STORY-202 DB-M01: Standardized FK to profiles(id)';
COMMENT ON CONSTRAINT user_oauth_tokens_user_id_profiles_fkey ON user_oauth_tokens IS
    'STORY-202 DB-M01: Standardized FK to profiles(id)';
COMMENT ON CONSTRAINT google_sheets_exports_user_id_profiles_fkey ON google_sheets_exports IS
    'STORY-202 DB-M01: Standardized FK to profiles(id)';
