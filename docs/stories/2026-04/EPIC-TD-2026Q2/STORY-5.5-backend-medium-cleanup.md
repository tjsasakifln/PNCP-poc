# STORY-5.5: Backend Medium Cleanup Bundle (TD-SYS-020 a 025)

**Priority:** P2 | **Effort:** L (30-50h) | **Squad:** @dev + @qa | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** dev SmartLic, **I want** débitos médios backend resolvidos em bundle, **so that** maintainability + DX melhorem.

## Acceptance Criteria
- [x] AC1 (TD-SYS-020): `sectors_data.yaml` validado em startup via Pydantic
- [x] AC2 (TD-SYS-021): Feature flags docs gerados automaticamente
- [x] AC3 (TD-SYS-022): Mock pattern padronizado em CLAUDE.md + conftest helpers
- [x] AC4 (TD-SYS-023): Integration tests isolated state (per-test DB ou pytest-xdist loadfile)
- [x] AC5 (TD-SYS-024): `schemas.py` decomposto em `schemas/{search,billing,user,pipeline}.py`
- [x] AC6 (TD-SYS-025): Logs JSON-only em prod (env-controlled)

## Tasks
- [x] Per AC, sub-PR
- [ ] Bundle merge final

## Dev Notes
- Esta é uma "umbrella story" — pode ser quebrada em sub-stories STORY-5.5.1 a 5.5.6 se preferir
- AC1: `SectorsYamlSchema.model_validate()` em `sectors.py:_load_sectors_from_yaml()` — 7 testes
- AC2: `backend/scripts/generate_feature_flags_docs.py` gera `docs/features/feature-flags-reference.md` (74 flags)
- AC3: `backend/tests/helpers/mock_factories.py` (MockSupabaseBuilder, MockPNCPBuilder, MockLLMBuilder) — 22 testes
- AC4: pytest-xdist já em requirements-dev.txt; --dist loadfile funciona com `-p no:benchmark` (75/80 passam, 5 pre-existing)
- AC5: `backend/schemas/` com 12 submodules + `__init__.py` wildcard re-exports (já implementado)
- AC6: `config/base.py:setup_logging()` JSON em production, texto em dev (já implementado)

## Definition of Done
- [x] All 6 AC met + tests pass

## Risks
- R1: schemas.py decompose quebra imports — mitigation: backward compat re-exports

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | YOLO: AC5+AC6 verificados (já implementados). Status Draft→InProgress. | @dev |
| 2026-04-15 | 1.2 | YOLO 5-front paralelo: AC1 (Pydantic 7t), AC2 (docgen 74 flags), AC3 (factories 22t), AC4 (xdist loadfile). Status→InReview. | @dev |
