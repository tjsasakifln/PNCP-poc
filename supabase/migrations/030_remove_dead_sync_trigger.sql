-- Migration 030: Remove dead sync_profile_plan_type() trigger
-- Date: 2026-02-16
-- Author: AIOS Development Team
-- Story: STORY-TD-004 (DB-01)
--
-- RATIONALE:
-- The sync_profile_plan_type() trigger (migration 017) references
-- user_subscriptions.status which DOES NOT EXIST. The table uses
-- is_active (boolean) instead. This trigger is dead code that would
-- throw "column status does not exist" if ever fired.
--
-- Plan sync is handled in the application layer via Stripe webhook
-- handlers in billing.py, which have full context for grace periods,
-- retries, and logging.
--
-- See: docs/architecture/td004-trigger-evolution.md
-- See: docs/architecture/ADR-TD004-trigger-consolidation.md

-- 1. Drop the trigger from user_subscriptions
DROP TRIGGER IF EXISTS trg_sync_profile_plan_type ON user_subscriptions;

-- 2. Drop the function
DROP FUNCTION IF EXISTS sync_profile_plan_type();

-- 3. Document the removal
COMMENT ON TABLE user_subscriptions IS
    'Migration 030: Removed trg_sync_profile_plan_type trigger — referenced non-existent status column (dead code since migration 017). Plan sync handled by billing.py Stripe webhooks.';
