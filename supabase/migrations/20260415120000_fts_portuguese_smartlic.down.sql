-- ============================================================================
-- DOWN: fts_portuguese_smartlic — reverses 20260415120000_fts_portuguese_smartlic.sql
-- Date: 2026-04-16
-- Story: STORY-5.4 AC1 (TD-SYS-015)
-- ============================================================================
-- Context:
--   Up migration created the custom text-search configuration
--   public.portuguese_smartlic (clone of pg_catalog.portuguese + unaccent filter).
--
--   Rollback:
--     1. Drop the custom FTS configuration (idempotent with IF EXISTS).
--     2. The unaccent extension is NOT dropped — it is a shared extension
--        that may be used elsewhere. Dropping it would be unsafe.
--
--   NOTE: If 20260415120001_search_datalake_use_portuguese_smartlic.sql is
--   still applied (i.e., search_datalake still references public.portuguese_smartlic),
--   run THAT down migration first before this one, or the DROP will fail.
-- ============================================================================

DROP TEXT SEARCH CONFIGURATION IF EXISTS public.portuguese_smartlic;

-- unaccent extension intentionally NOT dropped — shared dependency.
