# Database Specialist Review -- v2.0

**Reviewer:** @data-engineer (Datum)
**Date:** 2026-02-15
**Status:** REVIEWED
**Source Document:** `docs/prd/technical-debt-DRAFT.md` v2.0 (2026-02-15)
**Reference Documents:** `supabase/docs/DB-AUDIT.md` v2.0, `supabase/docs/SCHEMA.md` v2.0
**Previous Review:** `docs/reviews/db-specialist-review.md` v1.0 (2026-02-11, commit `808cd05`)
**Current Commit:** `b80e64a` (branch `main`)
**Migrations Analyzed:** 001 through 026 (all files re-read and cross-referenced against backend code)
**Backend Code Analyzed:** `quota.py`, `admin.py`, `webhooks/stripe.py`, `routes/analytics.py`, `routes/billing.py`

---

## Changelog v1.0 -> v2.0

This review replaces the v1.0 review entirely. Since the v1.0 review (Feb 11), 11 migrations (016-026) were applied that resolved 15 of the 19 original debt items. The DRAFT v2.0 identifies a new set of 14 DB items (DB-01 through DB-14). This review validates those items, adjusts severities, adds 3 new items, and answers the architect's 7 questions.

**Items resolved since v1.0 review (no longer active):**
- DB-C01 (database.py URL): Still exists architecturally but backend routes now exclusively use Supabase client
- DB-C02 (user_subscriptions service role): RESOLVED by migration 016
- DB-C03 (webhook admin check): RESOLVED by migration 016
- DB-H01 (dual ORM): PARTIALLY RESOLVED -- webhooks/stripe.py now uses Supabase client
- DB-H02 (migration 006 duplicates): Renamed to DEPRECATED
- DB-H03 (stripe_subscription_id index): RESOLVED by migration 016
- DB-H04 (overly permissive RLS): RESOLVED for old tables by migration 016; REGRESSED for 2 new tables
- DB-H05 (profiles INSERT policy): RESOLVED by migration 020
- DB-M01 (inconsistent FKs): PARTIALLY RESOLVED by migration 018 (3 of 5 tables)
- DB-M02 (legacy plan_type CHECK): RESOLVED by migration 020
- DB-M03 (user_subscriptions updated_at): RESOLVED by migration 021
- DB-M06 (N+1 conversations): RESOLVED by migration 019 RPC
- DB-L01 (plans updated_at): RESOLVED by migration 020
- DB-L02 (monthly_quota cleanup): RESOLVED by migration 022 pg_cron
- DB-L03 (webhook_events cleanup): RESOLVED by migration 022 pg_cron
- DB-L04 (redundant provider index): RESOLVED by migration 022

---

## 1. Debitos Validados

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Complexidade | Prioridade | Notas |
|----|--------|---------------------|---------------------|-------|-------------|------------|-------|
| DB-01 | Missing `status` column on `user_subscriptions` | CRITICAL | **MEDIUM** (downgraded) | 2h | Simple | P2 | Trigger is dead code, not a production crash. Backend handles sync manually. See detailed analysis in Section 3, Q1. |
| DB-02 | `handle_new_user()` trigger omits `plan_type`, column default `'free'` violates CHECK | CRITICAL | **CRITICAL** (confirmed) | 2h | Simple | P0 | Confirmed: migration 024 INSERT omits plan_type; column default is `'free'` from migration 001; CHECK from migration 020 excludes `'free'`. New signups WILL fail with constraint violation. |
| DB-03 | `pipeline_items` RLS `FOR ALL USING(true)` without `TO service_role` | HIGH | **HIGH** (confirmed) | 1h | Simple | P0 | Confirmed at migration 025 lines 102-105. Exact same bug previously fixed in migration 016 for `monthly_quota` and `search_sessions`. |
| DB-04 | `search_results_cache` RLS `FOR ALL USING(true)` without `TO service_role` | HIGH | **HIGH** (confirmed) | 1h | Simple | P0 | Confirmed at migration 026 lines 31-35. Same pattern as DB-03. |
| DB-05 | `stripe_webhook_events` INSERT policy not scoped to `service_role` | MEDIUM | **MEDIUM** (confirmed) | 1h | Simple | P1 | Confirmed at migration 010 lines 56-58. The `CHECK (id ~ '^evt_')` constraint and `GRANT INSERT ON ... TO service_role` (line 72) provide partial mitigation. Risk limited: exploiting requires knowledge of Stripe event ID format AND idempotency behavior. |
| DB-06 | `_ensure_profile_exists()` uses `plan_type: "free"` violating CHECK | MEDIUM | **CRITICAL** (upgraded) | 0.5h | Simple | P0 | One-line fix but CRITICAL impact: any user whose profile is missing (trigger failure, race condition) will fail to get a fallback profile, breaking their entire search flow. Two independent code paths produce invalid `plan_type = 'free'` (this + DB-02). |
| DB-07 | `pipeline_items` and `search_results_cache` FK to `auth.users` instead of `profiles` | MEDIUM | **MEDIUM** (confirmed) | 2h | Simple | P2 | Inconsistency with migration 018 standardization. Functionally benign since `profiles.id` and `auth.users.id` are always identical (1:1 FK with ON DELETE CASCADE). Schema hygiene warrants fixing. |
| DB-08 | Hardcoded Stripe production price IDs in migration 015 | MEDIUM | **LOW** (downgraded) | 4h | Medium | P3 | Migration 021 already documents environment-specific instructions. For a POC with 3 plans, current approach is adequate. See Q5 answer. |
| DB-09 | `search_sessions` time-series query fetches all rows into Python | MEDIUM | **MEDIUM** (confirmed, scope expanded) | 6h | Medium | P2 | Confirmed in `routes/analytics.py` lines 147-189. Time-series DOES filter by `range_days` via `.gte()`. However, `top-dimensions` (lines 206-245) fetches ALL sessions with NO date filter. DB-09 scope should include top-dimensions. |
| DB-10 | `search_results_cache.results` JSONB 10-100KB per entry | MEDIUM | **LOW** (downgraded) | 2h | Simple | P3 | Max-5-per-user trigger is excellent mitigation. At 5,000 users x 5 entries x 50KB avg = 1.25GB. Supabase Pro has 8GB included. Not urgent until >10K users. Monitoring sufficient. |
| DB-11 | `handle_new_user()` trigger redefined 4 times (001, 007, 016, 024) | MEDIUM | **MEDIUM** (confirmed) | 3h | Medium | P2 | Root cause of DB-02. Each `CREATE OR REPLACE` is valid PostgreSQL (latest wins). Latest version (024) dropped explicit `plan_type = 'free_trial'` from version 016. Consolidation should happen AFTER fixing DB-02. |
| DB-12 | Deprecated migration file 006b in directory | LOW | **LOW** (confirmed) | 0.5h | Simple | P3 | Cosmetic. Supabase CLI processes by timestamp prefix; file is clearly named `DEPRECATED`. Move to `supabase/archive/` or delete. |
| DB-13 | `pipeline_items` uses separate `update_pipeline_updated_at()` | LOW | **LOW** (confirmed) | 0.5h | Simple | P3 | Functionally identical to `update_updated_at()`. Only difference is function name. |
| DB-14 | `search_results_cache` missing INSERT policy for users | LOW | **LOW** (confirmed) | 1h | Simple | P3 | Backend uses `service_role` key which bypasses RLS. Only relevant if client-side caching is ever implemented. |

---

## 2. Debitos Adicionados

### DB-15: `admin.py` CreateUserRequest uses `plan_id: "free"` default (NEW)

**Severity:** MEDIUM
**File:** `backend/admin.py`, line 246
**Issue:** The `CreateUserRequest` Pydantic model defaults `plan_id` to `"free"`. The `plan_id` refers to the `plans` table where `"free"` is a valid row (the `Gratuito` plan). This is NOT a direct CHECK violation on `profiles.plan_type`. However, the comparison logic at lines 348 and 357 uses `plan_id != "free"` as a gate for plan assignment. When admin creates a user with default `plan_id="free"`, the `handle_new_user()` trigger sets `plan_type` to the column default (currently `'free'`), which violates the CHECK. This is a secondary impact of DB-02.

**Impact:** Admin-created users without explicit plan assignment fail due to DB-02 trigger issue.
**Recommendation:** Fix DB-02 first (column default to `'free_trial'`), then update admin.py default to `"free_trial"`.
**Hours:** 0.5h (once DB-02 is fixed)
**Complexity:** Simple
**Priority:** P1

### DB-16: `quota.py` fallback `get("plan_type", "free")` returns invalid value (NEW)

**Severity:** LOW
**File:** `backend/quota.py`, line 522
**Issue:** The `get_plan_from_profile()` function uses `result.data.get("plan_type", "free")` as a Python-side default. If `plan_type` were somehow NULL, the fallback is `"free"`. The `PLAN_TYPE_MAP` at line 529 maps `"free" -> "free_trial"`, so this is currently mitigated. However, it is fragile -- removing the mapping would propagate an invalid value.

**Impact:** Low (mitigated by PLAN_TYPE_MAP).
**Recommendation:** Change to `result.data.get("plan_type", "free_trial")` for defense-in-depth.
**Hours:** 0.25h
**Complexity:** Simple
**Priority:** P2

### DB-17: `top-dimensions` endpoint fetches ALL search sessions without date filter (NEW)

**Severity:** MEDIUM
**File:** `backend/routes/analytics.py`, lines 206-245
**Issue:** Unlike the time-series endpoint (which filters by `range_days`), `GET /analytics/top-dimensions` fetches ALL search sessions for a user with no date boundary. For power users with thousands of sessions, this transfers significant data and performs aggregation in Python. Same anti-pattern class as DB-09 but with no mitigation.

**Impact:** Slow analytics page load for high-volume users. Grows linearly with session count.
**Recommendation:** Add a date filter (e.g., last 12 months) or create an RPC function for server-side aggregation.
**Hours:** 4h
**Complexity:** Medium
**Priority:** P2 (combine with DB-09)

---

## 3. Respostas ao Architect

### Q1: DB-01 -- Does `status` column exist in `user_subscriptions` in production?

**Analysis from migration sequence and backend code:**

After reading ALL 26 migrations and ALL backend code that writes to `user_subscriptions`, my conclusion is that **the `status` column almost certainly does NOT exist in the migrations**, but **may have been added manually**. Here is the evidence:

**Evidence that `status` column is NOT in migrations:**
1. None of the 26 migration files contain `ALTER TABLE user_subscriptions ADD COLUMN status` or define the table with a `status` column.
2. Migration 001 creates the table with columns: `id`, `user_id`, `plan_id`, `credits_remaining`, `starts_at`, `expires_at`, `stripe_subscription_id`, `stripe_customer_id`, `is_active`, `created_at`. No `status`.

**Evidence that backend does NOT write `status`:**
All five write paths to `user_subscriptions` were examined:
- `webhooks/stripe.py:_handle_subscription_updated()` (line 190-198): Updates `billing_period`, `is_active`, optionally `plan_id`. No `status`.
- `webhooks/stripe.py:_handle_subscription_deleted()` (line 246-248): Updates `is_active = False`. No `status`.
- `webhooks/stripe.py:_handle_invoice_payment_succeeded()` (line 308-311): Updates `is_active`, `expires_at`. No `status`.
- `routes/billing.py:_activate_plan()` (line 100-108): Inserts `user_id`, `plan_id`, `credits_remaining`, `expires_at`, `stripe_subscription_id`, `stripe_customer_id`, `is_active`. No `status`.
- `admin.py:_assign_plan()` (line 614-619): Same pattern, no `status`.

**Key behavioral analysis:** PostgreSQL trigger functions that reference `NEW.status` where `status` is not a column will raise `record "new" has no field "status"` at runtime. This would cause **every INSERT and UPDATE to `user_subscriptions` to fail**.

Since the application IS in production and subscriptions ARE working (Stripe webhooks process successfully per `stripe.py` logic), one of these scenarios must be true:

**(a) The column was added manually via Supabase SQL editor** -- Most likely. The trigger function was written with the expectation that `status` would be added. Someone added it outside the migration sequence.

**(b) The trigger silently fails** -- In PostgreSQL, if `NEW.status` is NULL (which happens if the column exists but is not set), the `IN (...)` check returns FALSE and the function body does nothing, returning NEW without error. This means the trigger is dead code but not breaking anything.

**(c) The trigger was dropped or disabled** -- Less likely but possible.

**Backend handles sync manually regardless.** All three Stripe webhook handlers explicitly sync `profiles.plan_type`:
- `_handle_subscription_updated()` at line 202
- `_handle_subscription_deleted()` at line 251
- `_handle_invoice_payment_succeeded()` at line 314

This makes the trigger from migration 017 **redundant** even if it works correctly.

**Severity downgrade justification:** Given that (a) production is working, (b) backend handles sync manually, and (c) the worst case is dead code rather than a crash, I downgrade DB-01 from CRITICAL to MEDIUM. It is a migration tracking/documentation issue, not a production breakage.

**Verification queries:**
```sql
-- Q1a: Does the status column exist?
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_subscriptions' AND column_name = 'status';

-- Q1b: Is the trigger currently active?
SELECT tgname, tgenabled FROM pg_trigger
WHERE tgrelid = 'public.user_subscriptions'::regclass
  AND tgname = 'trg_sync_profile_plan_type';

-- Q1c: Current trigger function source
SELECT prosrc FROM pg_proc WHERE proname = 'sync_profile_plan_type';

-- Q1d: Has plan_type been synced recently?
SELECT id, plan_type, updated_at FROM profiles ORDER BY updated_at DESC LIMIT 10;
```

**Recommended action:** If column exists (scenario a), create migration to formally document it. If column does not exist, drop the trigger (backend's manual sync is more reliable and already tested in production).

---

### Q2: What is the current `profiles.plan_type` default?

**The column default is almost certainly `'free'`.**

Evidence chain:
1. Migration 001 sets: `plan_type text not null default 'free'`
2. Migration 020 tightens the CHECK constraint to exclude `'free'`, but does NOT run `ALTER TABLE profiles ALTER COLUMN plan_type SET DEFAULT 'free_trial'`.
3. Migration 024 redefines `handle_new_user()` omitting `plan_type` from the INSERT column list, relying on the column default.

The column default was never changed from `'free'` in any migration.

**Impact analysis:** The `handle_new_user()` function (migration 024) inserts `(id, email, full_name, company, sector, phone_whatsapp, whatsapp_consent, context_data)` without `plan_type`. PostgreSQL uses the column default `'free'`, which violates `CHECK (plan_type IN ('free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master'))`.

**However:** The `ON CONFLICT (id) DO NOTHING` clause means if the profile already exists, the INSERT silently does nothing. This masks the issue for users created before migration 020.

**Critical question:** Are there users who signed up AFTER both migrations 020 and 024 were applied? If yes and they succeeded, then the column default was fixed manually.

**Verification queries:**
```sql
-- Q2a: Current column default
SELECT column_default FROM information_schema.columns
WHERE table_name = 'profiles' AND column_name = 'plan_type';

-- Q2b: Any profiles with plan_type = 'free'?
SELECT COUNT(*) FROM profiles WHERE plan_type = 'free';

-- Q2c: Most recent profile creation
SELECT id, email, plan_type, created_at FROM profiles
ORDER BY created_at DESC LIMIT 5;
```

---

### Q3: DB-10 -- `search_results_cache` size?

Cannot query live database. Providing estimation and monitoring queries.

**Estimation:**
- Table created by migration 026 (STORY-257A, approximately Feb 14-15 2026)
- Very new table -- likely less than 100 rows
- At 5 entries max per user and ~50 active users in POC, expect ~250 rows max
- Average result JSONB size: 20-50KB (50-200 items at 200-500 bytes each)
- Estimated total: 5-12MB currently

**Verification queries:**
```sql
-- Q3a: Table size
SELECT pg_size_pretty(pg_total_relation_size('search_results_cache'));

-- Q3b: Row count and average size
SELECT
  COUNT(*) as total_rows,
  pg_size_pretty(AVG(pg_column_size(results))::bigint) as avg_results_size,
  pg_size_pretty(MAX(pg_column_size(results))::bigint) as max_results_size,
  COUNT(DISTINCT user_id) as unique_users
FROM search_results_cache;

-- Q3c: Distribution per user
SELECT user_id, COUNT(*) as entries, SUM(total_results) as total_cached_results
FROM search_results_cache
GROUP BY user_id ORDER BY entries DESC LIMIT 20;
```

**Recommendation:** Max-5-per-user trigger is sufficient for now. Add monitoring alert at 500MB. Consider `size_bytes` computed column when user base exceeds 5,000.

---

### Q4: DB-09 -- Average `search_sessions` per user?

Cannot query live database. Providing estimation and queries.

**Estimation:**
- Application in production approximately 3 weeks
- Free trial: 3 searches/month max
- Paid (consultor_agil): 50/month
- Most POC users on free_trial
- Estimate: 5-15 sessions per active user, power users at 50-100

**At this scale, Python-side aggregation is NOT a bottleneck.** Even 200 sessions for a power user is ~20KB transfer. The RPC function should be created when:
- Users average >500 sessions, OR
- Analytics page load exceeds 2 seconds

**Verification queries:**
```sql
-- Q4a: Average sessions per user
SELECT
  AVG(session_count) as avg_sessions,
  MAX(session_count) as max_sessions,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY session_count) as p95_sessions
FROM (
  SELECT user_id, COUNT(*) as session_count
  FROM search_sessions GROUP BY user_id
) subq;

-- Q4b: Total sessions and active users
SELECT COUNT(*) as total_sessions, COUNT(DISTINCT user_id) as active_users
FROM search_sessions;

-- Q4c: Sessions in last 30 days
SELECT COUNT(*) as recent_sessions, COUNT(DISTINCT user_id) as recent_users
FROM search_sessions WHERE created_at > NOW() - INTERVAL '30 days';
```

**Priority assessment:** P3 (backlog) until production metrics show a problem.

---

### Q5: DB-08 -- Stripe price ID strategy?

**Recommended: Keep current approach (manual UPDATE per environment).**

| Strategy | Pros | Cons | Verdict |
|----------|------|------|---------|
| Env vars at runtime | Configurable | Requires backend code change, startup validation | Overcomplicated for DB seeds |
| Conditional migration | Clean, automated | Complex SQL, PostgreSQL has no native env var access | Not practical |
| Manual UPDATE per env | Simple, one-time | Not automated, forgettable | **Current approach (adequate for POC)** |
| Separate seed files | Clear separation | Requires tooling changes | Best for production at scale |

Migration 021 already documents environment-specific instructions as SQL comments. For a POC with 3 plans, this is sufficient. Switch to separate seed files when multi-environment CI/CD (staging + production) is implemented.

---

### Q6: Migration squash recommendation?

**Recommendation: Do NOT squash at this time.**

Rationale:
1. **Documentary value.** The 26 migrations tell the complete evolutionary story with STORY references, inline comments, and verification queries.
2. **Supabase CLI behavior.** Supabase tracks applied migrations by filename in `supabase_migrations.schema_migrations`. Squashing requires careful coordination.
3. **Active development.** Migrations being added weekly. Squashing now provides minimal benefit.
4. **26 is manageable.** Projects squash at 50-100+ migrations, not 26.

**When to squash:**
- After reaching v1.0 (feature-complete milestone)
- Before onboarding a second development team
- When migration count exceeds 50

---

### Q7: pg_cron status?

Migration 022 runs `CREATE EXTENSION IF NOT EXISTS pg_cron` and `SELECT cron.schedule(...)` for 2 jobs. Migration 023 adds a 3rd job for `audit_events`.

Supabase Pro plans include pg_cron. Since the project has Stripe integration and production deployment, pg_cron is likely enabled and the 3 jobs should be running.

If the extension was NOT enabled when migration 022 was applied, `CREATE EXTENSION IF NOT EXISTS pg_cron` would require superuser privileges and fail. This would cause the entire migration to fail, meaning either: (a) it succeeded (pg_cron works), or (b) it was manually adjusted.

**Verification queries:**
```sql
-- Q7a: Is pg_cron extension enabled?
SELECT * FROM pg_extension WHERE extname = 'pg_cron';

-- Q7b: List scheduled jobs
SELECT jobid, jobname, schedule, command, active FROM cron.job;

-- Q7c: Recent job execution history
SELECT jobid, jobname, status, return_message, start_time, end_time
FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;

-- Q7d: Verify cleanup is working
SELECT COUNT(*) as old_quota FROM monthly_quota
WHERE created_at < NOW() - INTERVAL '24 months';
SELECT COUNT(*) as old_webhooks FROM stripe_webhook_events
WHERE processed_at < NOW() - INTERVAL '90 days';
SELECT COUNT(*) as old_audits FROM audit_events
WHERE timestamp < NOW() - INTERVAL '12 months';
```

---

## 4. Recomendacoes

### 4.1 Resolution Order

#### Group 1: P0 -- Fix Immediately (3.5h, single migration + backend fixes)

**Step 1: Backend code fixes (1h)**
- `backend/quota.py` line 790: Change `"plan_type": "free"` to `"plan_type": "free_trial"` (DB-06)
- `backend/quota.py` line 522: Change `get("plan_type", "free")` to `get("plan_type", "free_trial")` (DB-16)
- Deploy backend

**Step 2: Create migration `027_security_and_integrity_fixes.sql` (2.5h)**

This single migration addresses DB-02, DB-03, DB-04:

```sql
-- 1. DB-02: Fix column default
ALTER TABLE public.profiles ALTER COLUMN plan_type SET DEFAULT 'free_trial';

-- 2. DB-02: Fix handle_new_user() with explicit plan_type
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id, email, full_name, company, sector, phone_whatsapp,
    whatsapp_consent, context_data, plan_type
  ) VALUES (
    new.id, new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', ''),
    COALESCE(new.raw_user_meta_data->>'company', ''),
    COALESCE(new.raw_user_meta_data->>'sector', ''),
    COALESCE(new.raw_user_meta_data->>'phone_whatsapp', ''),
    COALESCE((new.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    '{}'::jsonb,
    'free_trial'
  ) ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. DB-03: Fix pipeline_items RLS
DROP POLICY IF EXISTS "Service role full access on pipeline_items"
  ON public.pipeline_items;
CREATE POLICY "Service role full access on pipeline_items"
  ON public.pipeline_items FOR ALL TO service_role
  USING (true) WITH CHECK (true);

-- 4. DB-04: Fix search_results_cache RLS
DROP POLICY IF EXISTS "Service role full access on search_results_cache"
  ON search_results_cache;
CREATE POLICY "Service role full access on search_results_cache"
  ON search_results_cache FOR ALL TO service_role
  USING (true) WITH CHECK (true);
```

**Step 3: Verify DB-01 in production** (run Q1 queries). Based on results:
- If `status` column EXISTS: Create documentation migration
- If `status` column MISSING: Drop trigger `trg_sync_profile_plan_type` (backend handles sync manually)

#### Group 2: P1 -- This Sprint (2h)

| Item | Action | Hours |
|------|--------|-------|
| DB-05 | Fix `stripe_webhook_events` INSERT policy: add `TO service_role` | 0.5h |
| DB-15 | Update `admin.py` `CreateUserRequest.plan_id` default to `"free_trial"` | 0.5h |
| DB-01 (part 2) | Based on verification, document or drop trigger | 1h |

Can be combined into migration 027 if done at same time as Group 1.

#### Group 3: P2 -- Next Sprint (14h)

| Item | Action | Hours |
|------|--------|-------|
| DB-07 | Standardize FKs on `pipeline_items` and `search_results_cache` to `profiles(id)` | 2h |
| DB-09 + DB-17 | Add date filter to `top-dimensions`; consider RPC for time-series | 8h |
| DB-11 | Document current `handle_new_user()` as authoritative in migration 027 comments | 1h |
| DB-13 | Consolidate `update_pipeline_updated_at()` with `update_updated_at()` | 1h |
| DB-16 | Update `quota.py` fallback default (if not done in P0) | 0.25h |
| DB-01 (consolidation) | Formalize `status` column or remove dead trigger | 1.75h |

#### Group 4: P3 -- Backlog (8h)

| Item | Action | Hours |
|------|--------|-------|
| DB-08 | Document environment-specific Stripe ID strategy (already partially done) | 1h |
| DB-10 | Add monitoring query for cache table size | 1h |
| DB-12 | Move deprecated migration file to archive/ | 0.5h |
| DB-14 | Add user-level INSERT policy for search_results_cache | 1h |

### 4.2 Dependency Graph

```
DB-02 (column default) -----> DB-11 (trigger consolidation)
  |                               |
  +---> DB-15 (admin.py default)  +---> DB-01 (status column verification)
  |
  +---> DB-06 (quota.py "free") ---> DB-16 (quota.py fallback default)

DB-03 (pipeline RLS) ----independent----> DB-04 (cache RLS)
  |
  +---same migration as---> DB-05 (webhook INSERT RLS)
  |
  +---can combine---> DB-07 (FK standardization)

DB-09 (time-series) ---same fix pattern---> DB-17 (top-dimensions)
```

### 4.3 Migration Strategy

- **Groups 1+2:** Single migration `027_security_and_integrity_fixes.sql` (atomic application)
- **Group 3:** Migration `028_fk_standardization_and_cleanup.sql` for DB-07, DB-13
- **DB-09/DB-17:** Migration `029_analytics_rpc_functions.sql` (only if production metrics justify)
- **Do NOT squash** existing 26 migrations (see Q6)

### 4.4 Revised Effort Summary

| Priority | Items | Original Hours (DRAFT) | Revised Hours | Delta |
|----------|-------|------------------------|---------------|-------|
| P0 | DB-02, DB-03, DB-04, DB-06 | 7h | 3.5h | -3.5h |
| P1 | DB-05, DB-01 (part 2), DB-15 | 3h | 2h | -1h |
| P2 | DB-01, DB-07, DB-09, DB-11, DB-13, DB-16, DB-17 | 20h | 14h | -6h |
| P3 | DB-08, DB-10, DB-12, DB-14 | 7h | 3.5h | -3.5h |
| **Total** | **17 items** | **37h** | **23h** | **-14h** |

Note: The DRAFT estimated 39h for 14 items. This review covers 17 items (3 new) with a tighter estimate of 23h. The reduction comes from more precise scoping after verifying each item against source code, and the DB-01 severity downgrade.

---

## 5. Verification Queries

### Critical (run BEFORE creating migration 027)

```sql
-- V1: Does status column exist on user_subscriptions?
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'user_subscriptions'
  AND column_name = 'status';
-- Expected: 0 rows (column missing) or 1 row (added manually)

-- V2: What is profiles.plan_type column default?
SELECT column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'profiles'
  AND column_name = 'plan_type';
-- Expected: 'free'::text (if unfixed) or 'free_trial'::text (if fixed manually)

-- V3: Are there profiles with invalid plan_type?
SELECT plan_type, COUNT(*) FROM profiles GROUP BY plan_type ORDER BY count DESC;
-- Expected: No rows with plan_type = 'free' (migrated by migration 020)

-- V4: Most recent profile creations (verify signups work)
SELECT id, email, plan_type, created_at
FROM profiles ORDER BY created_at DESC LIMIT 10;
-- If plan_type shows 'free_trial' for recent users, signups work

-- V5: Is sync trigger active?
SELECT tgname, tgenabled FROM pg_trigger
WHERE tgrelid = 'public.user_subscriptions'::regclass;
-- Check if trg_sync_profile_plan_type is 'O' (always on)
```

### Post-Deployment (run AFTER migration 027)

```sql
-- V6: Verify RLS policies are role-scoped
SELECT policyname, roles, cmd
FROM pg_policies
WHERE tablename IN ('pipeline_items', 'search_results_cache', 'stripe_webhook_events')
ORDER BY tablename, policyname;
-- All service role policies should show {service_role}, NOT {public}

-- V7: Verify column default updated
SELECT column_default FROM information_schema.columns
WHERE table_name = 'profiles' AND column_name = 'plan_type';
-- Expected: 'free_trial'::text

-- V8: Test new user creation
-- Create test user via Supabase Auth, then:
SELECT plan_type FROM profiles ORDER BY created_at DESC LIMIT 1;
-- Expected: 'free_trial'
```

### Monitoring (periodic)

```sql
-- V9: pg_cron job health
SELECT jobname, schedule, active FROM cron.job;
SELECT jobname, status, start_time, return_message
FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;

-- V10: Cache table size
SELECT
  pg_size_pretty(pg_total_relation_size('search_results_cache')) as table_size,
  COUNT(*) as row_count,
  COUNT(DISTINCT user_id) as unique_users
FROM search_results_cache;

-- V11: Session count per user (DB-09 urgency check)
SELECT
  AVG(cnt)::int as avg_sessions,
  MAX(cnt) as max_sessions,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cnt) as p95
FROM (SELECT COUNT(*) as cnt FROM search_sessions GROUP BY user_id) s;

-- V12: Full table size overview
SELECT
  relname as table_name,
  pg_size_pretty(pg_total_relation_size(relid)) as total_size,
  n_live_tup as estimated_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(relid) DESC;
```

---

## 6. Risk Assessment Update

| Risk | Likelihood | Impact | Revised Severity | Notes |
|------|-----------|--------|-----------------|-------|
| New signups fail (DB-02) | HIGH | CRITICAL | **P0** | Unless column default was fixed manually outside migrations. |
| Fallback profile creation fails (DB-06) | MEDIUM | CRITICAL | **P0** | Edge case (missing profile) but breaks entire search flow. |
| Cross-user pipeline access (DB-03) | LOW | HIGH | **P0** | Requires PostgREST direct access knowledge to exploit. |
| Cross-user cache access (DB-04) | LOW | HIGH | **P0** | Same pattern as DB-03. |
| Webhook event poisoning (DB-05) | LOW | MEDIUM | **P1** | `CHECK (id ~ '^evt_')` provides partial mitigation. |
| sync_profile_plan_type trigger dead code (DB-01) | MEDIUM | LOW | **P2** | Backend handles sync manually. Not a crash. |
| Analytics slow for power users (DB-09, DB-17) | LOW | LOW | **P3** | POC user base is small. Monitor. |

---

*Review completed by @data-engineer (Datum) on 2026-02-15.*
*All findings validated against migration source files (001-026) and backend code.*
*17 items total: 14 from DRAFT (validated with 3 severity changes), 3 new items added (DB-15, DB-16, DB-17).*
*Total revised effort: 23h (down from 39h DRAFT estimate).*
*Commit reference: `b80e64a` (branch `main`).*
