# STORY-BTS-006 — Search Pipeline & Async Flow (13 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1
**Effort:** S (2-3h)
**Agents:** @dev + @qa
**Status:** Ready

---

## Contexto

13 testes cobrindo o fluxo async de `/buscar` (CRIT-072 async-first), contracts de resposta, precision/recall do datalake (Layer 1), e progressive results (entrega parcial antes do complete).

---

## Arquivos (tests)

- `backend/tests/test_search_async.py` (5 failures)
- `backend/tests/test_search_contracts.py` (3 failures)
- `backend/tests/test_search_pipeline_generate_persist.py` (2 failures)
- `backend/tests/test_progressive_results_295.py` (2 failures)
- `backend/tests/test_progressive_delivery.py` (1 failure)
- `backend/tests/test_precision_recall_datalake.py` (1 failure)
- `backend/tests/test_precision_recall_benchmark.py` (1 failure)

_Nota: precision_recall pode ter fixtures faltando; verificar se existe sample data._

---

## Acceptance Criteria

- [ ] AC1: `pytest` nos 7 arquivos acima retorna exit code 0 (13/13 PASS) com `--timeout=30`.
- [ ] AC2: CI verde.
- [ ] AC3: RCA por sub-grupo (async flow drift, progressive emit drift, datalake query shape drift).
- [ ] AC4: Cobertura não caiu; threshold precision>=85%, recall>=70% mantidos se tests de precision_recall forem tocados.
- [ ] AC5: zero quarantine.

---

## Investigation Checklist

- [ ] Para `test_search_async`: validar se `search_state_manager` state machine continua com mesmos nomes de estados
- [ ] Para `test_search_contracts`: re-gerar `frontend/app/api-types.generated.ts` e ver se schema drift
- [ ] Para `test_progressive_*`: validar mock de SSE `emit_partial`/`emit_complete`

---

## Dependências

- **Bloqueado por:** BTS-001 (quota), BTS-002 (pipeline), BTS-005 (consolidation)
- **Bloqueia:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready.
- **2026-04-19** — @po (Pax): Validação GO — 7/10. Gaps: P4 escopo, P7 valor, P8 riscos. Story confirmada Ready.
