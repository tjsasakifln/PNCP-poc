-- ============================================================================
-- DOWN: story64_search_results_store_cascade — reverses
--       20260416120200_story64_search_results_store_cascade.sql
-- Date: 2026-04-16
-- Story: STORY-6.4 AC3 (TD-DB-033)
-- ============================================================================
-- Context:
--   Up migration re-asserted search_results_store_user_id_fkey as
--   REFERENCES public.profiles(id) ON DELETE CASCADE.
--
--   Down restores the previous state from 20260304100000_fk_standardization_to_profiles.sql
--   which was identical (profiles(id) ON DELETE CASCADE). Since there is no
--   behavioral difference, the down is functionally a no-op but is included
--   for completeness and to satisfy STORY-6.2 down.sql pairing policy.
-- ============================================================================

ALTER TABLE public.search_results_store
    DROP CONSTRAINT IF EXISTS search_results_store_user_id_fkey,
    ADD CONSTRAINT search_results_store_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE
        NOT VALID;

COMMENT ON CONSTRAINT search_results_store_user_id_fkey ON public.search_results_store IS NULL;
