-- Migration 033: Fix missing cache columns from duplicate 027_ prefix
--
-- Context: Two migrations shared the 027_ prefix:
--   - 027_fix_plan_type_default_and_rls.sql (applied)
--   - 027_search_cache_add_sources_and_fetched_at.sql (NOT applied in production)
--
-- This migration ensures the missing columns exist, creates indexes,
-- and re-runs backfills that may have failed due to the missing columns.
--
-- IDEMPOTENT: Safe to execute multiple times (IF NOT EXISTS + WHERE IS NULL)

SET statement_timeout = '30s';

-- AC1: Add missing columns
ALTER TABLE search_results_cache ADD COLUMN IF NOT EXISTS sources_json JSONB NOT NULL DEFAULT '["pncp"]'::jsonb;
ALTER TABLE search_results_cache ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ DEFAULT now() NOT NULL;

-- AC1: Create index for TTL lookups
CREATE INDEX IF NOT EXISTS idx_search_cache_fetched_at ON search_results_cache(fetched_at);

-- AC6: Backfill sources_json for existing rows
UPDATE search_results_cache
SET sources_json = '["pncp"]'::jsonb
WHERE sources_json IS NULL;

-- AC7: Backfill fetched_at from created_at for existing rows
UPDATE search_results_cache
SET fetched_at = created_at
WHERE fetched_at IS NULL;

-- AC8: Re-run 031 backfill (may have failed if fetched_at didn't exist)
UPDATE search_results_cache
SET last_success_at = fetched_at,
    last_attempt_at = fetched_at
WHERE last_success_at IS NULL AND fetched_at IS NOT NULL;

-- AC8: Re-run 032 backfill (may have failed if fetched_at/last_success_at were NULL)
UPDATE search_results_cache
SET last_accessed_at = COALESCE(last_success_at, fetched_at, created_at)
WHERE last_accessed_at IS NULL;
