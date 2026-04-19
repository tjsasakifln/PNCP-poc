-- ============================================================================
-- Rollback for 20260420000002_add_profiles_cnae_primary
-- ============================================================================

BEGIN;

DROP INDEX IF EXISTS idx_profiles_cnae_consultoria;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS cnae_primary;

COMMIT;
