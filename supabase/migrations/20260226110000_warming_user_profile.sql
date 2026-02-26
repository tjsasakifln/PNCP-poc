-- STORY-271 AC1: Insert system profile for cache warming user.
-- Fixes FK violation: search_results_cache_user_id_profiles_fkey
-- when cache warming tries to save results for WARMING_USER_ID.
--
-- The nil UUID is used by the background cache warming job (job_queue.py)
-- to avoid counting warming requests against real user quotas.

-- Step 1: Ensure the system user exists in auth.users (required by profiles FK).
-- This uses a DO block because auth.users is managed by Supabase Auth and
-- INSERT ... ON CONFLICT is not reliable for the auth schema.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM auth.users WHERE id = '00000000-0000-0000-0000-000000000000'
    ) THEN
        INSERT INTO auth.users (
            id,
            instance_id,
            aud,
            role,
            email,
            encrypted_password,
            email_confirmed_at,
            created_at,
            updated_at,
            raw_app_meta_data,
            raw_user_meta_data,
            is_super_admin
        ) VALUES (
            '00000000-0000-0000-0000-000000000000',
            '00000000-0000-0000-0000-000000000000',
            'authenticated',
            'authenticated',
            'system-cache-warmer@internal.smartlic.tech',
            '',  -- no password (system account, cannot login)
            now(),
            now(),
            now(),
            '{"provider": "system", "providers": ["system"]}'::jsonb,
            '{"full_name": "System Cache Warmer"}'::jsonb,
            false
        );
    END IF;
END
$$;

-- Step 2: Insert the corresponding profile row.
-- profiles.email has NOT NULL constraint, so we must provide it.
-- profiles_plan_type_check allows: free_trial, consultor_agil, maquina, sala_guerra, master, smartlic_pro
-- Using 'master' for system account (no quota limits, internal use only).
INSERT INTO profiles (id, email, full_name, plan_type, is_admin)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system-cache-warmer@internal.smartlic.tech',
    'System Cache Warmer',
    'master',
    false
)
ON CONFLICT (id) DO NOTHING;
