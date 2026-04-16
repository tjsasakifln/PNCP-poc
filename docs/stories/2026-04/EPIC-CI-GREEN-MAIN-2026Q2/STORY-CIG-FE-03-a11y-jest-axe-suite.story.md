# STORY-CIG-FE-03 — a11y/jest-axe-suite — módulo `jest-axe` ausente bloqueia suite

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker (bloqueia verificação de a11y em outras suítes)
**Effort:** XS (<1h) para adicionar dep + S (1-3h) se a suíte revelar issues de a11y reais
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/a11y/jest-axe-suite.test.tsx` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● Test suite failed to run

Cannot find module 'jest-axe' from '__tests__/a11y/jest-axe-suite.test.tsx'

  at Resolver._throwModNotFoundError (node_modules/jest-resolve/build/resolver.js:427:11)
  at Object.<anonymous> (__tests__/a11y/jest-axe-suite.test.tsx:186:18)
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Dependência `jest-axe` foi removida de `package.json` (ou nunca adicionada após merge da suite). Fix: `npm install --save-dev jest-axe @types/jest-axe` + garantir setup em `jest.setup.js`. Depois que roda, a suite pode revelar a11y violations reais — cada violation vira sub-issue (não skip).

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/a11y/jest-axe-suite.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/a11y/jest-axe-suite.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/a11y/jest-axe-suite.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/a11y/jest-axe-suite.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `frontend/package.json`
- `frontend/jest.setup.js`
- `__tests__/a11y/jest-axe-suite.test.tsx`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
