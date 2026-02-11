# Database Audit Report - SmartLic/BidIQ

**Auditor:** @data-engineer (Dara)
**Date:** 2026-02-11
**Scope:** Full schema audit of Supabase (PostgreSQL 17) database
**Codebase:** `D:\pncp-poc` (branch: main, commit 808cd05)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Health** | 6.5 / 10 |
| **Critical Issues** | 3 |
| **High-Severity Issues** | 5 |
| **Medium-Severity Issues** | 7 |
| **Low-Severity Issues** | 4 |
| **Tables** | 11 |
| **Migrations** | 15 |
| **RLS Policies** | ~25 |
| **Functions** | 8 |
| **Indexes** | 36 |

The database schema is functional and supports the application well for a POC. However, there are several security gaps, architectural inconsistencies, and missing constraints that should be addressed before production hardening.

---

## 1. Security Audit (RLS)

### 1.1 Policies Found

All 11 public tables have RLS **enabled**. This is excellent -- zero tables have RLS disabled.

| Table | RLS Enabled | Policy Count | Coverage Assessment |
|-------|-------------|-------------|---------------------|
| profiles | YES | 2 | PARTIAL -- missing INSERT, DELETE |
| plans | YES | 1 | ADEQUATE -- read-only public catalog |
| user_subscriptions | YES | 1 | **CRITICAL GAP** -- SELECT only |
| search_sessions | YES | 3 | GOOD |
| monthly_quota | YES | 2 | GOOD |
| plan_features | YES | 1 | ADEQUATE -- read-only catalog |
| stripe_webhook_events | YES | 2 | GOOD |
| conversations | YES | 3 | GOOD |
| messages | YES | 3 | GOOD |
| user_oauth_tokens | YES | 4 | EXCELLENT |
| google_sheets_exports | YES | 4 | EXCELLENT |

### 1.2 Missing Policies (GAPS)

#### CRITICAL-RLS-1: `user_subscriptions` has no service role policy for writes

**File:** `supabase/migrations/001_profiles_and_sessions.sql` (lines 119-121)
**Severity:** CRITICAL
**Impact:** The backend uses `SUPABASE_SERVICE_ROLE_KEY` to INSERT and UPDATE subscriptions. While service_role key bypasses RLS by default in Supabase, if this behavior is ever changed or restricted, all subscription management will break silently.

The pattern inconsistency is the concern: `monthly_quota` and `search_sessions` both have explicit `"Service role can manage"` policies, but `user_subscriptions` does not. This is the **same bug** that was discovered and fixed for `search_sessions` in migration `006_search_sessions_service_role_policy.sql`.

**Current policies:** Only `subscriptions_select_own` (SELECT by user).
**Missing:** INSERT, UPDATE, DELETE policies for service role; INSERT policy for user (Stripe checkout).

**Recommendation:** Add explicit service role policy:
```sql
CREATE POLICY "Service role can manage subscriptions" ON public.user_subscriptions
    FOR ALL USING (true);
```

#### CRITICAL-RLS-2: `profiles` has no INSERT policy for auth trigger

**File:** `supabase/migrations/001_profiles_and_sessions.sql` (lines 110-113)
**Severity:** HIGH
**Impact:** The `handle_new_user()` trigger runs as `SECURITY DEFINER`, which bypasses RLS. However, if any application code attempts to insert a profile through the Supabase client (as `_ensure_profile_exists()` in `backend/quota.py:623-655` does), it relies on service_role key. An explicit INSERT policy would make the security model explicit.

**Missing:** INSERT policy for profiles.

#### CRITICAL-RLS-3: `stripe_webhook_events` admin check uses `plan_type = 'master'` instead of `is_admin`

**File:** `supabase/migrations/010_stripe_webhook_events.sql` (lines 61-68)
**Severity:** HIGH
**Impact:** The SELECT policy for viewing webhook events checks `profiles.plan_type = 'master'` but the actual admin flag is `profiles.is_admin`. A user with `is_admin = true` but `plan_type != 'master'` cannot view webhook events. Conversely, a non-admin master user CAN view webhook events.

**Current:**
```sql
CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.plan_type = 'master')
  );
```

**Should be:**
```sql
CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true)
  );
```

### 1.3 Overly Permissive Policies

#### RLS-PERM-1: Multiple `USING (true)` policies without role restriction

Several tables have `FOR ALL USING (true)` policies without restricting to `service_role`:

| Table | Policy | Concern |
|-------|--------|---------|
| monthly_quota | `Service role can manage quota` | No `TO service_role` clause |
| search_sessions | `Service role can manage search sessions` | No `TO service_role` clause |

Compare with `user_oauth_tokens` and `google_sheets_exports` which correctly use `TO service_role` in their service role policies. The policies on monthly_quota and search_sessions allow **any authenticated user** to perform any operation, not just the service role.

**Impact:** Medium. In practice, Supabase's PostgREST layer adds some protection, but this is defense-in-depth missing.

**Recommendation:** Add `TO service_role` to these policies:
```sql
CREATE POLICY "Service role can manage quota" ON monthly_quota
    FOR ALL TO service_role USING (true);
```

---

## 2. Performance Audit

### 2.1 Indexes Present

The project has **36 total indexes** across 11 tables, including 7 partial indexes and 1 GIN index. This is above average for a project of this size.

**Positive highlights:**
- Partial indexes on `is_active = true` for subscriptions (avoids scanning inactive rows)
- Partial indexes on unread message flags for badge count queries
- GIN index on `google_sheets_exports.search_params` for JSONB queries
- Descending index on `search_sessions(user_id, created_at DESC)` matches ORDER BY pattern

### 2.2 Missing Indexes (RECOMMENDATIONS)

#### PERF-IDX-1: `user_subscriptions.stripe_subscription_id` needs explicit index

**Severity:** HIGH
**Query Pattern:** Stripe webhook handler queries by `stripe_subscription_id` (see `backend/webhooks/stripe.py:187-189` and `backend/main.py:795`)
**Current:** The SQLAlchemy model defines `unique=True` on this column, but the SQL migration does NOT create this unique constraint. If the SQLAlchemy model's schema never ran `Base.metadata.create_all()`, the index may not exist.

**Recommendation:**
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_sub_id
  ON user_subscriptions(stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;
```

#### PERF-IDX-2: `user_subscriptions.stripe_customer_id` lacks index

**Severity:** MEDIUM
**Query Pattern:** Admin panel and Stripe webhook reconciliation may query by customer_id.
**Recommendation:**
```sql
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_customer_id
  ON user_subscriptions(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;
```

#### PERF-IDX-3: `profiles.email` lacks index

**Severity:** MEDIUM
**Query Pattern:** Admin search (`backend/admin.py:268-269`) uses `email.ilike.%search%` which requires a trigram index for efficiency.

**Recommendation:**
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_profiles_email_trgm
  ON profiles USING GIN(email gin_trgm_ops);
```

#### PERF-IDX-4: `user_oauth_tokens.provider` single-column index is redundant

**Severity:** LOW
**Explanation:** The table has at most a few hundred rows and the UNIQUE constraint on `(user_id, provider)` already creates an index that covers provider lookups when combined with user_id. The standalone `idx_user_oauth_tokens_provider` index on just `provider` (only 3 possible values) has very low selectivity and wastes space.

**Recommendation:** Drop `idx_user_oauth_tokens_provider`.

### 2.3 Query Performance Concerns

#### PERF-QUERY-1: N+1 query in conversation list endpoint

**File:** `backend/routes/messages.py:114-121`
**Issue:** For each conversation in the list, a separate query counts unread messages. With 50 conversations, this produces 51 queries.

**Recommendation:** Use a single aggregation query or a PostgreSQL CTE.

#### PERF-QUERY-2: Analytics endpoints fetch ALL sessions

**File:** `backend/routes/analytics.py:78-83`
**Issue:** `get_analytics_summary()` fetches ALL search sessions for a user (`SELECT id, total_raw, total_filtered, valor_total, created_at`). For power users with 1000+ sessions, this transfers significant data.

**Recommendation:** Use aggregate functions (`SUM`, `COUNT`, `AVG`) server-side via Supabase RPC or a database view.

---

## 3. Schema Design Issues

### SCHEMA-1: Dual ORM Architecture (Supabase Client + SQLAlchemy)

**Severity:** HIGH
**Files:**
- `backend/supabase_client.py` -- Used by 95% of code
- `backend/database.py` -- SQLAlchemy engine (used only by Stripe webhooks)
- `backend/models/` -- SQLAlchemy ORM models

**Issue:** The codebase maintains two completely separate database access layers:

1. **Supabase Python Client** (`supabase` library): Uses REST API to PostgREST, authenticated with service_role key. Used by auth, admin, quota, analytics, messaging, OAuth, exports.

2. **SQLAlchemy ORM** (`sqlalchemy`): Direct PostgreSQL connection. Used ONLY by `backend/webhooks/stripe.py`.

This creates several problems:
- `database.py` line 33 converts `SUPABASE_URL` (an HTTPS URL) to a PostgreSQL connection string, which is **incorrect**. `SUPABASE_URL` is `https://fqqyovlzdzimiwfofdjk.supabase.co`, not a PostgreSQL connection string. This means the SQLAlchemy connection likely fails silently or uses the localhost fallback.
- Two different transaction management strategies
- Two different connection pool configurations
- Schema drift risk between SQL migrations and SQLAlchemy models

**Recommendation:** Migrate the Stripe webhook handler to use the Supabase client (matching all other code), or introduce a proper `DATABASE_URL` env var with the actual PostgreSQL connection string from Supabase.

### SCHEMA-2: Inconsistent Foreign Key targets

**Severity:** MEDIUM
**Issue:** Some tables reference `auth.users(id)` while others reference `profiles(id)`:

| Table | FK Target | Consistent? |
|-------|-----------|-------------|
| profiles | auth.users(id) | N/A (bridge table) |
| user_subscriptions | profiles(id) | YES |
| search_sessions | profiles(id) | YES |
| monthly_quota | **auth.users(id)** | **NO** |
| conversations | profiles(id) | YES |
| messages | profiles(id) | YES |
| user_oauth_tokens | **auth.users(id)** | **NO** |
| google_sheets_exports | **auth.users(id)** | **NO** |

Tables from later migrations (002, 013, 014) reference `auth.users(id)` directly. While this works (because `profiles.id` has a cascading FK to `auth.users.id`), it creates an inconsistent pattern. If a profile is ever deleted independently of the auth user (hypothetically), the behavior differs.

**Recommendation:** Standardize all FKs to reference `profiles(id)` for consistency.

### SCHEMA-3: `plans` table lacks `updated_at` column

**Severity:** LOW
**Issue:** The `plans` table has `created_at` but no `updated_at`. When plan pricing or attributes change (as they did in migrations 005 and 015), there is no audit trail of when the change occurred.

### SCHEMA-4: `user_subscriptions` missing `updated_at` column in migration

**Severity:** LOW
**Issue:** The SQLAlchemy model (`backend/models/user_subscription.py:83`) defines `updated_at` with `onupdate=datetime.utcnow`, but the SQL migration `001_profiles_and_sessions.sql` does NOT include an `updated_at` column for `user_subscriptions`. The column exists in code but may not exist in the database unless added by a later migration or manual ALTER.

**Note:** Migration 008 writes to `updated_at` on user_subscriptions (`SET updated_at = now()` in backfill), suggesting this column was added at some point but the migration is not in the numbered series.

---

## 4. Data Integrity Concerns

### INTEGRITY-1: `plan_type` CHECK constraint includes legacy values

**File:** `supabase/migrations/006_update_profiles_plan_type_constraint.sql`
**Severity:** MEDIUM
**Issue:** The CHECK constraint allows 10 values including 4 legacy values (`'free'`, `'avulso'`, `'pack'`, `'monthly'`, `'annual'`) that no longer correspond to active plans. Code in `backend/quota.py:386-392` has a mapping from these legacy values, but nothing prevents new users from being assigned these deprecated plan types.

**Recommendation:** After confirming no users have legacy plan_type values, tighten the constraint:
```sql
ALTER TABLE profiles DROP CONSTRAINT profiles_plan_type_check;
ALTER TABLE profiles ADD CONSTRAINT profiles_plan_type_check
  CHECK (plan_type IN ('free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master'));
```

### INTEGRITY-2: `user_subscriptions.plan_id` FK has no ON DELETE action

**File:** `supabase/migrations/001_profiles_and_sessions.sql` (line 66)
**Severity:** MEDIUM
**Issue:** `plan_id text NOT NULL REFERENCES public.plans(id)` -- no ON DELETE clause. If a plan is deleted from the `plans` table, all subscriptions referencing it will cause a FK violation error. This is the PostgreSQL default (RESTRICT), which is actually a reasonable choice for plans (you should not delete a plan that has subscriptions). However, it should be explicitly documented.

### INTEGRITY-3: No validation that `billing_period` matches plan type

**Severity:** LOW
**Issue:** There is no constraint ensuring that `user_subscriptions.billing_period = 'annual'` is only valid for plans that support annual billing. Any plan (including `free_trial`) could theoretically have an annual billing period.

### INTEGRITY-4: `profiles.plan_type` and `user_subscriptions.plan_id` can drift

**Severity:** MEDIUM
**Issue:** Two sources of truth exist for a user's current plan:
1. `profiles.plan_type` (single column, always present)
2. `user_subscriptions` (latest active row's `plan_id`)

The code in `backend/quota.py:413-504` explicitly handles drift via a 4-layer fallback. While the fallback is well-designed for resilience, the underlying data model allows indefinite drift with no reconciliation mechanism.

**Recommendation:** Consider a periodic reconciliation job or trigger that syncs `profiles.plan_type` when `user_subscriptions` changes.

---

## 5. Migration Strategy Assessment

### 5.1 Migration Files

| # | File | Date | Story | Content |
|---|------|------|-------|---------|
| 001 | `001_profiles_and_sessions.sql` | - | - | Core schema: profiles, plans, user_subscriptions, search_sessions, RLS, triggers |
| 002 | `002_monthly_quota.sql` | 2026-02-03 | PNCP-165 | monthly_quota table |
| 003 | `003_atomic_quota_increment.sql` | 2026-02-04 | Issue #189 | increment_quota_atomic + check_and_increment_quota functions |
| 004 | `004_add_is_admin.sql` | - | - | profiles.is_admin column |
| 005 | `005_update_plans_to_new_tiers.sql` | 2026-02-05 | - | Deactivate old plans, add new tiers |
| 006a | `006_update_profiles_plan_type_constraint.sql` | 2026-02-06 | - | Update CHECK constraint for new plan types |
| 006b | `006_APPLY_ME.sql` | 2026-02-10 | P0-CRITICAL | Service role policy for search_sessions (manual apply) |
| 006c | `006_search_sessions_service_role_policy.sql` | 2026-02-10 | P0-CRITICAL | Same as 006b (duplicate file) |
| 007 | `007_add_whatsapp_consent.sql` | - | STORY-166 | Marketing consent fields on profiles |
| 008 | `008_add_billing_period.sql` | 2026-02-07 | STORY-171 | billing_period + annual_benefits on user_subscriptions |
| 008r | `008_rollback.sql.bak` | 2026-02-07 | STORY-171 | Rollback script for 008 |
| 009 | `009_create_plan_features.sql` | 2026-02-07 | STORY-171 | plan_features table + seed data |
| 010 | `010_stripe_webhook_events.sql` | - | STORY-171 | stripe_webhook_events table |
| 011 | `011_add_billing_helper_functions.sql` | 2026-02-07 | STORY-171 | Helper DB functions |
| 012 | `012_create_messages.sql` | - | - | conversations + messages tables (InMail) |
| 013 | `013_google_oauth_tokens.sql` | - | STORY-180 | user_oauth_tokens table |
| 014 | `014_google_sheets_exports.sql` | - | STORY-180 | google_sheets_exports table |
| 015 | `015_add_stripe_price_ids_monthly_annual.sql` | 2026-02-10 | - | Add stripe_price_id_monthly/annual to plans |

### 5.2 Migration Strategy Issues

#### MIGRATE-1: Duplicate migration number 006

**Severity:** HIGH
**Issue:** Three files share the `006_` prefix:
- `006_update_profiles_plan_type_constraint.sql`
- `006_APPLY_ME.sql`
- `006_search_sessions_service_role_policy.sql`

The latter two appear to be the same migration (service role policy for search_sessions). The `006_APPLY_ME.sql` file contains instructions to "COPY AND PASTE THIS SQL INTO SUPABASE DASHBOARD SQL EDITOR", indicating it was applied manually rather than through `supabase db push`.

This creates ambiguity about which migrations have been applied and in what order.

#### MIGRATE-2: No migration for `updated_at` on `user_subscriptions`

**Severity:** MEDIUM
**Issue:** The `user_subscriptions` table in migration 001 does NOT include an `updated_at` column, but migration 008 and application code both write to this column. Either:
- An unmigrated ALTER TABLE was applied manually
- The `updated_at` column was added via the Supabase dashboard
- The column does not exist and these writes fail silently

#### MIGRATE-3: Hardcoded Stripe price IDs in migration 015

**Severity:** MEDIUM
**Issue:** Migration `015_add_stripe_price_ids_monthly_annual.sql` contains production Stripe price IDs hardcoded in SQL:
```sql
stripe_price_id_monthly = 'price_1Syir09FhmvPslGYOCbOvWVB'
```

These are environment-specific values that should not be in migration files. If this migration is applied to a different environment (staging, dev), it will set incorrect Stripe prices.

**Recommendation:** Use seed scripts or environment-specific data loading, not migrations, for Stripe price IDs.

#### MIGRATE-4: Credentials in migration 013 comments are acceptable

**Observation:** Migration 013 (OAuth tokens) correctly does NOT contain any secrets. Tokens are encrypted at the application layer before storage. This is well-designed.

#### MIGRATE-5: `supabase db push` vs manual SQL execution

**Severity:** MEDIUM
**Issue:** The presence of `006_APPLY_ME.sql` with "COPY AND PASTE" instructions suggests some migrations are applied manually via the Supabase SQL editor rather than through `supabase db push`. This means:
- No automated tracking of which migrations have been applied
- Risk of applying migrations out of order
- Risk of missing migrations in certain environments

**Recommendation:** Standardize on `supabase db push` for all schema changes. Remove manual-apply files and integrate them into the numbered sequence.

---

## 6. Technical Debt Inventory

| ID | Issue | Severity | Category | File Reference | Recommendation |
|----|-------|----------|----------|---------------|----------------|
| TD-01 | Dual ORM (Supabase client + SQLAlchemy) | HIGH | Architecture | `database.py`, `webhooks/stripe.py` | Consolidate to single access layer |
| TD-02 | `database.py` incorrectly derives PostgreSQL URL from SUPABASE_URL | CRITICAL | Bug | `database.py:33` | Add proper `DATABASE_URL` env var or use Supabase client in webhooks |
| TD-03 | Duplicate migration 006 (3 files) | HIGH | Migration | `supabase/migrations/006_*` | Consolidate and renumber |
| TD-04 | Missing `updated_at` column in migration 001 for user_subscriptions | MEDIUM | Schema | `001_profiles_and_sessions.sql` | Add remediation migration |
| TD-05 | Inconsistent FK targets (auth.users vs profiles) | MEDIUM | Schema | migrations 002, 013, 014 | Standardize on profiles(id) |
| TD-06 | Legacy plan types in CHECK constraint | MEDIUM | Data Integrity | `006_update_profiles_plan_type_constraint.sql` | Tighten after data migration |
| TD-07 | `user_subscriptions` missing service role RLS policy | CRITICAL | Security | `001_profiles_and_sessions.sql` | Add explicit policy |
| TD-08 | `stripe_webhook_events` admin check uses `plan_type` not `is_admin` | HIGH | Security | `010_stripe_webhook_events.sql` | Fix policy expression |
| TD-09 | Overly permissive `USING (true)` without `TO service_role` | MEDIUM | Security | migrations 002, 006 | Add role restriction |
| TD-10 | Hardcoded Stripe price IDs in migration 015 | MEDIUM | DevOps | `015_add_stripe_price_ids_monthly_annual.sql` | Move to seed/config |
| TD-11 | N+1 query in conversation list | MEDIUM | Performance | `routes/messages.py:114-121` | Use aggregation |
| TD-12 | Analytics endpoints fetch all rows | MEDIUM | Performance | `routes/analytics.py:78-83` | Use server-side aggregation |
| TD-13 | Missing index on `user_subscriptions.stripe_subscription_id` | HIGH | Performance | SQL migrations | Add unique index |
| TD-14 | Missing trigram index on `profiles.email` for ILIKE search | MEDIUM | Performance | `admin.py:268` | Add pg_trgm index |
| TD-15 | No retention/cleanup for `monthly_quota` historical rows | LOW | Maintenance | - | Add periodic cleanup |
| TD-16 | No retention/cleanup for `stripe_webhook_events` | LOW | Maintenance | Migration 010 mentions 90-day retention | Implement cleanup job |
| TD-17 | `plan_type` and `user_subscriptions.plan_id` can drift indefinitely | MEDIUM | Data Integrity | `quota.py:413-504` | Add reconciliation job |
| TD-18 | `plans.plan_id` FK on user_subscriptions has no explicit ON DELETE | LOW | Schema | `001_profiles_and_sessions.sql:66` | Document as intentional RESTRICT |
| TD-19 | No database-level constraint linking billing_period to plan | LOW | Data Integrity | - | Add CHECK or trigger |

---

## 7. Recommendations (Prioritized)

### P0 - Critical (Fix Immediately)

1. **Fix `database.py` connection string derivation** (TD-02)
   - The SQLAlchemy engine constructs a PostgreSQL URL by replacing `https://` in `SUPABASE_URL`, which produces an invalid connection string. Either:
     - Add `DATABASE_URL` environment variable pointing to the actual Supabase PostgreSQL connection string (found in Supabase dashboard > Settings > Database)
     - OR migrate Stripe webhook handler to use the Supabase Python client

2. **Add service role RLS policy to `user_subscriptions`** (TD-07)
   - Follow the pattern established in migrations 006 (search_sessions) and 002 (monthly_quota)
   - Create migration `016_add_service_role_policy_subscriptions.sql`

3. **Fix `stripe_webhook_events` admin policy** (TD-08)
   - Change `plan_type = 'master'` to `is_admin = true` in the SELECT policy

### P1 - High (Fix This Sprint)

4. **Consolidate migration 006 duplicates** (TD-03)
   - Remove `006_APPLY_ME.sql`, keep `006_search_sessions_service_role_policy.sql`
   - Verify the policy was actually applied in production

5. **Add missing index on `stripe_subscription_id`** (TD-13)
   - Create partial unique index for non-null values

6. **Tighten overly permissive RLS policies** (TD-09)
   - Add `TO service_role` to monthly_quota and search_sessions service role policies

7. **Resolve dual ORM architecture** (TD-01)
   - Preferred approach: Migrate Stripe webhook handler to Supabase client
   - Alternative: Properly configure SQLAlchemy with correct PostgreSQL URL

### P2 - Medium (Fix Within 2 Sprints)

8. **Standardize FK references** (TD-05) -- Use `profiles(id)` consistently
9. **Tighten plan_type CHECK constraint** (TD-06) -- After migrating legacy users
10. **Add remediation migration for `updated_at` on user_subscriptions** (TD-04)
11. **Fix N+1 query in conversation list** (TD-11)
12. **Implement server-side aggregation for analytics** (TD-12)
13. **Add trigram index for admin email search** (TD-14)
14. **Move Stripe price IDs to seed/config** (TD-10)
15. **Add reconciliation job for plan_type drift** (TD-17)

### P3 - Low (Backlog)

16. **Add `updated_at` to `plans` table** (SCHEMA-3)
17. **Implement 90-day retention cleanup for webhook events** (TD-16)
18. **Implement periodic cleanup for historical monthly_quota rows** (TD-15)
19. **Drop redundant `idx_user_oauth_tokens_provider` index** (PERF-IDX-4)
20. **Add billing_period validation against plan capabilities** (TD-19)

---

## 8. Positive Observations

These aspects are well-designed and should be preserved:

1. **Atomic quota increment functions** (migration 003) -- Excellent race condition prevention using PostgreSQL `SELECT ... FOR UPDATE` and `ON CONFLICT DO UPDATE`. The two-function approach (raw increment + check-and-increment) provides flexibility.

2. **Multi-layer plan fallback in `quota.py`** -- The 4-layer resilience strategy (active subscription -> grace period -> profile fallback -> free_trial) with explicit "fail to last known plan" policy prevents paid users from being downgraded on transient errors.

3. **Comprehensive RLS on all tables** -- 11/11 tables have RLS enabled, which is uncommon for early-stage projects.

4. **Partial indexes** -- Good use of `WHERE is_active = true` and `WHERE is_admin = true` to reduce index size and improve lookup speed for the most common query patterns.

5. **GIN index on JSONB** -- The `google_sheets_exports.search_params` GIN index enables efficient JSONB queries for export history.

6. **Token encryption at rest** -- OAuth tokens are encrypted with AES-256 (Fernet) before storage, with the encryption happening in application code (`backend/oauth.py`), not relying on PostgreSQL TDE.

7. **Webhook idempotency** -- The `stripe_webhook_events` table with primary key on Stripe event ID provides clean deduplication.

8. **Well-structured migrations** -- Migrations include validation blocks (`DO $$ ... $$`), inline documentation with COMMENT ON, rollback scripts (008_rollback.sql.bak), and idempotent patterns (IF NOT EXISTS, ON CONFLICT DO NOTHING).

9. **Trigger-based auto-profiles** -- The `handle_new_user()` trigger automatically creates profiles on signup, including WhatsApp consent fields from user metadata.

10. **Partial indexes for unread message badges** -- The `idx_messages_unread_by_user` and `idx_messages_unread_by_admin` partial indexes are precisely tailored for the badge count queries, avoiding full table scans.

---

## Appendix A: Environment Variables for Database

| Variable | Required | Used By | Purpose |
|----------|----------|---------|---------|
| `SUPABASE_URL` | YES | supabase_client.py, database.py | Supabase project URL |
| `SUPABASE_ANON_KEY` | YES | supabase_client.py (frontend JWT verify) | Public anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | YES | supabase_client.py | Admin access key (bypasses RLS) |
| `ADMIN_USER_IDS` | NO | admin.py | Comma-separated admin UUIDs |
| `STRIPE_SECRET_KEY` | NO | webhooks/stripe.py, services/billing.py | Stripe API authentication |
| `STRIPE_WEBHOOK_SECRET` | NO | webhooks/stripe.py | Stripe webhook signature verification |
| `ENCRYPTION_KEY` | NO | oauth.py | AES-256 key for token encryption |
| `REDIS_URL` | NO | routes/features.py, routes/subscriptions.py | Feature flag cache |

## Appendix B: Tables by Migration Order

```
Migration 001: profiles, plans, user_subscriptions, search_sessions
Migration 002: monthly_quota
Migration 003: (functions only - increment_quota_atomic, check_and_increment_quota)
Migration 004: (ALTER profiles - add is_admin)
Migration 005: (UPDATE plans - new tiers)
Migration 006: (ALTER profiles - plan_type constraint; ADD policy search_sessions)
Migration 007: (ALTER profiles - whatsapp consent fields)
Migration 008: (ALTER user_subscriptions - billing_period, annual_benefits)
Migration 009: plan_features
Migration 010: stripe_webhook_events
Migration 011: (functions only - billing helpers)
Migration 012: conversations, messages
Migration 013: user_oauth_tokens
Migration 014: google_sheets_exports
Migration 015: (ALTER plans - stripe price ID columns)
```

## Appendix C: Database Size Estimates

| Table | Expected Row Count (1 year) | Growth Pattern |
|-------|---------------------------|----------------|
| profiles | 500-5,000 | Linear with signups |
| plans | 10-15 | Static (manual changes) |
| user_subscriptions | 1,000-10,000 | Linear (new subs + historical) |
| search_sessions | 10,000-100,000 | High growth (every search) |
| monthly_quota | 500-60,000 | Linear (users x months) |
| plan_features | 10-50 | Static (manual changes) |
| stripe_webhook_events | 1,000-50,000 | Linear with billing events |
| conversations | 100-1,000 | Low growth |
| messages | 500-5,000 | Low-medium growth |
| user_oauth_tokens | 100-2,000 | Linear with Google integrations |
| google_sheets_exports | 500-10,000 | Moderate growth |

**Largest tables to monitor:** `search_sessions`, `stripe_webhook_events`, `monthly_quota`
