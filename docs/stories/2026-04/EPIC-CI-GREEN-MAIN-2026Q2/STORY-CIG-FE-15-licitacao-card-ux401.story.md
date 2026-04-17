# STORY-CIG-FE-15 — LicitacaoCard-ux401 — suite passa local, falha em CI (snapshot ou render divergente)

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-6h — investigação CI)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/components/LicitacaoCard-ux401.test.tsx` roda em `frontend-tests.yml` e falha com diff de snapshot. Erro real capturado do CI run `24539387474` (job `71741727431`, PR #372, 2026-04-16):

```
FAIL __tests__/components/LicitacaoCard-ux401.test.tsx

  UX-401: Visual snapshot comparison
    ✕ card with valor=null renders correctly (20 ms)
    ✕ card with positive valor renders correctly (23 ms)

● UX-401: Visual snapshot comparison › card with valor=null renders correctly

  expect(received).toMatchSnapshot()
  Snapshot name: `UX-401: Visual snapshot comparison card with valor=null renders correctly 1`

  - Snapshot  - 1
  + Received  + 1
  @@ -123,11 +123,11 @@
         <a
-          class="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-button   hover:bg-brand-blue-hover transition-colors"
+          class="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-button hover:bg-brand-blue-hover transition-colors"
           href="https://pncp.gov.br/app/editais/12345678000190/2026/1"

    at Object.toMatchSnapshot (__tests__/components/LicitacaoCard-ux401.test.tsx:140:34)
    at Object.toMatchSnapshot (__tests__/components/LicitacaoCard-ux401.test.tsx:147:34)
```

12 sub-testes (valor=null display, currency formatting, valor=0 guards) **passam**. Apenas os 2 snapshots (`card with valor=null`, `card with positive valor`) falham — mesmo diff whitespace-only que FE-05 e FE-14.

**Hipótese inicial de causa raiz (a confirmar em Implement):** Idêntica a FE-05 e FE-14 — whitespace drift em template literal de `className` do link-CTA no `LicitacaoCard.tsx`. Stories devem ser implementadas juntas: um fix no componente + regeneração coordenada dos 3 snapshot sets resolve todas. Antes de `-u`, validar via `git log -p app/buscar/components/LicitacaoCard.tsx` que o refactor que introduziu o drift foi intencional (Prettier cleanup mais provável).

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/components/LicitacaoCard-ux401.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/components/LicitacaoCard-ux401.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.
- [ ] AC6 (snapshot): Regeneração de snapshot (`npm test -- -u`) só após análise diff-by-diff documentada em "Snapshot Diff Analysis". Se o diff reflete mudança UI não intencional, story vira bugfix — não snapshot regen.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/components/LicitacaoCard-ux401.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/components/LicitacaoCard-ux401.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## Snapshot Diff Analysis

_(preenchido por @dev em Implement apenas se AC6 aplicável)_

---

## File List (preditiva, a confirmar em Implement)

- `__tests__/components/LicitacaoCard-ux401.test.tsx`
- `__tests__/components/__snapshots__/LicitacaoCard-ux401.test.tsx.snap`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-14


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
