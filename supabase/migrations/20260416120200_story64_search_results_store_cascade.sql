-- ============================================================================
-- STORY-6.4 AC3 (TD-DB-033): Confirm search_results_store.user_id ON DELETE
-- CASCADE alignment with sister table search_results_cache.
-- Date: 2026-04-16
-- ============================================================================
-- Context:
--   Original AC3 description: "migrate ON NO ACTION → ON DELETE CASCADE for
--   consistency with search_results_cache (sister table)".
--
--   Current state audit:
--     - search_results_store.user_id: REFERENCES public.profiles(id) ON DELETE CASCADE
--       (set by 20260304100000_fk_standardization_to_profiles.sql)
--     - search_results_cache.user_id: REFERENCES profiles(id) ON DELETE CASCADE
--       (set by 20260224200000_fix_cache_user_fk.sql)
--
--   Both tables already use ON DELETE CASCADE to profiles(id). The tables are
--   consistent. This migration re-asserts the constraint idempotently to:
--     1. Document the TD-DB-033 resolution explicitly in the migration log.
--     2. Ensure future refactors don't accidentally weaken the cascade.
--
--   No behavioral change — this is a no-op if the constraint is already correct.
-- ============================================================================

-- Re-assert constraint idempotently (drop + add = always correct state)
ALTER TABLE public.search_results_store
    DROP CONSTRAINT IF EXISTS search_results_store_user_id_fkey,
    ADD CONSTRAINT search_results_store_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

COMMENT ON CONSTRAINT search_results_store_user_id_fkey ON public.search_results_store IS
    'STORY-6.4 TD-DB-033: ON DELETE CASCADE to profiles(id). '
    'Consistent with search_results_cache_user_id_profiles_fkey. '
    'When a user profile is deleted, their search results are also deleted.';
