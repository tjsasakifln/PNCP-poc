# HARDEN-009: Arbiter Cache LRU com Size Limit

**Severidade:** ALTA
**Esforço:** 10 min
**Quick Win:** Sim
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

`_arbiter_cache` em `llm_arbiter.py:65` é um `dict[str, Any]` sem size limit. Cresce com cada classificação LLM indefinidamente.

## Critérios de Aceitação

- [x] AC1: `_arbiter_cache` convertido para `OrderedDict` com max 5000 entries
- [x] AC2: LRU eviction (popitem oldest quando excede max)
- [x] AC3: Metric `smartlic_arbiter_cache_size` gauge
- [x] AC4: Teste unitário valida eviction
- [x] AC5: Zero regressions

## Solução

```python
from collections import OrderedDict
_ARBITER_CACHE_MAX = 5000
_arbiter_cache: OrderedDict[str, Any] = OrderedDict()

def _arbiter_cache_set(key, value):
    _arbiter_cache[key] = value
    _arbiter_cache.move_to_end(key)
    while len(_arbiter_cache) > _ARBITER_CACHE_MAX:
        _arbiter_cache.popitem(last=False)
```

## Arquivos Afetados

- `backend/llm_arbiter.py` — _arbiter_cache
- `backend/tests/test_llm_arbiter.py` — novo teste
