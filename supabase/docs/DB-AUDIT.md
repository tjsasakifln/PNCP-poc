# SmartLic Database Audit Report

**Audit Date:** 2026-03-07
**Auditor:** @data-engineer (AIOS Brownfield Discovery Phase 2)
**Scope:** 76 migration files (66 Supabase + 10 backend), 27+ tables, 13+ functions, 70+ indexes
**Severity Scale:** CRITICAL > HIGH > MEDIUM > LOW > INFO

---

## Table of Contents

1. [Missing Indexes](#1-missing-indexes)
2. [RLS Gaps](#2-rls-gaps)
3. [Schema Issues](#3-schema-issues)
4. [Normalization](#4-normalization)
5. [Migration Quality](#5-migration-quality)
6. [Performance Concerns](#6-performance-concerns)
7. [Security Issues](#7-security-issues)
8. [Data Integrity](#8-data-integrity)
9. [Backup/Recovery](#9-backuprecovery)

---

## 1. Missing Indexes

### DB-IDX-01 (MEDIUM) — `classification_feedback` missing user_id index for RLS

The `classification_feedback` table has RLS policies using `auth.uid() = user_id` but the migration in `backend/migrations/006_classification_feedback.sql` only creates `idx_feedback_sector_verdict` and `idx_feedback_user_created`. Migration `20260307100000_rls_index_user_id.sql` references `idx_feedback_user_id ON feedback(user_id)` but the actual table is named `classification_feedback`, not `feedback`. This index likely failed silently at deploy.

**Impact:** RLS policy evaluation triggers full table scan for every query from authenticated users.
**Fix:** `CREATE INDEX IF NOT EXISTS idx_classification_feedback_user_id ON classification_feedback(user_id);`

### DB-IDX-02 (MEDIUM) — `20260307100000_rls_index_user_id.sql` references non-existent tables

The migration creates indexes on `searches(user_id)`, `pipeline(user_id)`, and `feedback(user_id)`. These table names do not match the actual schema (`search_sessions`, `pipeline_items`, `classification_feedback`). These CREATE INDEX statements likely all failed silently (`IF NOT EXISTS` would succeed but on non-existent tables this would error).

**Impact:** Intended RLS performance indexes were never created.
**Fix:** Re-issue with correct table names. `search_sessions` and `pipeline_items` already have user_id indexes, but verify `search_results_store` does too (it does: `idx_search_results_user`).

### DB-IDX-03 (LOW) — `conversations` missing composite index for admin inbox

Admin inbox queries likely filter by `status` + order by `last_message_at DESC`. The individual indexes exist but a composite `(status, last_message_at DESC)` would be more efficient for the admin use case.

**Fix:** `CREATE INDEX idx_conversations_status_last_msg ON conversations(status, last_message_at DESC);`

### DB-IDX-04 (LOW) — `alert_preferences` has redundant user_id index

`idx_alert_preferences_user_id` is a plain B-tree on `user_id`, but the table also has `alert_preferences_user_id_unique` (UNIQUE constraint) which implicitly creates a unique index on the same column. The plain index is redundant.

**Fix:** `DROP INDEX IF EXISTS idx_alert_preferences_user_id;`

### DB-IDX-05 (LOW) — `trial_email_log` redundant user_id index

After migration 20260227140000, the UNIQUE constraint `trial_email_log_user_id_email_number_key` covers `(user_id, email_number)`. The standalone `idx_trial_email_log_user_id` is partially redundant since PostgreSQL can use the leading column of composite unique indexes.

**Fix:** Consider dropping `idx_trial_email_log_user_id` if all queries filter by `user_id` alone (the composite index covers this).

### DB-IDX-06 (INFO) — `search_results_cache` has 7 indexes

This table has one of the highest index counts in the schema. Each index adds write overhead (INSERT/UPDATE triggers cache eviction). Monitor index usage with `pg_stat_user_indexes` and drop unused ones.

---

## 2. RLS Gaps

### DB-RLS-01 (CRITICAL) — `classification_feedback` service_role policy uses `auth.role()`

In `backend/migrations/006_classification_feedback.sql`, the admin policy is:
```sql
CREATE POLICY feedback_admin_all ON classification_feedback
    FOR ALL USING (auth.role() = 'service_role');
```

Migration `20260304200000_rls_standardize_service_role.sql` was supposed to fix this but skipped `classification_feedback` because the table was noted as "does not exist yet." However, it does exist (created by backend migration 006). This means the policy still uses `auth.role() = 'service_role'` instead of `TO service_role USING (true)`.

**Impact:** While functionally equivalent in most cases, `auth.role()` is evaluated per-row (slower) and doesn't benefit from PostgreSQL's built-in role-based policy bypass optimization. Also inconsistent with the standard pattern.
**Fix:**
```sql
DROP POLICY IF EXISTS feedback_admin_all ON classification_feedback;
CREATE POLICY feedback_admin_all ON classification_feedback
    FOR ALL TO service_role USING (true) WITH CHECK (true);
```

### DB-RLS-02 (HIGH) — `health_checks` and `incidents` have no user-facing policies

These tables have RLS enabled (migration 20260303200000) and service_role ALL policies (migration 20260304120000), but no authenticated user policies. If the frontend ever queries these tables directly via Supabase client (e.g., for a status page), all queries from authenticated users will return empty results.

**Impact:** No user-facing access. If these tables are only accessed via backend service_role, this is correct by design. Document this decision.

### DB-RLS-03 (MEDIUM) — `mfa_recovery_attempts` has no user SELECT policy

Users cannot view their own MFA recovery attempt history. Only service_role can access this table. This may be intentional (prevent information leakage), but worth documenting.

### DB-RLS-04 (MEDIUM) — `trial_email_log` has no user-facing policies

Only accessible via service_role (no SELECT policy for users). Intentional for backend-only access, but if a user settings page ever needs to show email history, a policy will be needed.

### DB-RLS-05 (LOW) — `search_state_transitions` SELECT policy uses subquery

The user SELECT policy uses `search_id IN (SELECT search_id FROM search_sessions WHERE user_id = auth.uid() AND search_id IS NOT NULL)`. This subquery runs for every row evaluation. For large transition tables, this could be slow.

**Fix:** Consider adding `user_id` column to `search_state_transitions` for direct RLS evaluation, or ensure the subquery is well-indexed (it is, via `idx_search_sessions_search_id`).

---

## 3. Schema Issues

### DB-SCH-01 (HIGH) — `handle_new_user()` trigger has been rewritten 7+ times

The `handle_new_user()` function was redefined in migrations: 001, 007, 016, 024, 027, 20260224000000, 20260225110000. Each version had different field lists, causing silent data loss (fields dropped from INSERT without error). The final version (20260225110000) includes 10 fields with ON CONFLICT DO NOTHING, but this evolutionary churn indicates fragility.

**Recommendation:** Add a schema contract test that validates the trigger inserts all expected columns. The existing `get_table_columns_simple()` RPC could be used for this.

### DB-SCH-02 (HIGH) — Inconsistent `updated_at` trigger functions

Three different functions serve the same purpose:
1. `update_updated_at()` — original (migration 001)
2. `set_updated_at()` — canonical (migration 20260304120000)
3. Table-specific versions were dropped but `update_updated_at()` still exists alongside `set_updated_at()`

Some triggers use `update_updated_at()` (profiles, plans, user_subscriptions, organizations) while others use `set_updated_at()` (pipeline_items, alerts, alert_preferences). Both functions are identical (`NEW.updated_at = now(); RETURN NEW;`).

**Fix:** Consolidate all triggers to use a single function. Drop the unused one.

### DB-SCH-03 (MEDIUM) — `plans.stripe_price_id` is a legacy column

The `stripe_price_id` column coexists with `stripe_price_id_monthly`, `stripe_price_id_semiannual`, and `stripe_price_id_annual`. The legacy column is always set to the monthly price ID. This creates confusion and potential inconsistency.

**Fix:** Deprecate `stripe_price_id` column once all code references are updated to use the period-specific columns.

### DB-SCH-04 (MEDIUM) — `profiles.plan_type` vs `user_subscriptions.plan_id` duplication

Plan type is stored in two places: `profiles.plan_type` and `user_subscriptions.plan_id`. The sync trigger was removed (migration 030) because it referenced a non-existent column. Sync is now handled in application code (billing.py). This means database-level consistency is not enforced.

**Impact:** If application code fails to sync, `profiles.plan_type` and `user_subscriptions.plan_id` can drift. The circuit breaker fail-open behavior (STORY-291) explicitly allows this for availability, using `profiles.plan_type` as the reliable fallback.
**Recommendation:** Document this as an intentional design decision. Add a reconciliation check to the cron job.

### DB-SCH-05 (MEDIUM) — `search_sessions.status` default is `'created'` but no transition enforcement

The status column has a CHECK constraint listing valid values but no database-level enforcement of valid transitions (e.g., `completed` -> `processing` should be impossible). Transitions are enforced only in application code (`search_state_manager.py`).

### DB-SCH-06 (LOW) — Missing `NOT NULL` on several columns

- `google_sheets_exports.created_at` — nullable (should be NOT NULL with default)
- `google_sheets_exports.last_updated_at` — nullable
- `partners.created_at` — nullable
- `partner_referrals.signup_at` — nullable (has default `now()` but nullable)
- `organizations.stripe_customer_id` — nullable (acceptable, not all orgs have Stripe)

### DB-SCH-07 (LOW) — `search_results_cache.priority` lacks CHECK constraint

The `priority` column accepts any text value. Should have `CHECK (priority IN ('hot', 'warm', 'cold'))` to enforce valid values.

### DB-SCH-08 (LOW) — `alert_runs.status` has no CHECK constraint

Values documented as `matched, no_results, no_match, all_deduped, error` but no CHECK constraint enforces this. Default is `'pending'` which isn't in the documented list either.

### DB-SCH-09 (INFO) — Naming inconsistency in constraints

Some constraints use descriptive names (`profiles_plan_type_check`), while others use Supabase auto-generated names (`user_subscriptions_billing_period_check`). Some follow `chk_` prefix convention (`chk_profiles_subscription_status`), others don't.

---

## 4. Normalization

### DB-NORM-01 (MEDIUM) — `pipeline_items` stores denormalized licitacao snapshot

The `pipeline_items` table stores a copy of procurement data (`objeto`, `orgao`, `uf`, `valor_estimado`, `data_encerramento`, `link_pncp`). This is intentional (snapshot at save time), but the data can become stale. There's no mechanism to refresh snapshots.

**Recommendation:** Document this as a deliberate denormalization decision. Consider adding a `snapshot_at` timestamp.

### DB-NORM-02 (MEDIUM) — `search_sessions` stores arrays (`sectors[]`, `ufs[]`, `custom_keywords[]`)

Array columns prevent efficient querying (e.g., "find all sessions for sector X"). The backend migration `010_normalize_session_arrays.sql` normalizes existing data (sorts arrays) but doesn't create junction tables.

**Impact:** Acceptable for the current scale. If analytics queries on individual sectors/UFs become frequent, consider junction tables.

### DB-NORM-03 (LOW) — JSONB columns without schema validation

Several tables use JSONB for flexible storage without PostgreSQL-level schema validation:
- `profiles.context_data` — documented schema but no CHECK
- `search_results_cache.results` — only size CHECK (2MB), no structure validation
- `search_results_cache.search_params` — no validation
- `alerts.filters` — documented schema but no CHECK
- `search_results_cache.coverage` — no validation
- `audit_events.details` — no validation
- `reconciliation_log.details` — no validation

**Impact:** Application-level validation (Pydantic) provides the primary guardrail. Database-level validation would add safety but reduce flexibility.

---

## 5. Migration Quality

### DB-MIG-01 (HIGH) — Dual migration directories create confusion

Migrations exist in both `supabase/migrations/` (66 files) and `backend/migrations/` (10 files). The backend migrations were apparently never applied via Supabase CLI (they lack timestamp prefixes), leading to PGRST202 errors. Migration `20260305100000_restore_check_and_increment_quota.sql` explicitly states this was the root cause.

**Recommendation:** Consolidate all migrations into `supabase/migrations/` with proper timestamp prefixes. Mark `backend/migrations/` as deprecated.

### DB-MIG-02 (HIGH) — Non-sequential naming creates ordering ambiguity

Early migrations use `001_`, `002_`, ... `033_` format. Later migrations use timestamp format `20260220120000_`. Some timestamps are out of order with their content (e.g., `20260304110000_search_results_store_hardening.sql` has a timestamp before `20260304200000_rls_standardize_service_role.sql` but was meant to run after `20260303100000`). Migration `027b_` is a special case that may not sort correctly.

### DB-MIG-03 (MEDIUM) — No down-migrations (not reversible)

Only one migration has a rollback comment (`010_stripe_webhook_events.sql`). None of the 76 migrations include actual DOWN/rollback SQL. A disaster scenario requiring rollback would need manual SQL.

**Recommendation:** For critical schema changes, include a commented rollback section at the bottom of each migration.

### DB-MIG-04 (MEDIUM) — Some migrations are not idempotent

While most use `IF NOT EXISTS` and `DROP ... IF EXISTS` patterns, a few would fail on re-run:
- `008_add_billing_period.sql` — `ADD COLUMN` without `IF NOT EXISTS` for `billing_period` (but has the validation DO block)
- `20260228170000_trial_14_days.sql` — UPDATE statements would re-run, potentially re-setting trial dates for users who were already adjusted

### DB-MIG-05 (LOW) — Hardcoded Stripe Price IDs in migrations

Migrations 015, 029, 20260226120000, and 20260301300000 contain production Stripe Price IDs. These should be environment-specific but are baked into the migration SQL. Migration 021 documents this as a known issue but no fix has been applied.

**Recommendation:** Store Stripe Price IDs in a configuration table or environment variables, not in migrations.

---

## 6. Performance Concerns

### DB-PERF-01 (HIGH) — `search_results_cache.results` JSONB can be up to 2MB per row

The CHECK constraint allows up to 2MB per row. With 10 entries per user (eviction limit), a single user can store up to 20MB of JSONB. With many users, this table could grow large quickly.

**Monitoring needed:**
```sql
SELECT pg_size_pretty(pg_total_relation_size('search_results_cache')) AS total_size;
SELECT COUNT(*), pg_size_pretty(AVG(octet_length(results::text))) AS avg_size FROM search_results_cache;
```

### DB-PERF-02 (HIGH) — `search_results_store.results` JSONB with no retention enforcement in app

The `search_results_store` has a pg_cron job that deletes expired rows > 7 days, but the `expires_at` default is `now() + 24 hours`. Between 24h and 7 days, expired rows sit in the table unused but taking space. With high search volume, this could accumulate significant dead data.

### DB-PERF-03 (MEDIUM) — `search_state_transitions` grows unbounded per search

Each search produces multiple state transition records (typically 5-10 per search). There's no retention policy or cleanup job for this table. Over time, it will grow proportionally to total searches.

**Fix:** Add a pg_cron job: `DELETE FROM search_state_transitions WHERE created_at < NOW() - INTERVAL '30 days'`

### DB-PERF-04 (MEDIUM) — `cleanup_search_cache_per_user()` trigger runs on every INSERT

The eviction function counts all user entries, then potentially deletes in a subquery. For users near the 10-entry limit, this adds overhead to every cache write.

**Optimization:** Add a short-circuit: check if the user likely has > 10 entries before running the full eviction query.

### DB-PERF-05 (MEDIUM) — `get_conversations_with_unread_count()` uses correlated subquery

The function uses `(SELECT COUNT(*) FROM messages m WHERE ...)` inside the main query, which runs once per conversation. For users with many conversations, this could be slow.

### DB-PERF-06 (LOW) — No table partitioning

Tables like `audit_events`, `search_state_transitions`, and `search_sessions` are append-heavy and time-series in nature. At scale, they would benefit from time-based partitioning. Not needed at current (POC/beta) stage.

### DB-PERF-07 (LOW) — `alert_sent_items` has no retention cleanup

Sent items accumulate forever. If alerts are active and run daily, this table will grow continuously.

**Fix:** Add pg_cron cleanup for entries older than 30 days.

---

## 7. Security Issues

### DB-SEC-01 (HIGH) — OAuth tokens stored in plaintext in database

The `user_oauth_tokens` table columns `access_token` and `refresh_token` are documented as "AES-256 encrypted" but the encryption happens at the application layer (not database). If the Supabase service role key or database connection is compromised, tokens are exposed.

**Mitigation:** Verify that application-level encryption is actually implemented in the backend OAuth code. Consider using PostgreSQL `pgcrypto` for column-level encryption.

### DB-SEC-02 (HIGH) — `mfa_recovery_codes.code_hash` storage security

Recovery codes are stored as bcrypt hashes, which is correct. However, the table has no rate limiting at the database level. Rate limiting is only in the application code.

**Mitigation:** Ensure the `mfa_recovery_attempts` table is actively used by the application to enforce rate limits before code verification.

### DB-SEC-03 (MEDIUM) — Stripe Price IDs visible in `plans` table

The `plans` table has `FOR SELECT USING (true)` RLS policy (public read). This exposes Stripe Price IDs to any authenticated or anonymous user. While Price IDs are not secret (they're used in client-side checkout), exposing them could allow price inspection attacks.

**Impact:** Low risk since Stripe Price IDs are typically used in the frontend for checkout integration anyway. Document as accepted risk.

### DB-SEC-04 (MEDIUM) — `profiles.email` is exposed via partner RLS policy

The `partners_self_read` policy reads `auth.users.email` to match against `contact_email`:
```sql
contact_email = (SELECT email FROM auth.users WHERE id = auth.uid())
```
This is a cross-schema query that could be optimized but is functionally correct.

### DB-SEC-05 (LOW) — System cache warmer account in `auth.users`

Migration `20260226110000` inserts a system user (`00000000-0000-0000-0000-000000000000`) into `auth.users` with no password. While the `encrypted_password = ''` prevents login, the account exists in the auth system and could potentially be targeted.

**Mitigation:** Ensure Supabase Auth never allows login with empty password. Consider setting `is_sso_user = true` or `banned_until` to a future date.

---

## 8. Data Integrity

### DB-INT-01 (HIGH) — `partner_referrals.referred_user_id` ON DELETE SET NULL inconsistency

Migration `20260304100000` sets `ON DELETE SET NULL` for `partner_referrals.referred_user_id`, but the column is defined as `NOT NULL` in the original table creation (migration `20260301200000`). If a profile is deleted, the SET NULL would violate the NOT NULL constraint, causing the DELETE to fail.

**Fix:** Either change the column to nullable (`ALTER TABLE partner_referrals ALTER COLUMN referred_user_id DROP NOT NULL`) or change ON DELETE behavior to CASCADE.

### DB-INT-02 (MEDIUM) — No FK from `search_state_transitions.search_id` to `search_sessions.search_id`

The `search_state_transitions` table references `search_sessions` via `search_id`, but there's no FK constraint. Orphan transition records could exist for deleted sessions. The RLS policy relies on this join, so orphan records would be invisible to users but still consume space.

**Fix:** Consider adding: `ALTER TABLE search_state_transitions ADD CONSTRAINT fk_transitions_session FOREIGN KEY (search_id) REFERENCES search_sessions(search_id) ON DELETE CASCADE;`
**Caveat:** `search_sessions.search_id` is nullable and not unique, so this FK may not be valid. The column would need a UNIQUE constraint first.

### DB-INT-03 (MEDIUM) — `user_subscriptions.billing_period` constraint may conflict with legacy data

The CHECK constraint was updated to `('monthly', 'semiannual', 'annual')` but legacy rows might have been inserted with the original constraint `('monthly', 'annual')` before `semiannual` was added. Migration 029 handles this correctly with `DROP CONSTRAINT IF EXISTS` + `ADD CONSTRAINT`, but verify no rows were missed.

### DB-INT-04 (MEDIUM) — `profiles.phone_whatsapp` CHECK constraint only validates format, not content

The regex `'^[0-9]{10,11}$'` validates length and digits-only, but doesn't validate Brazilian phone number structure (area code + number). Invalid area codes like `00` would be accepted.

### DB-INT-05 (LOW) — `search_results_cache` UNIQUE constraint allows same params for different date ranges

The UNIQUE constraint is `(user_id, params_hash)`. If two searches have the same sector+UFs but different date ranges, they would produce different `params_hash` values (STORY-306 cache key includes dates). However, the `params_hash_global` column allows cross-user sharing, which could serve stale date ranges to other users.

### DB-INT-06 (LOW) — `plan_billing_periods` and `plan_features` no updated_at column

`plan_billing_periods` has no `updated_at` column or trigger, making it impossible to track when pricing was last changed. `plan_features` does have `updated_at` with a trigger.

---

## 9. Backup/Recovery

### DB-BAK-01 (HIGH) — No documented disaster recovery procedure

There are 76 migrations but no documented procedure for:
1. Recreating the database from scratch (would need to run all 76 in order)
2. Restoring from Supabase point-in-time recovery
3. Handling migration failures mid-way (no savepoints or manual intervention guide)

**Recommendation:** Create a `supabase/docs/DISASTER-RECOVERY.md` documenting:
- How to recreate the database from migrations
- Known migration order dependencies
- Post-migration verification queries
- Supabase PITR restoration procedure

### DB-BAK-02 (HIGH) — `backend/migrations/` were never applied via Supabase CLI

The 10 files in `backend/migrations/` lack timestamp prefixes and were likely applied manually or via a different mechanism. Migration `20260305100000_restore_check_and_increment_quota.sql` confirms the `check_and_increment_quota` RPC was missing because `003_atomic_quota_increment.sql` (in `backend/migrations/`) was never applied by the CLI.

**Impact:** If the database is recreated from `supabase/migrations/` alone, the `classification_feedback` table (backend migration 006) would not exist, and the quota RPC functions might be missing (fixed by migration 20260305100000).

### DB-BAK-03 (MEDIUM) — pg_cron jobs are not in migrations

The pg_cron jobs are created in migrations 022, 023, and 20260225150000. However, if pg_cron extension is not available, these migrations fail silently (they use `CREATE EXTENSION IF NOT EXISTS pg_cron` which requires superuser). On a fresh Supabase project, pg_cron must be explicitly enabled via the dashboard.

### DB-BAK-04 (MEDIUM) — Stripe webhook idempotency depends on `stripe_webhook_events`

If this table is lost or truncated, Stripe webhook retries could cause duplicate processing (double charges, double plan assignments). The 90-day retention means events older than 90 days can't be checked for idempotency.

### DB-BAK-05 (LOW) — No database-level audit of schema changes

Schema changes are tracked via migrations in git, but there's no database-level logging of DDL changes. If a manual ALTER TABLE is run via Supabase Dashboard, it won't be captured.

**Mitigation:** Migration 20260225100000 was created specifically to codify dashboard-applied changes. Establish a policy: never modify schema via dashboard without creating a corresponding migration.

---

## Summary of Findings by Severity

| Severity | Count | Key Issues |
|----------|-------|------------|
| CRITICAL | 1 | DB-RLS-01: classification_feedback uses auth.role() pattern |
| HIGH | 10 | DB-IDX-01/02 (wrong table names in index migration), DB-SCH-01 (trigger rewrite churn), DB-MIG-01 (dual migration dirs), DB-PERF-01/02 (JSONB size), DB-SEC-01/02 (token/MFA security), DB-INT-01 (SET NULL on NOT NULL), DB-BAK-01/02 (no DR docs) |
| MEDIUM | 15 | RLS gaps, schema inconsistencies, normalization, migration quality, performance, data integrity |
| LOW | 12 | Redundant indexes, naming inconsistencies, missing NOT NULL, missing CHECKs |
| INFO | 2 | Index count monitoring, naming conventions |

---

## Recommended Priority Actions

1. **Fix DB-IDX-01/02** — Re-create the RLS user_id indexes with correct table names
2. **Fix DB-RLS-01** — Standardize classification_feedback service_role policy
3. **Fix DB-INT-01** — Resolve partner_referrals NOT NULL vs SET NULL conflict
4. **Document DB-BAK-01** — Create disaster recovery procedure
5. **Fix DB-SCH-02** — Consolidate updated_at trigger functions
6. **Add DB-PERF-03** — Retention cleanup for search_state_transitions
7. **Consolidate DB-MIG-01** — Move backend migrations to supabase/ with proper timestamps

---

## 10. Accepted Risks & Design Decisions (DEBT-017)

**Added:** 2026-03-09 — DEBT-017 Database Long-Term Optimization

### DB-004 — `mfa_recovery_codes` no rate limiting in DB

**Status:** ACCEPTED — App-layer rate limiting is the correct pattern.
**Rationale:** Database-level rate limiting via triggers would add complexity and coupling. The `mfa_recovery_attempts` table + application code in `auth.py` provides rate limiting with proper backoff and lockout. DB-level triggers cannot implement exponential backoff or account-level lockout policies.
**Owner:** Backend auth module (`auth.py`)

### DB-005 — `mfa_recovery_attempts` no SELECT policy for users

**Status:** ACCEPTED — Intentional information leakage prevention.
**Rationale:** Exposing recovery attempt history to users would reveal timing information about brute-force attempts against their account. Only `service_role` can read this table. Users see "too many attempts" errors via the API without knowing attempt counts.

### DB-006 — `trial_email_log` no user-facing policies

**Status:** ACCEPTED — Backend-only table.
**Rationale:** This table tracks automated trial drip emails sent by the worker process. Users have no legitimate need to query their email send history. If a user settings page needs this data in the future, add a SELECT policy scoped to `user_id = auth.uid()`.

### DB-008 — Stripe Price IDs visible in `plans` table

**Status:** ACCEPTED — Used client-side by design (Stripe Checkout).
**Rationale:** Stripe Price IDs are not secret — they are used in the Stripe Checkout flow. The `plans` table has `FOR SELECT USING (true)` because the pricing page needs to display plan information. The actual checkout session creation happens server-side with additional validation. Note: STORY-210 AC11 strips `stripe_price_id_*` from the API response, so frontend never receives them directly.

### DB-009 — Partner RLS uses `auth.users.email` (cross-schema query)

**Status:** OPTIMIZED — Already uses `partners.contact_email` pattern.
**Rationale:** The `partners_self_read` policy compares `contact_email = (SELECT email FROM auth.users WHERE id = auth.uid())`. This is the standard Supabase pattern for email-based RLS. The query is to `auth.users` (not `profiles`), which is the canonical source of email. No further optimization needed — the `auth.uid()` call is already indexed.

### DB-016 — `search_sessions.status` no DB-level transition enforcement

**Status:** ACCEPTED — App-layer state machine is the correct pattern.
**Rationale:** Complex FSM transition logic (with stages, error recovery, retries, cancellation) is better expressed in application code (`search_state_manager.py`) than in SQL triggers. DB-level enforcement would require duplicating the state machine logic, creating a maintenance burden. The `search_state_transitions` audit table provides full traceability. Valid transitions documented via SQL COMMENT on the column (DEBT-017 migration).

### DB-020 — Naming inconsistency in constraints

**Status:** DOCUMENTED — Convention adopted for future constraints.
**Rationale:** Retroactively renaming all existing constraints would require DROP + ADD for each, risking downtime and FK dependency issues. Convention documented in schema COMMENT: `chk_{table}_{column}` for CHECK, `fk_{table}_{column}` for FK, `uq_{table}_{column}` for UNIQUE, `idx_{table}_{column}` for indexes. Legacy constraints retain original names.

### DB-022 — `profiles.phone_whatsapp` CHECK only validates digits/length

**Status:** ACCEPTED — App-layer validation is the correct pattern.
**Rationale:** Brazilian phone number validation rules (area codes, mobile prefixes, landline vs mobile) change over time. Encoding these rules in a CHECK constraint would require migrations for each regulatory change. The DB CHECK `'^[0-9]{10,11}$'` catches obvious errors; full validation happens in the frontend form and backend Pydantic schema.

### DB-023 — `search_results_cache` cross-user sharing with date range

**Status:** MONITORED — Low risk at current scale.
**Rationale:** The `params_hash_global` column enables SWR-style cross-user cache sharing. Date ranges ARE included in the hash (STORY-306), so different date ranges produce different hashes. The risk is that a cached result from user A could be served to user B for identical params — this is intentional for performance. Stale data risk is mitigated by the 24h TTL and background revalidation.

### DB-024 — `plan_billing_periods` no `updated_at` column

**Status:** RESOLVED — Column added in DEBT-017 migration.
**Rationale:** Pricing changes are infrequent but should be trackable. Added `updated_at TIMESTAMPTZ DEFAULT now()` with auto-update trigger.

### DB-027 — No down-migrations

**Status:** ACCEPTED — PITR is the rollback mechanism.
**Rationale:** Supabase provides Point-in-Time Recovery (PITR) as the primary rollback mechanism. Down-migrations for 76+ files would be expensive to write and maintain. For critical schema changes, the rollback procedure is: (1) Identify the timestamp before the migration, (2) Use Supabase PITR to restore, (3) Re-apply any migrations after the restore point that should be kept. Manual rollback scripts can be added as comments in individual migrations for high-risk changes.

### DB-036 — No table partitioning

**Status:** DEFERRED — Plan when row count > 1M/month.
**Rationale:** Tables `audit_events`, `search_state_transitions`, and `search_sessions` are append-heavy and time-series. At current beta scale (~10K rows/month), partitioning overhead exceeds benefit. Monitor via: `SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE relname IN ('audit_events', 'search_state_transitions', 'search_sessions') ORDER BY n_live_tup DESC;`. Partition by month when any table exceeds 1M rows/month.

### DB-044 — pg_cron jobs not in migrations (require superuser)

**Status:** ACCEPTED — Manual setup required.
**Rationale:** pg_cron requires the `cron` extension which needs superuser. On Supabase, this is enabled via the Dashboard (Database > Extensions > pg_cron). Migrations use `CREATE EXTENSION IF NOT EXISTS pg_cron` but this only works if the extension is already enabled. Manual setup steps:
1. Enable pg_cron in Supabase Dashboard > Database > Extensions
2. Run migrations normally — pg_cron jobs will be created
3. Verify with: `SELECT * FROM cron.job;`

### DB-046 — No audit trail for DB-level schema changes

**Status:** ACCEPTED — Policy: "never modify schema via dashboard".
**Rationale:** All schema changes MUST go through migration files in `supabase/migrations/`. Direct Dashboard modifications are prohibited. If a Dashboard change is unavoidable (e.g., enabling extensions), create a corresponding migration file documenting the change. This policy is documented in the schema COMMENT and enforced by code review.

### DB-050 — No FK from `search_state_transitions.search_id` to `search_sessions`

**Status:** ACCEPTED — Cannot add FK due to schema constraints.
**Rationale:** `search_sessions.search_id` is nullable and not unique (retries can share search IDs). Adding a FK would require: (1) making search_id NOT NULL on search_sessions (breaks existing rows), (2) adding UNIQUE constraint (breaks retry semantics). Orphan transitions are cleaned up by the pg_cron retention job (30-day retention). Documented via SQL COMMENT on the column.
