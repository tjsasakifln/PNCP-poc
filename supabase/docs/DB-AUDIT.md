# SmartLic Database Audit Report

**Date:** 2026-03-23 | **Auditor:** @data-engineer (Dara) -- Brownfield Discovery Phase 2
**Scope:** 80+ Supabase migration files, backend query patterns (supabase_client.py, auth.py, quota.py)
**Severity:** CRITICAL (production risk) | HIGH (fix soon) | MEDIUM (improve when convenient) | LOW (nice to have)

---

## Executive Summary

The SmartLic database is well-structured for a POC-to-production system. Recent DEBT sprints (001, 002, 009, 010, 017, 100, 104, 113, 120, W4) have addressed the most critical issues including FK standardization, RLS hardening, JSONB size governance, and retention via pg_cron. The remaining findings are primarily consistency gaps and hardening items.

**Overall Health:** GOOD (7/10) -- Major structural issues resolved, remaining items are medium/low priority.

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 1 | Open |
| HIGH | 4 | Open |
| MEDIUM | 8 | Open |
| LOW | 5 | Open |

---

## Findings

### CRITICAL

#### C-01: FK Inconsistency -- 3 tables still reference auth.users instead of profiles

**Tables affected:** `search_results_store`, `mfa_recovery_codes`, `mfa_recovery_attempts`

**Risk:** Profile deletion via Supabase admin dashboard cascades through `profiles` but orphans rows in these 3 tables (FK points to auth.users, not profiles). This creates ghost data and potential FK violations if auth.users is deleted but profiles cascade doesn't reach these tables.

**Evidence:** Migration 20260303100000 creates search_results_store with `REFERENCES auth.users(id)`. Migration 20260228160000 creates mfa_recovery_codes and mfa_recovery_attempts with `REFERENCES auth.users(id)`. Multiple DEBT sprints (018, 20260225120000, debt100, debt104, debt113) standardized other tables but missed these three.

**Fix:** Apply the same NOT VALID + VALIDATE pattern used in DEBT-104:
```sql
ALTER TABLE search_results_store DROP CONSTRAINT IF EXISTS search_results_store_user_id_fkey;
ALTER TABLE search_results_store ADD CONSTRAINT fk_search_results_store_user_id
  FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
ALTER TABLE search_results_store VALIDATE CONSTRAINT fk_search_results_store_user_id;
-- Repeat for mfa_recovery_codes, mfa_recovery_attempts
```

**Effort:** 1 migration, low risk (existing pattern), ~30 min.

---

### HIGH

#### H-01: RLS uses auth.role() instead of TO service_role -- 4 remaining policies

**Tables affected:** `organizations`, `organization_members`, `partners`, `partner_referrals`, `reconciliation_log`, `search_results_store`

**Risk:** `auth.role() = 'service_role'` checks the JWT claim, not the actual Postgres role. This is functionally equivalent for Supabase but is the deprecated pattern. The DEBT-009 migration standardized most tables but these were created later and slipped through.

**Evidence:**
- `20260301100000_create_organizations.sql` line 123: `USING (auth.role() = 'service_role')`
- `20260301200000_create_partners.sql` lines 102-105: `auth.role() = 'service_role'`
- `20260228140000_add_reconciliation_log.sql` line 32: `auth.role() = 'service_role'`
- `20260303100000_create_search_results_store.sql` line 26: `auth.role() = 'service_role'`

**Fix:** Replace with `TO service_role USING (true) WITH CHECK (true)` pattern.

**Effort:** 1 migration, minimal risk, ~20 min.

---

#### H-02: health_checks and incidents tables lack RLS policies for user access

**Tables affected:** `health_checks`, `incidents`

**Risk:** These tables have RLS enabled (debt009 added service_role_all) but no SELECT policy for authenticated users. The backend health endpoint uses service_role, so this works, but if a future frontend status page queries these directly, all reads would be blocked.

**Evidence:** Migration 20260228150000 and 20260228150001 created the tables without user-facing RLS. DEBT-009 (20260308300000) added service_role_all but no authenticated user policies.

**Fix:** Add read-only SELECT policies for authenticated users (public status data).

**Effort:** 1 migration, ~15 min.

---

#### H-03: Duplicate updated_at trigger functions still exist

**Tables affected:** pipeline_items, alert_preferences, alerts

**Observation:** DEBT-001 consolidated `update_updated_at()` into `set_updated_at()` and re-pointed most triggers. However, `pipeline_items` still uses `update_pipeline_updated_at()` (from 025), `alert_preferences` uses `update_alert_preferences_updated_at()` (from 20260226), and `alerts` uses `update_alerts_updated_at()` (from 20260227). These are 3 identical functions that should use the canonical `set_updated_at()`.

**Risk:** Low functional risk (all do the same thing), but maintenance burden -- any change to updated_at logic requires updating 4 functions.

**Fix:** Re-point triggers to `set_updated_at()`, drop duplicate functions.

**Effort:** 1 migration, ~20 min.

---

#### H-04: Missing NOT NULL on several created_at columns

**Tables affected:** `classification_feedback.created_at`, `user_oauth_tokens.created_at`, `user_oauth_tokens.updated_at`

**Risk:** These columns use `DEFAULT now()` but are nullable. A programmatic INSERT that explicitly passes NULL would store a NULL created_at, breaking ORDER BY queries and retention pg_cron jobs.

**Evidence:** Migration 013 (user_oauth_tokens) uses `TIMESTAMPTZ DEFAULT NOW()` without NOT NULL. Migration debt002 (classification_feedback) uses `TIMESTAMPTZ DEFAULT now()` without NOT NULL.

**Fix:** Backfill NULLs, add NOT NULL constraints.

**Effort:** 1 migration, ~15 min.

---

### MEDIUM

#### M-01: search_results_store.user_id lacks index for RLS performance

**Status:** The RLS policy on search_results_store uses `auth.uid() = user_id`. Migration 20260307100000 attempted to create `idx_search_results_store_user_id` but referenced wrong table names. DEBT-001 (20260308100000) re-created the index correctly. However, DEBT-100 (20260309200000) later dropped the duplicate `idx_search_results_store_user_id` while keeping `idx_search_results_user`.

**Verified:** `idx_search_results_user` exists and covers user_id. No action needed -- this finding is informational only.

---

#### M-02: organizations.owner_id FK references auth.users with ON DELETE RESTRICT

**Risk:** This is intentional (documented in migration comments) -- prevents deleting a user who owns an organization. However, this creates a hard dependency on auth.users rather than profiles. If the project decides to standardize all FKs to profiles, this would need special handling.

**Recommendation:** Document as intentional, add CHECK constraint or app-layer validation that owner must also exist in profiles.

**Effort:** Documentation only, or 1 migration for app-level guard.

---

#### M-03: partner_referrals.referred_user_id uses ON DELETE SET NULL but FK goes to profiles after DEBT-104

**Status:** DEBT-001 (20260308100000) fixed the NOT NULL vs SET NULL conflict by dropping NOT NULL. DEBT-104 changed FK from auth.users to profiles. The current state should be: nullable, FK to profiles with CASCADE. However, the original ON DELETE SET NULL from 20260304100000 (referenced in DEBT-001 comment) may have been lost during FK replacement.

**Recommendation:** Verify in production that the FK behavior matches expectations. If CASCADE is set but business logic expects SET NULL, the churned_at tracking would break.

**Effort:** 1 verification query, potentially 1 migration.

---

#### M-04: No CHECK constraint on search_sessions.response_state

**Column values:** live, cached, degraded, empty_failure (documented in COMMENT)

**Risk:** Any arbitrary string can be stored. The status and error_code columns have CHECK constraints (added by W4 migration), but response_state does not.

**Fix:** Add CHECK constraint.

**Effort:** 1 migration, ~10 min.

---

#### M-05: No CHECK constraint on search_sessions.pipeline_stage

**Column values:** validate, prepare, execute, filter, enrich, generate, persist (documented in COMMENT). Also 'consolidating' used per state machine documentation.

**Risk:** Same as M-04.

**Fix:** Add CHECK constraint.

**Effort:** 1 migration, ~10 min.

---

#### M-06: plan_features.billing_period CHECK does not match user_subscriptions CHECK

**Evidence:** plan_features CHECK (from 029): `monthly, semiannual, annual`. user_subscriptions CHECK (from debt010): `monthly, semiannual, annual`. These now match after DEBT-010 fixed the drift. However, the original 008 migration used `CHECK (billing_period IN ('monthly', 'annual'))` without semiannual. The constraint was replaced in 029.

**Status:** RESOLVED. Informational only.

---

#### M-07: profiles.subscription_status and user_subscriptions.subscription_status use different enum values

**profiles CHECK:** trial, active, canceling, past_due, expired
**user_subscriptions CHECK:** active, trialing, past_due, canceled, expired

**Mapping trigger exists:** sync_subscription_status_to_profile() maps between the two (trialing->trial, canceled->canceling). This is correct and documented.

**Risk:** Adding a new status to one table without updating the other and the trigger would cause silent failures.

**Recommendation:** Add a SQL COMMENT documenting the enum mapping on both constraints.

**Effort:** 1 migration with COMMENTs, ~10 min.

---

#### M-08: Hardcoded Stripe price IDs in 5 migration files

**Files:** 015, 021, 029, 20260226120000, plus reference in 20260321130200

**Risk:** Running migrations against a staging/dev environment installs production Stripe price IDs. This is documented (DEBT-DB-009 migration adds comments + recommends seed_stripe_prices.py script), but the fundamental issue remains.

**Status:** ACCEPTED RISK. SQL migrations cannot inject env vars. The documentation and seed script mitigate this.

---

### LOW

#### L-01: Migration file naming inconsistency

The migration directory contains two naming conventions:
1. Sequential numbers: `001_profiles_and_sessions.sql` through `033_fix_missing_cache_columns.sql`
2. Timestamp-based: `20260220120000_add_search_id_to_search_sessions.sql` onwards

Additionally, `008_rollback.sql.bak` is a backup file that should not be in the migrations directory.

**Recommendation:** Remove `.bak` file. Standardize on timestamp format for all new migrations.

**Effort:** 1 cleanup commit, ~5 min.

---

#### L-02: Redundant trigger function update_updated_at() may still exist

DEBT-001 (20260308100000) runs `DROP FUNCTION IF EXISTS public.update_updated_at()`. However, DEBT-100 (20260309200000) later runs `CREATE OR REPLACE FUNCTION public.update_updated_at()` again (for organizations trigger). Then the same migration re-points the trigger to set_updated_at(). DEBT-001 also runs `CREATE OR REPLACE FUNCTION public.set_updated_at()`.

**Status:** Both functions may co-exist in production. set_updated_at() is canonical. update_updated_at() may have 0 dependents.

**Fix:** Verify in production with `SELECT * FROM pg_proc WHERE proname IN ('update_updated_at', 'set_updated_at')`, then drop if unused.

**Effort:** 1 query + potentially 1 migration.

---

#### L-03: Missing COMMENT on several tables

Tables created in earlier migrations (profiles, user_subscriptions, monthly_quota before COMMENT was added, conversations, messages) lack table-level COMMENTs. Later tables have thorough documentation.

**Effort:** 1 migration with COMMENTs, ~15 min.

---

#### L-04: alert_runs lacks service_role INSERT policy granularity

alert_runs has a broad `FOR ALL TO service_role` policy. The user-facing policy uses a correlated subquery through alerts table. This is correct but the correlated subquery may become slow at scale.

**Recommendation:** Consider adding user_id column directly (like search_state_transitions optimization in debt009) if alert_runs grows past ~10K rows.

**Effort:** Future optimization, 1 migration when needed.

---

#### L-05: search_results_cache cleanup trigger inconsistency

The cleanup trigger function has been modified 3 times:
1. Migration 026: FIFO eviction, limit 5
2. Migration 032: Priority-aware eviction, limit 10
3. Migration debt017: Short-circuit optimization, limit 5

The final version (debt017) reverted the limit from 10 back to 5, which contradicts the priority system's intent (032 increased to 10 specifically for hot/warm/cold). This may cause hot entries to be evicted prematurely.

**Recommendation:** Verify intended behavior. If priority system is active, limit should be 10.

**Effort:** 1 migration, ~10 min.

---

## Summary of Resolved Issues (Prior DEBT Sprints)

These issues were found in earlier audits and have been fully resolved:

| Issue | Resolution | Sprint |
|-------|-----------|--------|
| FK auth.users -> profiles standardization (10 tables) | NOT VALID + VALIDATE pattern | DEBT-001/104/113 |
| RLS auth.role() -> TO service_role (5 tables) | Policy replacement | DEBT-009 |
| Missing retention pg_cron jobs | 16 jobs created | DEBT-009/100/113/W4 |
| JSONB size governance (13 columns) | CHECK constraints < 512KB | DEBT-DB-010 |
| Dead sync_profile_plan_type trigger | Dropped (referenced non-existent column) | Migration 030 |
| Duplicate indexes (5 identified) | Dropped after idx_scan verification | DEBT-100/120 |
| Overly permissive RLS (pipeline_items, search_results_cache) | Scoped to service_role | Migration 027 |
| plan_type CHECK constraint drift | Unified across profiles, organizations | DEBT-100/W4 |
| handle_new_user() field regressions | Full 10-field INSERT restored | 20260225110000 |
| search_state_transitions RLS optimization | Added user_id column, removed correlated subquery | DEBT-009 |

---

## Recommendations (Priority Order)

1. **[CRITICAL] Fix C-01:** Standardize remaining 3 FK references to profiles(id). Single migration, zero downtime.

2. **[HIGH] Fix H-01:** Replace 6 remaining `auth.role()` RLS policies with `TO service_role`. Single migration.

3. **[HIGH] Fix H-04:** Add NOT NULL to created_at/updated_at columns missing it. Backfill first.

4. **[MEDIUM] Fix M-04 + M-05:** Add CHECK constraints on search_sessions.response_state and pipeline_stage.

5. **[LOW] Cleanup L-01:** Remove .bak file, standardize naming convention.

6. **[LOW] Fix L-05:** Verify cache cleanup limit (5 vs 10) matches business intent.

---

## Migration Health

| Metric | Value |
|--------|-------|
| Total migration files | 80+ |
| Naming conventions | 2 (sequential + timestamp) |
| Idempotent migrations | ~95% (IF NOT EXISTS, DROP IF EXISTS) |
| Destructive operations | 0 (all data changes are backfills or constraint additions) |
| Rollback scripts | 1 (.bak file for 008) |
| Transaction wrappers (BEGIN/COMMIT) | ~5 migrations |
| NOTIFY pgrst reload | 8 migrations |

**Risk:** No rollback mechanism exists beyond manual SQL. Supabase CLI does not support `db rollback`. All migrations are append-only, which is the correct pattern for production Supabase.
