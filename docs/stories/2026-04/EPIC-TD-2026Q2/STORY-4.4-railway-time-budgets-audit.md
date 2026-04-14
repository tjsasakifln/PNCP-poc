# STORY-4.4: Railway 120s Time Budgets Audit + Tuning (TD-SYS-003)

**Priority:** P1 (Railway hard timeout sub-utilizado)
**Effort:** S (8-16h)
**Squad:** @architect + @dev + @devops
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3

---

## Story

**As a** SmartLic,
**I want** time budgets stage-wise alinhados com Railway 120s hard timeout,
**so that** requests >120s sejam evitados ou degradem graciosamente.

---

## Acceptance Criteria

### AC1: Audit timeouts

- [ ] Documentar todos timeouts: ARQ Job (300s), Pipeline (110s), Consolidation (100s), PerSource (80s), PerUF (30s), httpx (?), Gunicorn (180s)
- [ ] Identificar inconsistências com Railway 120s

### AC2: Reduce + align

- [ ] Pipeline timeout: 110s → 100s (margin de 20s antes Railway kill)
- [ ] PerSource: 80s → 70s
- [ ] PerUF: 30s → 25s
- [ ] Gunicorn: 180s → manter (Railway kill mata antes mesmo)

### AC3: Graceful degradation

- [ ] If pipeline excede 90s, return partial results + degradation banner (TD-FE atual)
- [ ] Métricas: % requests que excedem 100s

### AC4: Documentation

- [ ] CLAUDE.md "Railway/Gunicorn Critical Notes" atualizado
- [ ] Time budget waterfall diagram

---

## Tasks / Subtasks

- [ ] Task 1: Audit (AC1)
- [ ] Task 2: Adjust configs (AC2)
- [ ] Task 3: Graceful degradation logic (AC3)
- [ ] Task 4: Métricas Prometheus
- [ ] Task 5: Docs (AC4)

## Dev Notes

- CLAUDE.md "Railway/Gunicorn Critical Notes" tem detalhes
- `backend/config.py` tem timeout constants

## Testing

- Load test (STORY-3.3) verifica % requests >100s reduce
- Smoke prod canary

## Definition of Done

- [ ] Timeouts aligned + degradation tested + docs

## Risks

- **R1**: Reduce demais → user gets partial sempre — mitigation: monitoring + adjust

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
