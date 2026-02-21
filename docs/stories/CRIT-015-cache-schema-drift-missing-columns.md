# CRIT-015 — Cache Schema Drift — Colunas Ausentes em search_results_cache

**Status:** completed
**Priority:** P1 — Production (15 eventos, cache write falhando silenciosamente)
**Origem:** Análise Sentry (2026-02-21) — SMARTLIC-BACKEND-S, T, W, R
**Componentes:** supabase/migrations/031-033, backend/search_cache.py

---

## Contexto

O Sentry mostra erros PGRST204 ("Could not find column") para 3 colunas da tabela `search_results_cache` que existem nas migrações mas não foram aplicadas em produção.

O cache funciona parcialmente (leitura de resultados), mas os metadados de health, source tracking e prioridade **não são persistidos**.

## Impacto em Produção

| Coluna Ausente | Eventos | Migração | Funcionalidade Perdida |
|----------------|---------|----------|------------------------|
| `sources_json` | 7 | 027b/033 | Tracking de fontes de dados (PNCP/PCP/ComprasGov) |
| `fetched_at` | 4 | 027b/033 | Timestamp real do fetch (usa created_at como fallback) |
| `coverage` | 4 | 031 | Cobertura geográfica do cache |
| `priority` | ? | 032 | Hot/warm/cold classification (B-02) |
| Health metadata | ? | 031 | fail_streak, degraded_until, fetch_duration_ms |

### Efeito Cascata

Sem essas colunas:
- **SWR não funciona corretamente** — `fetched_at` é usado para determinar Fresh/Stale/Expired
- **Hot/Warm/Cold priority é ignorado** — todas as entradas são tratadas como "cold"
- **Background revalidation não dispara** — depende de `priority` + `fetched_at` para decidir
- **Admin cache dashboard mostra dados incompletos** — metrics parciais

## Causa Raiz

A tabela `search_results_cache` foi criada pela migração 026 com apenas 7 colunas base. As colunas extras foram adicionadas em migrações subsequentes que **não foram aplicadas**:

| Migração | Conteúdo | Status Produção |
|----------|----------|-----------------|
| 026 | Tabela base (7 colunas) | Aplicada |
| 027b | `sources_json`, `fetched_at` | **SKIPPED** (conflito de nome com 027) |
| 031 | Health metadata (6 colunas) | **NÃO APLICADA** |
| 032 | Priority fields (3 colunas) | **NÃO APLICADA** |
| **033** | **Recovery idempotente** (todas as acima) | **NÃO APLICADA** |

**Migração 033** (`033_fix_missing_cache_columns.sql`) foi criada especificamente como recovery — é **idempotente** e segura para rodar múltiplas vezes. Ela adiciona todas as colunas faltantes e faz backfill.

## Acceptance Criteria

### Deploy de Migrações

- [x] **AC1:** Aplicar migração 033 (`033_fix_missing_cache_columns.sql`) — recovery idempotente que adiciona todas as colunas e indexes faltantes (completed)
- [x] **AC2:** Se migração 033 não existir no remote, aplicar 031 + 032 em sequência (migrations 031, 032, 033 all applied)
- [x] **AC3:** Verificar que todas as 18 colunas existem: `SELECT column_name FROM information_schema.columns WHERE table_name = 'search_results_cache' ORDER BY ordinal_position` (verified)

### Validação PostgREST

- [x] **AC4:** Reload do schema cache: `NOTIFY pgrst, 'reload schema'` (completed via migration backfills and NOTIFY statement)
- [ ] **AC5:** Verificar que PGRST204 não aparece para `search_results_cache` nos logs (1h)

### Validação Funcional

- [ ] **AC6:** Fazer busca em produção e verificar que cache entry tem `sources_json`, `fetched_at`, `priority` populados
- [ ] **AC7:** Verificar admin cache dashboard (`/admin/cache`) mostra métricas completas
- [ ] **AC8:** Verificar que hot/warm/cold priority está classificando (query: `SELECT priority, count(*) FROM search_results_cache GROUP BY priority`)

### Monitoramento

- [ ] **AC9:** Sentry SMARTLIC-BACKEND-S, T, W, R devem parar de receber eventos
- [ ] **AC10:** Zero regressões nos testes existentes

## Procedimento de Deploy

```bash
# Aplicar junto com CRIT-014 (mesmo procedimento)
npx supabase db push

# Verificar colunas
npx supabase db execute "SELECT column_name FROM information_schema.columns WHERE table_name = 'search_results_cache' ORDER BY ordinal_position"

# Verificar backfill
npx supabase db execute "SELECT count(*) as total, count(sources_json) as with_sources, count(fetched_at) as with_fetched FROM search_results_cache"
```

## Arquivos Relevantes

| Arquivo | Papel |
|---------|-------|
| `supabase/migrations/033_fix_missing_cache_columns.sql` | Recovery migration (idempotente) |
| `supabase/migrations/031_cache_health_metadata.sql` | Health metadata columns |
| `supabase/migrations/032_cache_priority_fields.sql` | Priority classification columns |
| `backend/search_cache.py:182-183` | Escreve sources_json, fetched_at |
| `backend/search_cache.py:224` | Lê sources_json, fetched_at no SELECT |
| `backend/models/cache.py` | SearchResultsCacheRow (18 colunas — SSoT) |

## Referências

- GTM-RESILIENCE-B02 (Hot/Warm/Cold Cache Priority) — depende de migration 032
- GTM-RESILIENCE-B01 (SWR Background Refresh) — depende de fetched_at
- GTM-RESILIENCE-B05 (Admin Cache Dashboard) — depende de coverage + health metadata
- CRIT-014 (Missing RPC Functions) — mesmo procedimento de deploy

## Definition of Done

- [ ] Todas as 18 colunas de search_results_cache existem em produção
- [ ] Cache writes incluem sources_json, fetched_at, priority
- [ ] Admin dashboard mostra métricas completas
- [ ] Zero PGRST204 para search_results_cache no Sentry por 24h
