-- ============================================================================
-- Migration 022: Retention Cleanup with pg_cron
-- STORY-203 Track 1: Database Cleanup
-- Date: 2026-02-12
-- ============================================================================
-- This migration combines:
--   DB-L02: Delete monthly_quota rows older than 24 months
--   DB-L03: Delete stripe_webhook_events rows older than 90 days
--   DB-L04: Drop redundant index idx_user_oauth_tokens_provider
--   NEW-DB-04: Add index on user_subscriptions.stripe_customer_id
--   NEW-DB-05: Document plan_id FK ON DELETE RESTRICT as intentional
-- ============================================================================

-- ============================================================
-- 1. DB-L04: Drop redundant index idx_user_oauth_tokens_provider
--    This index is redundant because:
--    - unique_user_provider constraint creates a unique B-tree index
--      on (user_id, provider) which can serve single-column queries
--    - PostgreSQL can use multi-column indexes for prefix matches
-- ============================================================

DROP INDEX IF EXISTS public.idx_user_oauth_tokens_provider;

COMMENT ON INDEX public.idx_user_oauth_tokens_expires_at IS
  'Index for token expiration lookups (OAuth refresh background job)';

-- ============================================================
-- 2. NEW-DB-04: Add index on user_subscriptions.stripe_customer_id
--    Improves webhook processing performance when looking up
--    subscriptions by Stripe customer ID
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_customer_id
  ON public.user_subscriptions(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;

COMMENT ON INDEX public.idx_user_subscriptions_customer_id IS
  'Accelerates Stripe webhook processing (customer.subscription.* events lookup by customer_id)';

-- ============================================================
-- 3. NEW-DB-05: Document plan_id FK ON DELETE RESTRICT
--    The FK constraint on user_subscriptions.plan_id uses
--    default ON DELETE RESTRICT behavior. This is INTENTIONAL
--    to prevent accidental deletion of plan catalog entries
--    that have active subscriptions.
-- ============================================================

COMMENT ON CONSTRAINT user_subscriptions_plan_id_fkey ON public.user_subscriptions IS
  'FK to plans catalog. ON DELETE RESTRICT (default) is intentional - prevents deleting plans with active subscriptions. To deprecate a plan, set plans.is_active = false instead.';

-- ============================================================
-- 4. DB-L02 + DB-L03: pg_cron scheduled cleanup jobs
--    IMPORTANT: pg_cron extension must be enabled by Supabase
--    support team. These jobs will fail silently if extension
--    is not installed.
-- ============================================================

-- Enable pg_cron extension (requires superuser - may need Supabase support)
-- This will succeed silently if extension is already enabled
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- ============================================================
-- Job 1: Delete monthly_quota rows older than 24 months
-- Schedule: 1st day of every month at 2:00 AM UTC
-- Retention: Keep 24 months of quota history for analytics
-- ============================================================

SELECT cron.schedule(
  'cleanup-monthly-quota',                              -- job name
  '0 2 1 * *',                                          -- cron: 2am on 1st of month
  $$
    DELETE FROM public.monthly_quota
    WHERE created_at < NOW() - INTERVAL '24 months'
  $$
);

COMMENT ON EXTENSION pg_cron IS
  'Automated retention cleanup jobs: monthly_quota (24mo), stripe_webhook_events (90d). See migration 022.';

-- ============================================================
-- Job 2: Delete stripe_webhook_events older than 90 days
-- Schedule: Daily at 3:00 AM UTC
-- Retention: Keep 90 days for compliance and debugging
-- ============================================================

SELECT cron.schedule(
  'cleanup-webhook-events',                             -- job name
  '0 3 * * *',                                          -- cron: 3am daily
  $$
    DELETE FROM public.stripe_webhook_events
    WHERE processed_at < NOW() - INTERVAL '90 days'
  $$
);

-- ============================================================
-- Manual cleanup (run once to clean up existing old data)
-- ============================================================

-- Clean up monthly_quota older than 24 months
DELETE FROM public.monthly_quota
WHERE created_at < NOW() - INTERVAL '24 months';

-- Clean up stripe_webhook_events older than 90 days
DELETE FROM public.stripe_webhook_events
WHERE processed_at < NOW() - INTERVAL '90 days';

-- ============================================================================
-- pg_cron Verification and Management
-- ============================================================================
--
-- View scheduled jobs:
--   SELECT * FROM cron.job;
--
-- View job run history:
--   SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;
--
-- Unschedule a job (if needed):
--   SELECT cron.unschedule('cleanup-monthly-quota');
--   SELECT cron.unschedule('cleanup-webhook-events');
--
-- Manually trigger a job (for testing):
--   SELECT cron.schedule('test-cleanup-quota', '* * * * *',
--     'DELETE FROM public.monthly_quota WHERE created_at < NOW() - INTERVAL ''24 months''');
--   -- Check cron.job_run_details after 1 minute
--   SELECT cron.unschedule('test-cleanup-quota');
--
-- TROUBLESHOOTING:
--   If jobs don't run:
--   1. Verify pg_cron extension is enabled: \dx
--   2. Check Supabase project settings for pg_cron support
--   3. Contact Supabase support to enable pg_cron
--   4. Verify job is scheduled: SELECT * FROM cron.job;
--
-- ============================================================================

-- ============================================================================
-- Verification queries (run after applying):
-- ============================================================================
-- 1. Verify redundant index was dropped:
--    SELECT indexname FROM pg_indexes
--    WHERE tablename = 'user_oauth_tokens' AND indexname = 'idx_user_oauth_tokens_provider';
--    -- Should return 0 rows
--
-- 2. Verify new customer_id index exists:
--    SELECT indexname FROM pg_indexes
--    WHERE tablename = 'user_subscriptions' AND indexname = 'idx_user_subscriptions_customer_id';
--
-- 3. Check pg_cron jobs are scheduled:
--    SELECT jobname, schedule, command FROM cron.job;
--    -- Should show 2 jobs: cleanup-monthly-quota, cleanup-webhook-events
--
-- 4. Verify manual cleanup ran successfully:
--    SELECT COUNT(*) FROM monthly_quota WHERE created_at < NOW() - INTERVAL '24 months';
--    SELECT COUNT(*) FROM stripe_webhook_events WHERE processed_at < NOW() - INTERVAL '90 days';
--    -- Both should return 0
--
-- 5. Check FK constraint comment:
--    SELECT pg_catalog.obj_description(oid, 'pg_constraint') AS constraint_comment
--    FROM pg_constraint
--    WHERE conname = 'user_subscriptions_plan_id_fkey';
-- ============================================================================
