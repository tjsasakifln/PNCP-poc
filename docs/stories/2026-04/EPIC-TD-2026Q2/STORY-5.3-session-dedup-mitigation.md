# STORY-5.3: Session Dedup Eventual Consistency Mitigation (TD-SYS-013)

**Priority:** P2 | **Effort:** M (16h) | **Squad:** @dev + @architect | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** usuário SmartLic, **I want** menos duplicatas em busca consolidada, **so that** confiança nos resultados aumente.

## Acceptance Criteria
- [ ] AC1: `consolidation.py` adiciona dedup adicional via fuzzy match (orgao_cnpj + objeto_compra similarity)
- [ ] AC2: Threshold configurável via env `DEDUP_FUZZY_THRESHOLD` (default 0.85)
- [ ] AC3: Métrica `dedup_fuzzy_hits_total`
- [ ] AC4: User feedback negativo de duplicate < 1% (medir 30d post-deploy)

## Tasks
- [ ] Audit dedup atual
- [ ] Implement fuzzy (Levenshtein ou similar)
- [ ] Métrica
- [ ] A/B test em staging

## Dev Notes
- Atual: dedup por `numeroControlePNCP` + hash exato
- TD-SYS-013 ref

## Definition of Done
- [ ] Fuzzy active + metrics show reduction

## Risks
- R1: Falso positivo → bid legítimo escondido — mitigation: threshold conservador

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
