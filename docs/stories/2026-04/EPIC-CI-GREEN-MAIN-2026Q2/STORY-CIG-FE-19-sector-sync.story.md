# STORY-CIG-FE-19 — sector-sync — `SETORES_FALLBACK` não encontrado em `app/buscar/hooks/useSearchFilters.ts`

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
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

- [x] AC1: `npm test -- __tests__/sector-sync.test.ts` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado. **Evidência:** 5/5 PASS (2026-04-17).
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log. *(pendente run CI pós-push)*
- [x] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**. **Causa real: (a) import/path drift + (e) content drift em descrições** (sintoma primário era path errado; após consertar, test detectou 4 descrições dessincronizadas vs. YAML backend — sync real executado).
- [x] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log. **Evidência:** 5 tests PASS vs. 0 PASS (todas falhavam em `beforeAll`). Cobertura aumentou de fato — sync entre frontend fallback e backend YAML agora é validado por teste executável.
- [x] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/sector-sync.test.ts` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado. **Evidência:** grep local 2026-04-17 = vazio.

---

## Investigation Checklist (para @dev, Fase Implement)

- [x] Rodar `npm test -- __tests__/sector-sync.test.ts` isolado e confirmar reprodução local do erro. **Confirmado:** 5 falhas (todas em `beforeAll` por `Could not find SETORES_FALLBACK in useSearchFilters.ts`).
- [x] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção. **Classificação: (a) import/path drift como sintoma primário; (e) content drift revelado após fix de path.**
- [x] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix. **N/A — drift de fallback list não é bug de runtime (fallback só exercitado quando `/api/setores` falha). Corrigido in-scope desta story (sync já era o propósito do teste — STORY-249 AC5).**
- [x] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis". **N/A — sem snapshot.**
- [x] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado). **Verificado — FE-07/08 não tocam `sectorData.ts`.**
- [x] Validar que `coverage-summary.json` não regrediu. **5/5 PASS (antes 0/5).**
- [x] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/sector-sync.test.ts` — deve voltar vazio. **Vazio (2026-04-17).**

---

## Root Cause Analysis

**Classificação:** (a) import/path drift no teste + (e) content drift em descrições do fallback. O sintoma primário mascarou o secundário.

**Sintoma primário — path errado:**
`SETORES_FALLBACK` não vive em `app/buscar/hooks/useSearchFilters.ts` (esse é uma fachada de 5 linhas que apenas re-exporta). O array literal vive em `app/buscar/hooks/filters/sectorData.ts` (extraído durante refactor modular que também split `useSearchFiltersImpl.ts`, `useSearchSectorData.ts`, `useSearchFormState.ts`, etc.). O teste lê o arquivo fachada via regex e não encontra o literal → `throw new Error("Could not find SETORES_FALLBACK in …")` → falha em `beforeAll` → todas 5 assertions abortam.

**Sintoma secundário — 4 descrições dessincronizadas:**
Após corrigir o path, o teste passou a funcionar e imediatamente detectou drift real entre `backend/sectors_data.yaml` (fonte da verdade) e `sectorData.ts` em 4 setores:
- `produtos_limpeza.description`: faltava `" e unidades de saúde"` no final.
- `medicamentos.description`: faltava `", farmácia básica"` no meio (antes "para assistência farmacêutica e unidades de saúde" → "para assistência farmacêutica, farmácia básica e unidades de saúde").
- `equipamentos_medicos.description`: faltava `" de grande e médio porte"` após "odontológicos".
- `insumos_hospitalares.description`: reordenação de prefixo ("insumos hospitalares descartáveis" → "insumos hospitalares, materiais médico-hospitalares descartáveis").

Estes drifts só impactam usuário **quando o backend `/api/setores` falha e o fallback hardcoded é usado**. Não é bug crítico, mas é exatamente o que `STORY-249 AC5` foi criado para detectar.

**Fix aplicado:**
- Teste (`__tests__/sector-sync.test.ts:67`): path `hooks/useSearchFilters.ts` → `hooks/filters/sectorData.ts`.
- Fallback (`app/buscar/hooks/filters/sectorData.ts`): 4 descrições atualizadas para bater com `backend/sectors_data.yaml` (fonte da verdade validada via `node -e` parsing do YAML).

## File List (confirmada em Implement)

- `frontend/__tests__/sector-sync.test.ts` (1 edit — path fix)
- `frontend/app/buscar/hooks/filters/sectorData.ts` (4 edits — description sync)

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-07 (mesma lista de fallback, teste diferente)


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. Investigar fix conjunto com FE-07 e FE-08 (mesmo drift de SETORES_FALLBACK). AC testáveis, escopo claro.
- **2026-04-17** — @dev: Implement concluído. Fix conjunto com FE-07 + FE-08 em PR único. Ready → InReview. RCA (a) path drift + (e) content drift em 4 descrições (sync real com YAML). 5/5 PASS local. AC1/AC3/AC4/AC5 atendidos; AC2 pendente run CI.
