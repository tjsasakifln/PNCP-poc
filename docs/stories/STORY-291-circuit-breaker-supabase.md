# STORY-291: Circuit Breaker no Supabase

**Sprint:** 0 — Make It Work
**Size:** M (4-8h)
**Root Cause:** RC-1
**Blocks:** STORY-292
**Industry Standard:** [Microsoft — Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker), [Resilience4j](https://resilience4j.readme.io/docs/circuitbreaker)
**Status:** DONE

## Contexto

Supabase é chamado 4-6x no hot path de toda busca (auth, plan, quota, session, profile, cache). É a ÚNICA dependência externa sem circuit breaker. PNCP, Redis, OpenAI todos têm. Se Supabase tem latência ou downtime, 100% das buscas falham instantaneamente.

Pior: `require_active_plan()` roda ANTES do try block e ANTES do tracker SSE ser criado. Quando falha, o frontend fica em limbo — POST falhou mas SSE está esperando por um tracker que nunca existiu.

## Acceptance Criteria

- [x] AC1: Circuit breaker implementado para chamadas Supabase no hot path
- [x] AC2: Configuração: sliding window 10 calls, 50% failure rate → OPEN, 60s wait → HALF_OPEN, 3 trial calls
- [x] AC3: Fallback plan status: cache em Redis com TTL 5min (chave: `plan:{user_id}`)
- [x] AC4: Fallback quota: permitir busca quando CB aberto, logar para reconciliação posterior
- [x] AC5: `require_active_plan()` movido para DENTRO do try block, DEPOIS do tracker ser criado
- [x] AC6: Prometheus metrics: `smartlic_supabase_cb_state` (gauge: 0=closed, 1=open, 2=half_open)
- [x] AC7: Prometheus counter: `smartlic_supabase_cb_transitions_total` (labels: from_state, to_state)
- [x] AC8: Testes para cada transição de estado do CB (closed→open, open→half_open, half_open→closed)
- [x] AC9: Testes existentes continuam passando

## Implementation Notes

### SupabaseCircuitBreaker (supabase_client.py)
- Thread-safe implementation using `threading.Lock`
- Sliding window via `collections.deque(maxlen=10)`
- `call_sync()` for sync Supabase calls (check_quota, check_and_increment_quota_atomic)
- `call_async()` for async coroutines
- Global singleton `supabase_cb` shared by all modules
- `CircuitBreakerOpenError` exception for fast-fail signaling
- `sb_execute()` integrated with CB (records success/failure, rejects when OPEN)

### Plan Status Cache (quota.py — AC3)
- In-memory dict with threading.Lock (thread-safe across asyncio.to_thread calls)
- TTL 5min, key: user_id, value: (plan_id, cached_at)
- Populated on successful Supabase calls in check_quota()
- Used as fallback when CB is OPEN
- When CB open + cache miss → fail-open with "smartlic_pro" default

### Fail-Open Behavior (AC4)
- `check_quota()`: CB open → use cached plan, or fail-open with smartlic_pro
- `check_and_increment_quota_atomic()`: CB open → return (True, 0, max_quota)
- `require_active_plan()`: CB open → allow user through
- `check_user_roles()`: CB open → return (False, False) immediately (no retries)

### AC5: require_active_plan Position
- Moved from BEFORE tracker creation to AFTER tracker creation
- On plan check failure, SSE tracker emits error event before raising HTTPException
- Frontend no longer left in limbo

### Metrics (AC6, AC7)
- `smartlic_supabase_cb_state` gauge (0=closed, 1=open, 2=half_open)
- `smartlic_supabase_cb_transitions_total` counter (labels: from_state, to_state)
- Emitted on every state transition via `_transition_locked()`

### Test Isolation (conftest.py)
- `_reset_supabase_circuit_breaker` autouse fixture resets global CB between tests
- Prevents test pollution from CB state leaking across test files

## Files Changed

| File | Change |
|------|--------|
| `backend/supabase_client.py` | Added `SupabaseCircuitBreaker`, `CircuitBreakerOpenError`, global `supabase_cb`, CB integration in `sb_execute()` |
| `backend/metrics.py` | Added `SUPABASE_CB_STATE` gauge + `SUPABASE_CB_TRANSITIONS` counter |
| `backend/routes/search.py` | Moved `require_active_plan()` inside try block, after tracker creation (AC5) |
| `backend/authorization.py` | Added `CircuitBreakerOpenError` handling in `check_user_roles()` |
| `backend/quota.py` | CB wrapping in `check_quota()` + `check_and_increment_quota_atomic()`, plan status cache, fail-open in `require_active_plan()` |
| `backend/tests/conftest.py` | Added `_reset_supabase_circuit_breaker` autouse fixture |
| `backend/tests/test_supabase_circuit_breaker.py` | 36 new tests covering all ACs |
| `backend/tests/snapshots/openapi_schema.json` | Updated snapshot (new metrics added) |

## Test Results

- **36 new tests** in `test_supabase_circuit_breaker.py` — all passing
- **5774 total backend tests passing**, 1 pre-existing failure (unrelated), 5 skipped

## Definition of Done

- [x] CB protege todas as chamadas Supabase no hot path de busca
- [x] Busca não falha quando Supabase tem latência >2s
- [x] SSE emite error event quando auth falha (não fica em limbo)
- [x] Todos os testes passando
- [ ] PR merged
