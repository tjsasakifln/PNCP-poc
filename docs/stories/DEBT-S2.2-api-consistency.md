# DEBT-S2.2: Backend Cleanup -- Cache, Keywords, Pools
**Epic:** EPIC-DEBT
**Sprint:** 2
**Priority:** P2
**Estimated Hours:** 26h
**Assignee:** TBD

## Objetivo

Resolver debitos de arquitetura backend: adicionar monitoramento para ComprasGov offline, migrar keywords hardcoded para YAML, unificar multiplas implementacoes de cache, adicionar schema version assertion no startup, e implementar pool budget unificado com backpressure.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| SYS-03 | ComprasGov v3 offline sem monitoramento. Fora do ar desde 2026-03-03 (17 dias). | MEDIUM | 2h |
| SYS-11 | `filter.py` keyword sets hardcoded. `KEYWORDS_UNIFORMES` default hardcoded ao lado de keywords setoriais do YAML. | MEDIUM | 4h |
| SYS-12 | Multiplas implementacoes de cache. `search_cache.py`, `cache.py`, `redis_pool.py`, `auth.py`, `llm_arbiter.py`, `quota.py` com logica propria. | MEDIUM | 8h |
| SYS-13 | Sem version tracking de migrations em runtime. CI cobre, mas sem assertion no startup do backend. | MEDIUM | 4h |
| SYS-16 | Dual connection pool management. Supabase (25 conn, CB) e Redis (50 conn) sem budget unificado ou backpressure. | MEDIUM | 8h |

## Acceptance Criteria

- [ ] AC1: Cron job (15min) verifica disponibilidade de ComprasGov v3 e loga status
- [ ] AC2: Metrica `smartlic_comprasgov_available` (gauge 0/1) em Prometheus
- [ ] AC3: `KEYWORDS_UNIFORMES` e todas keyword sets hardcoded migrados para `sectors_data.yaml`
- [ ] AC4: `filter.py` le keywords exclusivamente do YAML (zero hardcoded sets)
- [ ] AC5: Interface comum `CacheBackend` implementada por todos cache providers
- [ ] AC6: `search_cache.py`, `cache.py`, `auth.py`, `llm_arbiter.py`, `quota.py` usam interface unificada
- [ ] AC7: Backend verifica schema version no startup (tabela `schema_migrations` ou check de migrations pendentes)
- [ ] AC8: Startup falha gracefully (WARNING log) se schema version diverge, mas NAO bloqueia
- [ ] AC9: Pool budget unificado: total connections = Supabase(25) + Redis(50) com configuracao centralizada
- [ ] AC10: Backpressure: quando total connections > 90%, log WARNING e rejeita novas requests com 503

## Tasks

### Track 1: ComprasGov Monitoring (2h)
- [ ] T1: Criar cron job em `cron_jobs.py` que pinga ComprasGov a cada 15 minutos
- [ ] T2: Expor metrica Prometheus gauge `smartlic_comprasgov_available`

### Track 2: Keywords YAML Migration (4h)
- [ ] T3: Mapear todas keyword sets hardcoded em `filter.py`
- [ ] T4: Migrar para `sectors_data.yaml` como secao dedicada
- [ ] T5: Atualizar `filter.py` para ler do YAML
- [ ] T6: Atualizar testes de filter

### Track 3: Cache Unification (8h)
- [ ] T7: Definir interface `CacheBackend` (get, set, delete, clear, health)
- [ ] T8: Refatorar `search_cache.py` para implementar interface
- [ ] T9: Refatorar `cache.py` (InMemoryCache) para implementar interface
- [ ] T10: Adaptar cache usage em `auth.py`, `llm_arbiter.py`, `quota.py`
- [ ] T11: Atualizar testes de cache

### Track 4: Schema Version (4h)
- [ ] T12: Implementar check de schema version no startup (query `supabase_migrations` table)
- [ ] T13: Log WARNING se versao diverge (nao bloquear startup)
- [ ] T14: Testar com migrations pendentes simuladas

### Track 5: Pool Management (8h)
- [ ] T15: Centralizar configuracao de pools em `config.py`
- [ ] T16: Implementar health monitor que tracked total connections ativas
- [ ] T17: Implementar backpressure middleware (503 quando > 90% capacity)
- [ ] T18: Adicionar metricas de pool usage ao Prometheus

## Testes Requeridos

- [ ] `test_comprasgov_health.py`: cron job detecta indisponibilidade
- [ ] `test_filter_yaml.py`: keywords carregadas do YAML, zero hardcoded
- [ ] `test_cache_interface.py`: todos backends implementam mesma interface
- [ ] `test_schema_version.py`: startup WARNING quando schema diverge
- [ ] `test_pool_backpressure.py`: 503 retornado quando pools > 90%
- [ ] Backend test count >= 7332

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **SYS-12 (cache unification)** se beneficia de SYS-02 (PNCP async) feito no Sprint 1.
- **SYS-16 (pool budget):** Numeros atuais (25+50=75 connections) sao adequados para beta. O debt e sobre visibilidade e backpressure, nao sobre redimensionamento.
- **SYS-03:** ComprasGov pode nunca voltar -- o cron e para detectar quando/se voltar.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Sistema"
- Cache: `backend/search_cache.py`, `backend/cache.py`, `backend/redis_pool.py`
- Filter: `backend/filter.py`
- Sectors: `backend/sectors_data.yaml`
- Config: `backend/config.py`
- Cron: `backend/cron_jobs.py`
