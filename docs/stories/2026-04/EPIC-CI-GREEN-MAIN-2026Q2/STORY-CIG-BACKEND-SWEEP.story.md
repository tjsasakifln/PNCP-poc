# STORY-CIG-BACKEND-SWEEP — Backend Sweep — auditar 292 pre-existing failures + criar stories filhas

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Meta-story
**Effort:** L (1-2 dias — triage completo dos 292)
**Agents:** @dev, @qa, @devops

---

## Contexto

Meta-story de triage — não tem suíte única. O insumo bruto foi gerado via `python scripts/run_tests_safe.py --parallel 4` em 2026-04-16 (exit 1):

```
Running 435 test files (timeout=120s, parallel=4)

FAILED files (133):
- 424 falhas individuais contadas nos arquivos cujo sumário reporta N failures
- 133 arquivos com pelo menos 1 falha
- Drift de +132 vs. baseline historica de memory/MEMORY.md (292 pre-existing em 2026-03-22)

Top arquivos por N failures:
  18 tests\test_sse_last_event_id.py
  17 tests\test_story364_excel_resilience.py
  13 tests\test_alerts.py
  13 tests\test_timeout_chain.py
  11 tests\test_crit052_canary_false_positive.py
  11 tests\test_debt017_database_optimization.py
   9 tests\test_debt110_backend_resilience.py
  ...
```

**Enumeração bruta completa** (133 arquivos, 424 falhas): ver `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/backend-failure-triage-raw.md` (gerado pelo @sm em 2026-04-16). Este arquivo é **insumo** — a triage taxonômica é trabalho do @dev em Implement.

**Hipótese inicial de causa raiz (a confirmar em Implement):** Mix esperado dos 424 (drift acima da baseline 292 sugere múltiplas regressões recentes não atribuídas): (a) testes que exigem Supabase live / Redis real (movem para integration-external.yml); (b) drift de mock após refactor de produção (fix inline); (c) flakiness em testes SSE/async (investigar timing); (d) bugs reais de produção escondidos atrás de "pre-existing". Top 5 (SSE last-event-id, Excel resilience, alerts, timeout chain, canary false positive) sugerem forte contribuição de (b) + (c) — investigar primeiro.

---

## Acceptance Criteria

- [ ] AC1: Doc `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/backend-failure-triage.md` criado. Lista completa dos **424 testes** (corrigido — memory estava desatualizada em 292) com, para cada um: (path do teste, mensagem de erro principal, categoria, verdict). Usar `backend-failure-triage-raw.md` como ponto de partida.
- [ ] AC2: Cada teste tem verdict em uma das 4 categorias: `fix-inline` | `story-filha` | `move-to-integration-external` | `reopened-bug` (bug real de produção).
- [ ] AC3: Para cada teste com verdict `move-to-integration-external`, justificativa técnica documentada (ex.: "requer Supabase live schema; não mockável sem copiar migrations completas"). Verdict sem justificativa é inaceitável.
- [ ] AC4: Stories filhas `STORY-CIG-BE-NN-<slug>.story.md` criadas no próximo ciclo de `@sm` (não nesta sessão — esta é meta-story de triage). Cada story filha segue template padrão AC1-5.
- [ ] AC5 (NEGATIVO): Nenhum `@pytest.mark.skip` ou `pytest.skip()` introduzido durante o triage. `pytest --collect-only` no final do epic conta o mesmo número de testes da baseline (7656 pass + 424 fail ≈ 8080 executáveis, a validar com contagem real da baseline atual), provando que nada foi silenciosamente pulado.
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
- **2026-04-16** — @po: *validate-story-draft GO (7/10) — Draft → Ready. Meta-story de triage; Investigation Checklist contém artefatos de template (N/A) — @dev deve seguir ACs diretamente, não o checklist padrão de test suite.
