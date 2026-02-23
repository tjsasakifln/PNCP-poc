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

- [ ] AC1: Quando busca falha e nao ha cache do user, sistema tenta buscar cache de QUALQUER user com mesmo `params_hash_global` (hash sem user_id)
- [ ] AC2: `params_hash_global` = hash de (setor, ufs, data_inicio, data_fim) — sem user_id
- [ ] AC3: Cache global e read-only fallback — cada user continua tendo seu proprio cache write
- [ ] AC4: Supabase L2 query: `search_cache.where(params_hash_global=X).order(created_at.desc).limit(1)`

### Warmup Cron

- [ ] AC5: `cron_jobs.py` conectado a `get_stale_entries_for_refresh()` — executa a cada 4h
- [ ] AC6: Top 10 combinacoes (setor+UFs) mais populares pre-aquecidas via cron
- [ ] AC7: Warm-up pos-deploy: `startup` event em `main.py` enfileira refresh dos top 10 params

### Revalidation Multi-Source

- [ ] AC8: Background revalidation usa `ConsolidationService` (3 fontes) em vez de PNCP-only
- [ ] AC9: Se PNCP falha, revalidation usa PCP+ComprasGov (resultado parcial > nada)

## Testes Obrigatorios

```bash
cd backend && pytest -k "test_cache_global or test_warmup" --no-coverage
```

- [ ] T1: Trial user recebe cache global quando cache pessoal vazio
- [ ] T2: `params_hash_global` nao inclui user_id
- [ ] T3: Cache global nao sobrescreve cache pessoal existente
- [ ] T4: Cron refresh executa para HOT entries
- [ ] T5: Warmup pos-deploy enfileira top 10 params
- [ ] T6: Revalidation usa ConsolidationService (nao PNCP-only)

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/search_cache.py` | Modificar — adicionar `params_hash_global`, fallback cross-user |
| `backend/cron_jobs.py` | Modificar — conectar `get_stale_entries_for_refresh()` |
| `backend/main.py` | Modificar — startup warm-up event |
| `backend/consolidation.py` | Modificar — expor para revalidation |
| `supabase/migrations/` | Nova migration — indice em `params_hash_global` |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Depende de | GTM-ARCH-001 | Busca funcional necessaria para cache funcionar |
| Paralela | GTM-INFRA-003 | Revalidation multi-source complementa esta story |
