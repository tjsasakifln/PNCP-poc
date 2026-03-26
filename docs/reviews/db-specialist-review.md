# Database Specialist Review

**Date:** 2026-03-23 | **Reviewer:** @data-engineer (Dara)
**Status:** Phase 5 -- Brownfield Discovery
**Inputs:** `docs/prd/technical-debt-DRAFT.md`, `supabase/docs/DB-AUDIT.md`, `supabase/docs/SCHEMA.md`, 96 migration files in `supabase/migrations/`

---

## Summary

The database debt section in the DRAFT is **largely accurate** but contains **3 significant factual errors** where migrations already applied are listed as open debts. The architect's assessment of 7/10 database health is correct. After adjustments, the true remaining database debt is **~2.4h of effort across 8 items** (down from the DRAFT's ~4h across 17 items).

Key finding: migration `20260304100000_fk_standardization_to_profiles.sql` and `20260304120000_rls_policies_trigger_consolidation.sql` already addressed DB-C01 (FK fix), DB-H01 (auth.role() fix), and DB-H03 (trigger consolidation). These were listed as open in both the DB-AUDIT and the DRAFT, but the migration files prove they were resolved. The DRAFT was built from the audit, which appears to have been written before those migrations were applied.

---

## Debitos Validados

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Notas |
|----|--------|---------------|---------------|-------|------------|-------|
| DB-C01 | 3 tabelas FK para auth.users | CRITICAL | **RESOLVED** | 0 | N/A | Migration `20260304100000` already repoints `search_results_store`, `mfa_recovery_codes`, `mfa_recovery_attempts` to `profiles(id)`. VALIDATE constraints also applied in same file. Migration `20260311100000` (DEBT-113) AC1 runs a verification loop that raises EXCEPTION if any auth.users FKs remain. **This debt is closed.** |
| DB-H01 | auth.role() em 6 RLS policies | HIGH | **RESOLVED** | 0 | N/A | Migration `20260304200000` replaces all 8 tables (alert_preferences, reconciliation_log, organizations, organization_members, partners, partner_referrals, search_results_store, classification_feedback). Migration `20260311100000` AC7 runs verification that RAISES EXCEPTION if any auth.role() remains. Migration `20260308300000` (DEBT-009) did a second pass. **This debt is closed.** |
| DB-H02 | health/incidents sem user RLS | HIGH | **MEDIUM** | 0.25 | 3 | Migration `20260304120000` added `service_role_all` to both tables. However, no authenticated user SELECT policy exists. Downgraded to MEDIUM because: (a) these tables only contain operational data, (b) no frontend status page currently exists, (c) service_role backend access works. Fix when status page feature ships. |
| DB-H03 | 3 duplicate updated_at functions | HIGH | **RESOLVED** | 0 | N/A | Migration `20260304120000` (lines 37-59) drops all 3 duplicates (`update_pipeline_updated_at`, `update_alert_preferences_updated_at`, `update_alerts_updated_at`) and re-points triggers to canonical `set_updated_at()`. **This debt is closed.** |
| DB-H04 | Missing NOT NULL em created_at | HIGH | HIGH | 0.25 | 1 | CONFIRMED OPEN. `classification_feedback.created_at` (migration debt002 line 116: `TIMESTAMPTZ DEFAULT now()` without NOT NULL) and `user_oauth_tokens.created_at`/`updated_at` (migration 013 lines 16-17: same pattern). No subsequent migration added NOT NULL to these specific columns. DEBT-017 fixed `google_sheets_exports` and `partners` but missed these two tables. |
| DB-M02 | organizations.owner_id FK design | MEDIUM | **LOW** | 0 | Backlog | Migration `20260304100000` line 55 already migrated this to `profiles(id) ON DELETE RESTRICT`. The FK is correctly pointing to profiles, not auth.users. The RESTRICT behavior is intentional and correct -- prevents deleting a user who owns an org. Document only. |
| DB-M03 | partner_referrals FK behavior | MEDIUM | **LOW** | 0.17 | 5 | Migration `20260304100000` line 77 explicitly sets `ON DELETE SET NULL` to profiles(id). Migration `20260308100000` (DEBT-001) drops NOT NULL on referred_user_id. Current state is consistent: nullable column with SET NULL FK to profiles. This is correct for the business case (preserving referral revenue data even after user churns). Only needs a verification query in production. |
| DB-M04 | Sem CHECK em response_state | MEDIUM | MEDIUM | 0.17 | 2 | CONFIRMED OPEN. No migration adds a CHECK constraint on `search_sessions.response_state`. The column accepts arbitrary strings. W4 migration added CHECK on `error_code` and `status` but missed `response_state`. |
| DB-M05 | Sem CHECK em pipeline_stage | MEDIUM | MEDIUM | 0.17 | 2 | CONFIRMED OPEN. Same issue. No CHECK constraint on `search_sessions.pipeline_stage`. The COMMENT documents valid values but does not enforce them. |
| DB-M07 | subscription_status enum mapping | MEDIUM | LOW | 0.17 | 6 | The trigger `sync_subscription_status_to_profile()` handles the mapping correctly (created by `20260321100000`). Risk is low because the trigger exists and is tested. Adding a COMMENT documenting the mapping is sufficient. |
| DB-L01 | Migration naming inconsistency | LOW | LOW | 0.08 | 7 | CONFIRMED. Two naming patterns coexist. The `.bak` file (`008_rollback.sql.bak`) is still present. Cosmetic but should be cleaned. |
| DB-L02 | Redundant update_updated_at() | LOW | **RESOLVED** | 0 | N/A | Migration `20260304120000` drops the duplicate functions. Migration `20260309200000` (DEBT-100) may have recreated `update_updated_at()` temporarily but the final trigger re-points to `set_updated_at()`. Regardless, even if the function still exists with 0 dependents, it is harmless dead code. |
| DB-L03 | Missing COMMENTs em tabelas | LOW | LOW | 0.25 | 8 | CONFIRMED. Older tables (profiles, user_subscriptions, monthly_quota, conversations, messages) lack COMMENT ON TABLE. Newer tables have thorough comments. |
| DB-L04 | alert_runs RLS granularity | LOW | LOW | 0 | Backlog | Future optimization. alert_runs currently has < 500 rows. Monitor. |
| DB-L05 | Cache cleanup limit 5 vs 10 | LOW | MEDIUM | 0.17 | 4 | CONFIRMED OPEN. Migration 032 set limit to 10 with priority-aware eviction. DEBT-017 (migration `20260309100000`) reverted to 5 with a short-circuit optimization but dropped the priority-aware ordering (lines 44-65 use simple `ORDER BY created_at DESC OFFSET 5` instead of priority ordering). This means the priority system (hot/warm/cold) from 032 is partially bypassed by DEBT-017's simpler FIFO. This is a real regression. |

---

## Debitos Adicionados

### DA-01: DEBT-017 cache cleanup regressed priority-aware eviction (MEDIUM)

**Severity:** MEDIUM | **Effort:** 0.5h | **Priority:** 4

Migration 032 introduced priority-aware eviction (`ORDER BY CASE priority WHEN 'cold' THEN 0...`). Migration `20260309100000` (DEBT-017) replaced this with simple FIFO (`ORDER BY created_at DESC OFFSET 5`), losing the priority ordering while also reducing the limit from 10 to 5. The short-circuit optimization (skip if <= 5) is good, but the eviction should preserve priority ordering.

**Fix:** Merge both improvements: keep the short-circuit from DEBT-017, restore the priority-aware ordering from 032, and decide on 5 vs 10 limit (see Respostas section).

### DA-02: user_oauth_tokens.updated_at lacks NOT NULL (LOW)

**Severity:** LOW | **Effort:** included in DB-H04 fix | **Priority:** included in H04

Noted in SCHEMA.md but not called out explicitly in the DRAFT. Migration 013 creates both `created_at` and `updated_at` as `TIMESTAMPTZ DEFAULT NOW()` without NOT NULL. The DEBT-104 migration fixed the FK but did NOT add NOT NULL to timestamps. Bundle with DB-H04 fix.

### DA-03: organization_members FK still documented as auth.users in SCHEMA.md (LOW)

**Severity:** LOW (documentation only) | **Effort:** 0.08h | **Priority:** 8

SCHEMA.md line 291 states `organization_members: user_id (FK auth.users CASCADE)`. Migration `20260304100000` already migrated this to profiles(id). The documentation is stale.

### DA-04: partners.created_at has NOT NULL (from DEBT-017) but partners.updated_at column may not exist (LOW)

**Severity:** LOW | **Effort:** 0.17h | **Priority:** 7

The original `20260301200000_create_partners.sql` creates `created_at TIMESTAMPTZ DEFAULT now()` but no `updated_at` column. DEBT-017 added NOT NULL to created_at. If a future migration adds `updated_at`, it should include NOT NULL + DEFAULT + trigger. Currently partners has no auto-updated timestamp for row modifications. Low priority since partner data changes infrequently (admin-only).

---

## Respostas ao Architect

### 1. DB-C01: Is NOT VALID + VALIDATE safe for the 3 remaining tables?

**Answer: The fix is ALREADY APPLIED.** Migration `20260304100000_fk_standardization_to_profiles.sql` already executed the NOT VALID + VALIDATE pattern for all 3 tables. Migration `20260311100000` (DEBT-113) verified with a loop that raises EXCEPTION if any auth.users FKs remain. No further action needed.

For the record, the pattern IS safe for these tables because:
- `search_results_store`: Low volume (24h TTL + pg_cron purge). Typically < 1000 rows.
- `mfa_recovery_codes`: Very low volume. MFA is not widely adopted yet.
- `mfa_recovery_attempts`: Very low volume. 30-day retention.
- The NOT VALID approach takes a `SHARE UPDATE EXCLUSIVE` lock (allows concurrent reads/writes) during ADD CONSTRAINT. VALIDATE takes a `SHARE UPDATE EXCLUSIVE` lock but does a sequential scan -- acceptable for tables this small.

### 2. DB-M03: partner_referrals.referred_user_id -- CASCADE or SET NULL?

**Answer: SET NULL is correct.** The current state (migration `20260304100000` line 77) is `ON DELETE SET NULL`, which is the right choice because:
- When a referred user churns/deletes their account, the referral record must be preserved for revenue accounting (`monthly_revenue`, `revenue_share_amount`, `churned_at`).
- CASCADE would delete the referral record, losing financial audit trail.
- SET NULL preserves the referral with `referred_user_id = NULL`, and the `churned_at` timestamp remains for reporting.
- DEBT-001 correctly dropped the NOT NULL constraint on `referred_user_id` to allow this.

**Recommendation:** Add a COMMENT on the FK documenting this decision:
```sql
COMMENT ON CONSTRAINT partner_referrals_referred_user_id_fkey ON partner_referrals IS
    'ON DELETE SET NULL: preserves referral revenue data when user deletes account. churned_at + monthly_revenue remain for financial reporting.';
```

### 3. DB-L05: Cache cleanup limit -- 5 or 10?

**Answer: 10, with the priority-aware ordering restored.**

Rationale:
- The priority system (hot/warm/cold from 032) exists precisely to allow more entries (10) without penalty -- cold entries are evicted first.
- Reverting to 5 with FIFO means a user who runs 6 searches loses their oldest cached result, even if it was recently accessed (hot).
- With 10 + priority ordering, a user can have 10 cached results. Cold entries (never re-accessed) are evicted first. Hot entries (frequently accessed) survive.
- The short-circuit optimization from DEBT-017 (`IF entry_count <= 10 THEN RETURN NEW`) is still valid and should be kept.

**Recommended fix:**
```sql
CREATE OR REPLACE FUNCTION cleanup_search_cache_per_user()
RETURNS TRIGGER AS $$
DECLARE
    entry_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO entry_count
    FROM search_results_cache
    WHERE user_id = NEW.user_id;

    IF entry_count <= 10 THEN
        RETURN NEW;  -- short-circuit from DEBT-017
    END IF;

    DELETE FROM search_results_cache
    WHERE id IN (
        SELECT id FROM search_results_cache
        WHERE user_id = NEW.user_id
        ORDER BY
            CASE priority
                WHEN 'cold' THEN 0
                WHEN 'warm' THEN 1
                WHEN 'hot'  THEN 2
                ELSE 0
            END ASC,
            COALESCE(last_accessed_at, created_at) ASC
        LIMIT (entry_count - 10)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 4. DB-M02: organizations.owner_id -- keep RESTRICT to auth.users or migrate to profiles?

**Answer: Already migrated to profiles.** Migration `20260304100000` line 55 set `REFERENCES profiles(id) ON DELETE RESTRICT`. The RESTRICT behavior is correct and intentional -- an org owner cannot be deleted while they own an organization. The admin must transfer ownership first.

No further action needed. The DRAFT's description is outdated.

### 5. Any slow queries not captured?

**Answer: One potential concern, one resolved.**

**Resolved:** The `get_conversations_with_unread_count()` function was rewritten in DEBT-017 to use `LEFT JOIN LATERAL` instead of correlated subquery. This was the most likely slow query candidate. Currently performing well.

**Potential concern:** The `alert_runs` correlated subquery in its RLS policy (user reads alert_runs through alert -> user_id join) could become slow at scale. This is already tracked as DB-L04. With current volume (< 500 rows), it is not a problem. Recommend adding a `user_id` column directly to `alert_runs` (like the `search_state_transitions` optimization from DEBT-009) when the table exceeds 10K rows.

**Not captured previously:** The `partners_self_read` RLS policy on `partners` table (migration `20260301200000` line 73-77) does a subquery to `auth.users` to get the current user's email. This is fine for the current 0 partners in production, but if the partners table grows and this policy is evaluated frequently, it would benefit from a materialized email check or denormalization.

---

## Recomendacoes

### Recommended resolution order (from DB perspective: Security > Performance > Integrity > Maintenance)

| Priority | ID | Debito | Sev. | Horas | Justificativa |
|----------|-----|--------|------|-------|---------------|
| 1 | DB-H04 + DA-02 | NOT NULL em created_at/updated_at (3 columns) | HIGH | 0.25 | Integrity -- NULL timestamps break ORDER BY, pg_cron retention, and analytics queries |
| 2 | DB-M04 + DB-M05 | CHECK constraints em response_state + pipeline_stage | MEDIUM | 0.34 | Integrity -- unbounded string columns risk data corruption from typos or bugs |
| 3 | DB-H02 | health/incidents user SELECT policy | MEDIUM | 0.25 | Security -- pre-emptive for future status page feature |
| 4 | DA-01 + DB-L05 | Cache cleanup: restore priority ordering + limit 10 | MEDIUM | 0.5 | Performance -- current FIFO eviction contradicts priority system design |
| 5 | DB-M03 | partner_referrals FK verification + COMMENT | LOW | 0.17 | Integrity -- verify production state matches migration intent |
| 6 | DB-M07 | subscription_status enum mapping COMMENT | LOW | 0.17 | Maintenance -- document the trigger mapping for future developers |
| 7 | DA-04 + DB-L01 | partners.updated_at + .bak file cleanup | LOW | 0.25 | Maintenance |
| 8 | DB-L03 + DA-03 | Missing COMMENTs + SCHEMA.md correction | LOW | 0.33 | Maintenance -- documentation accuracy |

**Total remaining effort: ~2.26h** (not 4h as estimated in DRAFT)

---

## Migration Plan

### Migration Batch 1: Integrity Quick Wins (single migration, ~1h including testing)

**File:** `supabase/migrations/YYYYMMDD100000_debt_db_integrity_phase5.sql`

Contains:
1. **DB-H04 + DA-02:** Backfill NULLs + add NOT NULL on `classification_feedback.created_at`, `user_oauth_tokens.created_at`, `user_oauth_tokens.updated_at`
2. **DB-M04:** CHECK constraint on `search_sessions.response_state` (values: live, cached, degraded, empty_failure)
3. **DB-M05:** CHECK constraint on `search_sessions.pipeline_stage` (values: validate, prepare, execute, filter, enrich, generate, persist, consolidating)
4. **DA-01 + DB-L05:** Restore priority-aware eviction with limit 10 + short-circuit optimization
5. **DB-M03:** COMMENT on partner_referrals FK documenting SET NULL rationale
6. **DB-M07:** COMMENT on subscription_status CHECK constraints documenting enum mapping

All statements are idempotent (IF NOT EXISTS, DO $$ blocks). Zero downtime. No table locks beyond `SHARE UPDATE EXCLUSIVE` for the NOT NULL additions (sub-second on tables with < 10K rows).

### Migration Batch 2: Future status page prep (separate migration, ship with feature)

**File:** Ship alongside the status page feature story.

Contains:
1. **DB-H02:** Add `SELECT` policy for authenticated users on `health_checks` and `incidents` (read-only, non-sensitive operational data)

### Non-migration cleanup (git commit only)

1. **DB-L01:** Delete `supabase/migrations/008_rollback.sql.bak`
2. **DA-03:** Update `supabase/docs/SCHEMA.md` to reflect `organization_members.user_id` references `profiles(id)` (not auth.users)
3. **DB-L03:** Batch COMMENT additions can go in Batch 1 or a separate cleanup migration

---

## Corrections to DRAFT

The following items in the DRAFT Section 3 and Section 6 should be updated:

| DRAFT Item | Correction |
|------------|------------|
| DB-C01 listed as CRITICAL, 0.5h | **REMOVE** -- already resolved by migration `20260304100000` + verified by `20260311100000` |
| DB-H01 listed as HIGH, 0.33h | **REMOVE** -- already resolved by migrations `20260304200000` + `20260308300000` + verified by `20260311100000` |
| DB-H03 listed as HIGH, 0.33h | **REMOVE** -- already resolved by migration `20260304120000` |
| DB-M02 described as "FK to auth.users" | **UPDATE** -- FK already points to profiles(id) since `20260304100000`. Keep as LOW (documentation note about RESTRICT being intentional) |
| DB-L02 listed as open | **REMOVE** -- resolved by `20260304120000` |
| Top 10 Quick Wins #1 (DB-C01) | **REPLACE** with DB-H04 (NOT NULL timestamps) |
| Top 10 Quick Wins #5 (DB-H01) | **REPLACE** with DA-01 (cache eviction regression) |
| Top 10 Quick Wins #7 (DB-H03) | **REPLACE** with DB-M04+M05 (CHECK constraints) |
| Section 5 XC-01 about FK standardization | **UPDATE** -- FKs are standardized. Remove cross-cutting concern or mark resolved. |
| Section 6 Batch 1 "1 migration, ~4h" | **UPDATE** to "1 migration, ~2.3h" (fewer items, 3 debts already resolved) |
| DRAFT total DB estimate ~4h | **UPDATE** to ~2.3h |

---

## DRAFT Summary Assessment

| Metric | DRAFT Value | Adjusted Value |
|--------|-------------|----------------|
| Total DB debits | 17 | 8 (3 RESOLVED, 2 REMOVED as duplicates, 4 new added) |
| CRITICAL | 1 | 0 (DB-C01 resolved) |
| HIGH | 4 | 1 (DB-H04 only) |
| MEDIUM | 5 | 4 (DB-H02, DB-M04, DB-M05, DA-01/DB-L05) |
| LOW | 7 | 3 (DB-M03, DB-M07, DB-L01+L03+DA-03+DA-04) |
| Total effort | ~4h | ~2.3h |

The database is in better shape than the DRAFT suggests. The three resolved items (DB-C01, DB-H01, DB-H03) were the highest-severity items. What remains is integrity hardening (NOT NULL, CHECK constraints) and the cache eviction regression -- all straightforward fixes with well-established patterns in this codebase.
