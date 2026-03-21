# SmartLic Database Audit Report

**Date:** 2026-03-20 | **Auditor:** @data-engineer (Brownfield Discovery Phase 2)
**Scope:** All 86 migration files + backend query patterns
**Rating Scale:** CRITICAL (production risk) / HIGH (should fix soon) / MEDIUM (improve when convenient) / LOW (nice to have)

---

## Executive Summary

The SmartLic database is in good shape overall. Four rounds of systematic hardening (016, TD-003, DEBT-009, DEBT-113) have addressed most RLS and FK issues. The schema is well-indexed with comprehensive pg_cron retention. However, several findings remain worth addressing.

| Severity | Count | Est. Total Hours |
|----------|-------|-----------------|
| CRITICAL | 1 | 2h |
| HIGH | 5 | 14h |
| LOW | 6 | 8h |
| MEDIUM | 8 | 16h |
| **Total** | **20** | **~40h** |

---

## 1. Schema Issues

### S-01: `handle_new_user()` Trigger Omits New Columns (HIGH, 2h)

**Finding:** The latest version of `handle_new_user()` (migration 20260225110000) inserts 10 columns but omits several that were added later:
- `subscription_status` (added 20260225100000) -- defaults to 'trial' via column default, so not blocking
- `trial_expires_at` (added 20260225100000) -- **NULL for new users**, meaning trial expiration is not set at signup
- `marketing_emails_enabled` (added 20260227140000) -- defaults to TRUE via column default

**Impact:** New user signups will have `trial_expires_at = NULL`. The application layer in `quota.py` must handle this (and does, by computing from `created_at + TRIAL_DURATION_DAYS`). However, this creates a dependency on application-level logic that should be in the trigger.

**Fix:** Update `handle_new_user()` to set `trial_expires_at = NOW() + INTERVAL '14 days'` and `subscription_status = 'trial'`.

### S-02: `plans.stripe_price_id` Legacy Column Still Present (LOW, 1h)

**Finding:** The `stripe_price_id` column on `plans` is deprecated (documented in DEBT-017) but still exists. `billing.py` uses it as a fallback. Three newer columns (`stripe_price_id_monthly`, `_semiannual`, `_annual`) plus `plan_billing_periods.stripe_price_id` are the canonical sources.

**Impact:** Schema confusion. New developers may use the wrong column.

**Fix:** After confirming `billing.py` no longer falls back to it, drop the column. Currently: accept risk (LOW).

### S-03: Inconsistent `created_at` Nullability (LOW, 1h)

**Finding:** Most tables define `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, but a few use nullable defaults:
- `user_oauth_tokens.created_at` -- `DEFAULT NOW()` without NOT NULL
- `plan_billing_periods.created_at` -- `DEFAULT NOW()` without NOT NULL

**Impact:** Queries assuming non-null `created_at` could produce unexpected results.

**Fix:** `ALTER TABLE ... ALTER COLUMN created_at SET NOT NULL` on `user_oauth_tokens` and `plan_billing_periods`.

### S-04: `search_state_transitions.user_id` Is Nullable (MEDIUM, 1h)

**Finding:** The `user_id` column was added in DEBT-009 (20260308320000) as nullable for backfill purposes. After backfill, orphan rows (where `search_id` does not match any `search_sessions`) will have `user_id = NULL`.

**Impact:** The RLS policy `user_id = auth.uid()` silently excludes these rows from user queries (correct behavior). However, `NULL` user_id means the retention cleanup job deletes these rows anyway (30-day retention). Acceptable, but should be NOT NULL after initial backfill stabilizes.

**Fix:** After verifying no NULL user_id rows exist in production, add `NOT NULL` constraint.

### S-05: `classification_feedback.user_id` FK to `auth.users` vs `profiles` Race Condition (MEDIUM, 1h)

**Finding:** Migration 20260308200000 (DEBT-002) creates `classification_feedback` with `REFERENCES auth.users(id)`, but migration 20260311100000 (DEBT-113) re-points it to `profiles(id)`. On a fresh install, the table is created pointing to `auth.users` and then immediately re-pointed. This works but is fragile -- if DEBT-113 fails, the FK is wrong.

**Impact:** Works in practice. On disaster recovery (fresh migration replay), it self-corrects.

**Fix:** Update DEBT-002's CREATE TABLE to reference `profiles(id)` directly (requires migration edit or a new consolidation migration).

---

## 2. RLS Gaps

### R-01: `trial_email_log` Has No User-Facing Policies (LOW, 0.5h)

**Finding:** RLS is enabled but there are NO policies for `authenticated` or `anon` roles. Only `service_role` (which bypasses RLS) can access it. This is intentional (backend-only table), but there is no explicit `service_role_all` policy documented.

**Impact:** None -- service_role bypasses RLS anyway. However, if the backend ever switches from service_role to authenticated context, writes would silently fail.

**Fix:** Add explicit `service_role_all` policy for consistency and documentation.

### R-02: `reconciliation_log` Service Role Policy Uses `auth.role()` Pattern (MEDIUM, 0.5h)

**Finding:** Migration 20260228140000 creates the policy as:
```sql
USING (auth.role() = 'service_role')
```
This was supposed to be standardized to `TO service_role` in TD-003 (20260304200000), which did fix it. However, the runtime assertion in DEBT-113 would catch this. Verify the policy is correct in production.

**Impact:** Likely already fixed. If not, the `auth.role()` pattern works but is less efficient than `TO service_role`.

**Fix:** Verify in production; if still using `auth.role()`, apply the `TO service_role` pattern.

### R-03: `organizations` Members Can View Organization But Not Update (LOW, 0.5h)

**Finding:** Organization admins (members with role='admin') can SELECT the organization but there is no UPDATE policy for non-owner admins. Only the owner can UPDATE.

**Impact:** Org admins cannot modify organization settings (name, logo) through Supabase client directly. They must use the backend service role.

**Fix:** If org admin edits are needed via frontend: add UPDATE policy for admin members. Currently, backend handles all writes, so this is acceptable.

---

## 3. Performance Concerns

### P-01: `get_conversations_with_unread_count()` Uses COUNT(*) OVER() (HIGH, 4h)

**Finding:** The function computes `COUNT(*) OVER()` (window function for total count) inside the CTE that also does LIMIT/OFFSET. The window function counts ALL matching rows before pagination is applied, requiring a full scan of matching conversations.

**Impact:** As conversations grow, this query becomes slower. For admins (who see ALL conversations), this is an O(N) scan on every page load.

**Fix:** Split into two queries: one for paginated results, one for total count (with caching). Or use `SELECT count(*)` as a separate cheap query.

### P-02: `cleanup_search_cache_per_user()` Trigger Fires on Every INSERT (MEDIUM, 1h)

**Finding:** The trigger fires on every INSERT to `search_results_cache`, counts all entries for the user, and short-circuits if <= 5. The short-circuit was added in DEBT-017 but the COUNT query still runs every time.

**Impact:** Minor overhead per cache write. With the short-circuit, this is fast (index scan on user_id), but unnecessary for the common case.

**Fix:** Consider increasing the eviction threshold check. Current design is acceptable.

### P-03: Missing Composite Index on `alert_sent_items(alert_id, sent_at)` (MEDIUM, 0.5h)

**Finding:** The retention cleanup query is `DELETE WHERE sent_at < NOW() - 180 days`. There is a `sent_at` index but the retention query does not filter by `alert_id` first, leading to a full scan of old rows.

**Impact:** The daily cleanup job scans the entire table. With 180-day retention, this is bounded but could be large.

**Fix:** The existing `idx_alert_sent_items_sent_at` index handles this adequately. LOW priority.

### P-04: `search_sessions` Has Overlapping Indexes (LOW, 1h)

**Finding:** Multiple indexes cover `user_id`:
- `idx_search_sessions_user_id` ON (user_id) -- added by DEBT-001
- `idx_search_sessions_created` ON (user_id, created_at DESC) -- original
- `idx_search_sessions_user_status_created` ON (user_id, status, created_at DESC) -- STORY-264

**Impact:** Redundant indexes waste storage and slow writes. The composite indexes subsume the simple `user_id` indexes.

**Fix:** Drop `idx_search_sessions_user_id` if the composite indexes serve all query patterns. Verify with `pg_stat_user_indexes`.

---

## 4. Security Issues

### SEC-01: Hardcoded Stripe Price IDs in Migrations (CRITICAL, 2h)

**Finding:** Migrations 015, 029, 20260226120000, and 20260301300000 contain production Stripe price IDs (e.g., `price_1T54vN9FhmvPslGYgfTGIAzV`). These are:
1. Visible in the git repository to anyone with code access
2. Hardcoded, meaning staging/dev environments get production price IDs
3. Cannot be changed without a new migration

**Impact:** If the repository becomes public, Stripe price IDs are exposed. While price IDs are not secret (they are public in Stripe checkout), they allow anyone to construct checkout sessions for production prices. The bigger risk is staging environments accidentally charging production prices.

**Fix:** Move Stripe price IDs to environment variables or a separate config table. The IDs in migrations should be test/placeholder values, with production values set via Supabase dashboard or `railway variables`.

### SEC-02: System Cache Warmer Account in `auth.users` (MEDIUM, 1h)

**Finding:** Migration 20260226110000 inserts a system account (`00000000-0000-0000-0000-000000000000`) into `auth.users` with empty password. Migration 20260308330000 bans it until 2099.

**Impact:** The account exists in auth.users with `authenticated` role. While banned, it still appears in user listings and could confuse admin dashboards. The nil UUID is a well-known sentinel value.

**Fix:** Ensure admin user listing queries exclude `id = '00000000-0000-0000-0000-000000000000'`. The ban is adequate defense-in-depth.

### SEC-03: `user_oauth_tokens.access_token` Stored in Public Schema (MEDIUM, 2h)

**Finding:** OAuth access and refresh tokens are stored in the `user_oauth_tokens` table in the public schema. The column comments say "AES-256 encrypted" but the encryption is done at the application layer, not database layer.

**Impact:** If an attacker gains database read access (e.g., via SQL injection or leaked service role key), they get encrypted tokens. The encryption key must be in a separate system for this to be effective. If the `OAUTH_ENCRYPTION_KEY` env var is compromised along with DB access, tokens are fully exposed.

**Fix:** This is the standard pattern for token storage. Ensure `OAUTH_ENCRYPTION_KEY` is in a secrets manager, not just env vars. Consider using Supabase Vault (if available) for additional protection.

---

## 5. Migration Issues

### M-01: Three Naming Conventions for Migrations (MEDIUM, 4h)

**Finding:** Migration files use three different naming patterns:
1. **Numbered prefix:** `001_profiles_and_sessions.sql` through `033_fix_missing_cache_columns.sql` (33 files)
2. **Timestamped:** `20260220120000_add_search_id.sql` through `20260315100000_debt120.sql` (53 files)
3. **Lettered suffix:** `006a_...`, `006b_...`, `027b_...` (3 files)

**Impact:** Supabase CLI applies migrations in lexicographic order. The numbered migrations (001-033) sort before timestamped ones (20260...), which is correct since they were created first. However, `027b` sorts between `027` and `028`, which could cause ordering issues if `027b` depends on something after `027`.

**Fix:** Post-GTM, consider a migration squash to consolidate into a single baseline migration + new timestamped migrations going forward. This is a debt item, not a risk.

### M-02: `027b` Was Superseded by `033` (LOW, 0.5h)

**Finding:** `027b_search_cache_add_sources_and_fetched_at.sql` has a comment saying "SUPERSEDED by 033_fix_missing_cache_columns.sql". Both files use `IF NOT EXISTS` so they are safe to run in sequence, but `027b` is effectively dead code.

**Impact:** None -- Supabase CLI runs both, and the IF NOT EXISTS makes them idempotent. But it is confusing.

**Fix:** Leave as-is or add `-- DEPRECATED: see 033` comment to the file.

### M-03: No Down Migrations (MEDIUM, 2h)

**Finding:** None of the 86 migration files have corresponding "down" or "rollback" migrations. Some migrations include rollback instructions in comments, but these are not automated.

**Impact:** If a migration causes issues in production, rollback requires manual SQL. Supabase CLI does not natively support down migrations, so this is the standard pattern.

**Fix:** For critical migrations (billing, RLS), document rollback SQL in a `supabase/rollbacks/` directory. Not blocking.

### M-04: Legacy Backend Migrations Still Exist (LOW, 0.5h)

**Finding:** `backend/migrations/` contains 7 migration files that were bridged into Supabase migrations via DEBT-002 (20260308200000). The backend migrations are now redundant.

**Impact:** Confusion for new developers about which migrations are authoritative.

**Fix:** Add a `DEPRECATED.md` file in `backend/migrations/` pointing to `supabase/migrations/`. Or delete the files.

---

## 6. Naming Conventions

### N-01: Inconsistent Constraint Names (LOW, 2h)

**Finding:** Constraints use multiple naming patterns:
- `profiles_plan_type_check` (table_column_type)
- `chk_profiles_subscription_status` (chk_table_column)
- `unique_user_month` (descriptive)
- `user_subscriptions_plan_id_fkey` (table_column_fkey)
- `fk_monthly_quota_user_id` (fk_table_column)

DEBT-017 documented a naming convention (`chk_`, `fk_`, `uq_`, `idx_`), but legacy constraints retain original names.

**Impact:** Makes it harder to find constraints by name pattern.

**Fix:** Not worth renaming existing constraints. Enforce convention for new constraints going forward.

### N-02: Inconsistent Trigger Names (LOW, 0.5h)

**Finding:** Trigger naming varies:
- `profiles_updated_at` (table_purpose)
- `tr_pipeline_items_updated_at` (tr_table_purpose)
- `trg_update_conversation_last_message` (trg_purpose)
- `trigger_alerts_updated_at` (trigger_purpose)

**Impact:** Cosmetic. All triggers function correctly.

**Fix:** Not worth renaming. Enforce `trg_table_purpose` convention for new triggers.

---

## 7. Data Integrity

### D-01: `profiles.plan_type` Is a Denormalized Cache (HIGH, 4h)

**Finding:** `profiles.plan_type` is a cached copy of the user's current plan. It is kept in sync by:
1. Stripe webhook handlers in `billing.py` that update it on subscription changes
2. The `handle_new_user()` trigger that sets it to `'free_trial'`
3. The now-removed `sync_profile_plan_type()` trigger (migration 030 dropped it because it referenced a non-existent `status` column)

If webhook processing fails or is delayed, `plan_type` can drift from the actual subscription state in `user_subscriptions`.

**Impact:** The "fail to last known plan" design pattern means the system intentionally uses stale `plan_type` as a fallback. This is documented and accepted. However, there is no automated reconciliation to detect drift.

**Fix:** The existing `reconciliation_log` table and Stripe reconciliation job should include `profiles.plan_type` vs `user_subscriptions.plan_id` drift detection. Estimated: 4h to add this check.

### D-02: `search_state_transitions.search_id` Has No FK Constraint (MEDIUM, 1h)

**Finding:** `search_id` in `search_state_transitions` correlates with `search_sessions.search_id`, but there is no FK constraint. This is documented in DEBT-017 as intentional: `search_sessions.search_id` is nullable and not unique (retries share IDs).

**Impact:** Orphan rows are possible but cleaned up by the 30-day retention job.

**Fix:** Accept as-is. The app-layer integrity + retention cleanup is the correct pattern for an audit trail table.

### D-03: `organizations.plan_type` CHECK Is Overly Permissive (MEDIUM, 0.5h)

**Finding:** The CHECK constraint on `organizations.plan_type` (added in DEBT-100) allows 13 values including legacy types (`'free'`, `'avulso'`, `'pack'`, `'monthly'`, `'annual'`) that are no longer valid for profiles.

**Impact:** Organizations could be assigned legacy plan types that have no billing integration.

**Fix:** Tighten the CHECK to only allow active plan types: `'free_trial'`, `'smartlic_pro'`, `'consultoria'`, `'master'`.

### D-04: `partner_referrals.referred_user_id` Is Nullable After FK Change (HIGH, 1h)

**Finding:** Migration 20260304100000 changed the FK to `ON DELETE SET NULL`, and DEBT-001 dropped the NOT NULL constraint to match. This means when a referred user deletes their account, the referral record keeps `referred_user_id = NULL` instead of being deleted.

**Impact:** Revenue share calculations that filter by `referred_user_id IS NOT NULL` still work. But orphaned referral records accumulate. There is no retention cleanup for `partner_referrals`.

**Fix:** Add a pg_cron job to clean up `partner_referrals WHERE referred_user_id IS NULL AND churned_at IS NOT NULL AND churned_at < NOW() - INTERVAL '12 months'`.

### D-05: No Retention on `user_subscriptions` (HIGH, 1h)

**Finding:** The `user_subscriptions` table has no pg_cron retention job. Old, inactive subscriptions accumulate indefinitely.

**Impact:** Table will grow without bound. Each subscription change creates a new row (since `is_active=false` on old ones).

**Fix:** Add retention: `DELETE WHERE is_active = false AND created_at < NOW() - INTERVAL '24 months'`.

### D-06: `pipeline_items.search_id` Is TEXT, Not UUID (LOW, 0.5h)

**Finding:** The `search_id` column on `pipeline_items` (added in DEBT-120) is `TEXT`, while `search_sessions.search_id` is `UUID`. They represent the same value.

**Impact:** No FK can be created with mismatched types. Type comparison works (UUID auto-casts to text), but it is inconsistent.

**Fix:** Change to UUID in a future migration (requires backfill if data exists).

---

## 8. Findings Summary Table

| ID | Severity | Category | Finding | Est. Hours |
|----|----------|----------|---------|------------|
| SEC-01 | CRITICAL | Security | Hardcoded Stripe price IDs in migrations | 2h |
| S-01 | HIGH | Schema | handle_new_user() omits trial_expires_at | 2h |
| P-01 | HIGH | Performance | get_conversations_with_unread_count COUNT(*) OVER() | 4h |
| D-01 | HIGH | Integrity | profiles.plan_type denormalized without reconciliation check | 4h |
| D-04 | HIGH | Integrity | partner_referrals orphans accumulate (no retention) | 1h |
| D-05 | HIGH | Integrity | user_subscriptions no retention on inactive rows | 1h |
| R-02 | MEDIUM | RLS | Verify reconciliation_log policy in production | 0.5h |
| S-04 | MEDIUM | Schema | search_state_transitions.user_id should be NOT NULL | 1h |
| S-05 | MEDIUM | Schema | classification_feedback FK ordering on fresh install | 1h |
| SEC-02 | MEDIUM | Security | System cache warmer in auth.users | 1h |
| SEC-03 | MEDIUM | Security | OAuth tokens in public schema (app-layer encryption) | 2h |
| M-01 | MEDIUM | Migration | Three naming conventions | 4h |
| M-03 | MEDIUM | Migration | No down/rollback migrations | 2h |
| P-02 | MEDIUM | Performance | cleanup_search_cache fires COUNT on every INSERT | 1h |
| P-03 | MEDIUM | Performance | alert_sent_items retention scan pattern | 0.5h |
| D-02 | MEDIUM | Integrity | search_state_transitions.search_id no FK (by design) | 1h |
| D-03 | MEDIUM | Integrity | organizations.plan_type CHECK overly permissive | 0.5h |
| S-02 | LOW | Schema | Deprecated stripe_price_id column | 1h |
| S-03 | LOW | Schema | Inconsistent created_at nullability | 1h |
| P-04 | LOW | Performance | Overlapping user_id indexes on search_sessions | 1h |
| R-01 | LOW | RLS | trial_email_log missing explicit service_role policy | 0.5h |
| R-03 | LOW | RLS | Organization admins cannot UPDATE org | 0.5h |
| M-02 | LOW | Migration | Superseded 027b still in directory | 0.5h |
| M-04 | LOW | Migration | Legacy backend/migrations/ still present | 0.5h |
| N-01 | LOW | Naming | Inconsistent constraint naming | 2h |
| N-02 | LOW | Naming | Inconsistent trigger naming | 0.5h |
| D-06 | LOW | Integrity | pipeline_items.search_id TEXT vs UUID | 0.5h |

---

## 9. Recommended Priority Actions

### Immediate (before next release)
1. **SEC-01:** Move Stripe price IDs out of migrations into env vars or config table
2. **S-01:** Update `handle_new_user()` to set `trial_expires_at`

### Short-term (next sprint)
3. **D-05:** Add retention job for inactive `user_subscriptions`
4. **D-04:** Add retention job for orphaned `partner_referrals`
5. **D-01:** Add plan_type drift detection to reconciliation job
6. **P-01:** Optimize `get_conversations_with_unread_count()` total count

### Medium-term (next quarter)
7. **M-01:** Migration squash to single baseline
8. **M-03:** Create rollback SQL for critical migrations
9. **S-04:** Add NOT NULL to `search_state_transitions.user_id`
10. **D-03:** Tighten `organizations.plan_type` CHECK

---

*Generated 2026-03-20 by @data-engineer during Brownfield Discovery Phase 2.*
