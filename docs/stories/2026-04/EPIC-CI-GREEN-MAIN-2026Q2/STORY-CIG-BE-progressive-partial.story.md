# STORY-CIG-BE-progressive-partial — Partial SSE emite 1 vs 8 eventos; event_counter drift — 5 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
**Priority:** P1 — Gate (regressão SSE UX)
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Três suítes que cobrem entrega progressiva/partial de SSE rodam em `backend-tests.yml` e falham em **5 testes** do triage row #16/30. Causa raiz classificada como **assertion-drift**: o partial SSE (CRIT-071, STORY-295) agora emite 1 evento em vez de 8 esperados — ou o event_counter foi refatorado.

STORY-295 (progressive results) e CRIT-071 (partial data SSE) são garantias de UX — resultados parciais por UF chegam ao cliente conforme cada source completa. Regressão aqui é visível para usuário final.

**Arquivos principais afetados:**
- `backend/tests/test_progressive_results_295.py`
- `backend/tests/test_crit071_partial_data_sse.py`
- `backend/tests/test_progressive_delivery.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Possível **prod-bug**: refactor pode ter acidentalmente consolidado 8 eventos em 1. Validar com `git log -p backend/progress.py backend/search_pipeline.py`.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_progressive_results_295.py backend/tests/test_crit071_partial_data_sse.py backend/tests/test_progressive_delivery.py -v` retorna exit code 0 localmente (**37/37 PASS**, dos quais 5 eram os falhos do triage #16/30).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 3 suítes com **0 failed / 0 errored**. Link no Change Log. *(pendente de push por @devops)*
- [x] AC3: Causa raiz documentada em "Root Cause Analysis" abaixo — verdito **(a) assertion-drift benigna** com 4 mudanças de semântica independentes e rastreadas a stories/refactors prévios (UX-428, HARDEN-017, STORY-362, ISSUE-027). **Nenhum prod-bug detectado**; nenhuma regressão CRIT-071/STORY-295.
- [x] AC4: Nenhuma mudança de produção — somente assertions de teste foram atualizadas, logo cobertura backend não pode ter caído. Threshold 70% mantido por construção.
- [x] AC5 (NEGATIVO): grep por `@pytest.mark.skip|pytest.skip(|@pytest.mark.xfail|.only(` nos 3 arquivos retorna vazio (exit=1, nenhum match).

---

## Root Cause Analysis

**Verdito: (a) assertion-drift benigna.** Cinco testes, quatro semânticas independentes evoluídas em produção; zero prod-bug. O código de `backend/progress.py`, `backend/consolidation/` e `backend/routes/search_state.py` segue implementando CRIT-071 / STORY-295 corretamente — os testes é que envelheceram.

### Failure → prod-source map

| # | Test | Assertion falha | Prod source da evolução | Tipo |
|---|------|-----------------|-------------------------|------|
| 1 | `test_progressive_results_295.py::test_fast_source_emits_partial_before_slow_completes` | `result.total_after_dedup == 8` devolveu 1 | **ISSUE-027** — title-prefix fuzzy dedup (`consolidation/dedup.py::_deduplicate_by_title_prefix`) colapsa registros cujo `objeto` compartilha o mesmo prefixo de 60 chars. O helper `_make_record` usava `objeto="Material de limpeza"` fixo. | Dados de teste insuficientes. |
| 2 | `test_progressive_results_295.py::test_one_source_fails_others_deliver` | `result.total_after_dedup == 3` devolveu 1 | Mesma dedup ISSUE-027 — mesmos 3 registros com objeto idêntico colapsaram em 1. | Mesma causa do #1. |
| 3 | `test_progressive_results_295.py::test_tracker_emit_source_error` | `event.detail["error"] == "Connection refused"` recebeu `"PORTAL_COMPRAS: erro temporário"` | **UX-428 AC3** — `_sanitize_source_error` (progress.py:33-55) mapeia erros técnicos brutos para mensagens user-friendly antes de emitir SSE. Mudança intencional de UX. | Contrato de API evoluiu. |
| 4 | `test_crit071_partial_data_sse.py::test_emit_partial_data_increments_event_counter` | `len(tracker._event_history) == 2` era 0 | **HARDEN-017 AC2/AC3** — `_emit_event` (progress.py:217-222) exclui deliberadamente eventos `partial_data` de `_event_history` (ring buffer de replay) porque cada payload pode passar de 10KB. Contador monotônico continua incrementando; só o replay buffer é que ignora. | Contrato de replay evoluiu. |
| 5 | `test_progressive_delivery.py::TestBackgroundResultsStore::test_ttl_expiry` | `get_background_results(...)` devolveu resposta em vez de `None` | **STORY-362 AC1** — `_RESULTS_TTL` subiu de `600s` → `3600s` em `routes/search_state.py:34`. O teste forçava `stored_at = now - 700`, que agora está **dentro** do TTL. | Budget TTL tunado. |

### Por que não é prod-bug

- A hipótese inicial da story era "refactor consolidou 8 eventos em 1" (regressão SSE UX). O debug provou que o `on_source_done` callback continua sendo chamado **uma vez por source** (2 calls no teste #1), cada um com `count == 5` e `count == 3` respectivamente — a entrega progressiva está intacta. O `1` que o teste assertava era `total_after_dedup` (pós-dedup cross-org), não contagem de eventos SSE.
- `_event_counter` continua monotônico e igual ao número de `emit_partial_data` chamados (1, 2). A única mudança é que esses eventos não entram no ring buffer de replay — comportamento documentado em HARDEN-017.
- Nenhum teste de CRIT-071 ou STORY-295 que cobre o happy path (entrega progressiva de dados parciais por UF para cliente SSE) falhou. Zero coordenação com frontend (`EnhancedLoadingProgress`, `LoadingProgress`) necessária.

### Correção aplicada (apenas nos testes)

1. `_make_record` default agora gera `objeto` único por `(source_name, source_id)` para não colidir com título-prefix dedup. Docstring explica o porquê para evitar re-regressão.
2. `test_tracker_emit_source_error` importa `_sanitize_source_error` e compara contra o valor esperado computado, documentando o contrato UX-428 em vez de hard-codar a string final.
3. `test_emit_partial_data_increments_event_counter` mantém as asserções de counter (== 1, == 2) e passa a asserrir `len(_event_history) == 0` com comentário que explicita HARDEN-017 AC2/AC3.
4. `test_ttl_expiry` importa `_RESULTS_TTL` e expira via `stored_at = now - (_RESULTS_TTL + 100)` — future-proof para qualquer nova revisão do TTL.

---

## Investigation Checklist (para @dev, fase Implement)

- [x] Rodar as 3 suítes isoladas. `37 passed in 17.60s`.
- [x] Inspecionar `backend/progress.py`, `backend/consolidation/dedup.py`, `backend/routes/search_state.py` para identificar a semântica atual dos 4 pontos drift.
- [x] Confirmar ausência de prod-bug: entrega progressiva (CRIT-071/STORY-295) intacta, zero coordenação com frontend necessária.
- [x] Cobertura não regrediu — zero prod code alterado.
- [x] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #16/30)

## Stories relacionadas no epic

- STORY-CIG-BE-sse-redis-pool-refactor (#1 — mesma área SSE)
- STORY-CIG-BE-sse-last-event-id (#3 — mesma área SSE)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #16/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. **Atenção @po:** investigar prod-bug (regressão CRIT-071/STORY-295) vs drift benigna.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. Se @dev confirmar (b) prod-bug, coordenar com frontend (`EnhancedLoadingProgress`, `LoadingProgress`) antes de merge; UX visível.
- **2026-04-18** — @dev (Dex): implementação concluída. Verdito **(a) assertion-drift benigna** — 5 testes, 4 semânticas evoluídas independentes (ISSUE-027 title-prefix dedup, UX-428 error sanitization, HARDEN-017 partial_data replay exclusion, STORY-362 TTL 600s→3600s). Zero prod code alterado. `pytest tests/test_progressive_results_295.py tests/test_crit071_partial_data_sse.py tests/test_progressive_delivery.py -v` → **37 passed in 17.60s** (era 5 failed / 32 passed). Grep de skip markers vazio. Status Ready → InReview. Aguarda @qa *qa-gate e @devops push/PR.

## File List

- `backend/tests/test_progressive_results_295.py` — helper `_make_record` passa a gerar `objeto` único por registro (evita colisão com title-prefix dedup ISSUE-027); `test_tracker_emit_source_error` importa `_sanitize_source_error` e compara contra o valor esperado computado (UX-428).
- `backend/tests/test_crit071_partial_data_sse.py` — `test_emit_partial_data_increments_event_counter` passa a asserrir `len(_event_history) == 0` para eventos `partial_data` (HARDEN-017 AC2/AC3), com comentário documentando o contrato.
- `backend/tests/test_progressive_delivery.py` — `test_ttl_expiry` importa `_RESULTS_TTL` e expira via `stored_at = now - (_RESULTS_TTL + 100)` para ficar robusto a tuning futuro do TTL (STORY-362).
- `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/STORY-CIG-BE-progressive-partial.story.md` — este arquivo: RCA, ACs [x], File List, Status.
