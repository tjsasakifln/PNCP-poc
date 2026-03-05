# CRIT-057: Time Budget Guard Dentro do Filtro (Zero-Match LLM Timeout)

**Prioridade:** CRITICAL
**Componente:** Backend — filter.py, config.py, search_pipeline.py
**Origem:** Incidente 2026-03-05 — Busca Engenharia/7 UFs: filtro levou 157s (budget 90s), SSE AbortError em 208s
**Status:** TODO
**Dependencias:** Nenhuma (quick win independente)
**Estimativa:** 1-2h

## Problema

O guard de tempo do STAB-003 (`search_pipeline.py:165`) verifica o budget DEPOIS que `stage_filter` ja terminou. O estagio de filtro contem chamadas LLM zero-match sincronas que podem levar 60-150s para 1000+ itens, mas nao tem nenhum budget guard interno.

Na ultima busca de producao (search_id: `a0554f83`):
- 3.371 licitacoes cruas → 1.831 com 0% keyword density → LLM zero-match
- 92 batches (1831/20) via ThreadPoolExecutor(max_workers=3) → ~31 rounds × ~2s = ~62s de LLM
- Filtro total: 157s → STAB-003 dispara tarde demais (apos o estrago)
- Pipeline total: 208s → SSE pipe AbortError (usuario recebe NADA)

### Root Cause

```
search_pipeline.py:163-170
  # GTM-STAB-003 AC4: Time budget guard
  _elapsed_after_filter = time() - ctx.start_time
  if _elapsed_after_filter > 90:
      # TOO LATE — filter already ran for 157s
      ctx.is_simplified = True  # Only skips LLM summary + viability
```

O guard pula LLM summary e viability, mas o dano ja foi feito — o filtro ja consumiu 157s do budget.

### Evidencia nos Logs

```
[WARN] [STAB-003] Time budget exceeded after filter (157.0s > 90s) — skipping LLM and viability, marking is_simplified=True
[SSE-PROXY] CRIT-048: Pipe failure: {"error_type":"AbortError","search_id":"a0554f83","elapsed_ms":208430}
```

## Acceptance Criteria

### AC1: Time budget interno no loop zero-match
- [ ] Adicionar `FILTER_ZERO_MATCH_BUDGET_S` em config.py (default: 30s, env var configuravel)
- [ ] Dentro do loop de zero-match em `filter.py:3087+`, checar elapsed a cada batch completado
- [ ] Se elapsed > budget: interromper loop, NÃO descartar itens restantes
- [ ] Itens nao classificados devem ser marcados como `pending_review` (não rejeitados)

### AC2: Pending review fallback para itens nao classificados
- [ ] Itens que nao passaram pelo LLM por budget timeout recebem:
  - `_relevance_source = "pending_review"`
  - `_pending_review = True`
  - `_pending_review_reason = "zero_match_budget_exceeded"`
- [ ] Contador: `stats["zero_match_budget_exceeded"] = N` (quantos ficaram sem classificar)
- [ ] Log: `"[CRIT-057] Zero-match budget exceeded after {completed}/{total} items in {elapsed:.1f}s"`

### AC3: Metrica de duracao do zero-match
- [ ] Nova metrica Prometheus: `smartlic_filter_zero_match_duration_seconds` (Histogram)
- [ ] Observar duracao total do bloco zero-match (batch ou individual)
- [ ] Label: `mode=batch|individual`, `budget_exceeded=true|false`

### AC4: Propagacao do budget para contexto de busca
- [ ] `SearchContext.zero_match_budget_exceeded: bool = False`
- [ ] `SearchContext.zero_match_classified: int = 0`
- [ ] `SearchContext.zero_match_deferred: int = 0`
- [ ] Incluir no `filter_summary` dict retornado ao frontend

### AC5: Frontend awareness (informativo)
- [ ] Se `filter_summary.zero_match_budget_exceeded == true`, mostrar nota discreta:
  "Algumas oportunidades estao em revisao e podem aparecer em breve"
- [ ] Nao bloquear resultados — exibir o que ja foi classificado normalmente

### AC6: Testes
- [ ] `test_crit057_filter_time_budget.py` com no minimo:
  - Budget de 0.1s + 100 itens zero-match → interrompe apos poucos batches
  - Itens restantes marcados como `pending_review` (nao rejeitados)
  - Metrica observada corretamente
  - SearchContext atualizado com contadores
  - Budget alto (999s) + 10 itens → classifica todos normalmente
- [ ] Zero regressoes nos testes existentes de filter (306+)

## Notas de Implementacao

O ponto de insercao e `filter.py:3108` (loop `for future in as_completed(...)`):

```python
# CRIT-057: Check time budget after each batch completes
_zm_elapsed = _time_zm.time() - _batch_start
if _zm_elapsed > FILTER_ZERO_MATCH_BUDGET_S:
    logger.warning(
        f"[CRIT-057] Zero-match budget exceeded after {_llm_completed}/{_llm_total} "
        f"items in {_zm_elapsed:.1f}s (budget={FILTER_ZERO_MATCH_BUDGET_S}s)"
    )
    # Cancel remaining futures
    for remaining_future in future_to_idx:
        remaining_future.cancel()
    # Mark unclassified items as pending_review
    classified_indices = set()
    for idx, _ in all_results:
        for i in range(len(batch_lic_groups[idx])):
            classified_indices.add(idx * LLM_ZERO_MATCH_BATCH_SIZE + i)
    for global_idx, lic_item in enumerate(zero_match_pool):
        if global_idx not in classified_indices:
            lic_item["_relevance_source"] = "pending_review"
            lic_item["_pending_review"] = True
            lic_item["_pending_review_reason"] = "zero_match_budget_exceeded"
            resultado_pending_review.append(lic_item)
            stats["zero_match_budget_exceeded"] += 1
    break
```

## File List

| Arquivo | Mudanca |
|---------|---------|
| `backend/config.py` | `FILTER_ZERO_MATCH_BUDGET_S` (default 30s) |
| `backend/filter.py` | Budget guard no loop zero-match + pending_review fallback |
| `backend/search_pipeline.py` | `SearchContext` novos campos |
| `backend/metrics.py` | `smartlic_filter_zero_match_duration_seconds` histogram |
| `backend/tests/test_crit057_filter_time_budget.py` | Testes |
| `frontend/app/buscar/components/SearchResults.tsx` | Nota informativa (opcional) |
