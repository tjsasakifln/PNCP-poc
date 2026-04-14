# STORY-4.5: PNCP API Breaking Change Detection Alert (TD-SYS-002)

**Priority:** P1 (recurring risk — PNCP changed page size silently in Feb 2026)
**Effort:** XS (4h)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3

---

## Story

**As a** SmartLic,
**I want** alert se PNCP API rejeita `tamanhoPagina` >50 ou response shape muda,
**so that** descobrimos breaking changes em horas (não dias).

---

## Acceptance Criteria

### AC1: Health canary com tamanhoPagina=51

- [ ] `backend/health.py` (ou novo `pncp_canary.py`) tenta `tamanhoPagina=51`
- [ ] Se HTTP 400/422 → captura como métrica `pncp_max_page_size_changed`

### AC2: Sentry alert

- [ ] Se canary falha por 3 runs consecutivos → Sentry critical
- [ ] Tag: `pncp_breaking_change`

### AC3: Response shape canary

- [ ] Compara resposta atual vs schema cached
- [ ] Diff alerta se shape change

### AC4: Documentation

- [ ] CLAUDE.md "PNCP API" section atualizado com canary + alert process

---

## Tasks / Subtasks

- [ ] Task 1: Implementar canary (AC1)
- [ ] Task 2: Sentry integration (AC2)
- [ ] Task 3: Schema diff (AC3)
- [ ] Task 4: Schedule cron (10min interval)
- [ ] Task 5: Docs (AC4)

## Dev Notes

- Resolve a lacuna identificada na Phase 1: "Health canary uses tamanhoPagina=10 — doesn't detect page size limits"
- Overlap com STORY-3.4 (contract tests) mas mais granular/frequente

## Testing

- Mock PNCP API retornando 400 → assert Sentry capture
- Smoke prod

## Definition of Done

- [ ] Canary running + alert tested + docs

## Risks

- **R1**: PNCP rate limit no canary — mitigation: low frequency (10min)

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
