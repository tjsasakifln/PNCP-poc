# STORY-CIG-FE-17 — observatorio-page — `Cannot find module .../observatorio/[mes]-[ano]/page` (Next dynamic route)

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/app/observatorio-page.test.tsx` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● parseSlug — slug parsing › slug válido retorna mes e ano corretos

Cannot find module '../../app/observatorio/[mes]-[ano]/page' from '__tests__/app/observatorio-page.test.tsx'

    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    // __tests__/app/observatorio-page.test.tsx:55

(7 tests failing — all fail on same import)
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Route `app/observatorio/[mes]-[ano]/page.tsx` foi renomeada, removida, ou o slug composto `[mes]-[ano]` foi refatorado (possível conflito Next.js — ver memory/MEMORY.md "nextjs-slug-conflict-lesson" + STORY-428). Verificar estrutura atual de `app/observatorio/`. Se rota foi renomeada, atualizar import no teste. Se foi removida, decidir entre deletar teste OU recriar página.

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/app/observatorio-page.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/app/observatorio-page.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/app/observatorio-page.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/app/observatorio-page.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `app/observatorio/ (estrutura atual)`
- `__tests__/app/observatorio-page.test.tsx`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. AC testáveis, escopo claro, dependências mapeadas. Causa raiz a confirmar em Implement conforme política zero-quarentena do epic.
