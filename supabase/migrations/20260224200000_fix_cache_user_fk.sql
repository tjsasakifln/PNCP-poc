-- GTM-STAB-001 AC2: Fix FK constraint on search_results_cache
-- Changes user_id FK from auth.users(id) to profiles(id) for consistency
-- Pattern: same as migration 018 (standardize_fk_references)

DO $$
BEGIN
    -- Drop existing FK referencing auth.users
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'search_results_cache_user_id_fkey'
        AND table_name = 'search_results_cache'
    ) THEN
        ALTER TABLE search_results_cache DROP CONSTRAINT search_results_cache_user_id_fkey;
    END IF;

    -- Add new FK referencing profiles(id)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'search_results_cache_user_id_profiles_fkey'
        AND table_name = 'search_results_cache'
    ) THEN
        ALTER TABLE search_results_cache
            ADD CONSTRAINT search_results_cache_user_id_profiles_fkey
            FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
    END IF;
END $$;

COMMENT ON CONSTRAINT search_results_cache_user_id_profiles_fkey ON search_results_cache IS
    'GTM-STAB-001 AC2: Standardized FK to profiles(id), consistent with migration 018';
