# SmartLic Database Audit Report

**Audit Date:** 2026-03-04
**Auditor:** @data-engineer (AIOS Brownfield Discovery)
**Scope:** 66 migration files (56 Supabase + 10 backend), 32 tables, 15 functions, 60+ indexes
**Database:** Supabase PostgreSQL 17 (Project: `fqqyovlzdzimiwfofdjk`)
**Previous Audit:** 2026-02-25 (42 migrations, 15 tables documented)

---

## Executive Summary

The SmartLic database has grown substantially since the last audit (15 -> 32 tables) with the addition of alerting, organizations, partner/referral, MFA, health monitoring, and L3 search storage systems. All tables have RLS enabled. The migration history shows strong progressive hardening. However, the rapid growth has introduced **23 technical debts** across 7 categories.

### Severity Distribution

| Severity | Count | Immediate Action Required |
|----------|-------|---------------------------|
| CRITICAL | 2 | Yes -- security or data integrity risk |
| HIGH | 6 | Within next sprint |
| MEDIUM | 9 | Within next 2 sprints |
| LOW | 6 | Backlog |
| **Total** | **23** | |

### Key Metrics

| Metric | Value |
|--------|-------|
| Total tables | 32 |
| Tables with RLS enabled | 32 / 32 (100%) |
| Tables with service_role bypass policy | 28 / 32 |
| Tables WITHOUT any user-facing RLS policies | 4 (health_checks, incidents, mfa_recovery_attempts, trial_email_log) |
| Total indexes | ~65 |
| Total functions | 15 |
| Total triggers | 12 |
| pg_cron jobs | 4 |
| Extensions | pg_trgm, pg_cron |

---

## Issues Found

### Critical

| ID | Issue | Table(s) | Impact | Recommendation |
|----|-------|----------|--------|----------------|
| C-01 | **FK to auth.users instead of profiles** on 5 newer tables | search_results_store, mfa_recovery_codes, mfa_recovery_attempts, organizations (owner_id), organization_members, partner_referrals | Inconsistent with standardization effort (migrations 018, 20260225120000). ON DELETE CASCADE to auth.users bypasses profile-level cascades. If auth.users row is deleted directly, orphan data remains in profile-linked tables. | Re-point all user_id FKs from `auth.users(id)` to `profiles(id)` using the established NOT VALID + VALIDATE pattern from migration 20260225120000. For organizations.owner_id (ON DELETE RESTRICT), keep FK to auth.users but add a separate FK to profiles. |
| C-02 | **health_checks and incidents have RLS enabled but NO policies** | health_checks, incidents | Since RLS is enabled with no policies, no role (including authenticated) can read/write these tables directly. Only service_role bypasses RLS. If backend ever uses anon/authenticated client, all operations will silently fail. While service_role bypass works today, this is fragile. | Add explicit service_role ALL policy to both tables for defense-in-depth. Add read policy for admin users if status page needs client-side access. |

### High

| ID | Issue | Table(s) | Impact | Recommendation |
|----|-------|----------|--------|----------------|
| H-01 | **Duplicate updated_at trigger functions** | pipeline_items, alert_preferences, alerts | Three separate functions (`update_pipeline_updated_at`, `update_alert_preferences_updated_at`, `update_alerts_updated_at`) that are identical copies of `update_updated_at()`. Increases maintenance burden. | Consolidate to use the single `update_updated_at()` function. Drop the duplicates and update triggers to reference the shared function. |
| H-02 | **search_results_store FK not standardized** | search_results_store | user_id references auth.users(id) without ON DELETE CASCADE. If a user is deleted from auth.users, orphan rows remain. Also inconsistent with the profiles(id) FK standard. | Add `ON DELETE CASCADE` and re-point to `profiles(id)`. |
| H-03 | **No retention policy for search_results_store** | search_results_store | Table has `expires_at` column (default 24h) but no pg_cron job or application-level cleanup. Expired rows accumulate indefinitely. | Add pg_cron job: `DELETE FROM search_results_store WHERE expires_at < NOW()` daily at 6am UTC. |
| H-04 | **alert_preferences service_role policy uses auth.role()** | alert_preferences | Policy `USING (auth.role() = 'service_role')` works but is inconsistent with the `TO service_role` pattern used in 25+ other tables. The `auth.role()` approach is slightly less secure (relies on JWT role claim rather than connection role). | Replace with `FOR ALL TO service_role USING (true) WITH CHECK (true)` to match the standard pattern. |
| H-05 | **reconciliation_log service_role policy uses auth.role()** | reconciliation_log | Same issue as H-04. Uses `USING (auth.role() = 'service_role')` instead of `TO service_role`. | Replace with `FOR ALL TO service_role USING (true) WITH CHECK (true)`. |
| H-06 | **organizations and org_members service_role policies use auth.role()** | organizations, organization_members | Same pattern inconsistency as H-04/H-05. | Replace with `TO service_role` pattern. |

### Medium

| ID | Issue | Table(s) | Impact | Recommendation |
|----|-------|----------|--------|----------------|
| M-01 | **No updated_at column or trigger** on 11 tables | monthly_quota, search_state_transitions, stripe_webhook_events, classification_feedback, trial_email_log, alert_sent_items, alert_runs, reconciliation_log, health_checks, incidents, mfa_recovery_codes, mfa_recovery_attempts, partner_referrals | Cannot track when rows were last modified. Complicates debugging and audit. | Add `updated_at TIMESTAMPTZ DEFAULT now()` + trigger for tables that get UPDATE operations. Skip for append-only tables (search_state_transitions, health_checks, alert_runs). |
| M-02 | **No index on search_state_transitions.search_id for DELETE** | search_state_transitions | If retention cleanup is added, DELETE by date will be slow without an index on created_at alone. Current indexes include search_id prefix. | Add standalone index on `(created_at)` for future retention queries. |
| M-03 | **partner_referrals missing ON DELETE behavior** | partner_referrals | FK to `partners(id)` has no explicit ON DELETE -- defaults to RESTRICT. FK to `auth.users(id)` also has no ON DELETE. Deleting a partner or user will fail if referral rows exist. | Add `ON DELETE CASCADE` for partner_id (referrals are meaningless without partner). For referred_user_id, consider `ON DELETE SET NULL` to preserve revenue data. |
| M-04 | **No retention for mfa_recovery_attempts** | mfa_recovery_attempts | Brute force tracking rows accumulate forever. High-volume attack could fill storage. | Add pg_cron job to delete attempts older than 30 days. Add CHECK constraint or app-level limit on rows per user. |
| M-05 | **No retention for alert_runs** | alert_runs | Execution history accumulates indefinitely. | Add pg_cron job to delete runs older than 90 days. |
| M-06 | **No retention for alert_sent_items** | alert_sent_items | Dedup tracking grows unbounded. Old dedup entries serve no purpose after alert is deleted (CASCADE handles) but active alerts accumulate indefinitely. | Add pg_cron job to delete sent_items older than 90 days. |
| M-07 | **handle_new_user() trigger regression risk** | profiles | This function has been modified in 7 different migrations (001, 007, 016, 024, 027, 20260224000000, 20260225110000). Each modification risks dropping fields from the INSERT. The latest version (20260225110000) is correct but fragile. | Add a backend integration test that verifies all expected columns are inserted by the trigger. Consider extracting profile initialization to application layer. |
| M-08 | **Inconsistent CHECK constraint naming** | Multiple | Mix of naming patterns: `profiles_plan_type_check`, `chk_profiles_subscription_status`, `phone_whatsapp_format`, `check_event_id_format`. No consistent prefix/suffix convention. | Adopt `chk_{table}_{column}` naming convention for all CHECK constraints in future migrations. |
| M-09 | **classification_feedback admin policy uses auth.role()** | classification_feedback | Uses `USING (auth.role() = 'service_role')` instead of `TO service_role`. Same as H-04. | Standardize to `TO service_role` pattern. |

### Low

| ID | Issue | Table(s) | Impact | Recommendation |
|----|-------|----------|--------|----------------|
| L-01 | **Redundant index on alert_preferences.user_id** | alert_preferences | `idx_alert_preferences_user_id` is redundant because the UNIQUE constraint `alert_preferences_user_id_unique` already creates a B-tree index on user_id. | Drop `idx_alert_preferences_user_id`. |
| L-02 | **Redundant index on alert_sent_items.alert_id** | alert_sent_items | `idx_alert_sent_items_alert_id` (alert_id) is a prefix of the UNIQUE index `idx_alert_sent_items_dedup` (alert_id, item_id). PostgreSQL can use multi-column B-tree for prefix matches. | Drop `idx_alert_sent_items_alert_id`. |
| L-03 | **No COMMENT on several newer tables** | organizations, organization_members, health_checks (partial), incidents (partial) | Missing documentation comments on columns. | Add COMMENT ON COLUMN for key columns. |
| L-04 | **plan_type CHECK constraint rebuilt 6 times** | profiles | The profiles_plan_type_check constraint has been dropped and recreated in migrations 006a, 020, 029, 20260301300000. Each time adding new plan types. | Consider using a reference table (plan_types) instead of CHECK constraint for extensibility. |
| L-05 | **Stripe Price IDs hardcoded in migrations** | plans, plan_billing_periods | Production Stripe price IDs (price_1T5...) are hardcoded in migration SQL. Cannot use different IDs for staging/dev without manual UPDATE. | Move Stripe Price IDs to environment-driven seeding or a separate config table as documented in migration 021 comments. |
| L-06 | **search_results_store.user_id missing index for user+expiry queries** | search_results_store | Separate indexes on user_id and expires_at, but common query pattern is likely "find expired entries for user" which would benefit from composite index. | Add composite index `(user_id, expires_at)` if queried together. |

---

## Specific Checks

### RLS Coverage

**Status: EXCELLENT (100% tables have RLS enabled)**

All 32 tables have `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`. This is a significant improvement over the last audit.

**Tables with RLS enabled but no user-facing policies (service_role bypass only):**
- `health_checks` -- Only backend writes/reads (acceptable)
- `incidents` -- Only backend writes/reads (acceptable)
- `mfa_recovery_attempts` -- Only backend writes (acceptable)
- `trial_email_log` -- Only backend writes (acceptable)

**Policy pattern inconsistency:**
- 25 tables use `TO service_role USING (true)` (correct pattern)
- 4 tables use `USING (auth.role() = 'service_role')` (works but inconsistent): alert_preferences, reconciliation_log, organizations, organization_members
- 1 table uses `USING (auth.role() = 'service_role')` for admin policy: classification_feedback

### Index Analysis

**Well-indexed tables:** profiles (8 indexes), search_results_cache (6), search_sessions (6), user_subscriptions (6), conversations (4), messages (3), pipeline_items (3), audit_events (4)

**Potentially missing indexes:**
- `search_results_store(user_id, expires_at)` -- composite for cleanup queries
- `search_state_transitions(created_at)` -- standalone for retention cleanup
- `mfa_recovery_codes(user_id, used_at)` -- composite for verification queries

**Redundant indexes (safe to drop):**
- `idx_alert_preferences_user_id` -- covered by UNIQUE constraint
- `idx_alert_sent_items_alert_id` -- prefix of UNIQUE (alert_id, item_id)

### Data Integrity

**Foreign Key Standardization Status:**

| Table | FK Target | Status |
|-------|-----------|--------|
| profiles | auth.users(id) | OK (root table) |
| user_subscriptions | profiles(id) | OK |
| monthly_quota | profiles(id) | OK (standardized in 018) |
| search_sessions | profiles(id) | OK |
| search_results_cache | profiles(id) | OK (standardized in 20260224200000) |
| pipeline_items | profiles(id) | OK (standardized in 20260225120000) |
| classification_feedback | profiles(id) | OK (standardized in 20260225120000) |
| trial_email_log | profiles(id) | OK (standardized in 20260225120000) |
| user_oauth_tokens | profiles(id) | OK (standardized in 018) |
| google_sheets_exports | profiles(id) | OK (standardized in 018) |
| conversations | profiles(id) | OK |
| messages | profiles(id) | OK |
| alert_preferences | profiles(id) | OK |
| alerts | profiles(id) | OK |
| **search_results_store** | **auth.users(id)** | **NOT STANDARDIZED (C-01)** |
| **mfa_recovery_codes** | **auth.users(id)** | **NOT STANDARDIZED (C-01)** |
| **mfa_recovery_attempts** | **auth.users(id)** | **NOT STANDARDIZED (C-01)** |
| **organizations.owner_id** | **auth.users(id)** | **NOT STANDARDIZED (C-01)** |
| **organization_members.user_id** | **auth.users(id)** | **NOT STANDARDIZED (C-01)** |
| **partner_referrals.referred_user_id** | **auth.users(id)** | **NOT STANDARDIZED (C-01)** |

**Missing ON DELETE behavior:**
- `partner_referrals.partner_id` -> partners(id): defaults to RESTRICT (intentional? undocumented)
- `partner_referrals.referred_user_id` -> auth.users(id): defaults to RESTRICT (should be CASCADE or SET NULL)
- `search_results_store.user_id` -> auth.users(id): no explicit ON DELETE

### Naming Conventions

**Table naming:** All lowercase with underscores. Consistent.

**Column naming:** All lowercase with underscores. Consistent.

**Index naming patterns (inconsistent):**
- `idx_{table}_{columns}` -- most common (good)
- `idx_{shortname}_{columns}` -- some tables use abbreviations

**Constraint naming patterns (inconsistent):**
- `{table}_{column}_check` -- migration 001
- `chk_{table}_{column}` -- migration 20260225100000
- `{descriptive_name}_format` -- migration 007
- `check_{descriptive_name}` -- migration 010

**RLS policy naming (inconsistent):**
- Quoted descriptive: `"Users can view own quota"` -- most tables
- Lowercase with underscores: `feedback_insert_own` -- classification_feedback
- Camel-style: `conversations_select_own` -- conversations

### Migration Health

**Total migrations:** 66 (56 Supabase-prefixed + 10 backend-prefixed)

**Naming convention:**
- Legacy: `NNN_description.sql` (001-033) -- 33 files
- Timestamped: `YYYYMMDDHHMMSS_description.sql` -- 23 files
- Backend: `NNN_description.sql` (duplicated numbering, different directory)

**Potential issues:**
1. **Duplicate prefix 027:** Two files share the 027_ prefix (027_fix_plan_type_default_and_rls.sql and 027b_search_cache_add_sources_and_fetched_at.sql). This was caught and fixed in migration 033.
2. **handle_new_user() function modified 7 times:** High regression risk (see M-07).
3. **profiles_plan_type_check constraint modified 6 times:** Each plan addition requires a migration (see L-04).
4. **Backend migrations overlap with Supabase migrations:** Migrations in `backend/migrations/` create tables that are also referenced by Supabase migrations (classification_feedback in backend/006 and FK standardization in supabase/20260225120000). Order dependency is implicit.

**Applied vs Pending:** Cannot determine from file analysis alone. Use `supabase db diff` or `SELECT * FROM supabase_migrations.schema_migrations` to verify.

### Performance

**Potential N+1 patterns (already fixed with RPC):**
- Conversation list: Fixed by `get_conversations_with_unread_count()` (migration 019)
- Analytics summary: Fixed by `get_analytics_summary()` (migration 019)

**JSONB storage governance:**
- search_results_cache.results: 2MB CHECK constraint (migration 20260225150000). Good.
- search_results_store.results: NO size constraint. Risk of unbounded JSONB growth.
- Other JSONB columns (context_data, filters, details, payload): No size constraints. Low risk due to small payloads.

**Missing size constraint:**
- `search_results_store.results` should have a 2MB CHECK like search_results_cache.

### Security

**Strengths:**
- 100% RLS coverage
- Service role policies properly scoped with `TO service_role` (25/29 tables)
- Audit events PII stored as SHA-256 hashes (LGPD compliant)
- OAuth tokens documented as AES-256 encrypted
- MFA recovery codes stored as bcrypt hashes
- Phone uniqueness enforced at DB level

**Concerns:**
- 4 tables use `auth.role() = 'service_role'` pattern instead of `TO service_role` (H-04/05/06, M-09)
- Stripe Price IDs hardcoded in migration files (L-05) -- not a runtime security risk but visible in VCS
- `partners.contact_email` queried against `auth.users.email` in RLS policy -- could leak email existence

---

## Remediation Priority

### Sprint 1 (Immediate)
1. **C-01:** Standardize 6 remaining FKs from auth.users to profiles(id)
2. **C-02:** Add explicit service_role policies to health_checks and incidents
3. **H-03:** Add pg_cron retention for search_results_store

### Sprint 2
4. **H-01:** Consolidate duplicate updated_at trigger functions
5. **H-04/H-05/H-06:** Standardize 4 tables from auth.role() to TO service_role
6. **M-04/M-05/M-06:** Add pg_cron retention for mfa_recovery_attempts, alert_runs, alert_sent_items

### Backlog
7. **L-01/L-02:** Drop redundant indexes
8. **L-04:** Consider plan_types reference table
9. **M-08:** Standardize CHECK constraint naming
10. **M-07:** Add trigger regression test
