# STORY-CIG-BE-progressive-partial — Partial SSE emite 1 vs 8 eventos; event_counter drift — 5 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
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

- [ ] AC1: `pytest backend/tests/test_progressive_results_295.py backend/tests/test_crit071_partial_data_sse.py backend/tests/test_progressive_delivery.py -v` retorna exit code 0 localmente (5/5 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 3 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" distinguindo (a) assertion-drift benigna (semântica de partial mudou legitimamente) vs (b) prod-bug real (regressão CRIT-071/STORY-295). Se (b), adicionar teste de regressão.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 3 suítes isoladas.
- [ ] `git log -p backend/progress.py backend/search_pipeline.py | head -100`.
- [ ] Se (b) prod-bug: abrir issue P1, marcar `Status: Blocked` até decisão @po. Coordenar com frontend (`EnhancedLoadingProgress`, `LoadingProgress`).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

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
