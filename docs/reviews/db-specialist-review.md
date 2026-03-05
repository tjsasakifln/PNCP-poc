# Database Specialist Review — v2.0

**Reviewer:** @data-engineer (Dynamo)
**Date:** 2026-03-04
**Documents Reviewed:** technical-debt-DRAFT.md v2.0, DB-AUDIT.md, SCHEMA.md
**Validation Method:** Cross-referenced against all 66 migration SQL files, SCHEMA.md table definitions, and `auth.role()` grep across entire migration codebase
**Previous Review:** v1.0 (2026-02-25) -- this supersedes it entirely. All v1 Tier-1 blocking items (T1-01 through T1-04, MISSED-01/02) have been resolved in migrations 20260225100000 through 20260225150000.

---

## Review Summary

The DRAFT v2.0 accurately reflects the 23 database debts identified in DB-AUDIT.md. The consolidation is faithful to the original audit with correct severity assignments. However, my review uncovered **3 additional debts** missed during consolidation, and I recommend **2 severity adjustments**. The hour estimates in the DRAFT are broadly reasonable but some are underestimated given migration testing requirements in a production Supabase environment.

**Key findings:**
- The `auth.role() = 'service_role'` pattern is more widespread than documented (7 tables, not 4+1 as listed in H-04/05/06 + M-09)
- `search_results_store` has the highest density of debt (4 overlapping issues in a single recent table created 2026-03-03)
- The C-01 FK migration is safe to batch into a single migration file using the NOT VALID + VALIDATE pattern
- `handle_new_user()` should remain as a trigger (not application layer) with an integration test guard
- All v1 blocking items are resolved -- the current debt profile is structural/hardening, not blocking

---

## Debitos Validados

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade DB | Notas |
|----|--------|---------------|---------------|-------|---------------|-------|
| C-01 | FK auth.users -> profiles (6 tabelas) | CRITICAL | CRITICAL | 6h | P1 | Confirmed via migration files. 6 tables verified: search_results_store (20260303100000), mfa_recovery_codes (20260228160000), mfa_recovery_attempts (20260228160000), organizations.owner_id (20260301100000), organization_members.user_id (20260301100000), partner_referrals.referred_user_id (20260301200000). All reference auth.users(id) directly. |
| C-02 | health_checks + incidents: RLS enabled, zero policies | CRITICAL | **HIGH** | 2h | P2 | Migration 20260303200000 intentionally enabled RLS without policies. Migration comment: "Backend uses service_role which bypasses RLS -- no policies needed." Both tables are backend-only append logs with no user-identifiable data. Downgraded because: (1) service_role bypass is the intended and only access pattern, (2) no client-side status page is planned, (3) no PII exposure risk. |
| H-01 | 3 duplicate updated_at trigger functions | HIGH | HIGH | 2h | P4 | Confirmed. `update_pipeline_updated_at()` (migration 025 line 57), `update_alert_preferences_updated_at()` (20260226100000 line 49), `update_alerts_updated_at()` (20260227100000 line 53) are identical copies. organizations table already correctly uses shared `update_updated_at()` (20260301100000 line 78). |
| H-02 | search_results_store FK not standardized | HIGH | HIGH | 1h | P1 | Subsumed by C-01. Migration 20260303100000 line 6: `REFERENCES auth.users(id)` with no ON DELETE clause (defaults to NO ACTION). |
| H-03 | No retention for search_results_store | HIGH | HIGH | 2h | P3 | Confirmed. `expires_at` column with default 24h exists but no pg_cron job. Existing pg_cron jobs (migration 022) only cover monthly_quota and stripe_webhook_events. |
| H-04 | alert_preferences service_role policy uses auth.role() | HIGH | **MEDIUM** | 0.5h | P5 | Functionally equivalent. The `auth.role()` approach evaluates JWT role claim per-row, while `TO service_role` uses PostgreSQL native GRANT. Both work correctly in Supabase. Downgraded because: (1) all affected tables function correctly today, (2) the risk is theoretical (Supabase JWT structure change), (3) this is consistency debt, not security debt. |
| H-05 | reconciliation_log service_role uses auth.role() | HIGH | MEDIUM | 0.5h | P5 | Same rationale as H-04. Migration 20260228140000 line 32. |
| H-06 | organizations + org_members use auth.role() | HIGH | MEDIUM | 0.5h | P5 | Same rationale as H-04. Migration 20260301100000 lines 123, 193. |
| M-01 | No updated_at on 11+ tables | MEDIUM | MEDIUM | 1.5h | P7 | Correct list in audit, but should only add to tables receiving UPDATEs: monthly_quota, mfa_recovery_codes (used_at UPDATE), partner_referrals (converted_at/churned_at). Skip append-only tables: search_state_transitions, stripe_webhook_events, trial_email_log, alert_sent_items, alert_runs, health_checks, incidents, mfa_recovery_attempts. Reduces from 11 to 3 tables. |
| M-02 | No standalone index on search_state_transitions(created_at) | MEDIUM | MEDIUM | 0.5h | P6 | Correct. Current indexes are (search_id, created_at ASC) and (to_state, created_at). Neither efficiently serves `DELETE WHERE created_at < X`. |
| M-03 | partner_referrals FK missing ON DELETE | MEDIUM | MEDIUM | 1h | P5 | Confirmed via migration 20260301200000 lines 31-32. Both `partner_id -> partners(id)` and `referred_user_id -> auth.users(id)` have no ON DELETE clause (NO ACTION default). |
| M-04 | No retention for mfa_recovery_attempts | MEDIUM | MEDIUM | 1h | P6 | Confirmed. Append-only brute force tracking. Index `(user_id, attempted_at DESC)` exists for efficient cleanup. |
| M-05 | No retention for alert_runs | MEDIUM | MEDIUM | 1h | P6 | Confirmed. Index `(run_at DESC)` exists for efficient cleanup. |
| M-06 | No retention for alert_sent_items | MEDIUM | MEDIUM | 1h | P6 | Confirmed. Index `(sent_at)` exists. CASCADE from alerts handles orphans on alert deletion, but active alerts accumulate sent_items indefinitely. |
| M-07 | handle_new_user() modified 7x -- regression risk | MEDIUM | MEDIUM | 3h | P7 | Confirmed 7 modifications: 001, 007, 016, 024, 027, 20260224000000, 20260225110000. Latest version (20260225110000) is correct and includes all 10 columns + ON CONFLICT. |
| M-08 | Inconsistent CHECK constraint naming | MEDIUM | LOW | 1h | Backlog | Low practical impact. 4 naming patterns observed: `{table}_{column}_check`, `chk_{table}_{column}`, `{descriptive}_format`, `check_{descriptive}`. Only matters for future migrations. |
| M-09 | classification_feedback admin policy uses auth.role() | MEDIUM | MEDIUM | 0.5h | P5 | Confirmed in backend/migrations/006_classification_feedback.sql line 48. |
| L-01 | Redundant index alert_preferences.user_id | LOW | LOW | 0.5h | Backlog | UNIQUE constraint `alert_preferences_user_id_unique` creates implicit B-tree. Explicit `idx_alert_preferences_user_id` is redundant. Safe to drop. |
| L-02 | Redundant index alert_sent_items.alert_id | LOW | LOW | 0.5h | Backlog | `idx_alert_sent_items_alert_id` (alert_id) is prefix of UNIQUE `idx_alert_sent_items_dedup` (alert_id, item_id). PostgreSQL uses leftmost columns. Safe to drop. |
| L-03 | No COMMENT on newer tables | LOW | LOW | 1h | Backlog | Partially incorrect in audit. organizations and organization_members DO have table and column-level COMMENTs (migration 20260301100000 lines 33-56). health_checks and incidents have table-level COMMENTs but missing column-level ones. |
| L-04 | plan_type CHECK rebuilt 6x | LOW | LOW | 2h | Backlog | See detailed answer below. |
| L-05 | Stripe Price IDs hardcoded in migrations | LOW | LOW | 2h | Backlog | Confirmed in migrations 029, 20260226120000, 20260301300000. Blocks staging/dev environment setup but no production risk. |
| L-06 | No composite index (user_id, expires_at) on search_results_store | LOW | LOW | 0.5h | Backlog | Separate indexes exist but composite benefits retention DELETE queries. |

---

## Debitos Adicionados

### DA-01: partners and partner_referrals service_role policies use auth.role() (MEDIUM)

**Missed in DRAFT consolidation.** Migration 20260301200000 lines 102-105 show both `partners_service_role` and `partner_referrals_service_role` policies use `USING (auth.role() = 'service_role')`. These were not included in the H-04/05/06 scope.

**Complete auth.role() table list (7 tables, not 4+1 as documented):**
1. alert_preferences (H-04)
2. reconciliation_log (H-05)
3. organizations (H-06)
4. organization_members (H-06)
5. classification_feedback (M-09)
6. **partners** (MISSED)
7. **partner_referrals** (MISSED)

Note: search_results_store also uses `auth.role()` but is covered separately in DA-02.

**Effort:** 0.5h (batch with H-04/05/06 migration)
**Severity:** MEDIUM
**Priority:** P5

### DA-02: search_results_store service_role policy uses auth.role() (MEDIUM)

Migration 20260303100000 line 26: `FOR ALL USING (auth.role() = 'service_role')`. This table was only flagged for C-01 (FK) and H-02 (missing CASCADE) in the DRAFT, not for the policy pattern inconsistency.

**Total auth.role() occurrences: 8 tables** (including search_results_store).

**Effort:** Included in H-04/05/06 batch
**Severity:** MEDIUM

### DA-03: health_checks and incidents missing retention pg_cron job (MEDIUM)

Migration 20260228150000 table comment says "30-day retention" but no pg_cron job was ever created. At health check frequency of every 5 minutes, this generates ~8,640 rows/month. The incidents table grows more slowly but has no cleanup either.

**Effort:** 1h (batch with M-04/05/06)
**Severity:** MEDIUM
**Priority:** P6

---

## Respostas ao Architect

### C-01: Can 6 FK migrations be done in one? Impact on existing data?

**Yes, a single migration file is feasible and recommended.** Use the NOT VALID + VALIDATE pattern established in migration 20260225120000.

**Migration structure:**

```sql
-- Step 1: Drop old FK constraints (instant, metadata-only)
ALTER TABLE search_results_store DROP CONSTRAINT IF EXISTS search_results_store_user_id_fkey;
ALTER TABLE mfa_recovery_codes DROP CONSTRAINT IF EXISTS mfa_recovery_codes_user_id_fkey;
ALTER TABLE mfa_recovery_attempts DROP CONSTRAINT IF EXISTS mfa_recovery_attempts_user_id_fkey;
-- organizations.owner_id, organization_members.user_id, partner_referrals.referred_user_id

-- Step 2: Add new FKs with NOT VALID (instant, no table scan)
ALTER TABLE search_results_store
  ADD CONSTRAINT search_results_store_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
-- ... etc for all 6

-- Step 3: VALIDATE separately (concurrent reads OK, brief write lock)
ALTER TABLE search_results_store VALIDATE CONSTRAINT search_results_store_user_id_fkey;
-- ... etc
```

**Impact on existing data:**
- **Pre-condition:** Every `user_id` in these 6 tables must exist in `profiles`. Since `handle_new_user()` creates a profiles row on every signup, this should hold true. Run validation query before migration:
  ```sql
  SELECT 'search_results_store' AS tbl, count(*) FROM search_results_store
    WHERE user_id NOT IN (SELECT id FROM profiles)
  UNION ALL
  SELECT 'mfa_recovery_codes', count(*) FROM mfa_recovery_codes
    WHERE user_id NOT IN (SELECT id FROM profiles)
  -- ... repeat for all 6
  ```
- **Special cases:**
  - `organizations.owner_id`: Currently ON DELETE RESTRICT. Keep RESTRICT but repoint to profiles(id). Semantic preserved: cannot delete user who owns an org.
  - `partner_referrals.referred_user_id`: Currently NO ACTION. Recommend ON DELETE SET NULL to profiles(id) to preserve revenue share data when user is deleted.
  - All others: ON DELETE CASCADE to profiles(id).

**Downtime:** Zero. NOT VALID avoids full table scan. VALIDATE takes a brief ShareUpdateExclusive lock per table (allows reads, briefly blocks writes). All 6 tables are small (<1000 rows at current scale).

**Estimated time:** 4-6h (writing + staging test + verification queries + production deploy)

### C-02: Are health_checks/incidents service_role only?

**Yes, confirmed.** Both tables are written and read exclusively by backend health monitoring code using the service_role Supabase client. Verified:
- `health_checks`: Created by STORY-316 AC5 (migration 20260228150000). Used by `health.py` for periodic monitoring results.
- `incidents`: Created by STORY-316 AC9 (migration 20260228150001). Used for automated incident tracking.

No frontend component reads these tables directly. No public status page feature exists or is planned.

**Recommendation:** Add explicit `FOR ALL TO service_role USING (true) WITH CHECK (true)` policies for defense-in-depth. This makes the access pattern self-documenting and immune to Supabase configuration changes. Do NOT add user-facing policies unless a public status page feature is built.

### H-03: Volume of search_results_store? Retention period?

**Current state:**
- Table created 2026-03-03 (1 day old). Production volume is negligible.
- Each row stores a full JSONB search result payload (estimated 100KB-1.5MB based on search_results_cache data from migration 20260225150000 pre-check: avg=617KB, max=1.59MB).
- Default `expires_at` = `now() + 24 hours`.
- **No pg_cron cleanup exists.** Existing cron jobs (migration 022) only handle monthly_quota and stripe_webhook_events. Migration 20260225150000 added cleanup for search_results_cache cold entries but not for search_results_store.

**Volume projections:**

| Scale | Searches/Day | Rows/Day | Storage/Day (avg 500KB) | Monthly Accumulation |
|-------|-------------|----------|------------------------|---------------------|
| Current (50 beta users) | ~50 | ~50 | ~25 MB | ~750 MB |
| Target (500 users) | ~500 | ~500 | ~250 MB | ~7.5 GB |
| Growth (2000 users) | ~2000 | ~2000 | ~1 GB | ~30 GB |

**Recommended retention: 7 days** (not the 24h default).

Rationale:
- This is L3 persistent storage, designed to prevent "Busca nao encontrada ou expirada" after L1/L2 TTL expiry
- Users commonly revisit search results 2-3 days later (Monday search reviewed Wednesday)
- 7 days covers a full business week cycle
- At current scale: 50 rows/day x 7 days x 500KB = ~175 MB -- easily manageable
- At target scale: 500 x 7 x 500KB = ~1.75 GB -- still reasonable for Supabase Pro

**Implementation:**
```sql
-- 1. Change default expires_at to 7 days
ALTER TABLE search_results_store
  ALTER COLUMN expires_at SET DEFAULT now() + INTERVAL '7 days';

-- 2. Add pg_cron cleanup
SELECT cron.schedule(
  'cleanup-search-results-store',
  '0 4 * * *',  -- daily at 4am UTC
  $$DELETE FROM search_results_store WHERE expires_at < NOW()$$
);
```

### M-07: Migrate handle_new_user() to application layer?

**Recommendation: Keep as trigger. Add integration test guard.**

**Arguments to keep as trigger:**

1. **Atomicity** -- Profile creation is guaranteed within the same transaction as `auth.users` INSERT. Application-layer would require intercepting Supabase Auth callbacks (webhook or post-signup API call), creating a window where auth.users exists without a profiles row. During that window, any RLS policy using `auth.uid() = user_id` with a JOIN to profiles would fail.

2. **Multi-entry-point coverage** -- Supabase Auth handles email/password signup, Google OAuth, magic links, and phone OTP. All flow through the same `auth.users` INSERT trigger. Application-layer would need to handle each entry point separately.

3. **Battle-tested pattern** -- The current trigger (migration 20260225110000) is correct, includes all 10 columns, and has `ON CONFLICT (id) DO NOTHING`. The 7 historical modifications were a learning curve, not inherent trigger fragility.

**Mitigation for regression risk (3h total):**

1. **Backend integration test** (2h): Create `test_handle_new_user_trigger.py` that:
   - Inserts a row into auth.users with full raw_user_meta_data
   - Verifies all 10 profile columns are populated
   - Verifies ON CONFLICT behavior (double insert does not error)
   - Verifies phone normalization edge cases

2. **CI guard** (0.5h): Add a GitHub Actions step that greps new migration files for `handle_new_user` and flags for mandatory review.

3. **Canonical comment** (0.5h): Add a block comment in the function listing all expected columns and referencing this review document.

### L-04: CHECK constraint vs reference table for plan_types?

**Recommendation: Keep CHECK constraint now. Evaluate reference table when active plans exceed 10.**

**Current state:** 7 valid values (free_trial, consultor_agil, maquina, sala_guerra, master, smartlic_pro, consultoria). 3 legacy plans are inactive in the `plans` table.

**Analysis:**

| Factor | CHECK Constraint | Reference Table (plan_types) |
|--------|-----------------|------------------------------|
| Migration effort for new plan | 2-line migration (DROP + ADD) | 1-line INSERT |
| Schema clarity | Values hidden in constraint DDL | Self-documenting table |
| Query complexity | No JOIN needed | FK validation via JOIN |
| Application coupling | Constraint must match app code | App reads valid values from DB |
| Frequency of change | 6 times in 3 months (2/month) | Would be 0 DDL changes |

**Long-term path:** The `plans` table already functions as a partial reference table (its `id` column values match `plan_type` CHECK values). The cleanest future solution is:
```sql
ALTER TABLE profiles DROP CONSTRAINT profiles_plan_type_check;
ALTER TABLE profiles ADD CONSTRAINT profiles_plan_type_fk
  FOREIGN KEY (plan_type) REFERENCES plans(id);
```
This unifies validation with the existing catalog. Prerequisite: verify all `plan_type` values in profiles exist in `plans.id` (including legacy plans).

**Trigger for migration:** When the 4th active plan is added, or when plan metadata beyond `plans` table is needed.

### M-04/05/06: Appropriate retention periods?

| Table | Retention | Schedule | Rationale |
|-------|----------|----------|-----------|
| mfa_recovery_attempts | **30 days** | Daily 4:30 AM UTC | Brute force detection only needs recent window. 30 days covers security investigation needs. Worst case: 100 attempts/user/day x 100 users = 300K rows/month -- manageable but pointless to keep. |
| alert_runs | **90 days** | Daily 4:45 AM UTC | Execution debugging history. 90 days covers quarterly review. ~200 bytes/row x 100 alerts x 1 run/day = 9K rows/90d. |
| alert_sent_items | **180 days** | Weekly Sunday 5:00 AM UTC | Dedup tracking serves an active purpose. If deleted too early, same procurement item could be re-sent to user. 180 days is safe because procurement items older than 6 months are typically closed/expired anyway. |

**Implementation:** Single migration with 3 pg_cron jobs at staggered times to avoid concurrent cleanup load.

### Performance: search_results_store.results size constraint needed?

**Yes, absolutely.** This is a concrete gap.

**Evidence:** `search_results_cache.results` has a 2MB CHECK constraint (migration 20260225150000). `search_results_store.results` stores the same JSONB payload structure but with no size limit. Without constraint, a pathological multi-UF search could insert 5-10MB of JSONB per row.

**Recommendation:**
```sql
ALTER TABLE search_results_store
  ADD CONSTRAINT chk_store_results_max_size
  CHECK (octet_length(results::text) <= 2097152);
```

Match the 2MB limit from search_results_cache. The application-level truncation in `search_cache.py` should also be applied before writing to search_results_store.

**Pre-check required:** Run `SELECT max(octet_length(results::text)) FROM search_results_store` before applying. Table is 1 day old so unlikely to have violations.

**Effort:** 0.5h (bundle with H-03 retention migration)

---

## Dependencias Tecnicas

```
C-01 (FK standardization) ────────────────────────────────────────
  |-- H-02 (search_results_store FK)      -- subsumed, fix together
  |-- M-03 (partner_referrals ON DELETE)  -- subsumed, fix together
  |-- DA-02 (search_results_store policy) -- can batch same migration

H-03 (search_results_store retention) ────────────────────────────
  |-- L-06 (composite index)   -- create index BEFORE retention job
  |-- Q7 (2MB CHECK)           -- add in same migration

H-04/05/06 + M-09 + DA-01 + DA-02 (auth.role() standardization) ─
  |-- All 8 tables in a single migration (independent of C-01)

M-04/05/06 + DA-03 (retention pg_cron jobs) ──────────────────────
  |-- M-02 (created_at index) -- add before retention job
  |-- All 4+ jobs in one migration

H-01 (consolidate trigger functions) ─────────────────────────────
  |-- Independent. No data migration. Safe anytime.

M-07 (handle_new_user guard) ─────────────────────────────────────
  |-- Independent. Backend test + CI check, no DB migration needed.
```

**Cross-area dependencies:**
- TD-A01 (legacy route removal): No DB dependency
- TD-SEC02 (service_role key concern): Mitigated by proper RLS policies (C-02, auth.role() fixes)
- TD-S05 (time.sleep in quota.py): Already verified as fixed in v1 review -- `asyncio.sleep(0.3)` used everywhere
- Frontend debt has zero dependency on DB debt resolution

---

## Recomendacoes

### Recommended Resolution Order (5 migrations + 1 backend task)

**Migration 1 -- FK Standardization (Priority: Immediate, 6h)**
- C-01: Re-point 6 FKs from auth.users to profiles(id) using NOT VALID + VALIDATE
- H-02: ON DELETE CASCADE for search_results_store (part of C-01)
- M-03: ON DELETE CASCADE for partner_referrals.partner_id, ON DELETE SET NULL for referred_user_id
- Pre-migration: Run orphan detection query on all 6 tables

**Migration 2 -- search_results_store Hardening (Priority: Immediate, 3h)**
- H-03: pg_cron retention job (daily 4am, DELETE WHERE expires_at < NOW())
- L-06: Composite index (user_id, expires_at) -- before retention job for DELETE perf
- Q7: 2MB CHECK constraint on results JSONB
- Change expires_at default from 24h to 7 days

**Migration 3 -- RLS Policy Standardization (Priority: Next sprint, 2h)**
- H-04/05/06 + M-09 + DA-01 + DA-02: Standardize all 8 tables from `auth.role() = 'service_role'` to `FOR ALL TO service_role USING (true) WITH CHECK (true)`
- C-02: Add explicit service_role policies to health_checks and incidents (currently zero policies)

**Migration 4 -- Retention Jobs (Priority: Next sprint, 3h)**
- M-04: mfa_recovery_attempts 30-day retention
- M-05: alert_runs 90-day retention
- M-06: alert_sent_items 180-day retention
- DA-03: health_checks 30-day retention, incidents 90-day retention
- M-02: Standalone (created_at) index on search_state_transitions

**Migration 5 -- Trigger Consolidation + Index Cleanup (Priority: Next sprint, 2h)**
- H-01: Drop update_pipeline_updated_at(), update_alert_preferences_updated_at(), update_alerts_updated_at(); update 3 triggers to use shared update_updated_at()
- L-01: Drop redundant idx_alert_preferences_user_id
- L-02: Drop redundant idx_alert_sent_items_alert_id

**Backend Task (no migration, 3h):**
- M-07: Integration test for handle_new_user() + CI migration guard
- M-01: Add updated_at to 3 tables with UPDATE operations (monthly_quota, mfa_recovery_codes, partner_referrals)

### Summary

| Phase | Migrations | Hours | Sprint |
|-------|-----------|-------|--------|
| Immediate | Migration 1 + 2 | 9h | Current |
| Next Sprint | Migration 3 + 4 + 5 + Backend | 10h | Next |
| **Total Active** | | **19h** | |
| Backlog | L-03, L-04, L-05, M-08 | ~6h | When convenient |
| **Grand Total** | | **~25h** | |

### Backlog (do when convenient)
- L-03: Add column-level COMMENTs to health_checks, incidents (partially done)
- L-04: Evaluate plan_type FK to plans table when adding new active plans
- L-05: Move Stripe Price IDs to env-driven seeding
- M-08: Adopt `chk_{table}_{column}` naming for future migrations only

---

## Risk Assessment

### If C-01 is NOT fixed (FK to auth.users instead of profiles)

**Risk: HIGH -- Data integrity failure in disaster recovery or user deletion**
- If a user is deleted from auth.users directly (Supabase dashboard GDPR action), CASCADE flows through profiles for 26 properly-linked tables but creates orphan rows in the 6 non-standardized tables
- The `handle_new_user()` trigger creates profiles from auth.users, so under normal operations all user_ids exist in both tables -- but this is coincidental, not enforced by constraint
- In partial restore or cross-environment migration, the assumption breaks
- organizations.owner_id with NO ACTION means deleting a user who owns an org silently fails (no error, no cleanup)

### If H-03 is NOT fixed (no search_results_store retention)

**Risk: HIGH -- Unbounded storage growth with direct cost impact**
- Table accumulates JSONB payloads (100KB-1.5MB each) with no cleanup
- `expires_at` column is purely decorative without a cleanup job
- At 500 users: ~7.5 GB/month uncleaned storage growth
- Supabase Pro pricing is based on database size -- this becomes the single largest cost driver
- Query performance degrades as table grows (JSONB decompression on sequential scans)

### If auth.role() policies are NOT standardized (H-04/05/06, DA-01/02)

**Risk: LOW -- Functional but inconsistent**
- Both `auth.role()` and `TO service_role` work correctly in current Supabase PostgreSQL 17
- `TO service_role` is the PostgreSQL-native approach (GRANT-based role check)
- `auth.role()` parses JWT claim per-row -- marginally more expensive but negligible at current scale
- If Supabase changes JWT structure, `auth.role()` could theoretically break
- Practical risk is minimal in the short to medium term

### If retention jobs are NOT added (M-04/05/06, DA-03)

**Risk: MEDIUM -- Gradual storage growth, accelerating under attack**
- mfa_recovery_attempts: Low volume today but a brute force attack generates thousands of rows/hour with no cleanup
- alert_runs: Linear growth (~3K rows/month at 100 alerts). Manageable for 1-2 years without cleanup.
- alert_sent_items: Unbounded per active alert. A daily alert matching 10 items/day = 3,650 dedup rows/year/alert. At 100 alerts: 365K rows/year.
- health_checks: ~8,640 rows/month at 5-minute intervals. Most predictable.
- None are urgent at beta scale. All become problems at 500+ users with 100+ active alerts.

---

*Review completed 2026-03-04 by @data-engineer (Dynamo).*
*Methodology: Code-level verification of every DRAFT claim against actual migration SQL files, SCHEMA.md, and ripgrep across codebase.*
*Ready for architect consolidation into FINAL v3.0.*
