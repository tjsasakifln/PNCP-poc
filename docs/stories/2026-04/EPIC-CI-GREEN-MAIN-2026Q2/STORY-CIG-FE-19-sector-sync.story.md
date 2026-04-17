# STORY-CIG-FE-19 — sector-sync — `SETORES_FALLBACK` não encontrado em `app/buscar/hooks/useSearchFilters.ts`

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/sector-sync.test.ts` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● Sector Sync (STORY-249) › AC5: SETORES_FALLBACK has same number of sectors as backend

Error: Could not find SETORES_FALLBACK in D:\pncp-poc\frontend\app\buscar\hooks\useSearchFilters.ts

  at parseSectorsFromFile (__tests__/sector-sync.test.ts:31)

(5 tests failing — all fail reading same file)
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Constante `SETORES_FALLBACK` foi movida de `app/buscar/hooks/useSearchFilters.ts` para outro arquivo (ver `scripts/sync-setores-fallback.js` que edita `frontend/app/buscar/page.tsx`). Teste está lendo arquivo errado. Fix: atualizar `FALLBACK_PATH` em `sector-sync.test.ts` para refletir arquivo correto onde a constante vive hoje.

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/sector-sync.test.ts` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/sector-sync.test.ts` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/sector-sync.test.ts` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/sector-sync.test.ts` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `__tests__/sector-sync.test.ts`
- `app/buscar/page.tsx (provável local de SETORES_FALLBACK)`
- `scripts/sync-setores-fallback.js (ref)`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-07 (mesma lista de fallback, teste diferente)


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
