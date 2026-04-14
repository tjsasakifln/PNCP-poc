# STORY-6.4: DB Low Fixes (TD-DB-023, 032, 033)

**Priority:** P3 | **Effort:** XS (2-4h) | **Squad:** @data-engineer | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** débitos low DB resolvidos, **so that** schema seja consistente.

## Acceptance Criteria
- [ ] AC1 (TD-DB-023): Schedule `health_checks` cleanup cron (>30d delete)
- [ ] AC2 (TD-DB-032): COMMENT em `pncp_raw_bids.crawl_batch_id` documentando soft FK rationale
- [ ] AC3 (TD-DB-033): `search_results_store.user_id` migrate ON NO ACTION → ON DELETE CASCADE (consistency com sister table)

## Tasks
- [ ] AC1: cron schedule
- [ ] AC2: SQL COMMENT
- [ ] AC3: ALTER constraint

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
