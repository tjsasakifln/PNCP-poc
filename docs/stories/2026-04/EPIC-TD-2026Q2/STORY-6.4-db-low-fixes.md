# STORY-6.4: DB Low Fixes (TD-DB-023, 032, 033)

**Priority:** P3 | **Effort:** XS (2-4h) | **Squad:** @data-engineer | **Status:** Ready for Review
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** debitos low DB resolvidos, **so that** schema seja consistente.

## Acceptance Criteria
- [x] AC1 (TD-DB-023): Schedule `health_checks` cleanup cron (>30d delete). Note: job originally existed in 20260308310000_debt009 at '10 4 * * *' using `checked_at` column (not `created_at`). This migration re-registers it at '0 3 * * *' UTC, documents the correct column name, and adds COMMENT ON TABLE.
- [x] AC2 (TD-DB-032): COMMENT em `pncp_raw_bids.crawl_batch_id` documentando soft FK rationale (intentionally not a hard FK to allow batch deletion without cascade constraints; preserves audit trail).
- [x] AC3 (TD-DB-033): `search_results_store.user_id` FK confirmed and re-asserted as ON DELETE CASCADE to profiles(id). Audit note: both `search_results_store` and `search_results_cache` already use `profiles(id) ON DELETE CASCADE` (set by 20260304100000_fk_standardization_to_profiles.sql). Migration is idempotent and documents the TD-DB-033 resolution with COMMENT ON CONSTRAINT.

## Tasks
- [x] AC1: cron schedule (20260416120000_story64_schedule_health_checks_cleanup.sql)
- [x] AC2: SQL COMMENT (20260416120100_story64_comment_crawl_batch_id.sql)
- [x] AC3: ALTER constraint re-assert (20260416120200_story64_search_results_store_cascade.sql)

## Dev Notes
- **AC1**: health_checks uses `checked_at` (TIMESTAMPTZ NOT NULL DEFAULT now()), NOT `created_at`. The table has no `created_at` column. Using wrong column would silently fail or error.
- **AC3**: search_results_store was originally `auth.users(id)` (20260303100000_create_search_results_store.sql) then changed to `profiles(id) ON DELETE CASCADE` in 20260304100000_fk_standardization_to_profiles.sql. Both sister tables are now consistent. AC3 migration is idempotent (no behavioral change).
- All 3 migrations paired with `.down.sql` per STORY-6.2 convention.

## File List
| File | Action |
|------|--------|
| `supabase/migrations/20260416120000_story64_schedule_health_checks_cleanup.sql` | Created |
| `supabase/migrations/20260416120000_story64_schedule_health_checks_cleanup.down.sql` | Created |
| `supabase/migrations/20260416120100_story64_comment_crawl_batch_id.sql` | Created |
| `supabase/migrations/20260416120100_story64_comment_crawl_batch_id.down.sql` | Created |
| `supabase/migrations/20260416120200_story64_search_results_store_cascade.sql` | Created |
| `supabase/migrations/20260416120200_story64_search_results_store_cascade.down.sql` | Created |
| `docs/stories/2026-04/EPIC-TD-2026Q2/STORY-6.4-db-low-fixes.md` | Modified |

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-16 | 1.1 | AC1-AC3 completos. 3 migrations + 3 down.sql criados. Notas sobre schema atual (health_checks usa checked_at; search_results_store ja tem CASCADE). Status: Ready for Review. | @data-engineer |
