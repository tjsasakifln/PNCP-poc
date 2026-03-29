# Story: Beta Sprint 1 — GTM Blockers

**Epic:** Beta Issues Resolution
**Status:** Ready
**Sprint:** 1 (GTM Blocker)
**Esforço estimado:** ~12h
**Prioridade:** URGENT — blocks launch

---

## Scope

6 issues que bloqueiam GTM (P0 + P1 + P2 críticos):

### Task 1: ISSUE-029 (P0) — Fix zero-match false positives [4-6h]

- [ ] Adicionar `negative_keywords` por setor em `sectors_data.yaml` (vestuário: combustível, diesel, ambulância, pavimentação, software, obras civis, poço artesiano, biodescontaminação)
- [ ] `filter_llm.py:84-92`: Pre-filter pool — rejeitar bids com negative keywords ANTES do LLM
- [ ] `llm_arbiter.py:475`: Substituir `sorted(config.keywords)[:5]` por top-5 keywords por TF-IDF/discriminação (ex: "uniforme", "fardamento", "camisa", "calçado", "EPI")
- [ ] `filter_llm.py:260-277`: Circuit breaker — se acceptance ratio > 30%, demover a `pending_review`
- [ ] Testes: mock LLM false positives verificam pre-filter rejeita antes do LLM
- [ ] Benchmark: rodar 15-setor benchmark para verificar recall não regride

### Task 2: ISSUE-033 (P1) — Fix status filter auto-relaxation [3-4h]

- [ ] `filter_stage.py:285`: Adicionar guard `not user_selected_status` na condição de relaxation
- [ ] `filter_stage.py`: Quando 0 resultados + status explícito, retornar `status_distribution` no metadata
- [ ] `schemas/search.py`: Adicionar campo `status_distribution: Optional[dict]` em `SearchResponse`
- [ ] Frontend `StatusFilter.tsx`: Mostrar count badges pós-busca "Abertas (18) | Em Julgamento (0)"
- [ ] Frontend: Quando 0 resultados + status, mensagem: "Nenhuma licitação com status X. Y estão Abertas."
- [ ] Testes: unit test que relaxation NÃO override status; integration test distribuição

### Task 3: ISSUE-035 (P2) — Texto filtro dinâmico [0.5h]

- [ ] `useSearchFilters.ts:557-558`: Tornar `dateLabel` dinâmico baseado em `status`
- [ ] Mapeamento: recebendo_proposta→"abertas para proposta", em_julgamento→"em julgamento", encerrada→"encerradas", todos→""
- [ ] Teste: verificar label muda com status

### Task 4: ISSUE-034 (P2) — Limpar keywords ao trocar modo [0.5h]

- [ ] `ResultsFooter.tsx:61`: Scoped `termosArray` ao `searchMode`
- [ ] Se setor: URL usa `setor_id`, ignora keywords
- [ ] Se termos: URL usa keywords, ignora setor_id
- [ ] Teste: trocar modo e verificar URL limpo

### Task 5: ISSUE-022 (P2) — Consistência outlier detection [2-3h]

- [ ] `excel.py:240`: Substituir `sum()` naive por `compute_robust_total()` de `value_sanitizer.py`
- [ ] `schemas/search.py`: Adicionar `outlier_count: int = 0` e `valor_sanitizado: bool = False` ao `ResumoLicitacoes`
- [ ] `pipeline/stages/generate.py`: Popular novos campos do schema
- [ ] Frontend `ResultCard.tsx`: Quando `outlier_count > 0`, nota "Valor excl. N outlier(s)"
- [ ] Teste: mock bids com 1 outlier 1000x mediana, verificar exclusão + contagem

### Task 6: ISSUE-026 (P2) — Resumo IA contextual [1h]

- [ ] `llm.py` (prompt de resumo): Adicionar `setor_name` e `sector_keywords[:10]` como contexto
- [ ] Instrução no prompt: "Foque nos itens mais relevantes para o setor {setor_name}"
- [ ] Teste: verificar resumo menciona setor + keywords relevantes

---

## Acceptance Criteria

- [ ] AC1: Busca Vestuário SP+RJ retorna ≥80% resultados relevantes
- [ ] AC2: Filtro "Encerradas" retorna resultados DIFERENTES de "Abertas" (ou 0 com mensagem clara)
- [ ] AC3: Texto "Mostrando licitações..." reflete status selecionado
- [ ] AC4: Link "Criar alerta" sem keywords residuais ao trocar modo
- [ ] AC5: Valor total card = Valor total Excel
- [ ] AC6: Resumo IA menciona setor + keywords, não "serviços diversos"
- [ ] AC7: Todos os testes existentes passam (backend 7656, frontend 5733)
- [ ] AC8: Beta re-test confirma fixes

---

## File List

| File | Change |
|------|--------|
| `backend/sectors_data.yaml` | Add `negative_keywords` per sector |
| `backend/filter_llm.py` | Pre-filter + circuit breaker |
| `backend/llm_arbiter.py` | Discriminative keyword selection |
| `backend/pipeline/stages/filter_stage.py` | Status relaxation guard |
| `backend/schemas/search.py` | `status_distribution`, `outlier_count` fields |
| `backend/excel.py` | Use `compute_robust_total()` |
| `backend/pipeline/stages/generate.py` | Populate outlier fields |
| `backend/llm.py` | Sector context in summary prompt |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | Dynamic dateLabel |
| `frontend/app/buscar/components/ResultsFooter.tsx` | Scoped termosArray |
| `frontend/app/buscar/components/search-results/ResultCard.tsx` | Outlier note |
| `frontend/app/buscar/components/StatusFilter.tsx` | Count badges |
