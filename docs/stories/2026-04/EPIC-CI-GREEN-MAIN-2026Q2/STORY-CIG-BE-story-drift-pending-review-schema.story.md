# STORY-CIG-BE-story-drift-pending-review-schema — Campo `pending_review_count` removido/renomeado — 10 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Blocked
**Priority:** P1 — Gate
**Effort:** S (1-3h) — underestimated; real scope M-L (revive dropped prod logic)
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

## Root Cause Analysis

**A hipótese original da story estava ERRADA.** O campo `pending_review_count` **NÃO foi removido nem renomeado**:
- `backend/schemas/search.py:922` — `pending_review_count: int = Field(...)` ainda existe no schema.
- `backend/pipeline/stages/generate.py:449` — wiring ainda lê `ctx.filter_stats.get("pending_review_count", 0)`.

**Causa raiz real:** 3 regressões de produção introduzidas quando `backend/filter.py` (monolítico) foi refatorado em `backend/filter/pipeline.py` (DEBT-110/DEBT-07). A lógica de `PENDING_REVIEW` implementada originalmente pela **STORY-354** (commit `edf6fd16`) foi **perdida** durante o refactor. O campo no schema existe mas nunca é populado.

### Evidência do regression (3 vetores independentes)

| # | Regressão | Arquivo atual | Commit original | O que foi perdido |
|---|-----------|---------------|-----------------|-------------------|
| 1 | `stats["pending_review_count"]` nunca populado | `backend/filter/pipeline.py:61-81` | `edf6fd16` | Init `stats["pending_review_count"] = 0`, bucket `resultado_pending_review: List[dict] = []`, branch `if _is_pending:` no loop de resultado LLM zero-match, exception handler roteando para `pending_review` quando `LLM_FALLBACK_PENDING_ENABLED`, merge final `resultado_keyword.extend(resultado_pending_review)` |
| 2 | `stats["zero_match_candidates"]` nunca populado | `backend/filter/pipeline.py` (todo) | CRIT-059 AC4 | `pipeline/stages/filter_stage.py:384` lê desse campo mas o filter pipeline nunca o preenche; feature `ASYNC_ZERO_MATCH_ENABLED` quebrada silenciosamente |
| 3 | Endpoint `/v1/search/{id}/zero-match` agora tem `_verify_search_ownership` (IDOR fix), testes não mockam | `backend/routes/search_status.py:329-332` | N/A | Retorna 404 "Search not found" antes de atingir `get_zero_match_results` mockado |

**Corroboração:** `backend/tests/test_crit058_zero_match_cap.py` possui **23 xfails** anotados `"CRIT-058 cap/prioritization not yet implemented in filter/core.py"` — mesma família de regression já reconhecida, nunca resolvida.

### Drift antes → depois dos campos

| Campo | Definido (schema) | Populado (pipeline) | Status |
|-------|-------------------|---------------------|--------|
| `BuscaResponse.pending_review_count` | `schemas/search.py:922` SIM | NÃO (sempre 0) | **Regressão** — existe no contrato API mas sempre retorna 0 |
| `stats["pending_review_count"]` | esperado por `generate.py:449` | NÃO | **Regressão** |
| `stats["zero_match_candidates"]` | esperado por `filter_stage.py:384` | NÃO | **Regressão** |
| `lic["_pending_review"]` | parcialmente (só ISSUE-029 circuit-breaker em `pipeline.py:1008`) | Parcial | Incompleto |
| `LLM arbiter result["pending_review"]` | `llm_arbiter/classification.py:601` SIM (gray zone: zero_match, standard, conservative) | Sim mas filter pipeline ignora | **Regressão** (retorno do arbiter não é usado) |

### Drift intencional (não é regressão)

Commit `43b24d83` (CTO action plan, 2026-03-27) **expandiu intencionalmente** o escopo de `pending_review` no LLM arbiter de apenas `zero_match` para o conjunto `{zero_match, standard, conservative}` (gray-zone completo). 1 teste (`test_llm_arbiter_reject_non_zero_match`) assume o comportamento antigo estreito — é assertion-drift legítimo, mas fora do escopo de re-viver a lógica ausente.

### Buckets de falha (13 tests failed)

| Bucket | Tests | Natureza | Fix |
|--------|-------|----------|-----|
| **A — Prod regression** | 5 em `test_story354_pending_review.py` (Test 3 `reject_non_zero_match` exceto) + 1 em `test_crit059_async_zero_match.py::test_async_enabled_collects_candidates` | Requer re-implementação em `filter/pipeline.py` | **BLOQUEADO nesta story** |
| **B — Intentional drift** | 1 — `test_llm_arbiter_reject_non_zero_match` | 1-linha (remover `standard`/`conservative` do loop) | Fixable em test, mas sozinho não atinge AC1 |
| **C — ISSUE-029 drift** | 6 em `test_llm_zero_match.py` (AC17, AC18, AC19, AC23, AC25, Edge) | Bids usam "software"/"pavimentação" agora em `negative_keywords` do vestuario → pré-filter antes do LLM | Fixable em test — trocar objetoCompra dos bids de teste para termos neutros |
| **D — IDOR drift** | 2 em `test_crit059_async_zero_match.py::TestZeroMatchEndpoint` | `_verify_search_ownership` adicionado ao endpoint | Fixable em test — mockar `_verify_search_ownership` ou popular DB/tracker |

**AC1 (exit 0) impossível sem fix de Bucket A.** Corrigir B+C+D reduz de 13→6 failures — não atinge GO gate. Task diz literalmente: *"If prod-bug detected, mark Status: Blocked and stop."*

### Escopo da follow-up story (para @sm)

Re-implementar em `backend/filter/pipeline.py` (reviver lógica de `edf6fd16` adaptada para estrutura refatorada):

1. **Init stats** (~linha 81): `stats["pending_review_count"] = 0` + `stats["zero_match_candidates"] = []`
2. **Bucket** (~linha 801, junto de `zero_match_pool`): `resultado_pending_review: List[dict] = []`
3. **ASYNC_ZERO_MATCH_ENABLED branch** (antes da chamada LLM inline): se flag ligada, popular `stats["zero_match_candidates"]` e pular classificação inline
4. **LLM result handling** (~linha 969 dentro do loop de `futures`): checar `llm_result.get("pending_review", False)` → adicionar a `resultado_pending_review` com `_pending_review=True`, `_relevance_source="pending_review"`, incrementar `stats["pending_review_count"]`
5. **Exception handler** (~linha 981): quando `LLM_FALLBACK_PENDING_ENABLED=true`, rotear para `resultado_pending_review` em vez de `stats["llm_zero_match_rejeitadas"] += 1`
6. **Merge final** (~linha 1060-1080, junto de outros `resultado_keyword.extend`): `resultado_keyword.extend(resultado_pending_review)`
7. **Integração com ISSUE-029 circuit breaker** (linhas 1006-1010): unificar com contador `pending_review_count` em vez de apenas mutar `_pending_review` sem contar

Já existe `_pending_review=True` em `pipeline.py:1008` (ISSUE-029 zero_match_high_acceptance_ratio) mas sem contagem/merge — essa é a "cola" do follow-up.

Arquivos também afetados:
- `backend/tests/test_story354_pending_review.py` — 1 linha em Test 3 (assertion-drift CTO action plan)
- `backend/tests/test_llm_zero_match.py` — trocar bid objects para termos não-negativos (6 tests)
- `backend/tests/test_crit059_async_zero_match.py` — mockar `_verify_search_ownership` (2 tests)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #22/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. Story mais sólida do lote; se rename afetar `frontend/app/api-types.generated.ts`, regenerar via `npm --prefix frontend run generate:api-types` no mesmo PR.
- **2026-04-18** — @dev: **Status Ready → Blocked.** Investigação provou que a hipótese original da story está incorreta — `pending_review_count` não foi renomeado. Real cause: 3 regressões de produção do refactor `filter.py` → `filter/pipeline.py` (DEBT-07/DEBT-110) que perderam a lógica da STORY-354 AC1/AC2 e CRIT-059 AC4. 6 de 13 failing tests exigem produção; task constraint explícito proíbe prod-fixes nesta story. Ver "Root Cause Analysis" acima. **Próximo passo:** @sm deve criar follow-up story (M-L effort) com escopo descrito em "Root Cause Analysis → Escopo da follow-up story".
