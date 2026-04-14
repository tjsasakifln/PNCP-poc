# STORY-6.2: down.sql Migration Rollback Templates (TD-DB-030)

**Priority:** P3 | **Effort:** S (4-8h) | **Squad:** @data-engineer + @devops | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** templates de rollback `down.sql` para migrations, **so that** failed migrations possam ser revertidas.

## Acceptance Criteria
- [ ] AC1: Template em `.aios-core/development/templates/migration-tmpl.yaml` (ou similar)
- [ ] AC2: `up.sql` + `down.sql` per migration nova
- [ ] AC3: CI gate: nova migration sem `down.sql` → fail
- [ ] AC4: 5 migrations recentes back-filled com `down.sql`

## Tasks
- [ ] Template setup
- [ ] CI gate
- [ ] Backfill

## Dev Notes
- DB-AUDIT TD-DB-030 ref
- Supabase CLI suporta versioning mas não down — usar manual scripts

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
