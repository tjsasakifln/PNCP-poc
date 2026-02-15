# Database Audit Report - SmartLic/BidIQ

**Auditor:** @data-engineer (Datum)
**Date:** 2026-02-15
**Scope:** Full schema audit of Supabase (PostgreSQL 17) database
**Migrations Analyzed:** 001 through 026 (26 migration files)
**Backend Code Analyzed:** All Python files in `backend/` (excluding venv)
**Previous Audit:** 2026-02-11 (11 tables, 15 migrations)

---

## Executive Summary

| Metric | Previous (Feb 11) | Current (Feb 15) | Delta |
|--------|-------------------|-------------------|-------|
| **Overall Health** | 6.5 / 10 | **7.5 / 10** | +1.0 |
| **Critical Issues** | 3 | **1** | -2 (fixed by migrations 016-022) |
| **High-Severity Issues** | 5 | **3** | -2 |
| **Medium-Severity Issues** | 7 | **5** | -2 |
| **Low-Severity Issues** | 4 | **4** | 0 |
| **Tables** | 11 | **14** | +3 (audit_events, pipeline_items, search_results_cache) |
| **Migrations** | 15 | **26** | +11 |
| **RLS Policies** | ~25 | **~38** | +13 |
| **Functions** | 8 | **14** | +6 |
| **Indexes** | 36 | **~52** | +16 |

The database has improved significantly since the last audit. Migrations 016-022 (STORY-200, 202, 203) addressed the three previous P0-CRITICAL issues: service role RLS gaps, webhook admin policy bug, and overly permissive policies. The plan_type constraint has been tightened, FK references standardized, N+1 queries eliminated via RPC functions, and retention cleanup jobs added.

New issues introduced by migrations 023-026 are mostly medium/low severity (overly permissive RLS policies, FK inconsistency with auth.users), with one critical schema integrity gap (missing `status` column on user_subscriptions referenced by trigger).

---

## 1. Security Audit

### 1.1 RLS Coverage

All 14 public tables have RLS **enabled**. Zero tables lack RLS. This is excellent for a project of this maturity.

| Table | RLS Enabled | Policy Count | Coverage Assessment |
|-------|-------------|-------------|---------------------|
| profiles | YES | 4 | GOOD (SELECT, UPDATE, INSERT own + service) |
| plans | YES | 1 | ADEQUATE (read-only public catalog) |
| user_subscriptions | YES | 2 | GOOD (fixed in migration 016) |
| search_sessions | YES | 3 | GOOD (fixed in migration 016) |
| monthly_quota | YES | 2 | GOOD (fixed in migration 016) |
| plan_features | YES | 1 | ADEQUATE (read-only catalog) |
| stripe_webhook_events | YES | 2 | GOOD (admin check fixed in migration 016) |
| conversations | YES | 3 | GOOD |
| messages | YES | 3 | GOOD |
| user_oauth_tokens | YES | 4 | EXCELLENT (gold standard) |
| google_sheets_exports | YES | 4 | EXCELLENT (gold standard) |
| audit_events | YES | 2 | GOOD (service_role + admin read) |
| pipeline_items | YES | 5 | **HAS GAP** (service role policy too permissive) |
| search_results_cache | YES | 2 | **HAS GAP** (service role policy too permissive) |

### 1.2 Issues Found

#### SEC-01: Overly permissive RLS on `pipeline_items` (migration 025)

**Severity:** HIGH
**File:** `supabase/migrations/025_create_pipeline_items.sql`, line 102-105
**Issue:** The "Service role full access" policy uses `FOR ALL USING (true)` without `TO service_role`. This allows ANY authenticated user to perform INSERT, UPDATE, DELETE on ANY user's pipeline items, bypassing the per-user policies.

```sql
-- CURRENT (vulnerable):
CREATE POLICY "Service role full access on pipeline_items"
  ON public.pipeline_items
  FOR ALL
  USING (true);

-- SHOULD BE:
CREATE POLICY "Service role full access on pipeline_items"
  ON public.pipeline_items
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
```

**Impact:** Any authenticated user could read, modify, or delete other users' pipeline items by constructing direct PostgREST requests. The per-user policies (`Users can view/insert/update/delete own`) are effectively overridden by the permissive `FOR ALL USING (true)`.

**Note:** This is the same class of bug that was fixed for `monthly_quota` and `search_sessions` in migration 016. The pattern was not applied to the newer tables.

#### SEC-02: Overly permissive RLS on `search_results_cache` (migration 026)

**Severity:** HIGH
**File:** `supabase/migrations/026_search_results_cache.sql`, line 31-35
**Issue:** Same pattern as SEC-01. The service role policy lacks `TO service_role`, allowing any authenticated user to INSERT, UPDATE, DELETE on any user's cache entries.

```sql
-- CURRENT (vulnerable):
CREATE POLICY "Service role full access on search_results_cache"
    ON search_results_cache
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- SHOULD BE:
CREATE POLICY "Service role full access on search_results_cache"
    ON search_results_cache
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
```

**Impact:** An authenticated user could write arbitrary JSONB data to another user's cache, or read other users' cached search results (which may contain business-sensitive procurement data).

#### SEC-03: `stripe_webhook_events` INSERT policy not role-scoped

**Severity:** MEDIUM
**File:** `supabase/migrations/010_stripe_webhook_events.sql`, line 56-58
**Issue:** The INSERT policy `webhook_events_insert_service` uses `WITH CHECK (true)` without `TO service_role`. While migration 016 fixed the SELECT policy, the INSERT policy was not addressed.

```sql
CREATE POLICY "webhook_events_insert_service" ON public.stripe_webhook_events
  FOR INSERT
  WITH CHECK (true);  -- Any authenticated user can insert
```

**Impact:** Any authenticated user could insert fake webhook events, potentially poisoning the idempotency check and causing real webhook events to be skipped. The `CHECK (id ~ '^evt_')` constraint mitigates this slightly by requiring Stripe event ID format.

#### SEC-04: `search_results_cache` missing INSERT policy for users

**Severity:** LOW
**File:** `supabase/migrations/026_search_results_cache.sql`
**Issue:** Users only have a SELECT policy (`Users can read own search cache`). There is no user-level INSERT, UPDATE, or DELETE policy. All write operations depend on the overly-permissive service role policy (SEC-02). If SEC-02 is fixed by adding `TO service_role`, users will lose the ability to insert their own cache entries through client-side calls (though the backend uses service_role key, so this is only relevant if future client-side caching is implemented).

### 1.3 Issues Resolved Since Last Audit

| Previous Issue | Status | Fixed By |
|---------------|--------|----------|
| CRITICAL-RLS-1: user_subscriptions no service role policy | RESOLVED | Migration 016 |
| CRITICAL-RLS-2: profiles no INSERT policy | RESOLVED | Migration 020 |
| CRITICAL-RLS-3: webhook admin check uses plan_type | RESOLVED | Migration 016 |
| RLS-PERM-1: monthly_quota/search_sessions permissive USING(true) | RESOLVED | Migration 016 |

---

## 2. Data Integrity Audit

### 2.1 Schema Integrity Issues

#### INTEGRITY-01: Missing `status` column on `user_subscriptions` (CRITICAL)

**Severity:** CRITICAL
**File:** `supabase/migrations/017_sync_plan_type_trigger.sql`
**Issue:** The `sync_profile_plan_type()` trigger function references `NEW.status` with expected values `('active', 'trialing', 'canceled', 'expired', 'past_due')`. However, NO migration in the 001-026 sequence adds a `status` column to the `user_subscriptions` table.

The trigger is attached as:
```sql
CREATE TRIGGER trg_sync_profile_plan_type
    AFTER INSERT OR UPDATE ON user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION sync_profile_plan_type();
```

**Possible scenarios:**
1. The `status` column was added manually (via Supabase SQL editor) outside the migration sequence -- likely but not traceable.
2. The trigger silently fails on every INSERT/UPDATE because `NEW.status` is always NULL -- the IF conditions (`NEW.status IN (...)`) would never match NULL, so the function body would do nothing and return NEW. This means the auto-sync feature is DEAD CODE if the column does not exist.
3. PostgreSQL may throw an error if `NEW.status` references a nonexistent column in a trigger function -- this would break ALL INSERT and UPDATE operations on `user_subscriptions`.

**Investigation needed:** Check production database for the existence of this column:
```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'user_subscriptions' AND column_name = 'status';
```

**Recommendation:** Create a migration to formally add the `status` column:
```sql
ALTER TABLE public.user_subscriptions
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'trialing', 'canceled', 'expired', 'past_due'));
```

#### INTEGRITY-02: `handle_new_user()` trigger overwrites on each migration

**Severity:** MEDIUM
**File:** Multiple migrations: 001, 007, 016, 024
**Issue:** The `handle_new_user()` function has been redefined 4 times across migrations. Each redefinition changes what fields are set. The latest version (migration 024) sets `context_data`, `company`, `sector`, `phone_whatsapp`, but drops `avatar_url` and the explicit `plan_type = 'free_trial'` that was added in migration 016.

**Migration 016 version:** Includes `plan_type = 'free_trial'`, `avatar_url`
**Migration 024 version:** Includes `context_data`, `company`, `sector`, `phone_whatsapp`, but OMITS `avatar_url` and OMITS explicit `plan_type`

Since the column default for `plan_type` is still `'free'` (from migration 001), and the trigger no longer sets `'free_trial'` explicitly, new users created after migration 024 may get `plan_type = 'free'` -- which is NOT a valid value in the tightened constraint from migration 020.

**Wait:** The INSERT uses column defaults. If `plan_type` is not specified in the INSERT, it uses the column default `'free'`. But migration 020 tightened the CHECK constraint to only allow `'free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master'`. This means `'free'` will VIOLATE THE CHECK CONSTRAINT, and new user signups will FAIL.

**CRITICAL IMPACT:** New user registration is broken if migration 024 was applied after migration 020 AND the column default was not updated.

**Recommendation:** Update the column default AND the trigger:
```sql
ALTER TABLE public.profiles ALTER COLUMN plan_type SET DEFAULT 'free_trial';
```
AND ensure the trigger explicitly sets `plan_type = 'free_trial'`.

#### INTEGRITY-03: FK references to `auth.users` instead of `profiles`

**Severity:** MEDIUM
**Files:** Migrations 025 (pipeline_items), 026 (search_results_cache)
**Issue:** These newer tables reference `auth.users(id)` instead of `profiles(id)`, despite migration 018 having standardized the older tables to `profiles(id)`.

**Tables still referencing `auth.users(id)`:**
- `pipeline_items.user_id`
- `search_results_cache.user_id`

**Recommendation:** Create a new migration to standardize:
```sql
ALTER TABLE pipeline_items DROP CONSTRAINT pipeline_items_user_id_fkey;
ALTER TABLE pipeline_items ADD CONSTRAINT pipeline_items_user_id_profiles_fkey
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE search_results_cache DROP CONSTRAINT search_results_cache_user_id_fkey;
ALTER TABLE search_results_cache ADD CONSTRAINT search_results_cache_user_id_profiles_fkey
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
```

#### INTEGRITY-04: `_ensure_profile_exists()` uses wrong plan_type default

**Severity:** MEDIUM
**File:** `backend/quota.py`, line 787-791
**Issue:** The fallback profile creation uses `"plan_type": "free"`, which violates the tightened CHECK constraint from migration 020 that only allows `'free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master'`.

```python
sb.table("profiles").insert({
    "id": user_id,
    "email": email,
    "plan_type": "free",  # WRONG: should be "free_trial"
}).execute()
```

**Impact:** If a profile is missing and the code attempts to create one, the INSERT will fail with a CHECK constraint violation.

### 2.2 Issues Resolved Since Last Audit

| Previous Issue | Status | Fixed By |
|---------------|--------|----------|
| INTEGRITY-1: plan_type CHECK includes legacy values | RESOLVED | Migration 020 |
| INTEGRITY-4: profiles.plan_type and user_subscriptions.plan_id drift | PARTIALLY RESOLVED | Migration 017 (but trigger may be dead code, see INTEGRITY-01) |
| SCHEMA-2: Inconsistent FK targets | PARTIALLY RESOLVED | Migration 018 (3 of 5 tables fixed; 2 new tables regressed) |
| SCHEMA-3: plans table lacks updated_at | RESOLVED | Migration 020 |
| SCHEMA-4: user_subscriptions missing updated_at | RESOLVED | Migration 021 |

---

## 3. Performance Audit

### 3.1 N+1 Query Patterns

| Pattern | Status | Resolution |
|---------|--------|------------|
| Conversation list + unread counts | **RESOLVED** | RPC `get_conversations_with_unread_count()` (migration 019, used in `routes/messages.py`) |
| Analytics summary full-table scan | **RESOLVED** | RPC `get_analytics_summary()` (migration 019, used in `routes/analytics.py`) |

### 3.2 Remaining Performance Concerns

#### PERF-01: `search_sessions` time-series query still fetches all rows

**Severity:** MEDIUM
**File:** `backend/routes/analytics.py`, line ~148-207
**Issue:** The `GET /analytics/searches-over-time` endpoint fetches all search sessions for a user (using `.select("sectors, ufs, total_raw, total_filtered, valor_total, created_at")`), then processes them in Python to build time-series data. For power users with 1000+ sessions, this transfers significant data over the wire.

**Recommendation:** Create an RPC function that performs the time-series aggregation server-side:
```sql
CREATE FUNCTION get_searches_over_time(p_user_id UUID, p_period TEXT, p_days INT)
RETURNS TABLE (label TEXT, searches BIGINT, opportunities BIGINT, value NUMERIC) AS $$
...
```

#### PERF-02: `search_results_cache.results` JSONB can be very large

**Severity:** MEDIUM
**File:** `supabase/migrations/026_search_results_cache.sql`
**Issue:** The `results` column stores full search results as JSONB. A typical search may return 50-200 procurement items, each with 15+ fields. At ~500 bytes per item, a single cache entry could be 10-100KB of JSONB. With 5 entries per user and 5,000 users, this is 250MB-2.5GB.

**Recommendation:**
- Monitor table size: `SELECT pg_size_pretty(pg_total_relation_size('search_results_cache'));`
- Consider compressing or truncating cached results
- Consider adding a `size_bytes` column for monitoring
- The max-5-per-user trigger mitigates unbounded growth

#### PERF-03: `admin.py` user list query with embedded join

**Severity:** LOW
**File:** `backend/admin.py`, line 268
**Issue:** The admin user list query uses Supabase's embedded join syntax:
```python
sb.table("profiles").select("*, user_subscriptions(id, plan_id, credits_remaining, expires_at, is_active)", count="exact")
```
This is fine for small user bases (<5,000) but may become slow with pagination at scale due to the embedded join.

### 3.3 Index Coverage Assessment

| Query Pattern | Table(s) | Index Coverage | Status |
|---------------|----------|---------------|--------|
| User quota lookup by month | monthly_quota | `idx_monthly_quota_user_month` + unique constraint | GOOD |
| Active subscription lookup | user_subscriptions | `idx_user_subscriptions_active` (partial) | GOOD |
| Stripe webhook by sub_id | user_subscriptions | `idx_user_subscriptions_stripe_sub_id` (unique partial) | GOOD (fixed in 016) |
| Stripe webhook by customer_id | user_subscriptions | `idx_user_subscriptions_customer_id` (partial) | GOOD (added in 022) |
| Admin user search by email | profiles | `idx_profiles_email_trgm` (GIN trigram) | GOOD (added in 016) |
| Search history list | search_sessions | `idx_search_sessions_created` (user_id, created_at DESC) | GOOD |
| Pipeline items by stage | pipeline_items | `idx_pipeline_user_stage` | GOOD |
| Cache lookup by user | search_results_cache | `idx_search_cache_user` | GOOD |
| Audit events by type + time | audit_events | `idx_audit_events_type_timestamp` (composite) | GOOD |
| Unread message count | messages | `idx_messages_unread_by_user/admin` (partial) | GOOD |

All critical query patterns have appropriate index coverage.

### 3.4 Issues Resolved Since Last Audit

| Previous Issue | Status | Fixed By |
|---------------|--------|----------|
| PERF-IDX-1: Missing stripe_subscription_id index | RESOLVED | Migration 016 |
| PERF-IDX-2: Missing stripe_customer_id index | RESOLVED | Migration 022 |
| PERF-IDX-3: Missing profiles.email trigram index | RESOLVED | Migration 016 |
| PERF-IDX-4: Redundant provider index on user_oauth_tokens | RESOLVED | Migration 022 (dropped) |
| PERF-QUERY-1: N+1 in conversation list | RESOLVED | Migration 019 (RPC function) |
| PERF-QUERY-2: Analytics full-table scan | RESOLVED | Migration 019 (RPC function) |

---

## 4. Migration Strategy Assessment

### 4.1 Migration Quality

**Positive patterns (well-designed):**
- Idempotent operations: `IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, `DROP ... IF EXISTS`
- Inline documentation: `COMMENT ON TABLE/COLUMN/CONSTRAINT/INDEX`
- Validation blocks: `DO $$ ... $$` with RAISE EXCEPTION on failure
- Verification queries in comments (run after applying)
- Rollback scripts provided (008_rollback.sql.bak)
- Transactional safety: Data migration BEFORE constraint changes (migration 020)

**Issues:**

#### MIGRATE-01: Deprecated duplicate file still in directory

**Severity:** LOW
**File:** `006b_DEPRECATED_search_sessions_service_role_policy_DUPLICATE.sql`
**Issue:** This file is clearly marked as deprecated but still exists in the migrations directory. While it has a header saying "DO NOT APPLY", its presence could cause confusion during automated migration runs.

**Recommendation:** Move to an `archive/` or `deprecated/` subdirectory.

#### MIGRATE-02: Hardcoded Stripe price IDs persist in migration 015

**Severity:** MEDIUM
**File:** `015_add_stripe_price_ids_monthly_annual.sql`
**Issue:** Production Stripe price IDs are hardcoded in the migration. Migration 021 adds comments documenting this as environment-specific, but the underlying issue remains.

**Status:** Documented (migration 021 added environment-specific instructions as SQL comments). Not yet resolved structurally.

#### MIGRATE-03: `handle_new_user()` trigger has been redefined 4 times

**Severity:** HIGH
**Files:** Migrations 001, 007, 016, 024
**Issue:** Each migration uses `CREATE OR REPLACE FUNCTION` to redefine the trigger function. The latest version (024) may conflict with constraints set by intermediate migrations (see INTEGRITY-02 above).

**Recommendation:** Consolidate the trigger function into a single authoritative version. Future changes should be made in a single new migration that documents all fields.

### 4.2 Migration Coverage

| Schema Object | Fully Migration-Tracked | Notes |
|---------------|------------------------|-------|
| Tables (14) | YES | All tables created via migrations |
| Columns | MOSTLY | `status` on user_subscriptions may be missing (see INTEGRITY-01) |
| Indexes (~52) | YES | All indexes created via migrations |
| RLS Policies (~38) | YES | All policies created via migrations |
| Functions (14) | YES | All functions created via migrations |
| Triggers (9) | YES | All triggers created via migrations |
| Seed data (plans, plan_features) | YES | Seeded in migrations 001, 005, 009, 015 |
| Extensions (pg_trgm, pg_cron) | YES | Created in migrations 016, 022 |

---

## 5. Technical Debt Inventory

### Active Issues (Ordered by Severity)

| ID | Issue | Severity | Category | File Reference | Recommendation |
|----|-------|----------|----------|---------------|----------------|
| TD-01 | Missing `status` column on user_subscriptions (trigger 017 references it) | CRITICAL | Schema | `017_sync_plan_type_trigger.sql` | Add migration with status column + CHECK constraint |
| TD-02 | `handle_new_user()` trigger omits plan_type after migration 024, column default is `'free'` which violates CHECK | CRITICAL | Schema | `024_add_profile_context.sql` | Fix trigger AND column default to `'free_trial'` |
| TD-03 | `pipeline_items` RLS policy FOR ALL USING(true) without TO service_role | HIGH | Security | `025_create_pipeline_items.sql:102` | Add `TO service_role` |
| TD-04 | `search_results_cache` RLS policy FOR ALL USING(true) without TO service_role | HIGH | Security | `026_search_results_cache.sql:31` | Add `TO service_role` |
| TD-05 | `stripe_webhook_events` INSERT policy not scoped to service_role | MEDIUM | Security | `010_stripe_webhook_events.sql:56` | Add `TO service_role` |
| TD-06 | `_ensure_profile_exists()` uses `plan_type: "free"` violating CHECK | MEDIUM | Code | `backend/quota.py:791` | Change to `"free_trial"` |
| TD-07 | `pipeline_items` and `search_results_cache` FK to auth.users not profiles | MEDIUM | Schema | Migrations 025, 026 | Standardize to profiles(id) |
| TD-08 | Hardcoded Stripe price IDs in migration 015 | MEDIUM | DevOps | `015_add_stripe_price_ids_monthly_annual.sql` | Move to env/config |
| TD-09 | `search_sessions` time-series query fetches all rows | MEDIUM | Performance | `routes/analytics.py:148+` | Add RPC for server-side aggregation |
| TD-10 | `search_results_cache.results` JSONB can be very large | MEDIUM | Performance | `026_search_results_cache.sql` | Monitor size, consider compression |
| TD-11 | Deprecated migration file still in directory | LOW | Maintenance | `006b_DEPRECATED_...DUPLICATE.sql` | Move to archive/ |
| TD-12 | `pipeline_items` uses separate `update_pipeline_updated_at()` instead of reusing `update_updated_at()` | LOW | Code Style | `025_create_pipeline_items.sql:57` | Use shared function |

### Resolved Issues (Since Feb 11 Audit)

| Previous ID | Issue | Resolved By |
|-------------|-------|-------------|
| TD-01 (old) | Dual ORM (Supabase + SQLAlchemy) | Still exists but less critical (documented) |
| TD-02 (old) | database.py connection string derivation | Still exists but backend routes use Supabase client exclusively |
| TD-03 (old) | Duplicate migration 006 | Partially resolved (deprecated file renamed) |
| TD-04 (old) | Missing updated_at on user_subscriptions | RESOLVED (migration 021) |
| TD-05 (old) | Inconsistent FK targets | RESOLVED for 3 tables (migration 018); regressed for 2 new tables |
| TD-06 (old) | Legacy plan types in CHECK | RESOLVED (migration 020) |
| TD-07 (old) | user_subscriptions missing service role policy | RESOLVED (migration 016) |
| TD-08 (old) | webhook admin check uses plan_type | RESOLVED (migration 016) |
| TD-09 (old) | Overly permissive USING(true) | RESOLVED for old tables (migration 016); regressed for 2 new tables |
| TD-11 (old) | N+1 query in conversation list | RESOLVED (migration 019) |
| TD-12 (old) | Analytics full-table scan | RESOLVED (migration 019) |
| TD-13 (old) | Missing stripe_subscription_id index | RESOLVED (migration 016) |
| TD-14 (old) | Missing trigram index on profiles.email | RESOLVED (migration 016) |
| TD-15 (old) | No retention cleanup for monthly_quota | RESOLVED (migration 022, pg_cron) |
| TD-16 (old) | No retention cleanup for stripe_webhook_events | RESOLVED (migration 022, pg_cron) |
| TD-17 (old) | plan_type/plan_id drift | PARTIALLY RESOLVED (migration 017 trigger, but may be dead code) |
| TD-18 (old) | plan_id FK ON DELETE not documented | RESOLVED (migration 022 documents as intentional RESTRICT) |

---

## 6. Recommendations (Prioritized)

### P0 - Critical (Fix Immediately)

1. **Verify `user_subscriptions.status` column exists in production** (TD-01)
   - Run: `SELECT column_name FROM information_schema.columns WHERE table_name = 'user_subscriptions' AND column_name = 'status';`
   - If missing: Create migration `027_add_subscription_status.sql`
   - If present: Document which manual operation added it

2. **Fix `handle_new_user()` trigger and column default** (TD-02)
   - Create migration `027_fix_handle_new_user.sql` that:
     - Sets `ALTER TABLE profiles ALTER COLUMN plan_type SET DEFAULT 'free_trial'`
     - Redefines `handle_new_user()` with explicit `plan_type = 'free_trial'`
   - Verify new user signup works: create a test user via Supabase Auth

3. **Fix `_ensure_profile_exists()` in backend code** (TD-06)
   - Change `"plan_type": "free"` to `"plan_type": "free_trial"` in `backend/quota.py:791`

### P1 - High (Fix This Sprint)

4. **Fix overly permissive RLS on `pipeline_items`** (TD-03)
   - Create migration to drop and recreate with `TO service_role`

5. **Fix overly permissive RLS on `search_results_cache`** (TD-04)
   - Create migration to drop and recreate with `TO service_role`

6. **Fix `stripe_webhook_events` INSERT policy** (TD-05)
   - Add `TO service_role` to the INSERT policy

### P2 - Medium (Fix Within 2 Sprints)

7. **Standardize `pipeline_items` and `search_results_cache` FKs** (TD-07)
   - Change FK target from `auth.users(id)` to `profiles(id)`

8. **Add server-side time-series aggregation RPC** (TD-09)
   - Create RPC function for `GET /analytics/searches-over-time`

9. **Monitor `search_results_cache` table size** (TD-10)
   - Set up alert for when table exceeds 500MB

### P3 - Low (Backlog)

10. **Move deprecated migration to archive/** (TD-11)
11. **Consolidate `update_pipeline_updated_at()` with `update_updated_at()`** (TD-12)
12. **Move Stripe price IDs to environment variables** (TD-08)

---

## 7. Positive Observations

These aspects are well-designed and should be preserved:

1. **Comprehensive migration-driven schema evolution.** 26 migrations tell the complete story of the database from inception to current state. Each migration is well-documented with story references, inline comments, and verification queries.

2. **Atomic quota functions** (migration 003). The `increment_quota_atomic()` and `check_and_increment_quota()` functions use `SELECT ... FOR UPDATE` and `ON CONFLICT DO UPDATE` patterns to prevent race conditions. This is production-grade concurrency control.

3. **Multi-layer plan fallback in `quota.py`.** The 4-layer resilience strategy (active subscription -> grace period -> profile fallback -> free_trial) with explicit "fail to last known plan" policy prevents paid users from being downgraded on transient errors. The 3-day grace period covers Stripe billing gaps.

4. **100% RLS coverage.** All 14 tables have RLS enabled, with defense-in-depth policies. Most tables follow the gold standard pattern: user-level SELECT/INSERT/UPDATE/DELETE + explicit service_role policy.

5. **RPC functions for N+1 elimination.** Migration 019 introduced `get_conversations_with_unread_count()` and `get_analytics_summary()` to eliminate N+1 queries and full-table scans. These are used correctly in the backend routes.

6. **pg_cron retention automation.** Three cleanup jobs with staggered schedules (2 AM, 3 AM, 4 AM UTC) handle data retention for monthly_quota (24 months), stripe_webhook_events (90 days), and audit_events (12 months).

7. **Privacy-first audit logging.** The `audit_events` table hashes all PII (user IDs, IP addresses) with SHA-256 truncated to 16 hex chars before storage. This enables forensic investigation while complying with LGPD/GDPR.

8. **Search cache self-limitation.** The `cleanup_search_cache_per_user()` trigger automatically caps cache entries at 5 per user, preventing unbounded growth without requiring external cleanup jobs.

9. **Partial indexes for common patterns.** Excellent use of partial indexes: `WHERE is_active = true`, `WHERE is_admin = true`, `WHERE stripe_subscription_id IS NOT NULL`, `WHERE stage NOT IN ('enviada', 'resultado')`. These reduce index size and improve performance for the most common queries.

10. **Systematic resolution of previous audit findings.** Migrations 016-022 systematically addressed 15 of the 19 technical debt items from the February 11 audit, demonstrating a healthy engineering culture of addressing debt proactively.

---

## Appendix A: Query Patterns by Table

### High-Frequency Queries (Every Search Request)

```
1. auth.users -> JWT validation (Supabase Auth middleware)
2. profiles -> SELECT plan_type (quota.py:get_plan_from_profile)
3. user_subscriptions -> SELECT plan_id, expires_at WHERE is_active=true (quota.py:check_quota)
4. monthly_quota -> RPC check_and_increment_quota (quota.py)
5. search_sessions -> INSERT (quota.py:save_search_session)
6. audit_events -> INSERT (audit.py:audit_logger.log) [if audit enabled]
```

### Medium-Frequency Queries (User Navigation)

```
7. search_sessions -> SELECT WHERE user_id ORDER BY created_at DESC (routes/sessions.py)
8. conversations -> RPC get_conversations_with_unread_count (routes/messages.py)
9. pipeline_items -> SELECT WHERE user_id AND stage (routes/pipeline.py)
10. plans -> SELECT WHERE is_active=true (routes/plans.py)
```

### Low-Frequency Queries (Admin/Billing Events)

```
11. profiles -> SELECT with user_subscriptions JOIN (admin.py:list_users)
12. stripe_webhook_events -> SELECT id WHERE id=evt_xxx (webhook idempotency check)
13. user_oauth_tokens -> SELECT/UPSERT (oauth.py)
14. google_sheets_exports -> INSERT (routes/export_sheets.py)
```

## Appendix B: Schema Drift Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `handle_new_user()` trigger creates invalid plan_type | HIGH (if migration 024 was applied after 020) | CRITICAL (new signups fail) | Fix trigger + column default immediately |
| `sync_profile_plan_type()` trigger is dead code | MEDIUM (depends on status column existence) | HIGH (plan_type drift not auto-corrected) | Verify column, add if missing |
| Pipeline/cache RLS allows cross-user access | LOW (requires direct PostgREST knowledge) | HIGH (data breach) | Add `TO service_role` to policies |
| Stripe price IDs incorrect in staging/dev | LOW (only affects non-production) | MEDIUM (broken checkout) | Move to env vars |

## Appendix C: Comparison with Previous Audit

```
Feb 11, 2026 (Previous):
  Tables: 11 | Migrations: 15 | Policies: ~25 | Health: 6.5/10

Feb 15, 2026 (Current):
  Tables: 14 | Migrations: 26 | Policies: ~38 | Health: 7.5/10

Key Improvements:
  + 11 new migrations addressing 15 previous debt items
  + 3 new tables (audit_events, pipeline_items, search_results_cache)
  + 2 RPC functions eliminating N+1 queries
  + 3 pg_cron retention jobs
  + Tightened plan_type CHECK constraint
  + Standardized 3 FK references
  + Added 16 new indexes
  + Fixed webhook admin policy
  + Fixed overly permissive RLS on 3 tables

New Issues Introduced:
  - 2 new tables have same overly-permissive RLS pattern that was fixed
  - 2 new tables regress FK standardization
  - handle_new_user trigger regression may break signups
  - Missing status column for sync trigger
```
