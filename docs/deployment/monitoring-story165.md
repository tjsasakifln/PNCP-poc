# STORY-165 Monitoring Dashboard Specification

**Version:** 1.0
**Last Updated:** 2026-02-03
**Author:** @architect (Alex)
**Status:** Active Monitoring

## Executive Summary

This document defines comprehensive monitoring, alerting, and rollback procedures for STORY-165 (Plan Restrictions & Quota System). The feature introduces business-critical functionality (subscription enforcement, quota tracking) that requires continuous health monitoring and rapid incident response.

---

## 1. Key Metrics to Track

### 1.1 Error Rate Metrics

#### HTTP Status Codes (Priority: CRITICAL)

**403 Forbidden - Quota Exhausted**
- **What:** User blocked due to quota limit or trial expiration
- **Normal Range:** 0-5% of authenticated requests
- **Alert Threshold:** >10% of authenticated requests in 5-minute window
- **Business Impact:** Revenue signal (users hitting limits → upgrade opportunity)
- **Query:** `status=403 AND path=/api/buscar`

**429 Too Many Requests - PNCP Rate Limit**
- **What:** PNCP API rate limiting our backend
- **Normal Range:** 0-1% of search requests
- **Alert Threshold:** >5% of search requests in 5-minute window
- **Business Impact:** Service degradation, user frustration
- **Query:** `status=429 AND upstream=pncp.gov.br`

**500 Internal Server Error**
- **What:** Unhandled exceptions in backend/frontend
- **Normal Range:** <0.1% of all requests
- **Alert Threshold:** >1% of requests OR any 500 on /health endpoint
- **Business Impact:** System reliability, user churn risk
- **Query:** `status=500`

**503 Service Unavailable**
- **What:** Supabase/Redis down, PNCP timeout, quota check failure
- **Normal Range:** <0.5% of requests
- **Alert Threshold:** >2% of requests in 5-minute window
- **Business Impact:** System outage, revenue loss
- **Query:** `status=503`

#### Error Breakdown by Source
```
/api/buscar errors
├── 403: Quota enforcement (check_quota)
├── 429: PNCP rate limit (pncp_client)
├── 500: Backend exceptions (unhandled errors)
└── 503: Supabase/Redis unavailable

/api/me errors
├── 401: Invalid/expired token (auth)
├── 500: Quota check failure (check_quota)
└── 503: Supabase unavailable
```

---

### 1.2 Response Time Metrics

#### /api/buscar (Search Endpoint)
**Baseline (Pre-STORY-165):**
- **P50:** 3.2s (single UF, 7-day range)
- **P95:** 12.5s (3 UFs, 30-day range)
- **P99:** 45.8s (5+ UFs, 90-day range)

**Expected Impact (Post-STORY-165):**
- **P50:** +50ms (quota check overhead)
- **P95:** +150ms (Supabase query + Redis check)
- **P99:** +200ms (under database load)

**Alert Thresholds:**
- **P50 > 4s:** Investigate Supabase performance
- **P95 > 15s:** Check PNCP API latency + quota query optimization
- **P99 > 60s:** Critical - likely timeout, check connection pool

**Critical Path:**
```
/api/buscar
├── [NEW] check_quota(user_id) → Supabase query (50-150ms)
├── fetch_all(PNCP API) → 2-40s depending on UFs/date range
├── filter_batch() → 100-500ms
├── gerar_resumo() → 800ms-2s (OpenAI GPT-4)
└── [NEW] create_excel() - conditional (plan capability check)
    └── Only if allow_excel=True (500ms-2s depending on result size)
```

#### /api/me (User Profile)
**Baseline:** Not previously measured (new endpoint in STORY-165)

**Expected Performance:**
- **P50:** 150ms (single Supabase query)
- **P95:** 300ms (under load)
- **P99:** 500ms (cold start or DB congestion)

**Alert Thresholds:**
- **P95 > 500ms:** Check Supabase connection pool
- **P99 > 1s:** Critical - investigate database indexes

**Critical Path:**
```
/api/me
├── require_auth(token) → 50ms (Supabase auth check)
├── check_quota(user_id) → 100ms (quota + capabilities)
├── get_user_by_id() → 50ms (Supabase auth admin API)
└── Response serialization → 10ms
```

#### /api/checkout (Stripe Integration)
**Expected Performance:**
- **P50:** 800ms (Stripe API latency)
- **P95:** 1.5s
- **P99:** 3s (Stripe API slow response)

**Alert Thresholds:**
- **P95 > 2s:** Check Stripe API status
- **Any 500:** Critical - payment flow broken

---

### 1.3 Business Metrics (Revenue Critical)

#### Quota Exhaustion Events
**Metric:** `quota_exhaustion_count`
**Definition:** Number of 403 responses due to `quota_used >= quota_limit`
**Value:** High conversion opportunity (users hitting ceiling → upgrade prompt)

**Tracking:**
```python
# In check_quota() when quota_used >= quota_limit
logger.info("Quota exhausted", extra={
    "event": "quota_exhaustion",
    "user_id": user_id,
    "plan_id": plan_id,
    "quota_used": quota_used,
    "quota_limit": quota_limit,
    "upgrade_path": UPGRADE_SUGGESTIONS["max_requests_per_month"].get(plan_id)
})
```

**Dashboard Visualization:**
- **Daily exhaustion count by plan** (expect: free_trial=high, consultor_agil=medium, others=low)
- **Exhaustion → Upgrade conversion rate** (connect to Stripe webhook events)

#### Upgrade Flow Clicks
**Metric:** `upgrade_modal_shown`, `upgrade_button_clicked`
**Definition:** User engagement with monetization prompts

**Tracking Points:**
```typescript
// Frontend: UpgradeModal.tsx
analytics.track('upgrade_modal_shown', {
  trigger: 'quota_exhaustion' | 'excel_locked' | 'history_limit',
  current_plan: plan_id,
  suggested_plan: upgrade_plan_id
});

analytics.track('upgrade_button_clicked', {
  from_plan: plan_id,
  to_plan: upgrade_plan_id,
  trigger: trigger_source
});
```

**Alert Thresholds:**
- **Upgrade clicks < 5% of quota exhaustion events:** UX issue (modal not compelling)
- **Modal shown but no clicks (>20 consecutive):** A/B test needed

#### Excel Download Requests (Plan Enforcement)
**Metric:** `excel_blocked_count`, `excel_success_count`

**Definition:**
- `excel_blocked`: Free/Consultor users attempting download (no allow_excel capability)
- `excel_success`: Máquina/Sala users downloading reports

**Expected Ratio:**
- Free Trial: 100% blocked (no Excel capability)
- Consultor Ágil: 100% blocked
- Máquina: 0% blocked (full Excel access)
- Sala de Guerra: 0% blocked

**Alert:**
- **Máquina user blocked from Excel:** Critical bug in capability check
- **Free user gets Excel:** Security breach (capability bypass)

---

### 1.4 System Health Metrics

#### Supabase Connection Pool
**Metric:** `supabase_pool_active_connections`, `supabase_pool_wait_time`

**Normal Range:**
- Active connections: 2-10 (under normal load)
- Wait time: <50ms

**Alert Thresholds:**
- **Active connections > 20:** Risk of pool exhaustion
- **Wait time > 200ms:** Connection pool saturation (increase pool size)

**Critical Queries to Monitor:**
```sql
-- 1. Monthly quota check (called on every /api/buscar)
SELECT searches_count FROM monthly_quota
WHERE user_id = ? AND month_year = ?;

-- 2. User subscription lookup (check_quota)
SELECT id, plan_id, expires_at FROM user_subscriptions
WHERE user_id = ? AND is_active = true
ORDER BY created_at DESC LIMIT 1;

-- 3. Search session save (post-search)
INSERT INTO search_sessions (...) VALUES (...);
```

**Optimization Recommendations:**
- Add index: `CREATE INDEX idx_monthly_quota_user_month ON monthly_quota(user_id, month_year);`
- Add index: `CREATE INDEX idx_subscriptions_user_active ON user_subscriptions(user_id, is_active, created_at);`

#### Redis Cache (if implemented)
**Metric:** `redis_hit_rate`, `redis_latency`

**Expected Performance:**
- Hit rate: >80% for quota checks (same user, same month)
- Latency: <5ms for cache hits

**Fallback Strategy:**
- If Redis unavailable → fall back to Supabase direct queries (logged as warning)

#### PNCP API Health
**Metric:** `pncp_request_count`, `pncp_retry_count`, `pncp_timeout_count`

**Normal Behavior:**
- Retry rate: <5% of requests (PNCP is stable but occasionally slow)
- Timeout rate: <1%

**Alert Thresholds:**
- **Retry rate > 20%:** PNCP instability (wait for recovery)
- **Timeout rate > 5%:** Adjust client timeout or PNCP is down

---

## 2. Alert Thresholds & Severity Levels

### Alert Severity Matrix

| Severity | Response Time | Escalation | Examples |
|----------|---------------|------------|----------|
| **P0 - Critical** | 15 min | On-call + CTO | /health returns 503, Supabase down, Stripe webhook failing |
| **P1 - High** | 1 hour | On-call | 500 errors >1%, /api/buscar P95 >20s, Excel blocked for Máquina users |
| **P2 - Medium** | 4 hours | Team lead | 403 rate >15%, PNCP retry >20%, quota check >500ms |
| **P3 - Low** | 24 hours | Dev team | Upgrade modal CTR <5%, Redis cache miss >30% |

### Specific Alert Rules

```yaml
alerts:
  - name: "High 403 Rate - Quota Exhaustion Spike"
    condition: "403_count > 20 in 5 minutes"
    severity: P2
    action: |
      1. Check if legitimate (month-end spike expected)
      2. Verify upgrade flow is working
      3. Review quota limits (may need adjustment)

  - name: "Excel Blocked for Paid User"
    condition: "excel_blocked AND plan_id IN ('maquina', 'sala_guerra')"
    severity: P1
    action: |
      1. Check capability lookup logic (PLAN_CAPABILITIES)
      2. Verify Supabase subscription is_active=true
      3. Issue refund if downtime >1 hour

  - name: "Quota Check Timeout"
    condition: "check_quota() duration >1s"
    severity: P1
    action: |
      1. Check Supabase response time
      2. Verify connection pool not exhausted
      3. Consider adding Redis cache layer

  - name: "Trial Expiration Not Enforced"
    condition: "trial_expires_at < NOW() AND quota_used increases"
    severity: P0
    action: |
      1. Critical - users bypassing paywall
      2. Immediately rollback to v0.2
      3. Fix check_quota() trial validation

  - name: "Supabase Connection Pool Exhausted"
    condition: "pool_wait_time >500ms OR active_connections >25"
    severity: P1
    action: |
      1. Scale Supabase tier (increase connection limit)
      2. Optimize slow queries (check pg_stat_statements)
      3. Add connection pool monitoring
```

---

## 3. Rollback Trigger Conditions

### Automatic Rollback (Triggered by CI/CD)

**Condition:** Any of the following in first 30 minutes post-deployment:
1. **Health check failure:** `/health` returns 503 for >5 consecutive checks
2. **Error rate spike:** 500 errors >5% of total requests
3. **Critical metric regression:** /api/buscar P95 >2x baseline (>25s)

**Action:**
```bash
# Railway automatic rollback (configured in railway.json)
railway rollback --to-deployment <previous-stable-deployment-id>
```

### Manual Rollback Decision Matrix

| Scenario | Rollback? | Rationale |
|----------|-----------|-----------|
| 403 rate >20% (quota exhaustion spike) | ❌ No | **Expected behavior** - users hitting limits, validate upgrade flow working |
| Free users downloading Excel | ✅ Yes (Immediate) | **Security breach** - capability enforcement broken |
| Paid users blocked from Excel | ✅ Yes (within 1h) | **Revenue impact** - customer satisfaction critical |
| /api/buscar P95 >15s | ⚠️ Conditional | **Investigate first** - may be PNCP latency, not our code |
| check_quota() exceptions >10% | ✅ Yes (Immediate) | **Core flow broken** - all searches failing |
| Supabase timeout spike | ❌ No | **Infra issue** - scale Supabase, not code rollback |
| Stripe webhook 500s | ✅ Yes (Immediate) | **Payment critical** - can't process subscriptions |

### Rollback Execution Checklist

1. **Pre-Rollback Validation:**
   ```bash
   # Verify previous deployment is healthy
   railway logs --deployment <previous-deployment-id> | grep ERROR

   # Check database migrations status
   # (STORY-165 has no schema changes, safe to rollback)
   ```

2. **Execute Rollback:**
   ```bash
   # Via Railway CLI
   railway rollback --to-deployment <deployment-id>

   # Or via Railway Dashboard
   # https://railway.app/project/<project-id>/deployments
   # Click "Redeploy" on previous stable version
   ```

3. **Post-Rollback Validation:**
   ```bash
   # Wait 2 minutes for deployment
   curl https://smart-pncp-backend.up.railway.app/health

   # Test critical flow (authenticated search)
   curl -X POST https://smart-pncp-backend.up.railway.app/buscar \
     -H "Authorization: Bearer $TEST_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"ufs":["SP"],"data_inicial":"2026-02-01","data_final":"2026-02-03","setor_id":"vestuario"}'
   ```

4. **Communication:**
   - Update status page: "Investigating STORY-165 issues, rolled back to stable v0.2"
   - Notify team via Slack #alerts
   - Create incident post-mortem ticket

---

## 4. Performance Baseline Documentation

### Pre-STORY-165 Baseline (v0.2)

**Test Environment:**
- **Backend:** Railway (512MB RAM, 1 vCPU)
- **Database:** Supabase Free Tier (500MB, shared CPU)
- **Test Date:** 2026-02-02 (pre-deployment)
- **Load:** 5 concurrent users, 20 searches/min

#### /api/buscar Performance
```
Search Complexity: Light (1 UF, 7 days)
├── P50: 3.2s
├── P95: 5.8s
├── P99: 8.1s
└── Timeout rate: 0%

Search Complexity: Medium (3 UFs, 30 days)
├── P50: 8.4s
├── P95: 12.5s
├── P99: 18.3s
└── Timeout rate: <1%

Search Complexity: Heavy (5 UFs, 90 days)
├── P50: 22.7s
├── P95: 45.8s
├── P99: 78.2s (occasionally hits 5min timeout)
└── Timeout rate: 2-3%
```

**Bottlenecks Identified (Pre-STORY-165):**
1. **PNCP API latency:** 70% of total time (network + pagination)
2. **Filtering:** 10% (keyword matching across 1000s of records)
3. **LLM summary:** 15% (OpenAI GPT-4 API call)
4. **Excel generation:** 5% (openpyxl rendering)

#### Error Rates (Baseline)
```
Status Distribution (7-day average):
├── 200 OK: 94.2%
├── 400 Bad Request: 3.1% (invalid UF, missing dates)
├── 401 Unauthorized: 1.8% (expired tokens)
├── 429 PNCP Rate Limit: 0.5%
├── 500 Internal Error: 0.3% (LLM timeout, unexpected data)
└── 503 Service Unavailable: 0.1% (PNCP down)
```

---

### Post-STORY-165 Expected Performance

#### /api/buscar (With Quota Check)
```
Light Search (1 UF, 7 days):
├── P50: 3.25s (+50ms quota overhead)
├── P95: 6.0s (+200ms under DB load)
└── Timeout rate: 0% (no change)

Medium Search (3 UFs, 30 days):
├── P50: 8.5s (+100ms)
├── P95: 12.8s (+300ms)
└── Timeout rate: <1% (no change)

Heavy Search (5 UFs, 90 days):
├── P50: 22.9s (+200ms)
├── P95: 46.2s (+400ms)
└── Timeout rate: 2-3% (no change - PNCP latency dominates)
```

**New Overhead Breakdown:**
- **check_quota() call:** 50-150ms (Supabase query + logic)
- **increment_monthly_quota():** 30-80ms (upsert to monthly_quota table)
- **save_search_session():** 40-100ms (insert to search_sessions)
- **Total New Overhead:** 120-330ms per search

#### /api/me Performance
```
User Profile Endpoint (NEW in STORY-165):
├── P50: 150ms
├── P95: 300ms
├── P99: 500ms
└── Error rate: <0.1% (mostly auth failures)
```

#### Expected Error Distribution Changes
```
New Error Patterns:
├── 403 Forbidden: +2-5% (quota exhaustion - EXPECTED)
│   └── Triggers: Consultor users hitting 50/month limit
├── 500 Internal: +0.1% (quota check exceptions)
│   └── Causes: Supabase timeout, missing subscription record
└── 503 Unavailable: +0.2% (Supabase connection pool saturation)
    └── Mitigation: Increase connection pool from 5 → 15
```

---

## 5. Logging Strategy

### What to Log for Feature Monitoring

#### Quota Check Events (check_quota function)
```python
# SUCCESS: Quota check passed
logger.info("Quota check passed", extra={
    "event": "quota_check_success",
    "user_id": user_id,
    "plan_id": plan_id,
    "quota_used": quota_used,
    "quota_remaining": quota_remaining,
    "duration_ms": duration_ms,
})

# BLOCKED: Quota exhausted
logger.warning("Quota exhausted", extra={
    "event": "quota_exhausted",
    "user_id": user_id,
    "plan_id": plan_id,
    "quota_used": quota_used,
    "quota_limit": quota_limit,
    "reset_date": quota_reset_date.isoformat(),
    "upgrade_suggestion": UPGRADE_SUGGESTIONS["max_requests_per_month"].get(plan_id),
})

# BLOCKED: Trial expired
logger.warning("Trial expired", extra={
    "event": "trial_expired",
    "user_id": user_id,
    "plan_id": plan_id,
    "expired_at": trial_expires_at.isoformat(),
    "days_since_expiry": (datetime.now(timezone.utc) - trial_expires_at).days,
})

# ERROR: Quota check failed (DB error)
logger.error("Quota check failed", extra={
    "event": "quota_check_error",
    "user_id": user_id,
    "error": str(e),
    "fallback_applied": True,  # or False if request blocked
}, exc_info=True)
```

#### Plan Restriction Enforcement
```python
# Excel generation skipped (not allowed for plan)
logger.info("Excel generation skipped (plan restriction)", extra={
    "event": "excel_blocked",
    "user_id": user_id,
    "plan_id": plan_id,
    "allow_excel": False,
    "upgrade_message": upgrade_message,
})

# Excel generation success
logger.info("Excel generated", extra={
    "event": "excel_generated",
    "user_id": user_id,
    "plan_id": plan_id,
    "result_count": len(licitacoes_filtradas),
    "file_size_bytes": len(excel_base64),
})

# History date range blocked (exceeded max_history_days)
# (Future feature - STORY-166)
logger.warning("History range exceeded", extra={
    "event": "history_range_blocked",
    "user_id": user_id,
    "plan_id": plan_id,
    "requested_days": requested_days,
    "max_allowed_days": caps["max_history_days"],
})
```

#### Rate Limiting Events
```python
# Rate limit check (future - STORY-167 per-minute throttling)
logger.debug("Rate limit check", extra={
    "event": "rate_limit_check",
    "user_id": user_id,
    "requests_this_minute": request_count,
    "limit": caps["max_requests_per_min"],
    "allowed": request_count < caps["max_requests_per_min"],
})
```

### Log Retention & Analysis

**Retention Policy:**
- **Application Logs:** 30 days (Railway default)
- **Error Logs (500, 503):** 90 days (export to external storage)
- **Business Metrics (quota exhaustion, upgrades):** 1 year (analytics database)

**Log Aggregation Tools:**
```bash
# Railway Logs Query (via CLI)
railway logs --filter "event=quota_exhausted" --since 24h

# Export to CSV for analysis
railway logs --json --since 7d | jq -r '
  select(.extra.event == "quota_exhausted") |
  [.timestamp, .extra.user_id, .extra.plan_id, .extra.quota_used] |
  @csv
' > quota_exhaustion_analysis.csv
```

**Key Questions to Answer with Logs:**
1. **Conversion Funnel:** Quota exhaustion → Upgrade modal shown → Checkout started → Payment success
2. **Plan Distribution:** % of users on each plan over time
3. **Quota Utilization:** Average quota used per plan (are limits too high/low?)
4. **Error Patterns:** Which plans have highest error rates? (indicates UX confusion)

---

## 6. Architecture Health Checks

### Potential Bottlenecks Identified

#### 1. Supabase Query Performance (HIGH RISK)

**Bottleneck:** `check_quota()` performs 2 Supabase queries on every search:
```sql
-- Query 1: Get active subscription (uncached)
SELECT id, plan_id, expires_at
FROM user_subscriptions
WHERE user_id = ? AND is_active = true
ORDER BY created_at DESC LIMIT 1;

-- Query 2: Get monthly quota usage (uncached)
SELECT searches_count FROM monthly_quota
WHERE user_id = ? AND month_year = ?;
```

**Impact:**
- **Latency:** 50-150ms added to every search (P95: 200ms under load)
- **Connection Pool:** Each query holds connection for 20-50ms
- **Scalability:** At 100 req/min, queries consume 10-30 connections/sec

**Mitigation Strategy:**
1. **Redis Caching (Phase 1 - Week 2):**
   ```python
   # Cache quota info for 60 seconds (balances freshness + performance)
   cache_key = f"quota:{user_id}:{month_year}"
   cached = redis.get(cache_key)
   if cached:
       return QuotaInfo.parse_raw(cached)

   # Fallback to Supabase if cache miss
   quota_info = _fetch_from_supabase(user_id)
   redis.setex(cache_key, 60, quota_info.json())
   ```

2. **Database Indexes (Deploy Immediately):**
   ```sql
   -- Add composite index for user_subscriptions lookup
   CREATE INDEX CONCURRENTLY idx_subscriptions_user_active
   ON user_subscriptions(user_id, is_active, created_at DESC);

   -- Add composite index for monthly_quota lookup
   CREATE INDEX CONCURRENTLY idx_monthly_quota_user_month
   ON monthly_quota(user_id, month_year);
   ```

3. **Connection Pool Tuning:**
   ```python
   # Increase Supabase client pool size (default: 5 → 20)
   # In backend/supabase_client.py
   client = create_client(
       supabase_url,
       supabase_key,
       options={"pool_size": 20, "max_overflow": 10}
   )
   ```

#### 2. Monthly Quota Increment (MEDIUM RISK)

**Bottleneck:** `increment_monthly_quota()` uses upsert pattern:
```python
# Potential race condition if 2 searches finish simultaneously
current = get_monthly_quota_used(user_id)  # Read
new_count = current + 1
sb.table("monthly_quota").upsert({...})    # Write (could overwrite concurrent update)
```

**Impact:**
- **Race Condition:** Multiple searches from same user (parallel tabs) could lose increment
- **Accuracy:** Quota count may be slightly under-reported (user advantage)

**Mitigation Strategy:**
1. **Atomic Increment (PostgreSQL Function):**
   ```sql
   -- Create stored procedure for atomic increment
   CREATE OR REPLACE FUNCTION increment_quota(
       p_user_id UUID,
       p_month_year TEXT
   ) RETURNS INT AS $$
   DECLARE
       new_count INT;
   BEGIN
       INSERT INTO monthly_quota (user_id, month_year, searches_count, updated_at)
       VALUES (p_user_id, p_month_year, 1, NOW())
       ON CONFLICT (user_id, month_year)
       DO UPDATE SET
           searches_count = monthly_quota.searches_count + 1,
           updated_at = NOW()
       RETURNING searches_count INTO new_count;

       RETURN new_count;
   END;
   $$ LANGUAGE plpgsql;
   ```

2. **Call from Python:**
   ```python
   result = sb.rpc("increment_quota", {
       "p_user_id": user_id,
       "p_month_year": month_key
   }).execute()
   return result.data  # Returns new count atomically
   ```

#### 3. Redis Single Point of Failure (MEDIUM RISK - Future)

**Bottleneck:** If Redis cache is added, dependency on external service

**Mitigation Strategy:**
```python
def check_quota(user_id: str) -> QuotaInfo:
    try:
        # Try Redis cache first
        cached = redis_client.get(cache_key)
        if cached:
            return QuotaInfo.parse_raw(cached)
    except RedisConnectionError:
        # Redis down - log warning but continue with fallback
        logger.warning("Redis unavailable, falling back to Supabase", extra={
            "event": "redis_fallback",
            "user_id": user_id,
        })

    # Fallback: Direct Supabase query (slower but reliable)
    return _fetch_from_supabase(user_id)
```

**Monitoring:**
- Alert if Redis fallback rate >10% (indicates Redis instability)
- Track latency difference: Redis hit (5ms) vs. fallback (150ms)

---

### Recommended Caching Strategy

#### Cache Layers

**Layer 1: In-Memory (Python)** - NOT RECOMMENDED
- ❌ **Problem:** Multiple Railway instances (horizontal scaling) → cache inconsistency
- ❌ **Risk:** User hits quota on Instance A, still allowed on Instance B

**Layer 2: Redis (Recommended)**
- ✅ **Benefits:** Shared cache across instances, 5-10ms latency
- ✅ **TTL Strategy:** 60-second cache (balances freshness + performance)
- ⚠️ **Dependency:** Requires Redis Cloud or Railway Redis addon ($5-10/month)

**Layer 3: Database (Fallback)**
- ✅ **Always Available:** Supabase direct query (150ms latency)
- ✅ **Source of Truth:** No cache invalidation issues

#### Cache Invalidation Rules

```python
# Invalidate cache when quota changes
def increment_monthly_quota(user_id: str) -> int:
    # Update database
    new_count = _atomic_increment(user_id)

    # Invalidate Redis cache immediately
    redis_client.delete(f"quota:{user_id}:{get_current_month_key()}")

    return new_count

# Invalidate when subscription changes (Stripe webhook)
def _activate_plan(user_id: str, plan_id: str):
    # Update subscription in DB
    sb.table("user_subscriptions").insert({...})

    # Invalidate quota cache (plan capabilities changed)
    redis_client.delete(f"quota:{user_id}:*")
```

---

### Fallback Mechanisms

#### Graceful Degradation Hierarchy

**Level 1: Supabase Timeout (check_quota fails)**
```python
try:
    quota_info = check_quota(user_id)
except Exception as e:
    logger.error("Quota check failed", exc_info=True)

    # FALLBACK: Allow search with free_trial defaults (fail open)
    quota_info = QuotaInfo(
        allowed=True,
        plan_id="free_trial",
        capabilities=PLAN_CAPABILITIES["free_trial"],
        quota_used=0,
        quota_remaining=999999,
        ...
    )
```

**Rationale:** Better to allow a search (potential abuse) than block legitimate user (revenue loss)

**Level 2: PNCP API Unavailable**
```python
# Existing resilience in pncp_client.py (no changes needed)
- Exponential backoff (max 5 retries)
- Circuit breaker pattern (stop after 10 consecutive failures)
- User-friendly error: "PNCP API temporariamente indisponível"
```

**Level 3: OpenAI LLM Timeout**
```python
# Existing fallback in llm.py (no changes needed)
try:
    resumo = gerar_resumo(licitacoes_filtradas)
except Exception:
    resumo = gerar_resumo_fallback(licitacoes_filtradas)  # Template-based summary
```

**Level 4: Excel Generation Failure**
```python
# NEW: Don't fail entire request if Excel fails
try:
    excel_base64 = create_excel(licitacoes_filtradas)
except Exception as e:
    logger.error("Excel generation failed", exc_info=True)
    excel_base64 = None  # Return summary without Excel
    # Add warning to response
```

---

## 7. Testing & Validation Checklist

### Pre-Deployment Validation

- [ ] **Load Test:** 100 concurrent searches for 5 minutes (verify P95 <15s)
- [ ] **Quota Enforcement:** Test user reaches limit → gets 403 → correct error message
- [ ] **Plan Capabilities:** Verify free_trial blocked from Excel, Máquina allowed
- [ ] **Trial Expiration:** Set expires_at to past date → verify user blocked
- [ ] **Database Indexes:** Confirm indexes exist (`\d user_subscriptions`, `\d monthly_quota`)
- [ ] **Fallback Logic:** Simulate Supabase timeout → verify request doesn't hang
- [ ] **Monitoring Setup:** Confirm logs contain `event=quota_check_success` fields

### Post-Deployment Validation (First 2 Hours)

**Hour 1: Smoke Tests**
- [ ] `/health` returns 200 with `dependencies.supabase=healthy`
- [ ] Authenticated search completes successfully (check logs for quota_check_success)
- [ ] Free user blocked from Excel download (verify upgrade_message in response)
- [ ] Paid user gets Excel successfully (verify excel_base64 present)

**Hour 2: Performance Validation**
- [ ] `/api/buscar` P95 <15s (Railway metrics dashboard)
- [ ] No 500 errors in logs (search for `status=500`)
- [ ] Quota check latency <200ms (search logs for `duration_ms` in quota_check events)
- [ ] No connection pool warnings (search for `pool_wait_time`)

**Hours 2-24: Gradual Rollout**
- [ ] Monitor 403 rate (expect 2-5% increase from quota enforcement)
- [ ] Track upgrade modal impressions vs. clicks (conversion rate >5%)
- [ ] Watch for anomalies: sudden 500 spike, P95 degradation, Supabase errors

---

## 8. Incident Response Playbook

### Scenario 1: High 403 Rate (>20% of requests)

**Diagnosis Steps:**
1. Check Railway logs: `railway logs --filter "status=403" --since 30m`
2. Identify pattern: All users? Specific plan? Time-based spike?
3. Query Supabase: `SELECT plan_id, COUNT(*) FROM monthly_quota WHERE searches_count >= 50 GROUP BY plan_id;`

**Resolution:**
- **If legitimate (month-end spike):** No action, expected behavior
- **If bug (free users hitting limit incorrectly):** Emergency quota limit increase via SQL
  ```sql
  UPDATE user_subscriptions SET credits_remaining = 100 WHERE plan_id = 'free_trial';
  ```
- **If mass quota exhaustion:** Temporarily increase limits in `quota.py` PLAN_CAPABILITIES, redeploy

**Communication:**
- Slack #incidents: "Investigating high 403 rate, likely quota exhaustion spike"
- If bug confirmed: "Emergency fix deployed, users unblocked. Post-mortem in progress."

---

### Scenario 2: Paid Users Blocked from Excel

**Diagnosis Steps:**
1. Reproduce: Create Máquina plan user, attempt search → check `excel_available` in response
2. Check logs: Search for `event=excel_blocked AND plan_id IN (maquina, sala_guerra)`
3. Inspect `check_quota()` return value: Is `capabilities.allow_excel = True`?

**Resolution:**
- **If PLAN_CAPABILITIES wrong:** Fix in `quota.py`, redeploy immediately
- **If subscription lookup fails:** Check Supabase `user_subscriptions` table for is_active=false
- **Critical bug:** Issue immediate refund, rollback to v0.2

**Customer Impact:**
- Revenue-critical issue (paying customers blocked)
- SLA: Resolve within 1 hour or issue prorated refund

---

### Scenario 3: check_quota() Exceptions >10%

**Diagnosis Steps:**
1. Check Supabase status: https://status.supabase.com
2. Review exception logs: `railway logs --filter "quota_check_error" --since 1h`
3. Inspect connection pool: Look for `"pool_wait_time"` warnings

**Resolution:**
- **If Supabase down:** Enable fallback mode (fail open with free_trial defaults)
- **If connection pool saturated:** Increase pool size in `supabase_client.py`
- **If query timeout:** Add missing database indexes (see Section 6.1)

**Mitigation:**
```python
# Emergency feature flag (environment variable)
if os.getenv("QUOTA_CHECK_DISABLED") == "true":
    logger.warning("Quota check disabled via feature flag")
    return QuotaInfo(allowed=True, ...)  # Bypass enforcement temporarily
```

---

## 9. Dashboard Visualizations (Recommended)

### Grafana / Railway Metrics Setup

**Panel 1: Request Status Distribution (Pie Chart)**
```
Metric: http_requests_total
Grouping: status_code
Timeframe: Last 1 hour
```

**Panel 2: /api/buscar Latency (Line Graph)**
```
Metric: http_request_duration_seconds
Filter: path="/api/buscar"
Percentiles: P50, P95, P99
Baseline Overlay: Pre-STORY-165 values (3.2s, 12.5s, 45.8s)
```

**Panel 3: Quota Exhaustion Events (Bar Chart)**
```
Metric: Custom log query (Railway logs API)
Query: event="quota_exhausted"
Grouping: plan_id
Timeframe: Last 24 hours
```

**Panel 4: Business Metrics (Table)**
```
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Quota exhaustion → Upgrade clicks | 8.2% | >5% | ✅ OK |
| Excel blocked (Free) | 100% | 100% | ✅ OK |
| Excel success (Máquina) | 98.4% | >95% | ✅ OK |
| Trial expiration enforcement | 100% | 100% | ✅ OK |
```

**Panel 5: System Health (Status Grid)**
```
Component           Status    Latency   Error Rate
─────────────────────────────────────────────────
/api/buscar         Healthy   4.2s P95  0.3%
/api/me             Healthy   180ms P95 0.1%
Supabase            Healthy   45ms      0%
PNCP API            Degraded  2.1s      1.2%
OpenAI LLM          Healthy   980ms     0.4%
```

---

## 10. Long-Term Optimization Roadmap

### Week 2-4: Performance Enhancements

**Priority 1: Redis Caching (Est. -100ms P95 latency)**
- [ ] Add Railway Redis addon
- [ ] Implement quota cache with 60s TTL
- [ ] Add cache hit/miss metrics
- [ ] Target: 80% cache hit rate

**Priority 2: Database Optimization (Est. -50ms P95 latency)**
- [ ] Add composite indexes (see Section 6.1)
- [ ] Implement atomic increment function (PostgreSQL)
- [ ] Analyze slow query log (pg_stat_statements)
- [ ] Optimize search_sessions insert (batch if possible)

**Priority 3: Connection Pool Tuning (Prevent exhaustion)**
- [ ] Increase Supabase pool size: 5 → 20
- [ ] Add connection pool metrics (active, idle, wait_time)
- [ ] Monitor under peak load (100+ req/min)

### Month 2: Advanced Monitoring

**Priority 4: Business Intelligence Dashboard**
- [ ] Integrate with Mixpanel/Amplitude for user funnel tracking
- [ ] Build conversion report: Quota exhaustion → Upgrade → Payment
- [ ] Add cohort analysis: Free trial → Paid conversion rate by week
- [ ] Revenue metrics: MRR, churn rate, average quota utilization

**Priority 5: Predictive Alerting**
- [ ] ML model to predict quota exhaustion spike (day before month-end)
- [ ] Auto-scale Railway instances based on /api/buscar latency trend
- [ ] Anomaly detection: Alert on unusual 403 patterns (potential attack)

---

## 11. Success Metrics (OKRs)

### Week 1 (Post-Deployment Validation)
- ✅ **Zero rollbacks** due to STORY-165 issues
- ✅ **P95 latency <15s** for /api/buscar (target: <12.8s)
- ✅ **Error rate <1%** (500 errors)
- ✅ **Quota enforcement 100% accurate** (no paid users blocked, no free users getting Excel)

### Month 1 (Feature Adoption)
- ✅ **Quota exhaustion → Upgrade click rate >5%** (indicates upgrade prompts are effective)
- ✅ **Zero customer refunds** due to incorrect plan restrictions
- ✅ **<0.1% quota check errors** (Supabase reliability)
- ✅ **>80% Redis cache hit rate** (if implemented in Week 2)

### Quarter 1 (Business Impact)
- ✅ **10% of free trial users upgrade to paid** within 30 days of quota exhaustion
- ✅ **Excel download = top feature for Máquina plan** (validate pricing)
- ✅ **Average quota utilization 60-80%** (proves limits are well-calibrated)
- ✅ **Zero P0 incidents** related to subscription/quota system

---

## Appendix: Quick Reference

### Critical Endpoints to Monitor
```
GET  /health              → System health check (expect 200)
POST /api/buscar          → Main search flow (watch latency + 403s)
GET  /api/me              → User profile + quota (watch for 500s)
POST /checkout            → Stripe payment (watch for any errors)
POST /webhooks/stripe     → Subscription activation (critical for revenue)
```

### Key Log Events
```
quota_check_success       → Normal flow
quota_exhausted          → User hit limit (conversion opportunity)
trial_expired            → Trial ended (conversion critical)
quota_check_error        → System issue (investigate immediately)
excel_blocked            → Plan enforcement working
excel_generated          → Paid feature used successfully
```

### Emergency Contacts
```
On-Call Engineer:    Slack @oncall-dev
Database Admin:      Slack @db-team (for Supabase issues)
Revenue Critical:    Escalate to CTO immediately (Excel/payment issues)
```

### Quick Rollback Command
```bash
# Check last 5 deployments
railway deployments list

# Rollback to previous stable
railway rollback --to-deployment <deployment-id>

# Validate rollback
curl https://smart-pncp-backend.up.railway.app/health | jq
```

---

**Document Version:** 1.0
**Last Reviewed:** 2026-02-03
**Next Review:** 2026-02-10 (1 week post-deployment)
**Owner:** @architect (Alex)
