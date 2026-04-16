# STORY-CIG-FE-14 — LicitacaoCard-ux400 — suite passa local, falha em CI (snapshot ou render divergente)

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-6h — investigação CI)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/components/LicitacaoCard-ux400.test.tsx` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
[Local em 2026-04-16: suíte PASSOU com .npmrc legacy-peer-deps.]
[CI run 24539387474 em PR #372: suíte apareceu vermelha.]

Investigação necessária: reproduzir em ambiente CI (Node 20, Ubuntu, jsdom). Verificar snapshot files commitados vs gerados em CI.
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Snapshot drift entre Windows local e Ubuntu CI (LF vs CRLF, font rendering, CSS resolution). OU componente LicitacaoCard sofreu refactor visual mergeado e snapshot não foi atualizado em PR origem. **Não regenerar sem análise.**

---

## Acceptance Criteria

- [ ] AC1: `npm test -- __tests__/components/LicitacaoCard-ux400.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [ ] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/components/LicitacaoCard-ux400.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.
- [ ] AC6 (snapshot): Regeneração de snapshot (`npm test -- -u`) só após análise diff-by-diff documentada em "Snapshot Diff Analysis". Se o diff reflete mudança UI não intencional, story vira bugfix — não snapshot regen.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/components/LicitacaoCard-ux400.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/components/LicitacaoCard-ux400.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## Snapshot Diff Analysis

_(preenchido por @dev em Implement apenas se AC6 aplicável)_

---

## File List (preditiva, a confirmar em Implement)

- `__tests__/components/LicitacaoCard-ux400.test.tsx`
- `__tests__/components/__snapshots__/LicitacaoCard-ux400.test.tsx.snap`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-15 (LicitacaoCard-ux401 — mesmo componente)


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
