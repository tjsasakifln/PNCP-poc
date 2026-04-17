# STORY-CIG-FE-10 — chromatic visual-regression — módulo `@chromatic-com/playwright` ausente + decisão de gate

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P2 — decisão de gate
**Effort:** S (1-3h) — inclui decisão arquitetural
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `tests/chromatic/visual-regression.spec.ts` roda em `frontend-tests.yml + chromatic.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● Test suite failed to run

Cannot find module '@chromatic-com/playwright' from 'tests/chromatic/visual-regression.spec.ts'

  at tests/chromatic/visual-regression.spec.ts:28
    import { test } from '@chromatic-com/playwright';
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Dependência `@chromatic-com/playwright` não está em `package.json` — ou foi removida ou nunca foi adicionada. Também: este arquivo é **Playwright spec**, não Jest test — jest está tentando rodar um `.spec.ts` de Playwright. **Decisão requerida:** (a) excluir `tests/chromatic/` do jest testMatch (corrige gate jest); (b) adicionar dep `@chromatic-com/playwright`; (c) ambos. A suíte deve rodar em `chromatic.yml` (Playwright), NÃO em jest.

---

## Acceptance Criteria

- [ ] AC1: `tests/chromatic/visual-regression.spec.ts` **deixa de ser coletado por Jest** — `npx jest --listTests | grep chromatic` retorna vazio; `npm test` passa sem tentar executar este arquivo. Se a dep `@chromatic-com/playwright` for instalada, execução real deve rodar em `chromatic.yml` via Playwright, não em Jest. Evidência: `npm test` local sem failures ou skips relacionados a esta suíte.
- [ ] AC2: Última run do workflow `frontend-tests.yml + chromatic.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" tests/chromatic/visual-regression.spec.ts` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- tests/chromatic/visual-regression.spec.ts` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" tests/chromatic/visual-regression.spec.ts` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `frontend/jest.config.js (testPathIgnorePatterns)`
- `frontend/package.json`
- `tests/chromatic/visual-regression.spec.ts`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) condicional — AC1 reescrito por @po: critério original contraditório (npm test com --passWithNoTests banido pela política do epic). Novo AC1: arquivo deve deixar de ser coletado por Jest; execução real via Playwright no chromatic.yml. Draft → Ready.
