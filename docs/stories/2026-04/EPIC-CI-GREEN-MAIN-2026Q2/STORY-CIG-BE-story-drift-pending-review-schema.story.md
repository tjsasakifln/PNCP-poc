# STORY-CIG-BE-story-drift-pending-review-schema — Campo `pending_review_count` removido/renomeado — 10 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes relacionadas a pending-review LLM zero-match rodam em `backend-tests.yml` e falham em **10 testes** do triage row #22/30. Causa raiz classificada como **assertion-drift**: o campo `pending_review_count` foi removido ou renomeado nos response schemas (STORY-354, `LLM_FALLBACK_PENDING_ENABLED=true` semantics).

CLAUDE.md anota: *"Fallback = PENDING_REVIEW on LLM failure when `LLM_FALLBACK_PENDING_ENABLED=true` (gray zone + zero-match)"*. Mudanças em naming precisam preservar esse contrato.

**Arquivos principais afetados:**
- `backend/tests/test_story354_pending_review.py`
- `backend/tests/test_llm_zero_match.py`
- `backend/tests/test_crit059_async_zero_match.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Schema em `backend/schemas.py` ou Pydantic model retornou campo com outro nome (`pending_review`, `pending`, `review_pending_count`). Validar com `grep -rn "pending_review" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_story354_pending_review.py backend/tests/test_llm_zero_match.py backend/tests/test_crit059_async_zero_match.py -v` retorna exit code 0 localmente (10/10 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 3 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (assertion-drift). Tabela antes→depois dos nomes dos campos.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido. Métricas Prometheus (`smartlic_filter_decisions_by_setor_total`, `smartlic_llm_fallback_rejects_total`) continuam sendo emitidas (CLAUDE.md).
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 3 suítes isoladas.
- [ ] `grep -rn "pending_review" backend/ | head -30` — mapear nome atual.
- [ ] Se renomeação for recente e afetar frontend (via `frontend/app/api-types.generated.ts`): coordenar com story FE apropriada ou regenerar types.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #22/30)

## Stories relacionadas no epic

- STORY-CIG-BE-filter-budget-prazo-mode (#19 — mesma área pipeline filter)
- STORY-CIG-BE-progressive-partial (#16 — área LLM/zero-match)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #22/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. Story mais sólida do lote; se rename afetar `frontend/app/api-types.generated.ts`, regenerar via `npm --prefix frontend run generate:api-types` no mesmo PR.
