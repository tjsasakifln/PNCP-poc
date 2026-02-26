# STORY-291: Circuit Breaker no Supabase

**Sprint:** 0 — Make It Work
**Size:** M (4-8h)
**Root Cause:** RC-1
**Blocks:** STORY-292
**Industry Standard:** [Microsoft — Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker), [Resilience4j](https://resilience4j.readme.io/docs/circuitbreaker)

## Contexto

Supabase é chamado 4-6x no hot path de toda busca (auth, plan, quota, session, profile, cache). É a ÚNICA dependência externa sem circuit breaker. PNCP, Redis, OpenAI todos têm. Se Supabase tem latência ou downtime, 100% das buscas falham instantaneamente.

Pior: `require_active_plan()` roda ANTES do try block e ANTES do tracker SSE ser criado. Quando falha, o frontend fica em limbo — POST falhou mas SSE está esperando por um tracker que nunca existiu.

## Acceptance Criteria

- [ ] AC1: Circuit breaker implementado para chamadas Supabase no hot path
- [ ] AC2: Configuração: sliding window 10 calls, 50% failure rate → OPEN, 60s wait → HALF_OPEN, 3 trial calls
- [ ] AC3: Fallback plan status: cache em Redis com TTL 5min (chave: `plan:{user_id}`)
- [ ] AC4: Fallback quota: permitir busca quando CB aberto, logar para reconciliação posterior
- [ ] AC5: `require_active_plan()` movido para DENTRO do try block, DEPOIS do tracker ser criado
- [ ] AC6: Prometheus metrics: `smartlic_supabase_cb_state` (gauge: 0=closed, 1=open, 2=half_open)
- [ ] AC7: Prometheus counter: `smartlic_supabase_cb_transitions_total` (labels: from_state, to_state)
- [ ] AC8: Testes para cada transição de estado do CB (closed→open, open→half_open, half_open→closed)
- [ ] AC9: Testes existentes continuam passando

## Technical Design

```python
# Usar aiomisc ou implementação própria (simples)
class SupabaseCircuitBreaker:
    def __init__(self, failure_threshold=5, window_size=10, cooldown=60):
        self._state = "CLOSED"
        self._failures = deque(maxlen=window_size)
        self._cooldown = cooldown
        self._opened_at = None

    async def call(self, func, *args, fallback=None, **kwargs):
        if self._state == "OPEN":
            if time.time() - self._opened_at > self._cooldown:
                self._state = "HALF_OPEN"
            elif fallback:
                return await fallback()
            else:
                raise CircuitBreakerOpenError()

        try:
            result = await asyncio.to_thread(func, *args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            if fallback:
                return await fallback()
            raise
```

## Files to Change

- `backend/supabase_client.py` — add SupabaseCircuitBreaker wrapper
- `backend/routes/search.py` — move `require_active_plan()` inside try block
- `backend/auth.py` — wrap `_check_user_roles()` with CB
- `backend/quota.py` — wrap quota checks with CB + fallback
- `backend/metrics.py` — add CB metrics

## Definition of Done

- [ ] CB protege todas as chamadas Supabase no hot path de busca
- [ ] Busca não falha quando Supabase tem latência >2s
- [ ] SSE emite error event quando auth falha (não fica em limbo)
- [ ] Todos os testes passando
- [ ] PR merged
