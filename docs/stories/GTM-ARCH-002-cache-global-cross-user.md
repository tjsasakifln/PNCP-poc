# GTM-ARCH-002: Cache Global Cross-User + Warmup Cron

## Epic
Root Cause — Arquitetura (EPIC-GTM-ROOT)

## Sprint
Sprint 6: GTM Root Cause — Tier 1

## Prioridade
P0

## Estimativa
16h

## Descricao

O cache do SmartLic e per-user: `params_hash` inclui user_id, entao cada usuario tem seu proprio cache. Isso significa que trial users (o publico mais critico para GTM) tem ZERO protecao de cache — sua primeira busca SEMPRE vai live para PNCP/PCP/ComprasGov. Se a fonte estiver lenta ou fora, trial user recebe erro ou timeout.

Alem disso, `get_stale_entries_for_refresh()` existe em `search_cache.py` mas nunca foi conectado ao `cron_jobs.py`. Background revalidation (B-01) so funciona PNCP-only, nao multi-source.

### Situacao Atual

| Componente | Comportamento | Problema |
|------------|---------------|----------|
| `search_cache.py` L1 | `params_hash` inclui user_id | Trial user = zero cache hits |
| `search_cache.py` L2 | Supabase cache per-user | Mesma limitacao |
| `cron_jobs.py` | Cron existe, nao conectado a refresh | HOT entries nunca pre-aquecidas |
| Background revalidation | PNCP-only | Falha quando PNCP down (exatamente quando mais precisa) |
| Warm-up pos-deploy | Nao existe | Primeiro user pos-deploy = experiencia gelada |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| ARCH-5 | Architect | Cache per-user: trial users sem protecao alguma |
| DATA-002 | Data Engineer | `get_stale_entries_for_refresh()` existe mas desconectada |
| DATA-004 | Data Engineer | Revalidation PNCP-only — falha quando PNCP offline |
| DATA-011 | Data Engineer | Warm-up pos-deploy inexistente |

## Criterios de Aceite

### Cache Global Fallback

- [x] AC1: Quando busca falha e nao ha cache do user, sistema tenta buscar cache de QUALQUER user com mesmo `params_hash_global` (hash sem user_id)
- [x] AC2: `params_hash_global` = hash de (setor, ufs, data_inicio, data_fim) — sem user_id
- [x] AC3: Cache global e read-only fallback — cada user continua tendo seu proprio cache write
- [x] AC4: Supabase L2 query: `search_cache.where(params_hash_global=X).order(created_at.desc).limit(1)`

### Warmup Cron

- [x] AC5: `cron_jobs.py` conectado a `get_stale_entries_for_refresh()` — executa a cada 4h
- [x] AC6: Top 10 combinacoes (setor+UFs) mais populares pre-aquecidas via cron
- [x] AC7: Warm-up pos-deploy: `startup` event em `main.py` enfileira refresh dos top 10 params

### Revalidation Multi-Source

- [x] AC8: Background revalidation usa `ConsolidationService` (3 fontes) em vez de PNCP-only
- [x] AC9: Se PNCP falha, revalidation usa PCP+ComprasGov (resultado parcial > nada)

## Testes Obrigatorios

```bash
cd backend && pytest tests/test_cache_global_warmup.py -v --no-coverage
```

- [x] T1: Trial user recebe cache global quando cache pessoal vazio
- [x] T2: `params_hash_global` nao inclui user_id
- [x] T3: Cache global nao sobrescreve cache pessoal existente
- [x] T4: Cron refresh executa para HOT entries
- [x] T5: Warmup pos-deploy enfileira top 10 params
- [x] T6: Revalidation usa ConsolidationService (nao PNCP-only)

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/search_cache.py` | Modificado — `compute_global_hash()`, `_get_global_fallback_from_supabase()`, `_fetch_multi_source_for_revalidation()`, global fallback em `get_from_cache()` e `get_from_cache_cascade()`, `get_top_popular_params()` |
| `backend/cron_jobs.py` | Modificado — `start_cache_refresh_task()`, `refresh_stale_cache_entries()`, `warmup_top_params()` |
| `backend/main.py` | Modificado — startup warm-up event + cache refresh cron task |
| `backend/models/cache.py` | Modificado — adicionado campo `params_hash_global` ao model |
| `supabase/migrations/20260223100000_add_params_hash_global.sql` | Nova migration — coluna + indice em `params_hash_global` |
| `backend/tests/test_cache_global_warmup.py` | Novo — 14 testes cobrindo T1-T6 + edge cases |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Depende de | GTM-ARCH-001 | Busca funcional necessaria para cache funcionar |
| Paralela | GTM-INFRA-003 | Revalidation multi-source complementa esta story |
