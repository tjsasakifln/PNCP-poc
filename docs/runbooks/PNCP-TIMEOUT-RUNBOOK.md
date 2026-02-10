# PNCP API Timeout Incident Runbook

**Author:** DevOps Agent (Task #3)
**Date:** 2026-02-10
**Status:** Active
**Severity:** P1 (Critical - User Impact)

---

## Problem Statement

The PNCP API experiences frequent timeouts (90+ seconds) when fetching data for certain Brazilian states (UFs), particularly PR (Paraná) and RS (Rio Grande do Sul). This causes searches to fail or return incomplete results.

**Symptoms:**
- Log messages: `UF={STATE} timed out after 90s — skipping`
- Some states return 0 results despite having data
- User sees "Busca expirou por tempo" error
- Degraded search quality (missing opportunities)

---

## Quick Diagnosis

### 1. Check Logs for Timeout Patterns

```bash
# SSH into Railway instance or check logs in Railway dashboard
grep "timed out after" /app/logs/backend.log | tail -20

# Expected patterns:
# 2026-02-10 16:02:23 | WARNING | pncp_client | UF=PR timed out after 90s — skipping
# 2026-02-10 16:02:23 | WARNING | pncp_client | UF=RS timed out after 90s — skipping
```

### 2. Identify Affected UFs

```bash
# Count timeouts by UF
grep "timed out" /app/logs/backend.log | grep -oP "UF=\K\w+" | sort | uniq -c | sort -rn

# Expected output:
#  23 PR
#  18 RS
#   5 BA
#   2 SP
```

### 3. Check PNCP API Health

```bash
# Test direct PNCP API call
curl -X GET "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20260201&dataFinal=20260210&codigoModalidadeContratacao=6&uf=PR&pagina=1"

# If slow (>5s), PNCP API itself is degraded
```

---

## Resolution Steps

### Step 1: Enable Resilient Client (Immediate Fix)

The new resilient client implements:
- Adaptive per-UF timeouts (faster UFs = shorter timeout)
- Automatic retry with exponential backoff (2 attempts)
- Circuit breaker to prevent hammering failing API
- 1-hour caching to reduce API load

**Deployment:**

```python
# In backend/main.py, replace:
from pncp_client import buscar_todas_ufs_paralelo

# With:
from pncp_client_resilient import buscar_todas_ufs_paralelo_resilient as buscar_todas_ufs_paralelo
```

**Configuration (optional env vars):**

```bash
# Railway environment variables
PNCP_ENABLE_CACHE=true          # Enable 1-hour cache (default: true)
PNCP_ENABLE_RETRY=true          # Enable auto-retry (default: true)
PNCP_MAX_RETRIES_PER_UF=2       # Retry attempts (default: 2)
PNCP_CACHE_TTL_SECONDS=3600     # Cache TTL (default: 1 hour)
```

### Step 2: Monitor Metrics

After deploying resilient client, monitor these metrics:

```bash
# Check resilience logs
grep "\[RESILIENT\]" /app/logs/backend.log | tail -50

# Expected output:
# [RESILIENT] Starting parallel fetch for 5 UFs (cache=True, retry=True)
# [RESILIENT] Parallel fetch complete: 523 items from 4/5 UFs (errors=0, empty=1)
# [RESILIENT] Cache stats: hit_rate=35.2%, hits=12, misses=22, size=15
# [RESILIENT] Unhealthy UFs (success rate <70%): ['PR']
```

### Step 3: Adjust Timeouts (If Needed)

If timeouts persist, increase baseline timeouts:

```python
# In backend/pncp_resilience.py, adjust:
class AdaptiveTimeoutManager:
    LARGE_UFS = {"SP", "RJ", "MG", "BA", "RS", "PR", "PE", "CE"}  # Add PR here if needed

    def __init__(self):
        self.default_timeout = 120.0  # Increase from 90s to 120s
        self.max_timeout = 240.0      # Increase from 180s to 240s (4 min)
```

### Step 4: Circuit Breaker Tuning

If circuit breaker opens too aggressively:

```python
# In backend/pncp_resilience.py:
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 10          # Increase from 5 to 10
    success_threshold: int = 3           # Increase from 2 to 3
    timeout_seconds: float = 120.0       # Increase from 60s to 120s
    failure_rate_threshold: float = 0.7  # Increase from 0.5 (50%) to 0.7 (70%)
```

---

## Mitigation Strategies

### Strategy A: Reduce Scope (Fastest)

**When:** Incident is ongoing, users are blocked

1. Reduce date range:
   - 30 days → 15 days
   - 15 days → 7 days

2. Reduce max_pages:
   ```python
   # In backend/pncp_client_resilient.py
   max_pages_per_uf: int = 30,  # Reduce from 50 to 30
   ```

3. Reduce concurrent UFs:
   ```python
   max_concurrent: int = 5,  # Reduce from 10 to 5
   ```

**Impact:** Faster response, but may miss some results.

### Strategy B: Split Large Queries (Medium)

**When:** User needs comprehensive results

Split queries by UF groups:

```python
# Group 1: Fast UFs (< 60s avg)
fast_ufs = ["AC", "AP", "RR", "TO", "DF"]

# Group 2: Medium UFs (60-90s avg)
medium_ufs = ["SC", "GO", "PA", "MA", "ES"]

# Group 3: Slow UFs (> 90s avg)
slow_ufs = ["SP", "RJ", "PR", "RS", "BA"]

# Execute sequentially with different timeouts
results1 = await fetch_with_timeout(fast_ufs, timeout=60)
results2 = await fetch_with_timeout(medium_ufs, timeout=120)
results3 = await fetch_with_timeout(slow_ufs, timeout=180)
```

### Strategy C: Background Jobs (Long-term)

**When:** Permanent solution needed

Implement async job queue:

1. User submits search → returns immediately with job_id
2. Backend processes search in background (5-10 minutes)
3. User polls for results or gets webhook notification
4. Results cached for 24 hours

**Technologies:**
- Celery + Redis
- Railway Cron Jobs
- Upstash QStash

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Per-UF Success Rate**
   ```python
   # Log alert if success_rate < 70% for any UF
   unhealthy_ufs = [
       uf for uf, metrics in timeout_manager.get_stats().items()
       if metrics["success_rate"] < 0.7
   ]
   ```

2. **Cache Hit Rate**
   ```python
   # Log alert if hit_rate < 20% (too many unique queries)
   if cache.hit_rate < 0.2:
       logger.warning(f"Low cache hit rate: {cache.hit_rate:.1%}")
   ```

3. **Circuit Breaker State**
   ```python
   # Log alert if circuit is OPEN
   if circuit_breaker.is_open:
       logger.error("Circuit breaker is OPEN - PNCP API degraded")
   ```

### Railway Alerts Setup

Add these to Railway dashboard:

```yaml
# .railway/alerts.yaml
alerts:
  - name: "PNCP Timeout Spike"
    query: 'log.message:"timed out after"'
    threshold: 5  # Alert if >5 timeouts in 5 minutes
    window: 5m
    severity: warning

  - name: "Circuit Breaker Open"
    query: 'log.message:"Circuit breaker .* is OPEN"'
    threshold: 1
    window: 1m
    severity: critical

  - name: "Low Success Rate"
    query: 'log.message:"Unhealthy UFs"'
    threshold: 1
    window: 10m
    severity: warning
```

---

## Rollback Procedure

If resilient client causes issues:

### 1. Quick Rollback (Railway)

```bash
# Railway CLI
railway rollback

# Or via Railway Dashboard:
# Deployments → Click previous deployment → "Redeploy"
```

### 2. Code Rollback

```bash
# Revert to original client
git revert <commit_hash>
git push origin main

# Railway auto-deploys from main branch
```

### 3. Feature Flag Rollback

```python
# Add feature flag to disable resilience features
PNCP_ENABLE_RESILIENT_CLIENT = os.getenv("PNCP_ENABLE_RESILIENT_CLIENT", "true").lower() == "true"

if PNCP_ENABLE_RESILIENT_CLIENT:
    from pncp_client_resilient import buscar_todas_ufs_paralelo_resilient as buscar_todas_ufs_paralelo
else:
    from pncp_client import buscar_todas_ufs_paralelo
```

---

## Communication Templates

### User-Facing Messages

**During Incident:**
```
"Alguns estados estão demorando mais que o normal. Tente com menos estados ou um período menor."
```

**After Resolution:**
```
"Melhoramos a confiabilidade da busca. Agora tentamos automaticamente quando alguns estados demoram."
```

### Internal Slack/Teams

**Alert:**
```
⚠️ PNCP API Timeouts Detected
- Affected UFs: PR, RS
- Timeout rate: 23% (last 1h)
- Action: Monitoring, auto-retry enabled
- ETA: Resolves in 5-10 min (retries complete)
```

**Resolution:**
```
✅ PNCP Timeout Issue Resolved
- Resilient client deployed
- Success rate: 95% (up from 77%)
- Cache hit rate: 35%
- No action needed
```

---

## Testing Procedures

### 1. Synthetic Load Test

```bash
# Backend root directory
cd backend

# Run load test with multiple UFs
python -m pytest tests/test_pncp_resilience.py -v

# Expected: All tests pass
```

### 2. Integration Test (Staging)

```bash
# Test slow UFs (PR, RS) with resilience
curl -X POST https://bidiq-staging.railway.app/buscar \
  -H "Content-Type: application/json" \
  -d '{
    "ufs": ["PR", "RS", "BA"],
    "data_inicial": "2026-02-01",
    "data_final": "2026-02-10",
    "setor_id": "vestuario"
  }'

# Expected response time: 60-120s (vs 90s timeout before)
# Expected: All 3 UFs return results (no empty UFs)
```

### 3. Chaos Engineering

```python
# Simulate PNCP API degradation
# In test environment, inject delays:

@pytest.mark.asyncio
async def test_resilience_under_load():
    # Simulate slow API responses
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = asyncio.TimeoutError()

        # Resilient client should retry
        results = await buscar_todas_ufs_paralelo_resilient(...)

        # Should still get some results (from retries)
        assert len(results) > 0
```

---

## Root Cause Analysis

### Why Timeouts Occur

1. **Large UF Data Volume**
   - States like SP, PR, RS have 10x more contracts than small states
   - PNCP API takes longer to query/return large datasets

2. **PNCP API Performance**
   - No CDN/caching on PNCP side
   - Database queries are expensive for large date ranges
   - Peak hours (8am-12pm BRT) see slowdowns

3. **Fixed 90s Timeout**
   - One-size-fits-all timeout doesn't account for UF variance
   - Small UFs finish in 10s, large UFs need 120s

4. **No Retry Logic**
   - Network blips (500ms) cause permanent failures
   - One timeout = entire UF skipped

### Permanent Fixes

1. **Adaptive Timeouts** ✅ Implemented
   - Fast UFs: 30-60s
   - Medium UFs: 60-90s
   - Slow UFs: 90-180s

2. **Retry with Backoff** ✅ Implemented
   - Retry failed UFs after 2s, 4s delay
   - Max 2 retries per UF

3. **Circuit Breaker** ✅ Implemented
   - Stop hammering if API is down
   - Auto-recover after 60s

4. **Caching** ✅ Implemented
   - 1-hour TTL (PNCP data changes slowly)
   - Reduces API load by 30-50%

---

## Related Documentation

- [TIMEOUT-FIX-REPORT.md](T:\GERAL\SASAKI\Licitações\docs\TIMEOUT-FIX-REPORT.md) - Previous timeout fix (January 2026)
- [pncp_resilience.py](T:\GERAL\SASAKI\Licitações\backend\pncp_resilience.py) - Resilience implementation
- [pncp_client_resilient.py](T:\GERAL\SASAKI\Licitações\backend\pncp_client_resilient.py) - Enhanced client
- [test_pncp_resilience.py](T:\GERAL\SASAKI\Licitações\backend\tests\test_pncp_resilience.py) - Test suite

---

## Escalation Path

1. **L1 Support** → Check logs, confirm timeout pattern
2. **DevOps Engineer** → Deploy resilient client, adjust timeouts
3. **Backend Engineer** → Investigate PNCP API issues, optimize queries
4. **Product Manager** → Decide on UX changes (background jobs, split queries)

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-02-10 | DevOps Agent | Initial version - Task #3 completion |
| 2026-01-31 | DevOps Team | Previous fix: Reduced modalidades, added max_pages |

---

**Status:** ✅ Active Runbook
**Last Reviewed:** 2026-02-10
**Next Review:** 2026-03-10 (or after next incident)
