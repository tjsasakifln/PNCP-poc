# STORY-5.6: DB Medium Fixes Bundle (TD-DB-012, 015, 020, 021, 024)

**Priority:** P2 | **Effort:** M (13-23h) | **Squad:** @data-engineer + @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** débitos médios DB resolvidos, **so that** schema seja mais maintainable + LGPD compliance melhore.

## Acceptance Criteria
- [ ] AC1 (TD-DB-012): `messages.INSERT` policy COMMENT explicando triple-nested EXISTS pattern
- [ ] AC2 (TD-DB-015): `idx_alert_preferences_digest_scan` index criado
- [ ] AC3 (TD-DB-020): `audit_events.is_active` flag adicionado (soft-delete LGPD)
- [ ] AC4 (TD-DB-021): `classification_feedback` table schema documentado em SCHEMA.md
- [ ] AC5 (TD-DB-024): Stripe webhook PII archive script + S3 integration

## Tasks
- [ ] AC1: 1 migration COMMENT only
- [ ] AC2: Index migration
- [ ] AC3: Add column migration + RLS policy update
- [ ] AC4: Update SCHEMA.md
- [ ] AC5: Archive script + cron + S3 setup

## Dev Notes
- DB-AUDIT TD-DB-012, 015, 020, 021, 024 refs
- AC5 maior — pode separar em sub-story se necessário

## Definition of Done
- [ ] All 5 ACs met

## Risks
- R1: AC5 S3 setup requer infra config — mitigation: separate pre-req

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
