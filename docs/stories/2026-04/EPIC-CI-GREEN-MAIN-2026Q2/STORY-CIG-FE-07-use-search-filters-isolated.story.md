# STORY-CIG-FE-07 — useSearchFilters-isolated — SETORES_FALLBACK esperava 16 setores, tem 20

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/hooks/useSearchFilters-isolated.test.tsx` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● useSearchFilters (isolated) › uses cached sectors when fresh
TypeError: Cannot read properties of undefined (reading 'id')
  at __tests__/hooks/useSearchFilters-isolated.test.tsx:157
    expect(result.current.setores[0].id).toBe("cached");

● useSearchFilters (isolated) › SETORES_FALLBACK contains 16 sectors
expect(received).toHaveLength(expected)
Expected length: 16
Received length: 20
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Lista SETORES_FALLBACK cresceu de 16 para 20 setores (evolução legítima — SmartLic agora tem 15+ setores em `sectors_data.yaml`). Teste não foi atualizado. Decisão: atualizar expected length para `SETORES.length` dinâmico (não hardcode), ou manter hardcode se baseline declarada. Segundo erro (undefined `.id`) indica SWR fallback vazio — investigar separadamente.

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/hooks/useSearchFilters-isolated.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/hooks/useSearchFilters-isolated.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/hooks/useSearchFilters-isolated.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/hooks/useSearchFilters-isolated.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `__tests__/hooks/useSearchFilters-isolated.test.tsx`
- `app/buscar/hooks/useSearchFilters.ts`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-08 (mesmo hook, mesmo drift) — investigar fix conjunto
- STORY-CIG-FE-19 (SETORES_FALLBACK em arquivo diferente)


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
