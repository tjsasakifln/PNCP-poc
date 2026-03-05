# CRIT-051: Cache Composable por UF Individual

**Prioridade:** CRITICAL
**Componente:** Backend — search_cache.py, pipeline/cache_manager.py
**Origem:** Incidente 2026-03-05 — Busca engenharia 27 UFs retorna 0 apesar de cache warmup ter dados

## Problema

O cache usa hash exato de `setor_id + sorted(ufs) + status + modalidades + modo_busca`.
O warmup cacheia por UF individual (`ufs: ["SP"]`, `ufs: ["RJ"]`, etc.), mas a busca do usuario usa `ufs: ["SP","ES","MG","RJ","PR","RS","SC"]`.

Hashes diferentes = cache miss sistematico. O warmup e inutil para buscas reais.

### Evidencia nos Logs

```
16:39 P1.2 warmup: sectors=['engenharia'], ufs=['SP','RJ','MG','BA','PR'] → cacheia 5 hashes individuais
17:49 Cache MISS all levels for hash 468384211b24... (7 UFs)
17:50 Cache MISS all levels for hash e0904da5fb9a... (27 UFs)
```

## Solucao

Mudar a granularidade do cache de "conjunto exato de UFs" para "UF individual", compondo na hora da leitura.

## Acceptance Criteria

### AC1: Cache granular por UF
- [ ] `save_to_cache` persiste resultados por `(setor_id, uf_individual, status, modalidades, modo_busca)` — uma entrada por UF
- [ ] Cada entrada armazena os resultados raw daquela UF especifica
- [ ] TTL mantido: L1 InMemory 4h, L2 Supabase 24h

### AC2: Composicao na leitura
- [ ] `get_from_cache` recebe lista de UFs e compoe resultado agregando entradas individuais
- [ ] Retorna `cache_hit: true` se >= 50% das UFs tem cache (threshold configuravel via `CACHE_PARTIAL_HIT_THRESHOLD`)
- [ ] Campo `cached_ufs` e `missing_ufs` no retorno para transparencia

### AC3: Busca hibrida (cache + fetch)
- [ ] Se cache tem 20/27 UFs, buscar apenas as 7 faltantes nas fontes ao vivo
- [ ] Merge resultados cached + fresh antes de passar para filtragem
- [ ] Log: `"Hybrid fetch: 20 UFs from cache, 7 from live sources"`

### AC4: Warmup agora alimenta cache real
- [ ] Warmup por UF individual (ja faz) agora e diretamente util para buscas multi-UF
- [ ] Nenhuma mudanca necessaria no warmup — a composicao resolve

### AC5: Dedup cross-UF
- [ ] Licitacoes que aparecem em multiplas UFs (ex: licitacao federal) sao deduplicadas apos composicao
- [ ] Usar mesma logica de dedup do consolidation.py

### AC6: Retrocompatibilidade
- [ ] Cache entries antigas (hash exato) continuam sendo lidas por 24h (TTL natural)
- [ ] Novas escritas usam formato granular
- [ ] Zero downtime na transicao

### AC7: Metricas
- [ ] `smartlic_cache_composition_total` (labels: full_hit, partial_hit, miss)
- [ ] `smartlic_cache_composition_coverage` histogram (% de UFs encontradas no cache)

### AC8: Testes
- [ ] Test: warmup cacheia SP individual → busca SP+RJ retorna SP do cache + RJ live
- [ ] Test: todas UFs no cache → busca retorna 100% cached
- [ ] Test: nenhuma UF no cache → busca faz fetch completo
- [ ] Test: threshold 50% respeitado
- [ ] Test: dedup cross-UF funciona

## Arquivos Afetados

- `backend/search_cache.py` — save/get reescritos para granularidade por UF
- `backend/pipeline/cache_manager.py` — `_compute_cache_key` por UF, `_read_cache` com composicao
- `backend/search_pipeline.py` — stage_execute usa busca hibrida
- `backend/consolidation.py` — dedup apos merge cache+live

## Impacto

Elimina o problema fundamental de cache miss por mismatch de UFs. Warmup passa a ser efetivo.
Reduz latencia media de buscas recorrentes de ~25s para <5s (cache hit parcial ou total).
