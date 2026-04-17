# STORY-CIG-FE-08 — useSearchFilters — ufsSelecionadas inicializa vazio (size 0) quando deveria ter default

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
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

- [x] AC1: `npm test -- __tests__/hooks/useSearchFilters.test.ts` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado. **Evidência:** 30/30 PASS (2 suítes, 2026-04-17).
- [x] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log. **Evidência:** PR #379, run CI [24589958389](https://github.com/tjsasakifln/PNCP-poc/actions/runs/24589958389/job/71908401742) — `PASS __tests__/hooks/useSearchFilters.test.ts` (30/30, 0 failed / 0 errored).
- [x] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**. **Causa real: (d) drift de assertion** (testes assumem default UFs SP/SC/PR/RS que nunca existiu na branch atual — default é empty Set intencional).
- [x] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log. **Evidência:** 30 tests PASS vs. 27 PASS + 3 FAIL antes. Nenhum teste removido; teste "should toggle UF" ganhou asserção adicional (toggle OFF).
- [x] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/hooks/useSearchFilters.test.ts` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado. **Evidência:** grep local 2026-04-17 = vazio.

---

## Investigation Checklist (para @dev, Fase Implement)

- [x] Rodar `npm test -- __tests__/hooks/useSearchFilters.test.ts` isolado e confirmar reprodução local do erro. **Confirmado:** 3 falhas (ufs.size = 0; has('SP') false; canSearch false).
- [x] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção. **Classificação: (d) drift de assertion.**
- [x] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix. **N/A — decisão UX intencional confirmada em `useSearchFormState.ts:75-89`: default UFs é empty Set, populado via `smartlic-profile-context` do localStorage quando disponível.**
- [x] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis". **N/A — sem snapshot.**
- [x] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado). **Verificado — fixes independentes no mesmo PR (FE-07/08/19).**
- [x] Validar que `coverage-summary.json` não regrediu. **30/30 PASS (antes 27/30).**
- [x] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/hooks/useSearchFilters.test.ts` — deve voltar vazio. **Vazio (2026-04-17).**

---

## Root Cause Analysis

**Classificação:** (d) drift de assertion vs. implementação. Três sintomas, mesma causa:

O hook `useSearchFilters` hoje inicializa `ufsSelecionadas` como **Set vazio** (ver `frontend/app/buscar/hooks/filters/useSearchFormState.ts:75-89`). O fallback documentado é:
1. Ler `smartlic-profile-context` do localStorage — se o usuário preencheu onboarding com UFs de atuação, elas populam o Set.
2. Se ausente ou inválido → `new Set()` (vazio).

Isto é **decisão UX deliberada** (força usuário a escolher explicitamente antes da busca) — confirmada por comentário no código (`// UFs — smart default: profile context → empty (user must select explicitly)`). Não há bug de produção.

Os 3 testes falhando assumem um default antigo de SP/SC/PR/RS que nunca existiu nesta branch pós-onboarding. Fix: alinhar asserções à decisão UX atual.

**Fix aplicado (test-only):**
- L56: `toBeGreaterThan(0)` → `toBe(0)` com comentário explicando o default empty + referência ao arquivo fonte.
- L127-140 ("should toggle UF"): inverter expectativa inicial (SP **não** pré-selecionado) e adicionar segunda toggle para cobrir remover.
- L286-292 ("should allow search when valid"): selecionar SP via `toggleUf` antes de validar `canSearch=true` — caso contrário `validationErrors.ufs` marca inválido.

Zero mudança em código de produção nesta story.

## File List (confirmada em Implement)

- `frontend/__tests__/hooks/useSearchFilters.test.ts` (3 edits)

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-07 (mesmo hook)


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. Investigar fix conjunto com FE-07 e FE-19 (mesmo hook). AC testáveis, escopo claro, dependências mapeadas.
- **2026-04-17** — @dev: Implement concluído. Fix conjunto com FE-07 + FE-19 em PR único. Ready → InReview. RCA (d) drift vs. decisão UX default empty UFs. 30/30 PASS local. AC1/AC3/AC4/AC5 atendidos; AC2 pendente run CI.
- **2026-04-17** — @devops: PR #379 aberta, push via devops. Run CI 24589958389 confirma `useSearchFilters.test.ts` PASS 30/30. AC2 fechado. InReview → Done. PR gate job overall falha por 10 suítes pré-existentes mapeadas 1:1 a stories CIG-FE-01/02/04/06/09/11/12/16/17/18 (pendentes separadamente).
