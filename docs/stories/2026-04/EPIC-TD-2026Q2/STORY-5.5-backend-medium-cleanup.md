# STORY-5.5: Backend Medium Cleanup Bundle (TD-SYS-020 a 025)

**Priority:** P2 | **Effort:** L (30-50h) | **Squad:** @dev + @qa | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** dev SmartLic, **I want** débitos médios backend resolvidos em bundle, **so that** maintainability + DX melhorem.

## Acceptance Criteria
- [ ] AC1 (TD-SYS-020): `sectors_data.yaml` validado em startup via Pydantic
- [ ] AC2 (TD-SYS-021): Feature flags docs gerados automaticamente
- [ ] AC3 (TD-SYS-022): Mock pattern padronizado em CLAUDE.md + conftest helpers
- [ ] AC4 (TD-SYS-023): Integration tests isolated state (per-test DB ou pytest-xdist loadfile)
- [ ] AC5 (TD-SYS-024): `schemas.py` decomposto em `schemas/{search,billing,user,pipeline}.py`
- [ ] AC6 (TD-SYS-025): Logs JSON-only em prod (env-controlled)

## Tasks
- [ ] Per AC, sub-PR
- [ ] Bundle merge final

## Dev Notes
- Esta é uma "umbrella story" — pode ser quebrada em sub-stories STORY-5.5.1 a 5.5.6 se preferir

## Definition of Done
- [ ] All 6 AC met + tests pass

## Risks
- R1: schemas.py decompose quebra imports — mitigation: backward compat re-exports

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
