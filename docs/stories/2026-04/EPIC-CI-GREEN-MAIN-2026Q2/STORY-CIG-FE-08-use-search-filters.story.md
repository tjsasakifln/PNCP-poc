# STORY-CIG-FE-08 — useSearchFilters — ufsSelecionadas inicializa vazio (size 0) quando deveria ter default

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/hooks/useSearchFilters.test.ts` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● useSearchFilters hook › Initialization › should initialize with default values
expect(received).toBeGreaterThan(expected)
Expected: > 0
Received:   0
  expect(result.current.ufsSelecionadas.size).toBeGreaterThan(0); // Default SC, PR, RS

● UF selection › should toggle UF
Expected: true (ufsSelecionadas.has('SP'))
Received: false

● Validation › should allow search when valid
Expected: true (canSearch)
Received: false
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Default state do hook `useSearchFilters` mudou — antes inicializava com UFs (SC/PR/RS ou SP). Agora começa vazio, forçando usuário a escolher explicitamente. Isso é **decisão UX intencional** (STORY-???) ou **bug**? Verificar commits recentes em `useSearchFilters.ts`. Se intencional, teste é obsoleto e deve ser reescrito para refletir novo comportamento.

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/hooks/useSearchFilters.test.ts` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/hooks/useSearchFilters.test.ts` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/hooks/useSearchFilters.test.ts` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/hooks/useSearchFilters.test.ts` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `__tests__/hooks/useSearchFilters.test.ts`
- `app/buscar/hooks/useSearchFilters.ts`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-07 (mesmo hook)


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. Investigar fix conjunto com FE-07 e FE-19 (mesmo hook). AC testáveis, escopo claro, dependências mapeadas.
