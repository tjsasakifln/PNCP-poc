# STORY-5.2: Feature Flags Single Source of Truth (TD-SYS-011)

**Priority:** P2 | **Effort:** M (8-16h) | **Squad:** @dev + @architect | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** dev/admin SmartLic, **I want** feature flags em single source of truth (Redis ou DB), **so that** valores não conflitem entre env vars + Redis + código.

## Acceptance Criteria
- [ ] AC1: Tabela `feature_flags` em DB ou keys Redis namespace `flag:*`
- [ ] AC2: Backend `config.py` lê flags com fallback documented (DB > Redis cache > code default)
- [ ] AC3: Endpoint admin `/admin/feature-flags` GET/POST com audit_events log
- [ ] AC4: UI admin (em `/admin`) — list + toggle flags
- [ ] AC5: Migration de flags existentes (`DATALAKE_ENABLED`, `LLM_*`, `VIABILITY_*`, etc.)

## Tasks
- [ ] Tabela DB ou Redis schema
- [ ] Backend SoT lookup
- [ ] Endpoints admin
- [ ] UI admin
- [ ] Migration de flags + remove env duplicates

## Dev Notes
- TD-SYS-011 ref
- Atual evaluation: env > Redis > code (unclear)

## Definition of Done
- [ ] SoT + admin UI + migration completed

## Risks
- R1: Cache invalidation race — mitigation: TTL curto (60s)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
