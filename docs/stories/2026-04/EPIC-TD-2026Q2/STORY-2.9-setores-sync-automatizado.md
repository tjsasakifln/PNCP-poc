# STORY-2.9: Setores Backend↔Frontend Sync Automatizado (TD-SYS-012)

**Priority:** P1 (frontend stale se sync manual esquecido)
**Effort:** XS (4h)
**Squad:** @dev + @architect quality gate
**Status:** Ready for Review
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

- [x] `useSearchSectorData.ts` (consumido por `/buscar`) faz fetch direto de `/api/setores` (proxy ao backend `/v1/setores`)
- [x] Cache local 24h via `getCachedSectors`/`cacheSectors` (sectorData.ts) — equivalente funcional ao SWR
- [x] Fallback `SETORES_FALLBACK` preservado apenas para offline/error após 2 retries

### AC2: CI gate

- [x] GitHub Action `.github/workflows/setores-sync-check.yml` roda mensal (cron `0 9 1 * *`) + workflow_dispatch + PRs em arquivos relevantes
- [x] Sobe backend, compara `SETORES_FALLBACK` (sectorData.ts) vs `/v1/setores` — exit 1 em qualquer drift; abre issue auto via github-script

### AC3: Script melhorado

- [x] `scripts/sync-setores-fallback.js` aceita `--check` (read-only, exit 1 em drift) + JSON estruturado para CI parse + lê `BACKEND_URL` do env

---

## Tasks / Subtasks

- [x] Task 1: Audit `SETORES_FALLBACK` usage (5 callsites mapeados)
- [x] Task 2: Frontend já consumia `/api/setores` via useSearchSectorData (AC1 OK)
- [x] Task 3: Add CI gate `setores-sync-check.yml` (AC2)
- [x] Task 4: Test --check flag + workflow YAML válido (13 testes)

## Dev Notes

- Endpoint backend `/setores` já existe
- Script `scripts/sync-setores-fallback.js` em uso

## Testing

- jest mock `/setores` response
- E2E: load `/buscar` offline → fallback funciona

## Definition of Done

- [x] Runtime fetch ativo (já era — confirmado)
- [x] CI gate criado (`setores-sync-check.yml`)
- [x] Fallback testado (13 testes passando)

## Dev Agent Record

### File List

- `scripts/sync-setores-fallback.js` (modified) — flag `--check` + `BACKEND_URL` env + JSON output
- `.github/workflows/setores-sync-check.yml` (new) — cron mensal + auto-open issue em drift
- `frontend/__tests__/story-2-9-setores-sync.test.ts` (new) — 13 testes (AC1+AC2+AC3)

## Risks

- **R1**: Backend `/setores` lento → mitigation: SWR + cache 1h

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — --check flag + monthly workflow + tests | @dev |
