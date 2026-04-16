# STORY-CIG-BACKEND-SWEEP — Backend Sweep — auditar 292 pre-existing failures + criar stories filhas

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Meta-story
**Effort:** L (1-2 dias — triage completo dos 292)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `N/A (meta-story de triage)` roda em `backend-tests.yml + tests.yml matrix` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
[memory/MEMORY.md 2026-03-22: "Backend 7656 pass / 292 pre-existing fail / 0 timeout
(352 files via run_tests_safe.py, updated 2026-03-22)"]

Estas 292 falhas foram aceitas historicamente como "pre-existing" — esta story
ANULA essa aceitação. Cada uma deve ser: (a) consertada inline, (b) gerar story filha,
(c) mover para integration-external.yml com justificativa técnica. Sem skip.
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Mix esperado (a triar): (a) testes que exigem Supabase live / Redis real (movem para integration-external.yml); (b) drift de mock após refactor de produção (fix inline); (c) flakiness (investigar race conditions / timeout); (d) bugs reais de produção que ninguém notou (prioridade P0, abrir issue).

---

## Acceptance Criteria

- [ ] AC1: Doc `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/backend-failure-triage.md` criado. Lista completa dos 292 testes com, para cada um: (path do teste, mensagem de erro principal, categoria, verdict).
- [ ] AC2: Cada teste tem verdict em uma das 4 categorias: `fix-inline` | `story-filha` | `move-to-integration-external` | `reopened-bug` (bug real de produção).
- [ ] AC3: Para cada teste com verdict `move-to-integration-external`, justificativa técnica documentada (ex.: "requer Supabase live schema; não mockável sem copiar migrations completas"). Verdict sem justificativa é inaceitável.
- [ ] AC4: Stories filhas `STORY-CIG-BE-NN-<slug>.story.md` criadas no próximo ciclo de `@sm` (não nesta sessão — esta é meta-story de triage). Cada story filha segue template padrão AC1-5.
- [ ] AC5 (NEGATIVO): Nenhum `@pytest.mark.skip` ou `pytest.skip()` introduzido durante o triage. `pytest --collect-only` no final do epic conta o mesmo número de testes da baseline (292 + 7656 = 7948), provando que nada foi silenciosamente pulado.
- [ ] AC6: Workflow `integration-external.yml` criado (se algum teste receber `move-to-integration-external`), rodando com infra provisionada (Supabase preview / Redis local via docker-compose) em schedule não-PR.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- N/A (meta-story de triage)` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" N/A (meta-story de triage)` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- _(a confirmar)_

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
