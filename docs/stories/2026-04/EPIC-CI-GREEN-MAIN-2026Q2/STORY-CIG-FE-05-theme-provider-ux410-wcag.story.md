# STORY-CIG-FE-05 — ThemeProvider-ux410-wcag — suite passa local, falha em CI (ambiente divergente)

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker
**Effort:** M (3-6h, investigação de ambiente CI)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/components/ThemeProvider-ux410-wcag.test.tsx` roda em `frontend-tests.yml` e falha com diff de snapshot. Erro real capturado do CI run `24539387474` (job `71741727431`, PR #372, 2026-04-16) via `gh run view --job 71741727431 --log-failed`:

```
FAIL __tests__/components/ThemeProvider-ux410-wcag.test.tsx

● UX-410: LicitacaoCard dark mode snapshot › should render LicitacaoCard wrapped in dark ThemeProvider

  expect(received).toMatchSnapshot()
  Snapshot name: `UX-410: LicitacaoCard dark mode snapshot should render LicitacaoCard wrapped in dark ThemeProvider 1`

  - Snapshot  - 1
  + Received  + 1
  @@ -115,11 +115,11 @@
         <a
-          class="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-button   hover:bg-brand-blue-hover transition-colors"
+          class="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-button hover:bg-brand-blue-hover transition-colors"

    at Object.toMatchSnapshot (__tests__/components/ThemeProvider-ux410-wcag.test.tsx:447:18)
```

Suíte **PASSA local** (Windows/jsdom, 2026-04-16) mas **FALHA em CI** (Ubuntu). Todas as 19 sub-assertions de contraste WCAG passam — o único problema é o snapshot do wrapper dark mode. O diff é **whitespace-only**: snapshot commitado tem espaço triplo entre `rounded-button` e `hover:bg-brand-blue-hover`, versão atualmente renderizada em CI tem espaço simples.

**Hipótese inicial de causa raiz (a confirmar em Implement):** Alguém normalizou whitespace em template literal de `className` do `LicitacaoCard` (ex.: `rounded-button ${extra} hover:bg-...` quando `extra` fica vazio). Snapshots commitados não foram regenerados junto. Localmente o teste passou porque a comparação Windows pode ter tratado o whitespace diferente, ou porque a suite de local foi commitada com snapshot já drift. **Mesma causa raiz que FE-14 e FE-15** — 3 stories compartilham fix em `LicitacaoCard.tsx` + regeneração dos 3 snapshot sets. Após `git log -p app/buscar/components/LicitacaoCard.tsx` confirmar que refactor foi intencional, regenerar via `npm test -- -u` nos 3 suites.

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/components/ThemeProvider-ux410-wcag.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/components/ThemeProvider-ux410-wcag.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.
- [ ] AC6 (snapshot): Regeneração de snapshot (`npm test -- -u`) só após análise diff-by-diff documentada em "Snapshot Diff Analysis". Se o diff reflete mudança UI não intencional, story vira bugfix — não snapshot regen. Coordenar com FE-14 e FE-15 (3 snapshots compartilham mesma causa raiz — `LicitacaoCard.tsx`).

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/components/ThemeProvider-ux410-wcag.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/components/ThemeProvider-ux410-wcag.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

---

## Snapshot Diff Analysis

_(preenchido por @dev em Implement. Passos obrigatórios antes de `npm test -- -u`: (1) `git log -p app/buscar/components/LicitacaoCard.tsx` para achar commit que introduziu o whitespace cleanup; (2) verificar se esse commit foi mergeado em main; (3) verificar se regenerar é legítimo (whitespace não afeta UX observável, é apenas output de template literal); (4) apenas então rodar `-u` e commit dos 3 snapshot files atualizados.)_

---

## File List (preditiva, a confirmar em Implement)

- `__tests__/components/ThemeProvider-ux410-wcag.test.tsx`
- `jest.setup.js (polyfills)`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. AC testáveis, escopo claro, dependências mapeadas. Coordenar snapshot regen com FE-14 e FE-15 (mesma causa raiz em LicitacaoCard.tsx).
