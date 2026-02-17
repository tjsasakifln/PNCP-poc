# GTM-FIX-005: Raise Circuit Breaker Threshold

## Dimension Impact
- Moves D01 (Data Completeness) +0.5 (6.5/10 → 7/10)

## Problem
Global singleton circuit breaker in pncp_client.py:170 has threshold=20. With 27 UFs × 4 modalities = 108 parallel API slots, an 18% failure rate (20/108) trips the circuit breaker for ALL users globally. Single user's bad search (wrong date format, temporary PNCP downtime) can cascade to block all subsequent users until circuit resets (60s).

## Solution
**Option A (Quick fix):** Raise threshold to 50 via environment variable `PNCP_CIRCUIT_BREAKER_THRESHOLD` (default 50)

**Option B (Proper fix):** Implement per-user circuit breaker with separate failure counters

For this story: Implement Option A (quick fix), defer Option B to future enhancement.

## Acceptance Criteria
- [x] AC1: Add `PNCP_CIRCUIT_BREAKER_THRESHOLD` to pncp_client.py with default=50, add `PCP_CIRCUIT_BREAKER_THRESHOLD` with default=30
- [x] AC2: Pass threshold to CircuitBreaker constructor in pncp_client.py
- [x] AC3: Add `PNCP_CIRCUIT_BREAKER_THRESHOLD=50` and `PCP_CIRCUIT_BREAKER_THRESHOLD=30` to `.env.example`
- [ ] AC4: Set `PNCP_CIRCUIT_BREAKER_THRESHOLD=50` in Railway production environment
- [x] AC5: Backend test: test_circuit_breaker_threshold_configurable()
- [x] AC6: Backend test: test_circuit_breaker_does_not_trip_at_18_percent_failure()
- [x] AC7: Unit test covers 30 failures → circuit does NOT trip (test_circuit_breaker_does_not_trip_at_18_percent_failure)
- [x] AC8: Unit test covers 50 failures → circuit DOES trip (test_circuit_breaker_trips_at_50)
- [x] AC9: Refactored CircuitBreaker with `name` parameter — separate PNCP/PCP instances
- [x] AC10: Logging includes `[source]` tag in all circuit breaker messages

## Effort: XS (15min)
## Priority: P0 (Cascade failure risk)
## Dependencies: None

## Files to Modify
- `backend/config.py` (add PNCP_CIRCUIT_BREAKER_THRESHOLD)
- `backend/pncp_client.py` (line 170, use config value)
- `.env.example` (document new variable)
- `backend/tests/test_pncp_client.py` (add threshold tests)

## Testing Strategy
1. Unit test: Mock 30 PNCP failures in parallel search → verify circuit stays closed
2. Unit test: Mock 51 PNCP failures → verify circuit opens
3. Integration test: Simulate cascade scenario with 3 concurrent users → verify isolation
4. Monitoring: Add Sentry alert for circuit breaker trip events (should be rare)

## Code Changes

**config.py:**
```python
PNCP_CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("PNCP_CIRCUIT_BREAKER_THRESHOLD", "50"))
```

**pncp_client.py:170:**
```python
# Before:
circuit_breaker = CircuitBreaker(failure_threshold=20, timeout=60)

# After:
from config import PNCP_CIRCUIT_BREAKER_THRESHOLD
circuit_breaker = CircuitBreaker(failure_threshold=PNCP_CIRCUIT_BREAKER_THRESHOLD, timeout=60)
```

## Future Enhancement (Option B - not in scope)
- Replace global singleton with per-user circuit breaker
- Track failure rates by user_id in Redis
- Implement progressive backoff per user (not global)
- Add circuit breaker metrics to observability dashboard

## ⚠️ REVISÃO — Impacto PCP API (2026-02-16)

**Contexto:** Com a integração do Portal de Compras Públicas (GTM-FIX-011), o circuit breaker precisa ser per-source, não global.

**Alterações nesta story:**

1. **AC1 revisado:** Além de `PNCP_CIRCUIT_BREAKER_THRESHOLD`, adicionar `PCP_CIRCUIT_BREAKER_THRESHOLD` (default=30, mais conservador que PNCP pois não conhecemos a estabilidade da API PCP ainda).

2. **Novo AC9:** Refatorar `CircuitBreaker` para aceitar `name` parameter no construtor, permitindo instâncias independentes:
   ```python
   pncp_circuit_breaker = CircuitBreaker(name="pncp", failure_threshold=PNCP_CB_THRESHOLD)
   pcp_circuit_breaker = CircuitBreaker(name="pcp", failure_threshold=PCP_CB_THRESHOLD)
   ```
   Isso é crítico: falhas do PCP não devem afetar o PNCP e vice-versa.

3. **Novo AC10:** Logging de circuit breaker deve incluir `source` tag para distinguir trips: `"Circuit breaker [pcp] tripped after 30 failures"`.

4. **Impacto no effort:** De XS (15min) para XS (30min) — adicionar segundo threshold + name parameter.

**Nota:** Esta story é PRÉ-REQUISITO de GTM-FIX-011. Deve ser implementada antes para que o PCPClient tenha seu próprio circuit breaker.
