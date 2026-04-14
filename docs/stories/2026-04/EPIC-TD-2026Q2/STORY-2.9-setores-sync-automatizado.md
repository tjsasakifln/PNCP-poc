# STORY-2.9: Setores Backend↔Frontend Sync Automatizado (TD-SYS-012)

**Priority:** P1 (frontend stale se sync manual esquecido)
**Effort:** XS (4h)
**Squad:** @dev + @architect quality gate
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** SmartLic,
**I want** frontend consumir setores via endpoint runtime (não hardcoded fallback),
**so that** mudanças em `sectors_data.yaml` reflitam imediatamente no frontend sem sync manual.

---

## Acceptance Criteria

### AC1: Frontend usa `/setores` endpoint

- [ ] `frontend/app/buscar/page.tsx` consome `/api/setores` (proxy ao backend `/setores`)
- [ ] SWR cache 1h
- [ ] Fallback `SETORES_FALLBACK` mantido apenas pra offline/error case

### AC2: CI gate

- [ ] GitHub Action `setores-sync-check.yml` roda mensal
- [ ] Compara `SETORES_FALLBACK` vs `/setores` resposta — fail se >7 dias drift

### AC3: Script melhorado

- [ ] `scripts/sync-setores-fallback.js` mantido + adicionado ao CI

---

## Tasks / Subtasks

- [ ] Task 1: Audit `SETORES_FALLBACK` usage
- [ ] Task 2: Refactor para SWR-first (AC1)
- [ ] Task 3: Add CI gate (AC2)
- [ ] Task 4: Test offline behavior

## Dev Notes

- Endpoint backend `/setores` já existe
- Script `scripts/sync-setores-fallback.js` em uso

## Testing

- jest mock `/setores` response
- E2E: load `/buscar` offline → fallback funciona

## Definition of Done

- [ ] Runtime fetch ativo
- [ ] CI gate verde
- [ ] Fallback testado

## Risks

- **R1**: Backend `/setores` lento → mitigation: SWR + cache 1h

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
