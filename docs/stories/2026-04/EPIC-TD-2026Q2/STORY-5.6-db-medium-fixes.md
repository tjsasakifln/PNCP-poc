# STORY-5.6: DB Medium Fixes Bundle (TD-DB-012, 015, 020, 021, 024)

**Priority:** P2 | **Effort:** M (13-23h) | **Squad:** @data-engineer + @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** débitos médios DB resolvidos, **so that** schema seja mais maintainable + LGPD compliance melhore.

## Acceptance Criteria
- [x] AC1 (TD-DB-012): `messages.INSERT` policy COMMENT explicando triple-nested EXISTS pattern
- [x] AC2 (TD-DB-015): `idx_alert_preferences_digest_scan` index criado
- [x] AC3 (TD-DB-020): `audit_events.is_active` flag adicionado (soft-delete LGPD)
- [x] AC4 (TD-DB-021): `classification_feedback` table schema documentado em `docs/architecture/schema-classification-feedback.md`
- [ ] AC5 (TD-DB-024): Stripe webhook PII archive script + S3 integration — **BLOCKED: requires S3 bucket + IAM credentials**

## Tasks
- [x] AC1: 1 migration COMMENT on `insert_messages_authenticated` policy
- [x] AC2: Index migration `idx_alert_preferences_digest_scan(last_digest_sent_at, frequency)` partial
- [x] AC3: Add column `is_active BOOLEAN DEFAULT true` + partial index on active rows
- [x] AC4: Schema doc with full table definition, constraints, indexes, RLS, backend integration, migration history
- [ ] AC5: Archive script + cron + S3 setup — **BLOCKED: external infra**

## Implementation Notes
- Single migration file: `20260415140000_story56_db_medium_fixes.sql`
- AC1: COMMENT uses DO block to check policy exists before commenting (idempotent)
- AC2: Partial index `WHERE enabled = true AND frequency != 'off'` — optimized for range scan on `last_digest_sent_at` (cron pattern)
- AC3: `is_active` column + `idx_audit_events_active` partial index for common queries
- AC4: Full schema doc at `docs/architecture/schema-classification-feedback.md`

## File List
- `supabase/migrations/20260415140000_story56_db_medium_fixes.sql` — AC1+AC2+AC3
- `docs/architecture/schema-classification-feedback.md` — AC4
- `docs/stories/2026-04/EPIC-TD-2026Q2/STORY-5.6-db-medium-fixes.md` — this file

## Dev Notes
- DB-AUDIT TD-DB-012, 015, 020, 021, 024 refs
- AC5 blocked by S3 infrastructure — separate pre-req needed
- Policy renamed from `messages_insert_user` → `insert_messages_authenticated` in migration 20260331200000

## Definition of Done
- [x] AC1-AC4 met (4/5)
- [ ] AC5 deferred (external infrastructure)

## Risks
- R1: AC5 S3 setup requer infra config — mitigation: separate pre-req
- R2: Mixed-config index on alert_preferences — mitigation: partial index same WHERE clause as existing

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation: AC1-AC4 complete. AC5 blocked (S3 infra). | @dev |
