# GTM-RESILIENCE-B06 — Circuit Breaker + Rate Limiter com Estado Compartilhado no Redis

**Track:** B — Cache Inteligente
**Prioridade:** P0
**Sprint:** 1
**Estimativa:** 5-7 horas
**Gaps Endereados:** I-01, I-02
**Dependencias:** GTM-RESILIENCE-B04 (Redis provisionado)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

O SmartLic opera com 2 workers Gunicorn (`WEB_CONCURRENCY=2`) em producao. O circuit breaker (`PNCPCircuitBreaker`) e o rate limiter sao implementados como singletons per-worker em `pncp_client.py`. Isso causa divergencia de estado entre workers: worker A pode ter o circuit breaker tripped (PNCP degraded) enquanto worker B opera normalmente.

### Estado Atual — Circuit Breaker

```python
# pncp_client.py:200-220
_circuit_breaker = PNCPCircuitBreaker(name="pncp", threshold=50, cooldown_seconds=120)
_pcp_circuit_breaker = PNCPCircuitBreaker(name="pcp", threshold=30, cooldown_seconds=120)

def get_circuit_breaker(source: str = "pncp") -> PNCPCircuitBreaker:
    if source == "pcp":
        return _pcp_circuit_breaker
    return _circuit_breaker
```

- **Per-worker singletons**: `_circuit_breaker` e `_pcp_circuit_breaker` existem em cada worker
- **asyncio.Lock**: Thread-safe dentro do mesmo worker, mas nao cross-worker
- **Atributos**: `consecutive_failures: int`, `degraded_until: Optional[float]`
- **Threshold**: PNCP=50, PCP=30 (configuravel via env)
- **Cooldown**: 120s ambos

### Estado Atual — Rate Limiter

O rate limiting e feito via `asyncio.Semaphore(10)` em `pncp_client.py` e delays entre batches (`PNCP_BATCH_DELAY_S=2.0`). Tambem e per-worker.

### Impacto da Divergencia

| Cenario | Worker A | Worker B | UX |
|---------|----------|----------|-----|
| PNCP instavel | Degraded (50 falhas) | Healthy (0 falhas) | 50% dos requests degradam, 50% tentam e falham |
| Rate limit | 10 req/s | 10 req/s | 20 req/s total contra PNCP (2x o desejado) |
| Recovery | Recovered (cooldown expired) | Still degraded | Inconsistente |

---

## Problema

1. **Circuit breaker per-worker**: Workers divergem em estado de degradacao; UX inconsistente
2. **Rate limiter per-worker**: Taxa real contra PNCP e 2x a configurada (N workers x rate)
3. **Recovery assimetrica**: Um worker pode recuperar antes do outro
4. **Health endpoint impreciso**: `GET /v1/health` consulta circuit breaker do worker que atende o request — pode dar "healthy" quando outro worker esta degraded

---

## Solucao

### 1. Circuit Breaker com Estado no Redis

Persistir `consecutive_failures` e `degraded_until` como chaves Redis:

```
circuit_breaker:pncp:failures → INT (INCR/SET)
circuit_breaker:pncp:degraded_until → FLOAT (Unix timestamp)
circuit_breaker:pcp:failures → INT
circuit_breaker:pcp:degraded_until → FLOAT
```

Usar operacoes atomicas do Redis (INCR, GETSET) para evitar race conditions.

### 2. Rate Limiter com Token Bucket no Redis

Implementar token bucket no Redis usando script Lua atomico:

```lua
-- rate_limiter.lua
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or max_tokens
local last_refill = tonumber(bucket[2]) or now

-- Refill tokens
local elapsed = now - last_refill
local new_tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

if new_tokens >= 1 then
    redis.call('HMSET', key, 'tokens', new_tokens - 1, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return 1  -- Token granted
else
    redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return 0  -- Rate limited
end
```

### 3. Fallback Preservado

Quando Redis nao esta disponivel, manter comportamento atual (per-worker singletons). A migracao para Redis deve ser transparente e reversivel.

### 4. Interface Unificada

`get_circuit_breaker()` retorna um objeto que internamente usa Redis (se disponivel) ou fallback local. Callers nao precisam mudar.

---

## Criterios de Aceite

### AC1 — RedisCircuitBreaker com mesma interface
Nova classe `RedisCircuitBreaker` que implementa os mesmos metodos da `PNCPCircuitBreaker`: `record_failure()`, `record_success()`, `try_recover()`, `is_degraded`. Usa Redis como backend em vez de atributos locais.
**Teste**: Criar instancia; chamar todos os metodos; verificar que operacoes vao para Redis.

### AC2 — Estado compartilhado entre workers
Worker A chama `record_failure()` 50x; Worker B consulta `is_degraded` → True.
**Teste**: Em processo separado (simulando worker B), verificar que `is_degraded` reflete o estado setado por worker A via Redis.

### AC3 — record_failure atomico no Redis
`record_failure()` usa `INCR` atomico para `circuit_breaker:{source}:failures`. Se atingir threshold, faz `SET circuit_breaker:{source}:degraded_until {timestamp}` atomicamente.
**Teste**: Chamar `record_failure()` concorrentemente de 10 coroutines; verificar que `failures` == 10 exatamente (sem race condition).

### AC4 — record_success reseta no Redis
`record_success()` faz `SET circuit_breaker:{source}:failures 0` e `DEL circuit_breaker:{source}:degraded_until`.
**Teste**: Setar failures=10 e degraded_until; chamar `record_success()`; verificar ambos resetados.

### AC5 — try_recover com TTL automatico
`degraded_until` tem TTL no Redis igual ao cooldown_seconds. Apos expiracao natural, `is_degraded` retorna False sem necessidade de `try_recover()`.
**Teste**: Setar degraded_until com TTL=2s; aguardar 3s; verificar `is_degraded` == False.

### AC6 — Rate limiter compartilhado via Redis token bucket
Nova classe `RedisRateLimiter` com metodo `async acquire() -> bool`. Usa script Lua para token bucket atomico. Rate: 10 tokens/segundo, max burst 10.
**Teste**: De 2 processos simultaneos, fazer 15 chamadas em 1s; verificar que exatamente 10 foram aprovadas.

### AC7 — Rate limiter integrado no pncp_client
`_fetch_page_async()` e `_fetch_single_modality()` usam `RedisRateLimiter.acquire()` antes de cada request HTTP. Se rate limited, aguarda via backoff em vez de falhar.
**Teste**: Mock rate limiter para rejeitar; verificar que request aguarda (com timeout) em vez de falhar.

### AC8 — Fallback para per-worker quando Redis indisponivel
Se Redis nao esta disponivel, `get_circuit_breaker()` retorna `PNCPCircuitBreaker` local (comportamento atual). Transicao e transparente.
**Teste**: Inicializar sem REDIS_URL; verificar que `get_circuit_breaker()` retorna instancia local. Inicializar com REDIS_URL; verificar que retorna instancia Redis.

### AC9 — Health endpoint reflete estado compartilhado
`GET /v1/health` consulta Redis para estado do circuit breaker (em vez do singleton local). Mostra `failures_count` e `degraded_until` de cada source.
**Teste**: Setar 30 failures via Redis; chamar health; verificar `pncp_circuit_breaker: {failures: 30, degraded: false}`.

### AC10 — Metricas de rate limiting
Endpoint `GET /v1/health` inclui `rate_limiter: {tokens_available: N, requests_last_minute: N}` consultado do Redis.
**Teste**: Fazer 5 requests; chamar health; verificar `requests_last_minute >= 5`.

### AC11 — Zero breaking changes nos callers
Todos os callers existentes de `get_circuit_breaker()`, `_circuit_breaker.record_failure()`, etc. continuam funcionando sem alteracao.
**Teste**: Rodar suite completa de testes existentes (test_pncp_hardening.py, test_story252_resilience.py, test_story_257a.py); zero falhas novas.

### AC12 — TTL de protecao nas chaves Redis
Todas as chaves de circuit breaker e rate limiter tem TTL maximo de 300s (5min). Se o sistema parar de atualizar, as chaves expiram naturalmente e o comportamento volta ao default (healthy, sem rate limit).
**Teste**: Setar chaves sem chamar metodos por 6min; verificar que chaves expiraram.

---

## Arquivos Afetados

| Arquivo | Alteracao |
|---------|-----------|
| `backend/pncp_client.py` | `RedisCircuitBreaker` classe, `get_circuit_breaker()` atualizado com fallback |
| `backend/rate_limiter.py` | **Novo**: `RedisRateLimiter` com script Lua |
| `backend/redis_pool.py` | Possivelmente adicionar helper para scripts Lua |
| `backend/main.py` | Atualizar health endpoint com estado compartilhado |
| `backend/tests/test_redis_circuit_breaker.py` | **Novo**: 15+ testes |
| `backend/tests/test_redis_rate_limiter.py` | **Novo**: 10+ testes |
| `backend/tests/test_pncp_hardening.py` | Atualizar para funcionar com ambos backends (Redis e local) |

---

## Consideracoes de Implementacao

### Atomicidade

Redis INCR e atomico por natureza. Para operacoes compostas (check-and-set), usar pipeline ou scripts Lua para garantir atomicidade.

### Latencia

Operacoes Redis adicionam ~1ms por chamada. Para o rate limiter (chamado a cada HTTP request), isso e aceitavel. Circuit breaker e chamado menos frequentemente.

### Chaves Redis

```
circuit_breaker:pncp:failures          → INT
circuit_breaker:pncp:degraded_until    → STRING (ISO timestamp)
circuit_breaker:pcp:failures           → INT
circuit_breaker:pcp:degraded_until     → STRING (ISO timestamp)
rate_limiter:pncp                      → HASH {tokens, last_refill}
rate_limiter:pcp                       → HASH {tokens, last_refill}
```

---

## Dependencias

- **GTM-RESILIENCE-B04**: Redis DEVE estar provisionado antes desta story
- Sem dependencias de B-01, B-02, B-03

---

## Procedimento de Rollback

1. Setar env var `USE_REDIS_CIRCUIT_BREAKER=false` (nova flag)
2. Sistema cai no fallback per-worker automaticamente
3. Sem downtime, sem perda de funcionalidade (apenas volta ao per-worker)

---

## Definition of Done

- [x] Todos os 12 ACs implementados e testados
- [ ] Circuit breaker compartilhado entre workers verificado em producao
- [ ] Rate limiter compartilhado verificado em producao
- [x] Fallback per-worker testado (desconectar Redis)
- [x] Zero breaking changes nos callers existentes
- [x] Suite de testes existente passa sem regressoes
- [x] Health endpoint mostrando estado compartilhado
- [x] Scripts Lua para rate limiter revisados por seguranca
- [x] Documentacao inline completa
