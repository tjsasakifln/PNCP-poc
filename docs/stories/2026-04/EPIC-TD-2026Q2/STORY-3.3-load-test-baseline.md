# STORY-3.3: Load Test Baseline (k6/Grafana) (TD-QA-060)

**Priority:** P1 (sem baseline, perf improvements são narrativos)
**Effort:** S (8-16h)
**Squad:** @qa + @devops + @architect
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 2

---

## Story

**As a** SmartLic,
**I want** baseline de performance mensurável (RPS, latency, error rate) via k6 + Grafana,
**so that** improvements de TD-SYS-014 (LLM async) e TD-SYS-003 (Railway timeout) sejam verificáveis objetivamente.

---

## Acceptance Criteria

### AC1: k6 scripts

- [ ] `tests/load/buscar.k6.js` — POST /buscar 50 RPS por 5 min
- [ ] `tests/load/dashboard.k6.js` — GET /analytics 100 RPS por 5 min
- [ ] `tests/load/sse.k6.js` — SSE concurrent 50 connections

### AC2: Grafana dashboard

- [ ] Dashboard "SmartLic Load Test Baseline" com:
  - Latency p50, p95, p99
  - RPS sustained
  - Error rate
  - Throughput
- [ ] Snapshot baseline 2026-04-14

### AC3: Documentation

- [ ] `docs/performance/load-test-baseline.md` documenta:
  - Como rodar k6 scripts
  - Como interpretar resultados
  - Baseline numbers (referência)

### AC4: CI integration (optional)

- [ ] Workflow `.github/workflows/load-test.yml` weekly run
- [ ] Comparison vs baseline; alert se >20% degradation

---

## Tasks / Subtasks

- [ ] Task 1: Setup k6 local + Cloud account
- [ ] Task 2: Scripts (AC1)
- [ ] Task 3: Run baseline
- [ ] Task 4: Grafana dashboard (AC2)
- [ ] Task 5: Documentation (AC3)
- [ ] Task 6: CI workflow (AC4)

## Dev Notes

- k6 free tier suporta 50 VUs cloud
- Endpoints test: usar staging, não prod
- Auth: pre-generate 10 test user JWTs

## Testing

- Smoke: k6 script roda + Grafana shows data

## Definition of Done

- [ ] Scripts + dashboard + baseline + docs

## Risks

- **R1**: Load test em staging diff de prod (specs Railway) — mitigation: usar prod staging tier idêntico

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
