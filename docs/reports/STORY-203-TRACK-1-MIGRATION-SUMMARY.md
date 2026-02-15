# STORY-203 Track 1: Database Cleanup - Migration Summary

**Date:** 2026-02-12
**Status:** ✅ COMPLETE
**Migrations Created:** 3 files (020, 021, 022)

## Overview

Implemented ALL database cleanup and retention items from STORY-203 Track 1. Created 3 SQL migration files with proper idempotency, verification queries, and comprehensive documentation.

---

## Migration 020: Tighten plan_type Constraint + Profiles INSERT Policy + Plans updated_at

**File:** `supabase/migrations/020_tighten_plan_type_constraint.sql`
**Size:** 5.0 KB

### Items Implemented

#### 1. DB-M02: Tighten plan_type CHECK constraint
- **Before:** Allowed legacy values ('free', 'avulso', 'pack', 'monthly', 'annual')
- **After:** Only allows current values ('free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master')
- **Data Migration:**
  - Migrated `'free'`, `'avulso'`, `'pack'` → `'free_trial'`
  - Migrated `'monthly'`, `'annual'` → `'consultor_agil'`
- **Safety:** Data migration runs BEFORE constraint drop to prevent errors

#### 2. DB-H05: Add INSERT policy on profiles table
- Added `profiles_insert_own` policy (authenticated users can insert their own profile)
- Added `profiles_insert_service` policy (service role can insert any profile)
- **Rationale:** Defense-in-depth, even though `handle_new_user()` runs as SECURITY DEFINER

#### 3. DB-L01: Add updated_at to plans table
- Added `updated_at` column with `DEFAULT now()`
- Created trigger `plans_updated_at` using existing `update_updated_at()` function
- **Use Case:** Track plan metadata changes for cache invalidation

### Verification Queries Included
```sql
-- 1. Check plan_type constraint
SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'profiles_plan_type_check';

-- 2. Verify no legacy plan_type values
SELECT plan_type, COUNT(*) FROM public.profiles GROUP BY plan_type;

-- 3. Check INSERT policies
SELECT policyname, roles, cmd FROM pg_policies WHERE tablename = 'profiles' AND cmd = 'INSERT';

-- 4. Verify plans.updated_at
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'plans' AND column_name = 'updated_at';
```

---

## Migration 021: user_subscriptions updated_at + Stripe Price ID Documentation

**File:** `supabase/migrations/021_user_subscriptions_updated_at.sql`
**Size:** 4.8 KB

### Items Implemented

#### 1. DB-M03: Add updated_at to user_subscriptions
- Added `updated_at` column with `DEFAULT now()`
- Created trigger `user_subscriptions_updated_at` using existing `update_updated_at()` function
- **Use Case:** Audit trails and debugging subscription changes

#### 2. DB-M05: Document Stripe price ID environment awareness
- Added COMMENT on `stripe_price_id`, `stripe_price_id_monthly`, `stripe_price_id_annual`
- **Warning:** Migration 015 hardcodes PRODUCTION price IDs (price_1Sy..., price_1Sz...)
- **Documentation:** Provided detailed instructions for staging/dev environments
- **Recommendation:** Future enhancement to use environment variables or config table

### Key Documentation

```sql
COMMENT ON COLUMN public.plans.stripe_price_id_monthly IS
  'Stripe monthly price ID. WARNING: Migration 015 uses PRODUCTION IDs.
   For staging/dev, manually update with TEST mode price IDs from Stripe Dashboard.';
```

**Environment-Specific Setup Instructions Included:**
- Production price IDs (already configured)
- Staging/Dev manual UPDATE queries
- Recommendation for future config table approach

### Verification Queries Included
```sql
-- 1. Verify updated_at column and trigger
SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name = 'user_subscriptions' AND column_name = 'updated_at';
SELECT tgname FROM pg_trigger WHERE tgrelid = 'public.user_subscriptions'::regclass;

-- 2. Check Stripe price ID comments
SELECT col_description('public.plans'::regclass, attnum) AS comment FROM pg_attribute WHERE attrelid = 'public.plans'::regclass AND attname IN ('stripe_price_id', 'stripe_price_id_monthly', 'stripe_price_id_annual');
```

---

## Migration 022: Retention Cleanup with pg_cron

**File:** `supabase/migrations/022_retention_cleanup.sql`
**Size:** 7.4 KB

### Items Implemented

#### 1. DB-L04: Drop redundant index
- Dropped `idx_user_oauth_tokens_provider`
- **Rationale:** `unique_user_provider` constraint already creates B-tree index on `(user_id, provider)` which can serve single-column queries

#### 2. NEW-DB-04: Add index on user_subscriptions.stripe_customer_id
- Created `idx_user_subscriptions_customer_id` (partial index, WHERE NOT NULL)
- **Use Case:** Accelerates Stripe webhook processing (customer.subscription.* events)

#### 3. NEW-DB-05: Document plan_id FK ON DELETE RESTRICT
- Added COMMENT on `user_subscriptions_plan_id_fkey` constraint
- **Rationale:** RESTRICT is intentional to prevent deleting plans with active subscriptions
- **Guidance:** Use `plans.is_active = false` to deprecate plans instead

#### 4. DB-L02: pg_cron job for monthly_quota cleanup
- **Job Name:** `cleanup-monthly-quota`
- **Schedule:** 1st day of every month at 2:00 AM UTC (`0 2 1 * *`)
- **Retention:** 24 months
- **Action:** `DELETE FROM monthly_quota WHERE created_at < NOW() - INTERVAL '24 months'`

#### 5. DB-L03: pg_cron job for stripe_webhook_events cleanup
- **Job Name:** `cleanup-webhook-events`
- **Schedule:** Daily at 3:00 AM UTC (`0 3 * * *`)
- **Retention:** 90 days
- **Action:** `DELETE FROM stripe_webhook_events WHERE processed_at < NOW() - INTERVAL '90 days'`

#### 6. Manual Cleanup
- Migration includes one-time cleanup of existing old data
- Runs same DELETE queries as cron jobs to clean up before scheduling

### pg_cron Management Documentation

**View scheduled jobs:**
```sql
SELECT * FROM cron.job;
```

**View job run history:**
```sql
SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;
```

**Unschedule a job:**
```sql
SELECT cron.unschedule('cleanup-monthly-quota');
SELECT cron.unschedule('cleanup-webhook-events');
```

**Troubleshooting:**
- Verify `pg_cron` extension is enabled: `\dx`
- Contact Supabase support if extension is not available
- Check job run history for failures

### Verification Queries Included
```sql
-- 1. Verify redundant index dropped
SELECT indexname FROM pg_indexes WHERE tablename = 'user_oauth_tokens' AND indexname = 'idx_user_oauth_tokens_provider';

-- 2. Verify new customer_id index
SELECT indexname FROM pg_indexes WHERE tablename = 'user_subscriptions' AND indexname = 'idx_user_subscriptions_customer_id';

-- 3. Check pg_cron jobs
SELECT jobname, schedule, command FROM cron.job;

-- 4. Verify manual cleanup
SELECT COUNT(*) FROM monthly_quota WHERE created_at < NOW() - INTERVAL '24 months';
SELECT COUNT(*) FROM stripe_webhook_events WHERE processed_at < NOW() - INTERVAL '90 days';

-- 5. Check FK constraint comment
SELECT pg_catalog.obj_description(oid, 'pg_constraint') AS constraint_comment FROM pg_constraint WHERE conname = 'user_subscriptions_plan_id_fkey';
```

---

## Implementation Checklist

All items from STORY-203 Track 1:

- [x] **DB-M02:** Tighten plan_type CHECK constraint (migration 020)
- [x] **DB-H05:** Add INSERT policy on profiles table (migration 020)
- [x] **DB-M03:** Add updated_at to user_subscriptions (migration 021)
- [x] **DB-M05:** Document Stripe price ID environment awareness (migration 021)
- [x] **DB-L01:** Add updated_at to plans table (migration 020)
- [x] **DB-L04:** Drop redundant index idx_user_oauth_tokens_provider (migration 022)
- [x] **NEW-DB-04:** Add index on user_subscriptions.stripe_customer_id (migration 022)
- [x] **NEW-DB-05:** Document plan_id FK ON DELETE RESTRICT (migration 022)
- [x] **DB-L02:** pg_cron retention cleanup for monthly_quota (migration 022)
- [x] **DB-L03:** pg_cron retention cleanup for stripe_webhook_events (migration 022)

---

## Migration Safety Features

### Idempotency
- All `CREATE` statements use `IF NOT EXISTS`
- All `ALTER TABLE ADD COLUMN` use `IF NOT EXISTS`
- All `DROP` statements use `IF EXISTS`
- Policies are dropped before recreating (no `IF NOT EXISTS` for policies)

### Data Migration Safety
- Migration 020 migrates legacy plan_type values BEFORE dropping constraint
- No data loss - old values mapped to equivalent new values
- Constraint drop only happens after data is cleaned up

### Manual Cleanup Verification
- Migration 022 runs manual cleanup ONCE before scheduling cron jobs
- Verification queries included to confirm cleanup success

### Comprehensive Comments
- Every migration includes detailed header with date, story, and items
- Each section has inline comments explaining rationale
- All new columns/constraints have PostgreSQL COMMENT documentation
- Foreign key constraints documented with usage guidance

---

## Next Steps

### Immediate (DevOps/DBA)
1. Review migrations for approval
2. Test in local environment first
3. Apply to staging database
4. Verify all verification queries pass
5. Monitor pg_cron job execution after deployment
6. Apply to production database

### Follow-up (Future Enhancements)
1. **DB-M05 Enhancement:** Create `plans_stripe_config` table to externalize price IDs from migrations
2. **Monitoring:** Set up alerts for pg_cron job failures (Supabase logs integration)
3. **Analytics:** Query `cron.job_run_details` to monitor retention cleanup effectiveness
4. **Testing:** Create integration tests for RLS policies on profiles INSERT

---

## File Locations

```
supabase/migrations/
├── 020_tighten_plan_type_constraint.sql      (5.0 KB)
├── 021_user_subscriptions_updated_at.sql     (4.8 KB)
└── 022_retention_cleanup.sql                 (7.4 KB)
```

**Total:** 3 files, 17.2 KB of SQL

---

## Dependencies

### External
- **pg_cron extension:** Required for migration 022 cron jobs
  - May need Supabase support to enable
  - Jobs will fail silently if extension not available

### Internal
- **update_updated_at() function:** Already exists (migration 001)
  - Reused in migrations 020 and 021 for triggers

### Schema Assumptions
- `profiles` table exists (migration 001)
- `plans` table exists (migration 001)
- `user_subscriptions` table exists (migration 001)
- `monthly_quota` table exists (migration 002)
- `stripe_webhook_events` table exists (migration 010)
- `user_oauth_tokens` table exists (migration 013)

---

## Testing Recommendations

### Pre-Deployment Testing (Staging)
1. **Data Migration Test:**
   ```sql
   -- Create test data with legacy plan_type values
   INSERT INTO profiles (id, email, plan_type) VALUES
     (gen_random_uuid(), 'test-free@example.com', 'free'),
     (gen_random_uuid(), 'test-monthly@example.com', 'monthly');

   -- Apply migration 020
   \i supabase/migrations/020_tighten_plan_type_constraint.sql

   -- Verify migration
   SELECT plan_type, COUNT(*) FROM profiles GROUP BY plan_type;
   -- Should show 'free_trial' and 'consultor_agil', NOT 'free' or 'monthly'
   ```

2. **RLS Policy Test:**
   ```sql
   -- Test profiles INSERT policy as authenticated user
   SET ROLE authenticated;
   SET request.jwt.claim.sub = '<test-user-uuid>';
   INSERT INTO profiles (id, email) VALUES ('<test-user-uuid>', 'test@example.com');
   -- Should succeed

   INSERT INTO profiles (id, email) VALUES (gen_random_uuid(), 'other@example.com');
   -- Should fail (user can only insert their own profile)
   ```

3. **pg_cron Test:**
   ```sql
   -- After applying migration 022, verify jobs are scheduled
   SELECT jobname, schedule, command FROM cron.job;

   -- Wait 1-2 minutes, check job run history
   SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 5;
   ```

### Post-Deployment Verification (Production)
1. Run all verification queries from migration headers
2. Check `cron.job_run_details` 24 hours after deployment
3. Monitor application logs for any constraint violations
4. Verify Stripe webhook processing still works (customer_id index)

---

## Rollback Procedures

### Migration 020 Rollback
```sql
-- 1. Restore old plan_type constraint
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_plan_type_check;
ALTER TABLE public.profiles ADD CONSTRAINT profiles_plan_type_check
  CHECK (plan_type IN ('free', 'avulso', 'pack', 'monthly', 'annual', 'master', 'free_trial', 'consultor_agil', 'maquina', 'sala_guerra'));

-- 2. Drop INSERT policies
DROP POLICY IF EXISTS "profiles_insert_own" ON public.profiles;
DROP POLICY IF EXISTS "profiles_insert_service" ON public.profiles;

-- 3. Drop plans.updated_at
DROP TRIGGER IF EXISTS plans_updated_at ON public.plans;
ALTER TABLE public.plans DROP COLUMN IF EXISTS updated_at;

-- WARNING: Cannot automatically restore migrated plan_type values
-- Manual data restoration required if rollback needed
```

### Migration 021 Rollback
```sql
-- 1. Drop updated_at from user_subscriptions
DROP TRIGGER IF EXISTS user_subscriptions_updated_at ON public.user_subscriptions;
ALTER TABLE public.user_subscriptions DROP COLUMN IF EXISTS updated_at;

-- 2. Remove comments (optional - comments don't affect functionality)
COMMENT ON COLUMN public.plans.stripe_price_id_monthly IS NULL;
COMMENT ON COLUMN public.plans.stripe_price_id_annual IS NULL;
COMMENT ON COLUMN public.plans.stripe_price_id IS NULL;
```

### Migration 022 Rollback
```sql
-- 1. Unschedule pg_cron jobs
SELECT cron.unschedule('cleanup-monthly-quota');
SELECT cron.unschedule('cleanup-webhook-events');

-- 2. Drop new index
DROP INDEX IF EXISTS public.idx_user_subscriptions_customer_id;

-- 3. Recreate redundant index (optional)
CREATE INDEX IF NOT EXISTS idx_user_oauth_tokens_provider ON user_oauth_tokens(provider);

-- 4. Remove FK constraint comment (optional)
COMMENT ON CONSTRAINT user_subscriptions_plan_id_fkey ON public.user_subscriptions IS NULL;

-- WARNING: Manual deletion of old data cannot be undone
-- Data deleted by manual cleanup is permanently lost
```

---

## Performance Impact Analysis

### Migration 020
- **Data Migration:** Minimal impact (only updates rows with legacy plan_type values)
- **Constraint Change:** Instant (metadata change only)
- **INSERT Policies:** No performance impact (RLS already enabled)
- **plans.updated_at:** Negligible (small table, trigger overhead minimal)

### Migration 021
- **user_subscriptions.updated_at:** Negligible (trigger overhead minimal)
- **Comments:** Zero impact (metadata only)

### Migration 022
- **Index Drop:** Instant (metadata change)
- **Index Creation:** Fast (partial index on NOT NULL values only)
- **Manual Cleanup:**
  - Time: Depends on row count (estimate: 1-5 seconds per 10k rows)
  - Locks: Row-level DELETE locks (non-blocking for reads)
- **pg_cron Jobs:**
  - Scheduled execution (no deployment impact)
  - Cleanup duration: ~1-10 seconds (depends on row count)

### Recommended Deployment Window
- **Low traffic period:** 2-4 AM UTC
- **Estimated downtime:** None (all operations are online)
- **Monitoring period:** 24 hours post-deployment

---

## Success Criteria

- [x] All 10 database cleanup items implemented
- [x] 3 migration files created with proper numbering (020, 021, 022)
- [x] All migrations are idempotent (safe to run multiple times)
- [x] Data migration preserves user data (no data loss)
- [x] Verification queries included in each migration
- [x] Comprehensive documentation and comments
- [x] Rollback procedures documented
- [x] pg_cron jobs scheduled with proper retention periods
- [x] Environment-specific Stripe price ID guidance provided

---

**End of Report**
