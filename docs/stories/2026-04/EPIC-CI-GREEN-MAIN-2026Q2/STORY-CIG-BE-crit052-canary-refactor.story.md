# STORY-CIG-BE-crit052-canary-refactor — `ParallelFetchResult.canary_result` removido; `cron_status` retorna bool — 11 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_crit052_canary_false_positive.py` roda em `backend-tests.yml` e falha em **11 testes** do triage row #7/30. Causa raiz classificada como **mock-drift / assertion-drift** combinados:

1. `ParallelFetchResult.canary_result` foi removido do schema (CRIT-052 canary moveu para ARQ cron dedicado — ver STORY-4.5 PNCP Breaking Change Canary em CLAUDE.md).
2. `cron_status` agora retorna `bool` em vez de `dict` — assertions quebram.

**Arquivos principais afetados:**
- `backend/tests/test_crit052_canary_false_positive.py` (11 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Refactor legítimo pós-STORY-4.5: canary não faz mais parte do parallel fetch; virou cron background job (`backend/jobs/cron/pncp_canary.py`). Fix: atualizar testes para bater o novo contrato + remover asserções de `canary_result` no fetch pipeline.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_crit052_canary_false_positive.py -v` retorna exit code 0 localmente (11/11 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis". Referenciar STORY-4.5 como origem do refactor.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados. Canary contract assertion (STORY-4.5) continua validada em suíte própria.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_crit052_canary_false_positive.py -v` isolado.
- [ ] `grep -rn "canary_result\\|ParallelFetchResult\\|cron_status" backend/`.
- [ ] Decidir: refatorar testes para novo contrato OU mover para `backend/tests/jobs/cron/` junto com novo canary cron.
- [ ] Validar que STORY-4.5 canary (PNCP Breaking Change) continua coberta por outra suíte.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #7/30)

## Stories relacionadas no epic

- STORY-CIG-BE-consolidation-helpers-private (#10 — ParallelFetchResult vive em consolidation)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #7/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. STORY-4.5 refactor source claramente referenciado; canary contract preservation em AC5 bem definida.
