# CRIT-058: Cap e Priorizacao de Zero-Match LLM (Sampling Inteligente)

**Prioridade:** HIGH
**Componente:** Backend — filter.py, config.py
**Origem:** Incidente 2026-03-05 — 1.831 itens zero-match geraram 92 batches LLM (~62s so de API calls)
**Status:** TODO
**Dependencias:** CRIT-057 (budget guard deve existir como safety net)
**Estimativa:** 4-6h

## Problema

Buscas com setores amplos (Engenharia, Saude, TI) em multiplas UFs retornam 2.000-4.000 licitacoes cruas. Desses, 50-60% tem 0% keyword density e vao para classificacao LLM zero-match. Classificar TODOS e:

1. **Lento**: 1.831 itens → 92 batches → ~62s de latencia LLM pura
2. **Caro**: 92 calls GPT-4.1-nano × ~500 tokens = ~46K tokens/busca
3. **Diminishing returns**: Itens de baixo valor sem keywords raramente sao relevantes

A busca de producao (search_id: `a0554f83`) mostrou:
- 1.831 candidatos zero-match
- 434 calls LLM arbiter, 395 aprovados, 39 rejeitados
- Filtro total: 157 segundos

### Root Cause

Nao existe cap no volume de itens enviados ao LLM zero-match. `filter.py:2983` envia `zero_match_pool` inteiro sem limite.

## Acceptance Criteria

### AC1: Cap configuravel de itens zero-match
- [ ] `MAX_ZERO_MATCH_ITEMS` em config.py (default: 200, env var configuravel)
- [ ] Se `len(zero_match_pool) > MAX_ZERO_MATCH_ITEMS`:
  - Classificar apenas os primeiros `MAX_ZERO_MATCH_ITEMS`
  - Restantes vao para `pending_review`
- [ ] Log: `"[CRIT-058] Zero-match pool capped: {classified}/{total} items (cap={cap})"`

### AC2: Priorizacao por valor antes do cap
- [ ] Ordenar `zero_match_pool` por `valorTotalEstimado` decrescente ANTES de aplicar o cap
- [ ] Licitacoes de maior valor tem prioridade de classificacao LLM
- [ ] Licitacoes sem valor (`None`, `0`, `""`) ficam no final da fila

### AC3: Sampling misto (valor + aleatorio)
- [ ] Dos `MAX_ZERO_MATCH_ITEMS` slots:
  - 70% (140) para os de maior valor (deterministic, reproducible)
  - 30% (60) sample aleatorio do restante (diversidade)
- [ ] Seed do random baseado no `search_id` (reproducibilidade para debug)
- [ ] Proporção configuravel: `ZERO_MATCH_VALUE_RATIO` (default: 0.7)

### AC4: Metrica de cap atingido
- [ ] Counter: `smartlic_zero_match_cap_applied_total` (incrementa quando cap ativo)
- [ ] Histogram: `smartlic_zero_match_pool_size` (tamanho do pool antes do cap)
- [ ] Gauge/label no filter_summary: `zero_match_capped: true/false`, `zero_match_cap_value: N`

### AC5: Pending review para itens deferidos
- [ ] Itens que nao foram classificados por causa do cap recebem:
  - `_relevance_source = "pending_review"`
  - `_pending_review = True`
  - `_pending_review_reason = "zero_match_cap_exceeded"`
- [ ] Distinguir de CRIT-057 (`budget_exceeded`) vs CRIT-058 (`cap_exceeded`)

### AC6: Log de impacto
- [ ] Quando cap e aplicado, logar:
  - Valor total estimado dos itens classificados vs deferidos
  - Quantidade por faixa de valor: >1M, 100K-1M, 10K-100K, <10K
- [ ] Nivel: INFO (nao warning — cap e behavior esperado)

### AC7: Testes
- [ ] `test_crit058_zero_match_cap.py` com no minimo:
  - Pool de 500 itens, cap de 200 → 200 classificados, 300 pending_review
  - Priorizacao por valor: top-200 por valor sao classificados primeiro
  - Sampling misto: 70% valor + 30% random (com seed fixo)
  - Cap de 0 → todos pending_review (edge case)
  - Cap de 9999 + pool de 50 → classifica todos (cap nao ativado)
  - Itens sem valor vao pro final da fila de priorizacao
- [ ] Zero regressoes nos testes existentes de filter

### AC8: Compatibilidade com CRIT-057
- [ ] Cap (CRIT-058) aplica ANTES do loop LLM
- [ ] Budget guard (CRIT-057) aplica DURANTE o loop LLM
- [ ] Ambos geram `pending_review` — razoes distinguiveis
- [ ] Se cap reduz pool para 200 e budget de 30s e suficiente → CRIT-057 nao dispara

## Notas de Implementacao

Ponto de insercao: `filter.py:2983`, ANTES do bloco `if zero_match_pool:`:

```python
# CRIT-058: Cap + prioritize zero-match pool
from config import MAX_ZERO_MATCH_ITEMS, ZERO_MATCH_VALUE_RATIO
if len(zero_match_pool) > MAX_ZERO_MATCH_ITEMS:
    import random
    _rng = random.Random(hash(search_id) if search_id else 42)

    # Sort by value descending
    zero_match_pool.sort(
        key=lambda x: float(x.get("valorTotalEstimado") or x.get("valorEstimado") or 0),
        reverse=True
    )

    # Split: top by value + random sample
    n_value = int(MAX_ZERO_MATCH_ITEMS * ZERO_MATCH_VALUE_RATIO)
    n_random = MAX_ZERO_MATCH_ITEMS - n_value

    top_value = zero_match_pool[:n_value]
    remainder = zero_match_pool[n_value:]
    random_sample = _rng.sample(remainder, min(n_random, len(remainder)))

    to_classify = top_value + random_sample
    to_defer = [x for x in zero_match_pool if x not in set(map(id, to_classify))]
    # ... mark to_defer as pending_review
    zero_match_pool = to_classify
```

## Impacto Estimado

| Metrica | Antes (sem cap) | Depois (cap=200) |
|---------|-----------------|-------------------|
| Itens zero-match enviados ao LLM | 1.831 | 200 |
| Batches LLM (batch_size=20) | 92 | 10 |
| Tempo LLM zero-match | ~62s | ~7s |
| Tempo total do filtro | ~157s | ~40-50s |
| Tokens GPT-4.1-nano/busca | ~46K | ~5K |
| Custo/busca (nano) | ~$0.02 | ~$0.002 |

## File List

| Arquivo | Mudanca |
|---------|---------|
| `backend/config.py` | `MAX_ZERO_MATCH_ITEMS`, `ZERO_MATCH_VALUE_RATIO` |
| `backend/filter.py` | Cap + sort + sampling antes do loop LLM |
| `backend/metrics.py` | `smartlic_zero_match_cap_applied_total`, `smartlic_zero_match_pool_size` |
| `backend/tests/test_crit058_zero_match_cap.py` | Testes |
