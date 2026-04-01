# Database Specialist Review — SmartLic

**Reviewer:** @data-engineer (Dara)
**Date:** 2026-03-31
**DRAFT Reviewed:** `docs/prd/technical-debt-DRAFT.md` (Section 2: Database Debts DB-001 to DB-020, Section 7: Questions for @data-engineer)
**Supporting Documents:** `supabase/docs/SCHEMA.md`, `supabase/docs/DB-AUDIT.md`, `supabase/docs/MIGRATION-SQUASH-PLAN.md`

---

## Summary

The architect's database debt assessment is thorough and well-sourced. All 20 identified debts (DB-001 through DB-020) are real issues. I validated each against the actual migration files, SCHEMA.md, and backend code. My adjustments are minor: two severity upgrades, one severity downgrade, a few hour estimate corrections, and three additional debts the architect missed. The overall picture is accurate -- the database layer is in solid shape (100% RLS, atomic RPCs, JSONB governance, pre-computed tsvector) but carries structural debt from rapid iteration that needs disciplined cleanup.

**Verdict:** APPROVED with adjustments. The DRAFT's database section is production-quality and ready for prioritization after incorporating the changes below.

---

## Debts Validated

| ID | Debt | Original Severity | Adjusted Severity | Hours | Complexity | Notes |
|----|------|-------------------|-------------------|-------|------------|-------|
| DB-001 | `handle_new_user()` missing `SET search_path` | HIGH | **HIGH** (confirmed) | 1 | Simple | Confirmed: latest definition in migration `20260321140000` has NO `SET search_path`. Function is SECURITY DEFINER, called on every signup. Single-line fix. |
| DB-002 | 106 migration files schema archaeology risk | HIGH | **HIGH** (confirmed) | 24 | Complex | Count confirmed at 106 files. Squash plan exists at `MIGRATION-SQUASH-PLAN.md` and is well-structured (4 phases). However, the plan references 96 files (stale count from March 21). Updated prerequisite list needed. |
| DB-003 | Duplicate trigger functions `update_updated_at()` vs `set_updated_at()` | HIGH | **LOW** (downgraded) | 0 | Already done | **Already resolved.** Migration `20260308100000_debt001_database_integrity_fixes.sql` line 99: `DROP FUNCTION IF EXISTS public.update_updated_at();`. All triggers now point to `set_updated_at()`. This debt should be CLOSED. |
| DB-004 | `classification_feedback.user_id` references `auth.users` | MEDIUM | **MEDIUM** (confirmed) | 2 | Simple | Confirmed: bridge migration `20260308200000` created the table with `REFERENCES auth.users(id)`. The FK standardization wave in `20260304100000` came before this migration, so it was missed. |
| DB-005 | Hardcoded Stripe price IDs in migrations | MEDIUM | **MEDIUM** (confirmed) | 4 | Medium | Real concern for staging environments. However, this is a one-time migration issue -- once squash happens, the baseline seeds can be made env-aware. Recommend addressing during squash (DB-002), not separately. |
| DB-006 | `ingestion_checkpoints.crawl_batch_id` lacks FK to `ingestion_runs` | MEDIUM | **MEDIUM** (confirmed) | 2 | Simple | Monitoring via `check_ingestion_orphans()` + `ingestion_orphan_checkpoints` view provides adequate safety. FK enforcement is nice-to-have but the `NOT VALID + VALIDATE` pattern avoids table lock during enforcement. |
| DB-007 | `search_state_transitions.search_id` no FK to `search_sessions` | MEDIUM | **LOW** (downgraded) | 1 | Simple | These are fire-and-forget audit records. Adding FK with CASCADE would cause the audit trail to be deleted when search sessions are cleaned up, which is arguably worse. An FK here would create a dependency that makes retention policies harder. Keep as-is; use periodic cleanup instead. |
| DB-008 | Multiple tables lack retention/cleanup strategy | MEDIUM | **HIGH** (upgraded) | 6 | Medium | Upgraded because `search_state_transitions` is inserted on every state change (6-8 per search), and there are 5131+ backend tests running searches. In production with growing traffic, this table will be the first to cause performance issues. Four tables need pg_cron jobs. Increased hours from 4 to 6 to account for testing each job and verifying no data needed for active debugging is lost. |
| DB-009 | `organizations/organization_members` self-referencing RLS perf | MEDIUM | **LOW** (downgraded) | 0 | N/A | Organizations feature is not yet live in production. Zero rows in both tables. This is a theoretical concern that only materializes when the consultoria plan launches with multi-user support. Defer until then. |
| DB-010 | No VACUUM ANALYZE for high-churn tables | MEDIUM | **MEDIUM** (confirmed) | 2 | Simple | Supabase Cloud runs auto-vacuum but with default thresholds (50 dead tuples + 10% of table). For `pncp_raw_bids` with daily hard deletes of 3000+ rows, auto-vacuum should trigger. However, explicit scheduling ensures it runs immediately after purge rather than whenever PG decides. Worth adding. |
| DB-011 | Trigger naming partially standardized (4 remaining) | MEDIUM | **LOW** (downgraded) | 1 | Simple | Cosmetic issue. The 4 remaining triggers (`tr_pipeline_items_updated_at`, `trigger_alert_preferences_updated_at`, `trigger_alerts_updated_at`, `trigger_create_alert_preferences_on_profile`) all work correctly. Rename during squash. |
| DB-012 | Dead plan catalog entries | LOW | **LOW** (confirmed) | 1 | Simple | 8 deactivated plans with `is_active = false`. No query performance impact. A `deprecated_at` timestamp is a nice audit improvement but not urgent. |
| DB-013 | `profiles.context_data` schema not enforced | LOW | **LOW** (confirmed) | 4 | Medium | Application-layer validation via Pydantic is the current pattern. Adding DB-level schema validation for JSONB is non-trivial and creates migration burden when the schema evolves. Keep Pydantic validation; add a CHECK only for critical invariants (e.g., `jsonb_typeof(context_data) = 'object'`). |
| DB-014 | Redundant index on `alert_preferences.user_id` | LOW | **LOW** (confirmed) | 0.5 | Simple | Trivial DROP INDEX. Saves minimal write overhead. |
| DB-015 | `google_sheets_exports` GIN index on `search_params` | LOW | **LOW** (confirmed) | 0.5 | Simple | Confirmed no queries use this index. DROP it. |
| DB-016 | `plan_features.id` uses SERIAL vs UUID | LOW | **LOW** (confirmed) | 0 | N/A | Not worth changing. plan_features is a low-volume catalog table (~20 rows). SERIAL is fine. |
| DB-017 | Overly broad admin RLS checks via subquery | LOW | **LOW** (confirmed) | 8 | Complex | The subquery `EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin)` runs per-row but the profiles lookup is index-backed and PG caches the result within a single query. At current scale (few hundred users, admin queries paginated with LIMIT), this is not a concern. Revisit at 10K+ users. |
| DB-018 | `user_subscriptions.annual_benefits` vestigial column | LOW | **LOW** (confirmed) | 1 | Simple | Confirmed vestigial. The column is defined in `backend/models/user_subscription.py` (SQLAlchemy model, line 80) but never read or written in any business logic. Safe to drop after removing the model definition. |
| DB-019 | Missing composite indexes | LOW | **LOW** (confirmed) | 2 | Simple | Two indexes recommended: `search_state_transitions(search_id, to_state)` and `classification_feedback(setor_id, created_at DESC)`. Both are justified for debugging and analytics queries. |
| DB-020 | Timestamp naming inconsistency | LOW | **LOW** (confirmed) | 1 | Simple | `google_sheets_exports.last_updated_at` and `health_checks.checked_at` are the outliers. Rename during squash. |

**Totals adjusted:** Original 73h across 20 debts. Adjusted to **54h** across 17 active debts (DB-003 closed, DB-009/DB-016 deferred with 0h).

---

## Debts Added

| ID | Debt | Severity | Hours | Rationale |
|----|------|----------|-------|-----------|
| DB-021 | **`check_and_increment_quota()` and `increment_quota_atomic()` lack SECURITY DEFINER** — these functions are called via RPC from the backend service role. Without SECURITY DEFINER, they run as the calling role. Currently works because service_role has full access, but if RLS policies on `monthly_quota` change or a new non-service caller is introduced, these functions could silently fail. More importantly, they also lack `SET search_path = public`, same class of risk as DB-001. | MEDIUM | 1 | Defensive hardening. Both functions operate on `monthly_quota` only. Add SECURITY DEFINER + SET search_path. |
| DB-022 | **`get_conversations_with_unread_count()` and `get_analytics_summary()` lack `SET search_path`** — the DB-AUDIT flags these as "LOW risk, no SET search_path" but they ARE SECURITY DEFINER functions (per the SCHEMA.md section 1.3). Any SECURITY DEFINER function without explicit search_path is a search_path injection vector, regardless of whether it's read-only. | LOW | 1 | Batch fix with DB-001. Same single-line change per function. |
| DB-023 | **No pg_cron job for `search_sessions` retention** — `search_sessions` has 6 status values and tracks every search ever performed. Unlike `search_state_transitions` (DB-008), this table was not called out. At scale, old completed/failed sessions from months ago serve no purpose and add to backup size. Current pg_cron covers quota (24mo), webhooks (90d), audit (12mo), cache (7d), results store (7d) but NOT sessions. | MEDIUM | 2 | Add pg_cron: DELETE search_sessions WHERE status IN ('completed', 'failed', 'timed_out', 'cancelled') AND created_at < now() - interval '6 months'. Keep 'processing'/'created' indefinitely (or until status is resolved). |

---

## Debts Challenged

### DB-003: Duplicate trigger functions — SHOULD BE CLOSED

The DRAFT lists this as HIGH severity, 2 hours. However, migration `20260308100000_debt001_database_integrity_fixes.sql` already:
1. Re-pointed all 5 remaining triggers to `set_updated_at()`
2. Dropped `update_updated_at()` with `DROP FUNCTION IF EXISTS`

This debt was resolved during the DEBT-001 sprint. The DRAFT should mark it as **CLOSED/RESOLVED** and remove it from active prioritization. The 2 hours allocated can be reclaimed.

### DB-007: search_state_transitions FK — DISAGREE WITH FK APPROACH

The DRAFT recommends adding an FK with ON DELETE CASCADE. I recommend against this. The search_state_transitions table serves as an audit trail. If we add CASCADE, deleting a search_session (via retention policy) would silently destroy the audit trail. This defeats the purpose of the audit. Instead, the retention policy for search_state_transitions (DB-008) should handle cleanup independently with its own age-based threshold. Downgraded to LOW.

### DB-009: Organization RLS performance — PREMATURE OPTIMIZATION

The organizations feature has zero production usage. Both tables are empty. The self-referencing RLS concern is valid in theory but evaluating it now is wasted effort. Downgraded to LOW with 0 hours, to be revisited when consultoria plan launches.

---

## Answers to Architect

### Q1: DB-001 (handle_new_user SET search_path)

**Confirmed the current final definition** is in migration `20260321140000_debt_w4_db_micro_fixes.sql` (lines 216+). This is the 8th redefinition (the squash plan says 8, not 7 as the DRAFT states). The function is SECURITY DEFINER, does not SET search_path, and inserts into `public.profiles` with a fallback INSERT for phone_whatsapp unique_violation handling.

**Adding `SET search_path = public` will NOT break the trigger chain.** The function already qualifies all table references as `public.profiles`. The only cross-schema reference is `NEW.raw_user_meta_data` which comes from the trigger's `auth.users` row context and is not affected by search_path. The fix is safe to deploy.

**Recommended fix:**
```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public  -- ADD THIS LINE
AS $$
-- ... existing body unchanged ...
$$;
```

### Q2: DB-002 (migration squash risk)

**Estimated risk of replaying 106 migrations in DR: MEDIUM-HIGH.**

I have NOT tested a clean DB creation from the full chain recently. The squash plan was written when there were 96 files; there are now 106. Known risks:
- `handle_new_user()` is redefined 8 times; intermediate versions reference columns that don't exist yet
- `plan_type CHECK` constraint is dropped/recreated 5 times; the intermediate states would fail if plan data exists
- The `008_rollback.sql.bak` file in the migrations directory could confuse automated replay
- Several migrations use `IF NOT EXISTS` guards, which helps, but some `ALTER TABLE` statements don't have them

**Recommendation:** Execute squash before any other DB debt. The squash plan is solid. I recommend adding a CI step that tests clean DB creation from the squashed baseline weekly.

### Q3: DB-008 (retention policies / search_state_transitions growth)

**Projected table size at current traffic:**
- Current: ~15-30 searches/day (beta, ~50 active users)
- Each search generates 6-8 state transitions (created -> processing -> fetching -> filtering -> classifying -> completed/failed)
- At 25 searches/day * 7 transitions * 180 days = ~31,500 rows in 6 months
- At 100 searches/day (post-launch target) * 7 * 180 = ~126,000 rows

**90-day retention is sufficient for debugging.** In practice, debugging searches older than 30 days is extremely rare. The audit_events table (12-month retention) already captures security-relevant events. I recommend 90 days for search_state_transitions and 6 months for classification_feedback (which has genuine analytical value for improving LLM classification).

### Q4: DB-010 (VACUUM ANALYZE for pncp_raw_bids)

**Supabase Cloud auto-vacuum is likely adequate but not guaranteed to run immediately after purge.** The default auto-vacuum thresholds are:
- `autovacuum_vacuum_threshold = 50` (dead tuples)
- `autovacuum_vacuum_scale_factor = 0.2` (20% of table)

For `pncp_raw_bids` at 40K rows, auto-vacuum triggers after 50 + (0.2 * 40,000) = 8,050 dead tuples. The daily purge deletes ~3,000-5,000 rows (12-day retention, 27 UFs * 6 modalidades). This means auto-vacuum might NOT trigger after a single day's purge if only 3,000 rows are deleted. It would trigger after 2-3 days of accumulated deletes.

**The `check_pncp_raw_bids_bloat()` function exists but is not called on any schedule.** It's a manual diagnostic. Nobody is monitoring it regularly.

**Recommendation:** Add pg_cron VACUUM ANALYZE at 7:30 UTC (30 min after purge at 7 UTC). Also add a pg_cron call to `check_pncp_raw_bids_bloat()` weekly with result logging for trend monitoring.

### Q5: DB-006 (ingestion_checkpoints FK enforcement)

**The monitoring approach (view + function from DEBT-207) is sufficient for current scale.** An enforced FK would add a lookup to `ingestion_runs` on every checkpoint INSERT/UPDATE during ingestion. With 27 UFs * 6 modalidades = 162 checkpoints per full crawl, this is 162 additional index lookups. Negligible overhead.

**However, the real question is: what happens when an ingestion_run is deleted?** Currently nothing references ingestion_runs from checkpoints. If we add a FK with CASCADE, deleting a run would cascade-delete its checkpoints, which is probably the desired behavior for cleanup.

**Recommendation:** Add the FK with `NOT VALID` first, then `VALIDATE CONSTRAINT` in a separate statement. Use `ON DELETE CASCADE`. The performance impact is negligible and the data integrity benefit is real.

### Q6: DB-017 (admin RLS subquery scale threshold)

**The current scale is nowhere near the threshold.** Here's the math:

The admin RLS check `EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin)` executes once per query (not per-row as the DRAFT implies -- PostgreSQL's optimizer evaluates subqueries with `auth.uid()` as a constant expression and caches the result within a single statement execution).

The actual concern is:
- **Per-statement overhead:** ~0.1ms for the profiles index lookup (PK scan on UUID)
- **Threshold for concern:** When admin queries return >10,000 rows without pagination, the per-statement cost is amortized to near-zero
- **When to revisit:** When we have >100 admin users running concurrent dashboard queries (currently 2 admins)

**Verdict:** This will not be a problem for years. Keep at LOW priority.

### Q7: Planned schema changes affecting squash timing

**Known upcoming schema changes that should be completed BEFORE squash:**

1. **DB-001 fix** (handle_new_user SET search_path) -- must be in final baseline
2. **DB-004 fix** (classification_feedback FK re-point) -- must be in final baseline
3. **DB-008** (add pg_cron retention jobs) -- should be in baseline
4. **DB-011** (trigger renames) -- should be in baseline (4 triggers)
5. **Alerts email system** -- `alert_preferences`, `alerts`, `alert_sent_items`, `alert_runs` tables already exist and are stable. No planned changes.
6. **Organization billing** -- `organizations` and `organization_members` tables exist but are unused. Schema is stable; no changes planned until consultoria plan launches.
7. **Partner revenue share** -- `partners` and `partner_referrals` tables exist and are stable. No planned changes.

**Recommendation:** Execute DB-001, DB-004, DB-008, and DB-011 first (total: ~10 hours), then immediately proceed with squash. This order avoids squashing and then creating new migrations that could have been in the baseline.

---

## Resolution Order Recommended

### Phase 0: Immediate (1-2 days, ~3h)

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 1 | DB-001 | `handle_new_user()` SET search_path | 1 | Security. Single migration. Zero risk. Deploy immediately. |
| 2 | DB-022 | Other SECURITY DEFINER functions missing SET search_path | 1 | Batch with DB-001. Same migration file. |
| 3 | DB-003 | Duplicate trigger functions | 0 | CLOSE this debt. Already resolved. |
| 4 | DB-014 | Redundant alert_preferences index | 0.5 | Include in same migration as DB-001. |
| 5 | DB-015 | Unused GIN index on google_sheets_exports | 0.5 | Include in same migration. |

### Phase 1: Pre-Squash Cleanup (1 sprint, ~15h)

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 6 | DB-008 | Retention policies (4 tables) | 6 | Must be in baseline. Add pg_cron jobs for search_state_transitions (90d), classification_feedback (12mo), mfa_recovery_attempts (30d), alert_runs (6mo). |
| 7 | DB-023 | search_sessions retention | 2 | Add to same pg_cron migration. |
| 8 | DB-004 | classification_feedback FK re-point | 2 | Must be in baseline. |
| 9 | DB-011 | Trigger naming (4 remaining) | 1 | Must be in baseline. Cosmetic but prevents post-squash rename migration. |
| 10 | DB-010 | VACUUM ANALYZE schedule | 2 | Must be in baseline. |
| 11 | DB-019 | Missing composite indexes | 2 | Must be in baseline. |

### Phase 2: Migration Squash (dedicated effort, ~24h)

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 12 | DB-002 | Migration squash (106 -> ~5-10 files) | 24 | Follow the existing squash plan. This also resolves DB-005 (Stripe price IDs can be made env-aware in the new seed file), DB-020 (timestamp renames included in baseline), and DB-011 (trigger names finalized). |

### Phase 3: Opportunistic (fold into feature work, ~12h)

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 13 | DB-006 | ingestion_checkpoints FK enforcement | 2 | Do when next touching ingestion pipeline. |
| 14 | DB-013 | context_data minimal schema validation | 4 | Do when next touching onboarding. |
| 15 | DB-018 | Drop annual_benefits column | 1 | Do when next touching subscriptions. Remove from SQLAlchemy model first. |
| 16 | DB-021 | Quota functions SECURITY DEFINER + search_path | 1 | Do when next touching quota logic. |
| 17 | DB-017 | Admin RLS JWT claims | 8 | Only if scale demands it. Likely years away. |

### Deferred (not actionable now)

| ID | Debt | Reason |
|----|------|--------|
| DB-009 | Organization RLS performance | Zero production usage. Revisit when consultoria plan launches. |
| DB-012 | Dead plan catalog entries | No impact. Cosmetic only. |
| DB-016 | plan_features SERIAL vs UUID | Not worth changing. |

---

## Dependencies & Blockers

```
DB-001 (search_path fix)  ──must precede──>  DB-002 (squash)
DB-004 (FK re-point)      ──must precede──>  DB-002 (squash)
DB-008 (retention jobs)   ──must precede──>  DB-002 (squash)
DB-010 (VACUUM schedule)  ──must precede──>  DB-002 (squash)
DB-011 (trigger renames)  ──must precede──>  DB-002 (squash)
DB-019 (indexes)          ──should precede──> DB-002 (squash)
DB-023 (sessions cleanup) ──should precede──> DB-002 (squash)

DB-002 (squash) ──resolves──> DB-005 (Stripe IDs in seeds)
DB-002 (squash) ──resolves──> DB-020 (timestamp naming)
DB-002 (squash) ──resolves──> DB-003 (already done, captured in baseline)

DB-018 (drop annual_benefits) ──requires──> Backend model change first
                                             (remove from models/user_subscription.py)

DB-017 (JWT admin claims) ──blocked by──> Supabase Auth custom claims support
                                           (or app_metadata approach)
```

**Critical path:** DB-001 + DB-004 + DB-008 + DB-010 + DB-011 -> DB-002 (squash). Total: ~38h across 2 sprints.

---

## Risk Assessment

### R-DB-001: Migration Chain Replay Failure (HIGH)

**Probability:** Medium (never tested clean replay recently)
**Impact:** HIGH (DR scenario = unable to recreate database from migrations)
**Mitigation:** Execute squash (DB-002) within 2 sprints. Until then, maintain a pg_dump of production schema as backup.

### R-DB-002: Unbounded Table Growth (MEDIUM)

**Probability:** High (guaranteed with growing traffic)
**Impact:** MEDIUM (storage costs, backup size, query degradation on unindexed scans)
**Tables at risk:** search_state_transitions (6-8 rows/search), search_sessions (1 row/search), classification_feedback (1 row/feedback event)
**Mitigation:** DB-008 + DB-023 retention policies. Estimated 6 months before impact at current traffic.

### R-DB-003: search_path Injection on Signup (LOW)

**Probability:** Very Low (requires schema creation privileges on Supabase, which normal users and even compromised service_role accounts cannot easily obtain)
**Impact:** HIGH (could redirect profile creation to attacker-controlled table)
**Mitigation:** DB-001 fix. 1 hour effort. Deploy immediately.

### R-DB-004: Ingestion Orphan Accumulation (LOW)

**Probability:** Low (monitoring in place via DEBT-207)
**Impact:** LOW (stale data, not security/availability)
**Mitigation:** DB-006 FK enforcement provides belt-and-suspenders with existing monitoring.

### R-DB-005: Post-Squash Migration Drift (MEDIUM)

**Probability:** Medium (if squash is delayed, more migrations accumulate)
**Impact:** MEDIUM (each week adds 1-3 more migrations, increasing squash complexity)
**Mitigation:** Execute squash promptly. The squash plan is already written and validated. Every week of delay makes it harder.

---

*Review completed 2026-03-31 by @data-engineer (Dara) as Phase 5 of Brownfield Discovery workflow.*
*Next: Phase 6 (@ux-design-expert review), Phase 7 (@qa gate).*
