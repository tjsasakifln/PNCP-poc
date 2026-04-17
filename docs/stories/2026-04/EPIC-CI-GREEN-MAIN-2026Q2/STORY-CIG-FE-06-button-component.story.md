# STORY-CIG-FE-06 — button-component — DEBT-006 AC4: signup/planos não importam Button compartilhado

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/button-component.test.tsx` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● DEBT-006 AC4: Shared Button adoption across pages › signup/page.tsx imports Button from components/ui/button

expect(received).toContain(expected) // indexOf
Expected substring: "components/ui/button"
Received string: (conteúdo de signup/page.tsx sem import de components/ui/button)

● DEBT-006 AC4: ... planos/page.tsx imports Button from components/ui/button
(mesma falha — planos/page.tsx também não adotou)
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** DEBT-006 exigia que todas as páginas usassem `components/ui/button` compartilhado. signup e planos não foram migrados (ou foram revertidos). Fix: migrar imports nessas 2 páginas (cumprindo AC original) — NÃO relaxar o teste. Verificar se há outras páginas silenciosamente não-conformes.

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/button-component.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/button-component.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/button-component.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/button-component.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `app/signup/page.tsx`
- `app/planos/page.tsx`
- `__tests__/button-component.test.tsx`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. AC testáveis, escopo claro, dependências mapeadas. Causa raiz a confirmar em Implement conforme política zero-quarentena do epic.
