# STORY-165 On-Call Quick Reference Card

**Version:** 1.0
**Feature:** Plan Restrictions & Quota System
**Deploy Date:** 2026-02-03
**On-Call Rotation:** @oncall-dev (Slack)

---

## 🚨 Emergency Response (First 5 Minutes)

### Step 1: Assess Severity

```bash
# Quick health check
curl https://smart-pncp-backend.up.railway.app/health | jq

# Check error rate (last 10 minutes)
railway logs --since 10m | grep -E "status=(500|503)" | wc -l
# Normal: <5 errors | Alert: >10 errors | Critical: >50 errors
```

**Decision Tree:**
- ✅ **Health OK + Error rate <5:** Monitor, no action needed
- ⚠️ **Health OK + Error rate 5-50:** Investigate (P2 incident)
- 🚨 **Health 503 OR Error rate >50:** ROLLBACK NOW (P0 incident)

### Step 2: Execute Rollback (If Needed)

```bash
# Rollback backend (Railway)
railway deployments list
railway rollback --to-deployment <previous-stable-id>

# Rollback frontend (Vercel dashboard)
# Navigate to: https://vercel.com/your-project/deployments
# Click "..." on previous deployment → "Promote to Production"

# Validate rollback success
curl https://smart-pncp-backend.up.railway.app/health | jq .status
# Expected: "healthy"
```

**Rollback Triggers (any = IMMEDIATE rollback):**
1. ❌ /health returns 503 for >5 minutes
2. ❌ 500 error rate >5% in any 10-min window
3. ❌ Paid users blocked from Excel
4. ❌ P95 latency >25s for light searches

---

## 📊 Monitoring Dashboards

### Railway Metrics (Primary)
- **URL:** https://railway.app/project/your-project/metrics
- **Key Metrics:**
  - CPU: <80% (alert if >90%)
  - Memory: <400MB / 512MB (alert if >450MB)
  - Response time: P95 <15s
  - Error rate: <1%

### Supabase Dashboard
- **URL:** https://supabase.com/dashboard/project/your-project
- **Key Metrics:**
  - Active connections: <15 / 60 (free tier limit: 10)
  - Query performance: Slow queries tab
  - Disk usage: <500MB / 500MB (free tier)

### Frontend Analytics (Vercel)
- **URL:** https://vercel.com/your-project/analytics
- **Key Metrics:**
  - Page load time: <2s
  - Error rate: <1%
  - Traffic spike detection

---

## 🔍 Common Issues & Solutions

### Issue 1: High 403 Rate (Quota Exhaustion)

**Symptoms:**
```bash
railway logs --since 30m | grep "status=403" | wc -l
# >50 in 30 minutes = Investigate
```

**Diagnosis:**
```bash
# Check if legitimate (month-end spike?)
railway logs --since 1h | grep "event=quota_exhausted" | jq -r '.extra.plan_id' | sort | uniq -c

# Expected: Mostly free_trial and consultor_agil
# Suspicious: Many maquina or sala_guerra (paid users shouldn't hit limits)
```

**Solution:**
- **If legitimate:** No action (working as designed)
- **If bug (paid users blocked):**
  1. Check Supabase: `SELECT * FROM user_subscriptions WHERE plan_id IN ('maquina', 'sala_guerra') AND is_active = false;`
  2. Manually activate subscriptions if needed
  3. File P1 incident ticket
- **If mass exhaustion (all users):**
  1. Emergency quota increase: Update `PLAN_CAPABILITIES` in `quota.py`, redeploy
  2. Notify team in #incidents

---

### Issue 2: Paid Users Blocked from Excel

**Symptoms:**
```bash
railway logs --since 1h | grep "event=excel_blocked" | grep -E "plan_id=(maquina|sala_guerra)"
# Any results = CRITICAL BUG
```

**Diagnosis:**
```bash
# Test with paid user token
curl https://smart-pncp-backend.up.railway.app/me \
  -H "Authorization: Bearer $PAID_USER_TOKEN" | jq '.capabilities.allow_excel'

# Expected: true | Actual: false = Bug in PLAN_CAPABILITIES lookup
```

**Solution (IMMEDIATE ROLLBACK):**
1. **Rollback to previous version:**
   ```bash
   railway rollback --to-deployment <prev-deployment-id>
   ```
2. **Issue refunds** (if downtime >1 hour):
   - Query affected users: `SELECT email FROM auth.users WHERE id IN (...)`
   - Contact via support email with apology + prorated refund
3. **Root cause:** Check `backend/quota.py` line 35-68 (PLAN_CAPABILITIES dict)
4. **Fix + redeploy** with additional tests

---

### Issue 3: Supabase Timeout / 503 Errors

**Symptoms:**
```bash
railway logs --since 30m | grep "status=503" | wc -l
# >10 in 30 minutes = Database issue
```

**Diagnosis:**
```bash
# Check Supabase status
curl https://status.supabase.com/api/v2/status.json | jq

# Check connection pool saturation
railway logs --since 10m | grep "pool_wait_time" | tail -5

# Check slow queries in Supabase dashboard
# Navigate to: Database → Query Performance → Slow Queries
```

**Solution:**
1. **Immediate (if status.supabase.com shows incident):**
   - Wait for Supabase recovery (no action needed)
   - Monitor logs for automatic recovery

2. **If connection pool exhausted:**
   ```bash
   # Increase pool size via env var
   railway variables set SUPABASE_POOL_SIZE=20
   railway up  # Redeploy to apply
   ```

3. **If slow queries detected:**
   - Check missing indexes:
     ```sql
     SELECT tablename, indexname FROM pg_indexes
     WHERE tablename IN ('user_subscriptions', 'monthly_quota');
     ```
   - Add indexes if missing (see performance-baseline-story165.md Section 4.1)

---

### Issue 4: Quota Check Exceptions >10%

**Symptoms:**
```bash
railway logs --since 30m | grep "event=quota_check_error" | wc -l
# >20 in 30 minutes = System failure
```

**Diagnosis:**
```bash
# Inspect exception logs
railway logs --since 1h | grep "quota_check_error" | jq -r '.extra.error' | sort | uniq -c

# Common errors:
# - "connection timeout" → Supabase down/slow
# - "no active subscription" → User data issue (expected for new users)
# - "invalid plan_id" → Data corruption (critical)
```

**Solution:**
1. **Connection timeout (70% of errors):**
   - Check Supabase status (see Issue 3)
   - Increase connection timeout:
     ```bash
     railway variables set SUPABASE_TIMEOUT=15
     railway up
     ```

2. **Data corruption (any "invalid plan_id"):**
   - Query bad records:
     ```sql
     SELECT * FROM user_subscriptions
     WHERE plan_id NOT IN ('free_trial', 'consultor_agil', 'maquina', 'sala_guerra');
     ```
   - Fix manually or contact data team

3. **Emergency fallback (disable quota check temporarily):**
   ```bash
   # LAST RESORT: Bypass quota enforcement for 1 hour while fixing
   railway variables set QUOTA_CHECK_DISABLED=true
   railway up

   # REMEMBER TO RE-ENABLE after fix!
   railway variables set QUOTA_CHECK_DISABLED=false
   railway up
   ```

---

### Issue 5: Search Latency Spike (P95 >25s)

**Symptoms:**
```bash
# Check Railway metrics dashboard (Response Time P95)
# OR extract from logs:
railway logs --since 1h --json | jq -r '
  select(.path == "/buscar") | .elapsed_ms
' | awk '{sum+=$1; count++; if($1>max) max=$1} END {print "Avg:", sum/count, "ms | Max:", max, "ms"}'
```

**Diagnosis:**
```bash
# Check PNCP API health (external dependency)
curl -w "Time: %{time_total}s\n" \
  "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=2026-02-01&dataFinal=2026-02-03&pagina=1&tamanhoPagina=10"

# Healthy: <3s | Degraded: 3-10s | Down: timeout/error

# Check quota check latency
railway logs --since 30m | grep "quota_check_success" | jq -r '.extra.duration_ms' | \
  awk '{sum+=$1; count++} END {print "Avg quota check:", sum/count, "ms"}'
# Normal: <150ms | Slow: 150-500ms | Critical: >500ms
```

**Solution:**
1. **If PNCP API slow (>10s):**
   - No action needed (external dependency issue)
   - Users will see slower results, but searches still complete
   - Monitor PNCP status: https://pncp.gov.br

2. **If quota check slow (>500ms):**
   - Check Supabase query performance (see Issue 3)
   - Consider emergency Redis cache deployment (see Phase 2 optimization)

3. **If LLM timeout (rare):**
   ```bash
   railway logs --since 1h | grep "LLM generation failed"
   # Fallback mechanism should activate automatically (no action needed)
   ```

---

## 📞 Escalation Path

| Severity | Response Time | Notify | Action |
|----------|---------------|--------|--------|
| **P0 - Critical** | 15 min | @oncall-dev + @devops-lead + CTO | Rollback immediately |
| **P1 - High** | 1 hour | @oncall-dev + @devops-lead | Investigate + fix |
| **P2 - Medium** | 4 hours | @oncall-dev | Monitor + fix in next sprint |
| **P3 - Low** | 24 hours | @oncall-dev | Create ticket for backlog |

**Examples:**
- **P0:** /health returns 503, paid users blocked from Excel, error rate >10%
- **P1:** Error rate 5-10%, quota check timeout >1s, P95 latency >25s
- **P2:** 403 rate >15% (quota exhaustion spike), upgrade modal CTR <3%
- **P3:** Redis cache miss >30%, minor UI bugs, documentation updates

---

## 🛠️ Useful Commands

### Logs & Debugging

```bash
# Tail live logs
railway logs --follow

# Filter by event type
railway logs --since 1h | grep "event=quota_exhausted"

# Filter by HTTP status
railway logs --since 30m | grep "status=403"

# Extract JSON fields
railway logs --since 1h --json | jq -r 'select(.extra.event == "quota_check_success") | [.timestamp, .extra.user_id, .extra.duration_ms] | @csv'

# Count errors by type
railway logs --since 1h --json | jq -r '.status' | sort | uniq -c | sort -rn

# Find slowest searches
railway logs --since 1h --json | jq -r 'select(.path == "/buscar") | [.elapsed_ms, .extra.total_filtrado] | @csv' | sort -rn | head -10
```

### Database Queries (Supabase SQL Editor)

```sql
-- Check active subscriptions by plan
SELECT plan_id, COUNT(*) AS user_count, SUM(credits_remaining) AS total_credits
FROM user_subscriptions
WHERE is_active = true
GROUP BY plan_id;

-- Check quota usage this month
SELECT u.email, q.searches_count, s.plan_id
FROM monthly_quota q
JOIN auth.users u ON q.user_id = u.id
LEFT JOIN user_subscriptions s ON u.id = s.user_id AND s.is_active = true
WHERE q.month_year = to_char(NOW(), 'YYYY-MM')
ORDER BY q.searches_count DESC
LIMIT 20;

-- Find users near quota limit
SELECT u.email, s.plan_id, q.searches_count,
       CASE s.plan_id
           WHEN 'consultor_agil' THEN 50
           WHEN 'maquina' THEN 300
           WHEN 'sala_guerra' THEN 1000
           ELSE 999999
       END AS quota_limit
FROM monthly_quota q
JOIN auth.users u ON q.user_id = u.id
LEFT JOIN user_subscriptions s ON u.id = s.user_id AND s.is_active = true
WHERE q.month_year = to_char(NOW(), 'YYYY-MM')
  AND q.searches_count >= 0.8 * CASE s.plan_id
                                    WHEN 'consultor_agil' THEN 50
                                    WHEN 'maquina' THEN 300
                                    WHEN 'sala_guerra' THEN 1000
                                    ELSE 999999
                                END
ORDER BY q.searches_count DESC;

-- Check for expired trials still active
SELECT u.email, s.plan_id, s.expires_at
FROM user_subscriptions s
JOIN auth.users u ON s.user_id = u.id
WHERE s.is_active = true
  AND s.expires_at < NOW()
  AND s.plan_id = 'free_trial';
```

### Test User Login Tokens (for debugging)

```bash
# Get auth token for test user
curl -X POST https://smart-pncp-backend.up.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test-free@example.com","password":"Test123!"}' | jq -r '.access_token'

# Test quota check with token
curl https://smart-pncp-backend.up.railway.app/me \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 📋 Pre-Shift Checklist (Start of On-Call Rotation)

- [ ] **Test access:**
  - [ ] Railway CLI authenticated: `railway whoami`
  - [ ] Supabase dashboard accessible
  - [ ] Vercel dashboard accessible
  - [ ] Slack #alerts channel joined

- [ ] **Review recent deployments:**
  ```bash
  railway deployments list | head -5
  # Note latest deployment ID for rollback
  ```

- [ ] **Check baseline health:**
  ```bash
  curl https://smart-pncp-backend.up.railway.app/health | jq
  # Verify: status=healthy, dependencies.supabase=healthy
  ```

- [ ] **Review open incidents:**
  - Check Slack #incidents for any ongoing issues
  - Review recent Railway logs for warnings

- [ ] **Bookmark this document:**
  - Local: `docs/deployment/oncall-quick-reference-story165.md`
  - GitHub: https://github.com/your-org/pncp-poc/blob/main/docs/deployment/oncall-quick-reference-story165.md

---

## 📚 Reference Documents

1. **Monitoring Dashboard Spec:** `docs/deployment/monitoring-story165.md`
   - Detailed metrics, alert thresholds, rollback triggers

2. **Performance Baseline:** `docs/deployment/performance-baseline-story165.md`
   - Latency targets, optimization roadmap, bottleneck analysis

3. **Deployment Checklist:** `docs/deployment/story165-deployment-checklist.md`
   - Step-by-step deployment procedure, smoke tests

4. **Feature Story:** `docs/stories/STORY-165-plan-restrictions-ui.md`
   - Original requirements, acceptance criteria, implementation notes

---

## 🎯 Success Metrics (Week 1)

**Monitor these daily during first week:**

| Metric | Target | Status | Notes |
|--------|--------|--------|-------|
| Error rate (500) | <1% | _TBD_ | Check daily at 9am |
| P95 latency | <15s | _TBD_ | Review Railway dashboard |
| Quota exhaustion events | 5-20/day | _TBD_ | Expected behavior |
| Upgrade modal CTR | >5% | _TBD_ | Track via analytics |
| Customer complaints | 0 | _TBD_ | Monitor support email |
| Rollbacks executed | 0 | _TBD_ | Target: zero rollbacks |

**Daily Check-In (9am UTC):**
```bash
# Run this script daily for first week
railway logs --since 24h --json | jq -r '
  {
    total_requests: [.path] | length,
    errors_500: [select(.status == 500)] | length,
    errors_503: [select(.status == 503)] | length,
    quota_exhausted: [select(.extra.event == "quota_exhausted")] | length,
    avg_latency: [select(.path == "/buscar") | .elapsed_ms] | add / length
  }
'
```

---

**Document Version:** 1.0
**Last Updated:** 2026-02-03
**Owner:** @architect (Alex)
**On-Call Rotation:** @oncall-dev

**Emergency Hotline:** Slack @oncall-dev (DO NOT DM - use channel for visibility)
