# SmartLic Database Audit

> **Date:** 2026-03-31 | **Auditor:** @data-engineer (Dara) -- Brownfield Discovery Phase 2
> **Scope:** 106 migrations, 35 tables, PostgreSQL 17 (Supabase Cloud)
> **Baseline:** Zero-failure CI with 5131+ backend tests, 2681+ frontend tests

---

## Executive Summary

The SmartLic database is in **good shape** for a POC-to-production system. 100% RLS coverage, JSONB size governance, atomic quota RPCs, and comprehensive indexing demonstrate engineering maturity. However, 106 migration files create significant schema archaeology risk, and several structural debts warrant attention before scaling.

| Category | Score | Notes |
|----------|-------|-------|
| Security (RLS) | A | 100% coverage, service_role properly scoped |
| Data Integrity | B+ | CHECK constraints present, some FK gaps remain |
| Performance | B | Good indexing, some missing composite indexes |
| Maintainability | C+ | 106 migrations need squashing, naming partially standardized |
| Observability | B+ | Bloat monitoring, orphan detection, audit trail |

**Critical issues:** 0
**High issues:** 3
**Medium issues:** 8
**Low issues:** 7

---

## 1. Security Assessment

### 1.1 RLS Coverage

| Status | Count | Tables |
|--------|-------|--------|
| RLS enabled with policies | 35/35 | ALL |
| RLS enabled WITHOUT policies | 0 | -- |
| RLS disabled | 0 | -- |

**Verdict: EXCELLENT.** 100% RLS coverage.

### 1.2 Service Role Policy Consistency

Service role policies have been standardized across multiple migration waves (016, 027, 20260225130000, 20260304200000). The current state uses `TO service_role` consistently, though some tables still use `auth.role() = 'service_role'` pattern in older policies that may not have been caught by the standardization migrations.

### 1.3 SECURITY DEFINER Functions

| Function | Risk | Mitigation |
|----------|------|------------|
| handle_new_user() | MEDIUM | Runs on auth.users INSERT. Sets search_path implicitly. |
| upsert_pncp_raw_bids() | LOW | Explicit `SET search_path = public`. Service role only. |
| search_datalake() | LOW | Explicit `SET search_path = public`. Read-only. |
| purge_old_bids() | LOW | Explicit `SET search_path = public`. Service role only. |
| check_and_increment_quota() | LOW | No SET search_path but operates on single table. |
| get_conversations_with_unread_count() | LOW | No SET search_path. Read-only. |
| get_analytics_summary() | LOW | No SET search_path. Read-only. |
| cleanup_search_cache_per_user() | LOW | No SET search_path. Trigger function. |

### 1.4 Sensitive Data

| Table | Column | Classification | Protection |
|-------|--------|---------------|------------|
| user_oauth_tokens | access_token | SECRET | AES-256 encrypted (app layer) |
| user_oauth_tokens | refresh_token | SECRET | AES-256 encrypted (app layer) |
| mfa_recovery_codes | code_hash | SECRET | bcrypt hashed |
| audit_events | actor_id_hash | PII | SHA-256 truncated to 16 hex |
| audit_events | ip_hash | PII | SHA-256 truncated to 16 hex |
| stripe_webhook_events | payload | SENSITIVE | Full Stripe event (may contain email) |
| profiles | email | PII | Protected by RLS |
| profiles | phone_whatsapp | PII | Protected by RLS + format constraint |

---

## 2. Issues Found

### HIGH

#### H-01: handle_new_user() missing SET search_path

**Location:** Multiple migrations redefine `handle_new_user()` (001, 007, 016, 024, 027, 20260224000000, 20260225110000)
**Risk:** SECURITY DEFINER without explicit `SET search_path = public` is vulnerable to search_path injection. An attacker could create a `profiles` table in another schema.
**Impact:** The function is called on every signup. Exploitation requires schema creation privileges (unlikely for normal users but possible for a compromised service role).
**Recommendation:** Add `SET search_path = public` to the function definition. Priority: HIGH.

#### H-02: 106 migration files create schema archaeology risk

**Location:** `supabase/migrations/`
**Risk:** 106 files make it extremely difficult to understand the current schema state. Multiple migrations modify the same objects (handle_new_user redefined 7 times, profiles_plan_type_check redefined 5 times). A disaster recovery scenario (DB recreation from migrations) would be fragile.
**Impact:** Developer productivity, onboarding time, migration conflict risk.
**Recommendation:** Execute migration squash plan (already documented in `supabase/docs/MIGRATION-SQUASH-PLAN.md`). Consolidate into ~5-10 canonical migrations covering the final state.

#### H-03: Duplicate/legacy trigger functions not fully cleaned up

**Location:** `update_updated_at()` vs `set_updated_at()`
**Risk:** Two functions exist that do the same thing. `update_updated_at()` was the original (migration 001). `set_updated_at()` was created in migration 20260304120000 and 20260326000000. DEBT-207 re-pointed triggers to `set_updated_at()` but `update_updated_at()` still exists and may be referenced.
**Impact:** Confusion, potential for triggers using the wrong function after future migrations.
**Recommendation:** Drop `update_updated_at()` and alias it to `set_updated_at()`, or consolidate into one canonical name.

---

### MEDIUM

#### M-01: classification_feedback.user_id still references auth.users

**Location:** `20260308200000_debt002_bridge_backend_migrations.sql` line 104
**Risk:** All other tables had FKs standardized to `profiles(id)`, but classification_feedback was created in the bridge migration with `REFERENCES auth.users(id)`. The FK standardization in `20260225120000` attempted to fix this but the bridge migration came later and re-introduced the old pattern.
**Impact:** Inconsistent cascade behavior. If a profile is deleted via Supabase Dashboard, the classification_feedback FK may not cascade properly.
**Recommendation:** Create migration to re-point FK to profiles(id).

#### M-02: Hardcoded Stripe price IDs in migrations

**Location:** Migrations 015, 029, 20260226120000, 20260301300000
**Risk:** Production Stripe price IDs (price_1Sy..., price_1T1..., price_1T5...) are hardcoded in migration files. If migrations are re-run against a staging/test environment, they will insert production price IDs.
**Impact:** Staging environment could accidentally charge real Stripe prices if not manually overwritten.
**Recommendation:** Move Stripe price IDs to environment variables or a seed script that checks the environment.

#### M-03: ingestion_checkpoints.crawl_batch_id lacks enforced FK to ingestion_runs

**Location:** `20260326000000_datalake_raw_bids.sql` line 200
**Risk:** The relationship between ingestion_checkpoints and ingestion_runs is documented but not enforced via FK. Orphan checkpoints can accumulate.
**Impact:** Data integrity. Mitigated by the `check_ingestion_orphans()` monitoring function and `ingestion_orphan_checkpoints` view (DEBT-207).
**Recommendation:** Consider adding an enforced FK with NOT VALID + VALIDATE pattern if ingestion performance allows it. Current monitoring approach is acceptable.

#### M-04: search_state_transitions.search_id has no FK to search_sessions

**Location:** `20260221100002_create_search_state_transitions.sql`
**Risk:** No referential integrity between transitions and sessions. Orphan transitions possible.
**Impact:** Low — transitions are fire-and-forget audit data. But makes cleanup harder.
**Recommendation:** Add FK with ON DELETE CASCADE if performance is acceptable.

#### M-05: Multiple tables lack retention/cleanup strategy

**Location:** search_state_transitions, classification_feedback, alert_runs, mfa_recovery_attempts
**Risk:** These tables grow without bound. search_state_transitions especially will grow proportionally to search volume.
**Impact:** Storage costs, query performance degradation over time.
**Recommendation:** Add pg_cron cleanup jobs: search_state_transitions > 90 days, classification_feedback > 12 months, alert_runs > 6 months, mfa_recovery_attempts > 30 days.

#### M-06: organizations/organization_members FKs reference auth.users

**Location:** `20260301100000_create_organizations.sql` lines 25, 44
**Risk:** The original CREATE TABLE used `auth.users(id)`. Migration `20260304100000` re-pointed to `profiles(id)`. However, the organization_members table's self-referencing RLS policy queries itself, which PostgreSQL optimizes poorly.
**Impact:** Potential performance issue as org membership grows.
**Recommendation:** Monitor query performance. Consider denormalizing role into a materialized view if needed.

#### M-07: No VACUUM ANALYZE scheduled for high-churn tables

**Location:** pncp_raw_bids, search_results_cache, search_state_transitions
**Risk:** pncp_raw_bids has daily hard deletes (purge_old_bids). The bloat monitoring function (`check_pncp_raw_bids_bloat`) was added but no automated VACUUM ANALYZE is scheduled.
**Impact:** Dead tuples accumulate, degrading scan performance. Supabase auto-vacuum may not be aggressive enough for daily DELETE patterns.
**Recommendation:** Add a pg_cron job: `VACUUM ANALYZE public.pncp_raw_bids` daily at 7:30 UTC (after purge at 7:00 UTC).

#### M-08: Trigger naming only partially standardized

**Location:** DEBT-207 standardized to `trg_` prefix, but some triggers still use `tr_` or `trigger_` prefix.
**Risk:** Inconsistency makes automation and monitoring harder.
**Remaining:** `tr_pipeline_items_updated_at`, `trigger_alert_preferences_updated_at`, `trigger_alerts_updated_at`, `trigger_create_alert_preferences_on_profile`.
**Recommendation:** Complete the rename in a follow-up migration.

---

### LOW

#### L-01: Dead plan catalog entries

Multiple legacy plans exist in the `plans` table with `is_active = false`: pack_5, pack_10, pack_20, monthly, annual, consultor_agil, maquina, sala_guerra, free. These consume space and add noise to queries.
**Recommendation:** Consider adding a `deprecated_at` timestamp column instead of boolean for better audit trail. No rush.

#### L-02: profiles.context_data schema not enforced

The `context_data` JSONB column has a size constraint (< 512KB) but no schema validation at the database level. The expected shape (ufs_atuacao, faixa_valor_min/max, porte_empresa, etc.) is only documented in comments.
**Recommendation:** Consider a CHECK constraint with jsonb_typeof or a validation function.

#### L-03: Redundant index on alert_preferences.user_id

`idx_alert_preferences_user_id` is redundant because `alert_preferences_user_id_unique` (the UNIQUE constraint) already creates an index on user_id.
**Recommendation:** Drop the redundant index.

#### L-04: google_sheets_exports GIN index on search_params rarely queried

`idx_google_sheets_exports_search_params` is a GIN index on JSONB that is unlikely to be used in current query patterns. GIN indexes have write amplification cost.
**Recommendation:** Verify query patterns. Drop if unused.

#### L-05: plan_features.id uses SERIAL (int4) instead of UUID

All other tables use UUID primary keys. plan_features uses SERIAL. This is inconsistent but not harmful since plan_features is a low-volume catalog table.
**Recommendation:** No action needed unless migrating to a distributed database.

#### L-06: Some RLS policies use overly broad admin checks

Several policies check `profiles.is_admin = true` via subquery. This works but requires a profiles table scan for each row check. For high-volume tables, this could be slow.
**Tables affected:** stripe_webhook_events, audit_events, reconciliation_log, conversations, messages.
**Recommendation:** Consider caching admin status in a JWT claim for better RLS performance. Low priority given current scale.

#### L-07: user_subscriptions.annual_benefits column is vestigial

The `annual_benefits` JSONB column was added in migration 008 but appears to have been superseded by the `plan_features` table (migration 009). It defaults to '{}' and is not populated by any known code path.
**Recommendation:** Verify no code reads this column. If confirmed unused, drop it in a cleanup migration.

---

## 3. Missing Indexes

| Table | Suggested Index | Reason |
|-------|----------------|--------|
| search_state_transitions | (search_id, to_state) | Common debugging query: find specific state for a search |
| classification_feedback | (setor_id, created_at DESC) | Feedback analysis by sector over time |
| alert_sent_items | (sent_at) — already exists | Confirmed present |
| reconciliation_log | (divergences_found) partial WHERE > 0 | Quick lookup of problematic runs |

---

## 4. Schema Inconsistencies

| Issue | Details |
|-------|---------|
| FK target inconsistency | classification_feedback still FK to auth.users, all others to profiles |
| Trigger function duality | `update_updated_at()` and `set_updated_at()` both exist |
| Trigger name inconsistency | Mix of `trg_`, `tr_`, `trigger_` prefixes |
| RLS policy name inconsistency | DEBT-207 renamed many but some old names remain on tables added after the rename migration |
| Primary key type inconsistency | plan_features uses SERIAL, all others use UUID |
| Timestamp column naming | Most use `created_at`/`updated_at`, but google_sheets_exports uses `last_updated_at`, health_checks uses `checked_at` |

---

## 5. Performance Concerns

### 5.1 pncp_raw_bids — Largest Table

- **Current:** ~40K+ rows, 12-day retention with daily hard deletes
- **Indexes:** 8 indexes (GIN FTS + 7 B-tree), all appropriate
- **Concern:** Hard DELETEs generate dead tuples. Bloat monitoring exists but no automated VACUUM ANALYZE.
- **Mitigation:** Pre-computed tsv column eliminates double to_tsvector computation. Batch upsert replaced row-by-row loop.

### 5.2 search_datalake() RPC Performance

- **Current:** SECURITY DEFINER (bypasses RLS for speed), uses pre-computed tsv, limit capped at 5000
- **Good:** tsquery parse errors fall back to plainto_tsquery
- **Concern:** No query planner hints. Complex WHERE clause with multiple OR branches may not always pick optimal index.
- **Recommendation:** Monitor EXPLAIN ANALYZE output for common query patterns.

### 5.3 cleanup_search_cache_per_user() Trigger

- **Current:** Runs on every INSERT, counts all entries for user, may DELETE multiple rows
- **Concern:** COUNT(*) + DELETE in a trigger adds latency to cache write operations
- **Recommendation:** Acceptable at current scale (10 max per user). If cache write latency becomes an issue, consider moving cleanup to a periodic job.

### 5.4 RLS Subquery Performance

Admin-check RLS policies use `EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin)`. This executes per-row. For tables with many rows (audit_events, stripe_webhook_events), this adds overhead.
**Mitigation:** These tables are typically queried by admins with LIMIT/pagination. Acceptable at current scale.

---

## 6. Recommendations (Prioritized)

### Immediate (before next deploy)

1. **Add SET search_path to handle_new_user()** — Security hardening, 1 line change
2. **Add retention jobs for unbounded tables** — search_state_transitions, classification_feedback, mfa_recovery_attempts

### Short-term (next sprint)

3. **Fix classification_feedback FK** to reference profiles(id)
4. **Drop redundant idx_alert_preferences_user_id** index
5. **Schedule VACUUM ANALYZE** for pncp_raw_bids post-purge
6. **Complete trigger naming** standardization (4 remaining)

### Medium-term (next month)

7. **Execute migration squash plan** — Reduce 106 files to ~10 canonical migrations
8. **Remove hardcoded Stripe price IDs** from migrations, move to env-aware seed script
9. **Evaluate dropping** vestigial `annual_benefits` column from user_subscriptions
10. **Add schema validation** for profiles.context_data JSONB

### Long-term (quarterly)

11. **Evaluate partitioning** for pncp_raw_bids if row count exceeds 500K
12. **Consider JWT-based admin checks** in RLS policies for better performance
13. **Review and drop** unused indexes (google_sheets_exports GIN on search_params)

---

## 7. Positive Findings

These demonstrate good engineering practices:

1. **100% RLS coverage** — Every table has RLS enabled with appropriate policies
2. **JSONB size governance** — All JSONB columns have < 512KB or < 2MB constraints (DEBT-DB-010)
3. **Atomic quota RPCs** — Race condition prevention via FOR UPDATE and ON CONFLICT
4. **Pre-computed tsvector** — Eliminates double computation in search queries (DEBT-210)
5. **Batch upsert** — Single-statement INSERT ON CONFLICT replaces row-by-row loop (DEBT-210)
6. **Optimistic locking** — pipeline_items.version and stripe_webhook_events.status prevent concurrent update issues (STORY-318)
7. **Bloat monitoring** — Dedicated function and view for pncp_raw_bids dead tuple tracking (DEBT-203)
8. **Orphan detection** — View and function for ingestion checkpoint orphans (DEBT-207)
9. **Idempotent migrations** — Consistent use of IF NOT EXISTS, IF EXISTS, ON CONFLICT DO NOTHING
10. **Comprehensive comments** — Most tables and columns have descriptive COMMENT ON statements
