# SHIP-003: Redis Pool Fix + Circuit Breaker Graceful Degradation

**Status:** 🔴 Pendente
**Prioridade:** P0
**Sprint:** SHIP (Go-to-Market)
**Criado:** 2026-03-03
**Bloqueia:** SHIP-001

## Contexto

### Redis Pool Exhaustion (BACKEND-26)

`llm_arbiter.py:_arbiter_cache_get_redis()` usa pool sync Redis com **5 conexões**,
mas `filter.py` executa até **10 threads simultâneas** no ThreadPoolExecutor para
classificação LLM. Sob carga, pool esgota → `ConnectionError: Too many connections`.

- `redis_pool.py:393` — `_SYNC_POOL_MAX_CONNECTIONS = 5`
- `filter.py:3371` — `ThreadPoolExecutor(max_workers=10)`

### Circuit Breaker Cascade (BACKEND-20/12/22/23/21/1X/1W)

Quando Supabase fica intermitentemente unreachable, o CircuitBreaker abre (correto).
Mas cron jobs e health checks **logam como ERROR** ao invés de gracefully skip,
gerando cascade de 28+ events no Sentry que mascaram erros reais.

### Sentry Issues Resolvidos

- BACKEND-26: `ConnectionError: Too many connections` (13 events)
- BACKEND-20: `Failed to save health check: Supabase` (28 events, Escalating)
- BACKEND-12: `Incident detection failed` (28 events, Escalating)
- BACKEND-22: `CircuitBreakerOpenError` (4 events)
- BACKEND-23: `Health incident: System status change` (2 events)
- BACKEND-21: `Failed to process trial milestone` (16 events, Escalating)
- BACKEND-1X: `Failed to process trial email #7` (6 events)
- BACKEND-1W: `Failed to process trial email #4` (10 events, Escalating)

## Acceptance Criteria

### Redis Pool

- [ ] AC1: `redis_pool.py` — `_SYNC_POOL_MAX_CONNECTIONS` de `5` para `12`
- [ ] AC2: Sem outras mudanças no pool (async pool 50 e SSE pool 10 estão OK)

### CB Graceful Degradation

- [ ] AC3: `cron_jobs.py` — todo cron task que acessa Supabase faz `try/except (CircuitBreakerOpenError, Exception)` → `logger.warning(...)` + skip (não `logger.error`)
- [ ] AC4: `health.py` — `save_health_check()` e `detect_incidents()` fazem graceful skip quando CB OPEN → `logger.warning("Supabase CB open, skipping health persistence")`
- [ ] AC5: `health.py` — health endpoint GET /health continua retornando status mesmo com CB OPEN (usa cache ou último valor conhecido)
- [ ] AC6: Trial email jobs (`process_trial_emails`, `process_trial_milestones`) fazem skip individual por usuário quando DB inacessível (não aborta batch inteiro)

### Validação

- [ ] AC7: Rodar `pytest -k "test_circuit_breaker"` — todos passam
- [ ] AC8: Rodar `pytest -k "test_cron"` — todos passam
- [ ] AC9: Após deploy, Sentry confirma redução de events nas categorias listadas

## Notas

- Não mudar timeout chain, retry logic, ou circuit breaker thresholds
- Apenas mudar pool size e error handling level (error→warning) nos cron jobs
