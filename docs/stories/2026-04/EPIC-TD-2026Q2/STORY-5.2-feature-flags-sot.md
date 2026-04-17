# STORY-5.2: Feature Flags Single Source of Truth (TD-SYS-011)

**Priority:** P2 | **Effort:** M (8-16h) | **Squad:** @dev + @architect | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** dev/admin SmartLic, **I want** feature flags em single source of truth (Redis ou DB), **so that** valores não conflitem entre env vars + Redis + código.

## Acceptance Criteria
- [x] AC1: Tabela `feature_flags` em DB ou keys Redis namespace `flag:*`
- [x] AC2: Backend `config.py` lê flags com fallback documented (DB > Redis cache > code default)
- [x] AC3: Endpoint admin `/admin/feature-flags` GET/POST com audit_events log
- [x] AC4: UI admin (em `/admin`) — list + toggle flags
- [x] AC5: Migration de flags existentes (`DATALAKE_ENABLED`, `LLM_*`, `VIABILITY_*`, etc.)

## Tasks
- [x] Tabela DB ou Redis schema
- [x] Backend SoT lookup
- [x] Endpoints admin
- [x] UI admin
- [x] Migration de flags + remove env duplicates

## Dev Notes
- TD-SYS-011 ref
- Atual evaluation: env > Redis > code (unclear)

## Definition of Done
- [x] SoT + admin UI + migration completed

## Risks
- R1: Cache invalidation race — mitigation: TTL curto (60s)

## File List
- `backend/audit.py` — added `"admin.feature_flag_change"` to `VALID_EVENT_TYPES`
- `backend/routes/feature_flags.py` — added `audit_logger.log()` to PATCH handler (AC3)
- `frontend/app/api/admin/[...path]/route.ts` — added PATCH export + body forwarding
- `frontend/app/admin/feature-flags/page.tsx` — new admin UI page with toggle switches (AC4)
- `backend/tests/test_feature_flags_admin.py` — added `TestUpdateFeatureFlagAudit` class
- `frontend/__tests__/admin-feature-flags.test.tsx` — new frontend test file

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation: audit logging (AC3), frontend UI (AC4), PATCH proxy. Backend was ~80% complete (routes/feature_flags.py existed). 3 gaps closed. Status → InReview | @dev |
