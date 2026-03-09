# DEBT-017: Database Long-Term Optimization

**Sprint:** Backlog
**Effort:** 47h
**Priority:** LOW
**Agent:** @data-engineer (Delta)

## Context

After Sprint 1-2 resolve critical and high-priority database debts, numerous medium and low severity items remain. These are primarily documentation, optimization, and hardening tasks that improve long-term maintainability but do not pose immediate risk. Items include accepted risk documentation, minor schema improvements, query optimizations, and planning for future scale.

## Scope

| ID | Debito | Horas |
|----|--------|-------|
| DB-004 | `mfa_recovery_codes` no rate limiting in DB (app-layer rate limiting is correct pattern) | 2h |
| DB-005 | `mfa_recovery_attempts` no SELECT policy for user (intentional: information leakage prevention) | 0.5h |
| DB-006 | `trial_email_log` no user-facing policies (backend-only, document as accepted) | 0.5h |
| DB-008 | Stripe Price IDs visible in `plans` table (accepted risk: used client-side by design) | 0h (document) |
| DB-009 | `profiles.email` exposed via partner RLS policy — optimize via `partners.contact_email` | 2h |
| DB-014 | `plans.stripe_price_id` legacy column coexists with period-specific columns | 2h |
| DB-016 | `search_sessions.status` no enforcement of transitions in DB (app-layer via state_manager) | 4h |
| DB-017 | Missing `NOT NULL` in several columns (`google_sheets_exports.created_at`, `partners.created_at`) | 2h |
| DB-020 | Naming inconsistency in constraints — adopt `chk_{table}_{column}` convention | 1h |
| DB-022 | `profiles.phone_whatsapp` CHECK does not validate Brazilian structure (app-layer validation preferred) | 1h |
| DB-023 | `search_results_cache` UNIQUE allows cross-user sharing with potentially stale date range | 2h |
| DB-024 | `plan_billing_periods` no `updated_at` column (pricing changes are infrequent, tracked via git) | 1h |
| DB-027 | No down-migrations — standard for Supabase (PITR is rollback mechanism) | 8h |
| DB-029 | Hardcoded Stripe Price IDs in migrations (blocks staging/dev setup) | 2h |
| DB-034 | `cleanup_search_cache_per_user()` trigger fires on each INSERT (add short-circuit) | 2h |
| DB-035 | `get_conversations_with_unread_count()` uses correlated subquery (rewrite as JOIN) | 2h |
| DB-036 | No table partitioning for append-heavy tables (plan when row count > 1M/month) | 8h |
| DB-044 | pg_cron jobs not in migrations (require superuser) — document manual setup | 4h |
| DB-046 | No audit trail for DB-level schema changes (policy: "never modify via dashboard") | 1h |
| DB-050 | No FK from `search_state_transitions.search_id` to `search_sessions` (orphans possible) | 4h |

## Tasks

- [x] Document accepted risks: DB-005 (intentional), DB-006 (backend-only), DB-008 (accepted)
- [x] Add app-layer documentation for DB-004 MFA rate limiting pattern
- [x] Optimize partner RLS: use `partners.contact_email` instead of cross-schema `profiles.email` (DB-009)
- [x] Deprecate `plans.stripe_price_id` after confirming zero references in billing code (DB-014)
- [x] Document valid `search_sessions.status` transitions via SQL COMMENT (DB-016)
- [x] Add `NOT NULL DEFAULT now()` to `google_sheets_exports.created_at` and `partners.created_at` (DB-017)
- [x] Adopt naming convention `chk_{table}_{column}` for future constraints (DB-020)
- [x] Document phone validation as app-layer responsibility (DB-022)
- [x] Review SWR cache sharing risks and mitigate if necessary (DB-023)
- [x] Evaluate adding `updated_at` to `plan_billing_periods` (DB-024)
- [x] Create down-migration strategy document (PITR as primary, manual scripts as supplement) (DB-027)
- [x] Parameterize Stripe Price IDs in seed data (use env vars) (DB-029)
- [x] Add short-circuit to cleanup trigger: `IF count(*) <= 10 THEN RETURN NEW` (DB-034)
- [x] Rewrite conversations query as LEFT JOIN + GROUP BY (DB-035)
- [x] Plan partitioning strategy for `audit_events`, `search_state_transitions` (DB-036)
- [x] Document pg_cron manual setup steps (DB-044)
- [x] Document "never modify schema via dashboard" policy (DB-046)
- [x] Evaluate FK for search_state_transitions (requires UNIQUE on search_sessions.search_id) (DB-050)

## Acceptance Criteria

- [x] AC1: All accepted risks documented in DB-AUDIT.md or inline SQL COMMENTs
- [x] AC2: Partner RLS uses contact_email (no cross-schema query)
- [x] AC3: Legacy `stripe_price_id` deprecated or removed
- [x] AC4: All `created_at` columns have `NOT NULL DEFAULT now()`
- [x] AC5: Stripe Price IDs parameterized for staging/dev setup
- [x] AC6: Cleanup trigger has short-circuit optimization
- [x] AC7: Conversations query uses JOIN (not correlated subquery)
- [x] AC8: Zero regressions

## Tests Required

- Migration idempotency tests for all schema changes
- Query performance: EXPLAIN ANALYZE for conversations query (before/after)
- Cleanup trigger: verify short-circuit with <= 10 entries

## Definition of Done

- [x] All tasks complete
- [x] Tests passing (backend 5800+ / 0 fail)
- [x] No regressions
- [x] Documentation updated
- [x] Code reviewed

## File List

| File | Action | Purpose |
|------|--------|---------|
| `supabase/migrations/20260309100000_debt017_database_long_term_optimization.sql` | Created | Migration: NOT NULL constraints, trigger optimization, conversations query rewrite, SQL COMMENTs, plan_billing_periods updated_at |
| `supabase/docs/DB-AUDIT.md` | Updated | Added "Accepted Risks & Design Decisions" section documenting 18 DB-xxx items |
| `supabase/seed/seed_stripe_prices.sql` | Created | Parameterized Stripe Price ID seed script for staging/dev |
| `scripts/seed-stripe-prices.sh` | Created | Shell helper for seeding Stripe Price IDs via env vars |
| `backend/tests/test_debt017_database_optimization.py` | Created | 56 tests covering all 8 ACs |
| `docs/stories/DEBT-017-database-long-term-optimization.md` | Updated | All checkboxes marked complete |
