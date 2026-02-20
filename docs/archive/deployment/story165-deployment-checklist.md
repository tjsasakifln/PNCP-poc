# STORY-165 Deployment Checklist

**Feature:** Plan Restrictions & Quota System
**Target Deploy Date:** 2026-02-03
**Estimated Deploy Time:** 15 minutes
**Rollback Time:** <5 minutes

---

## Pre-Deployment (T-24 hours)

### Database Preparation
- [ ] **Verify Supabase indexes exist:**
  ```sql
  -- Run in Supabase SQL Editor
  \d user_subscriptions  -- Should show index on (user_id, is_active, created_at)
  \d monthly_quota       -- Should show index on (user_id, month_year)
  ```

- [ ] **If missing, create indexes (NON-BLOCKING):**
  ```sql
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_user_active
  ON user_subscriptions(user_id, is_active, created_at DESC);

  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_monthly_quota_user_month
  ON monthly_quota(user_id, month_year);
  ```
  **Expected Time:** 5-10 minutes (depends on table size)

- [ ] **Verify test data:**
  ```sql
  -- Ensure test users exist with different plans
  SELECT u.email, s.plan_id, s.is_active, s.expires_at
  FROM auth.users u
  LEFT JOIN user_subscriptions s ON u.id = s.user_id
  WHERE u.email IN ('test-free@example.com', 'test-paid@example.com')
  ORDER BY u.email, s.created_at DESC;
  ```

### Environment Variables
- [ ] **Confirm Railway env vars set:**
  - `SUPABASE_URL` ✅
  - `SUPABASE_SERVICE_ROLE_KEY` ✅
  - `OPENAI_API_KEY` ✅
  - `STRIPE_SECRET_KEY` ✅
  - `STRIPE_WEBHOOK_SECRET` ✅
  - `FRONTEND_URL` ✅

### Baseline Metrics Collection
- [ ] **Record current performance (run 10 test searches):**
  ```bash
  # Backend P95 latency
  curl -w "@curl-format.txt" -X POST \
    https://smart-pncp-backend.up.railway.app/buscar \
    -H "Authorization: Bearer $TEST_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"ufs":["SP"],"data_inicial":"2026-01-27","data_final":"2026-02-03","setor_id":"vestuario"}'

  # Expected: P95 ~6-8s (light search)
  ```

- [ ] **Document current error rate:**
  ```bash
  railway logs --since 1h | grep -E "status=(500|503)" | wc -l
  # Expected: <5 errors per hour
  ```

### Testing
- [ ] **Backend tests pass (106 tests):**
  ```bash
  cd backend
  pytest --cov --cov-fail-under=70
  # Expected: 106 passed, coverage >70%
  ```

- [ ] **Frontend tests pass (69 tests):**
  ```bash
  cd frontend
  npm test -- --coverage --watchAll=false
  # Expected: 69 passed, coverage >49%
  ```

- [ ] **E2E tests pass (60 tests):**
  ```bash
  cd frontend
  npm run test:e2e
  # Expected: 60 passed (search flow, quota display, plan badges)
  ```

---

## Deployment (T=0)

### Step 1: Deploy Backend (Railway)
- [ ] **Trigger deployment:**
  ```bash
  git checkout main
  git pull origin main
  railway up
  ```

- [ ] **Monitor deployment logs (2-3 minutes):**
  ```bash
  railway logs --follow
  # Watch for: "Uvicorn running on", no exceptions
  ```

- [ ] **Wait for health check:**
  ```bash
  # Poll every 10s until healthy
  while ! curl -f https://smart-pncp-backend.up.railway.app/health; do
    sleep 10
  done
  ```

### Step 2: Smoke Test Backend
- [ ] **Health endpoint (expect 200):**
  ```bash
  curl https://smart-pncp-backend.up.railway.app/health | jq
  # Verify: status=healthy, dependencies.supabase=healthy
  ```

- [ ] **Test quota check (free trial user):**
  ```bash
  curl https://smart-pncp-backend.up.railway.app/me \
    -H "Authorization: Bearer $FREE_TRIAL_TOKEN" | jq

  # Verify response contains:
  # - plan_id: "free_trial"
  # - capabilities.allow_excel: false
  # - quota_remaining: 999999
  ```

- [ ] **Test quota check (paid user):**
  ```bash
  curl https://smart-pncp-backend.up.railway.app/me \
    -H "Authorization: Bearer $PAID_USER_TOKEN" | jq

  # Verify response contains:
  # - plan_id: "maquina" (or consultor_agil)
  # - capabilities.allow_excel: true (if maquina)
  # - quota_used: <quota_limit
  ```

- [ ] **Test search with quota enforcement (free user):**
  ```bash
  curl -X POST https://smart-pncp-backend.up.railway.app/buscar \
    -H "Authorization: Bearer $FREE_TRIAL_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"ufs":["SP"],"data_inicial":"2026-02-01","data_final":"2026-02-03","setor_id":"vestuario"}' | jq

  # Verify response contains:
  # - excel_available: false
  # - upgrade_message: "Exportar Excel disponível no plano Máquina..."
  # - quota_used increased by 1
  ```

### Step 3: Deploy Frontend (Vercel)
- [ ] **Trigger deployment:**
  ```bash
  git push origin main
  # Vercel auto-deploys from GitHub
  ```

- [ ] **Monitor Vercel dashboard:**
  - Navigate to https://vercel.com/your-project/deployments
  - Wait for "Ready" status (1-2 minutes)

### Step 4: Smoke Test Frontend
- [ ] **Open production URL:** https://smart-pncp.vercel.app

- [ ] **Verify UI elements:**
  - [ ] QuotaBadge component renders in header
  - [ ] PlanBadge shows correct plan name
  - [ ] QuotaCounter shows "X / Y buscas" or "∞" for trial

- [ ] **Test search flow:**
  - [ ] Login as free trial user
  - [ ] Execute search (should succeed)
  - [ ] Verify "Fazer upgrade para exportar Excel" button disabled
  - [ ] Click upgrade button → UpgradeModal opens

- [ ] **Test paid user flow:**
  - [ ] Login as Máquina plan user
  - [ ] Execute search (should succeed)
  - [ ] Verify Excel download button ENABLED
  - [ ] Click download → Excel file downloads successfully

---

## Post-Deployment Monitoring (First 2 Hours)

### T+15 min: Initial Validation
- [ ] **No 500 errors in logs:**
  ```bash
  railway logs --since 15m | grep "status=500"
  # Expected: 0 results
  ```

- [ ] **Quota check success rate >99%:**
  ```bash
  railway logs --since 15m | grep "event=quota_check"
  # Expected: Mostly "quota_check_success", few/no "quota_check_error"
  ```

- [ ] **Search latency acceptable:**
  ```bash
  railway logs --since 15m | grep "/buscar" | grep "elapsed_ms"
  # Expected P95: <15s (may be higher depending on UF count)
  ```

### T+30 min: Performance Validation
- [ ] **Run 20 test searches (load test):**
  ```bash
  for i in {1..20}; do
    curl -s -w "Time: %{time_total}s\n" -X POST \
      https://smart-pncp-backend.up.railway.app/buscar \
      -H "Authorization: Bearer $TEST_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"ufs":["SP"],"data_inicial":"2026-02-01","data_final":"2026-02-03","setor_id":"vestuario"}' \
      -o /dev/null &
  done
  wait
  ```

- [ ] **Check Railway metrics dashboard:**
  - CPU usage: <80%
  - Memory usage: <400MB (out of 512MB)
  - No restart events

### T+1 hour: Business Metrics Check
- [ ] **Query quota exhaustion events:**
  ```bash
  railway logs --since 1h | grep "event=quota_exhausted" | wc -l
  # Expected: 0-5 events (depends on user activity)
  ```

- [ ] **Verify upgrade modal impressions (frontend analytics):**
  - Check Vercel Analytics or browser console for `upgrade_modal_shown` events
  - Expected: >0 if any quota exhaustion occurred

- [ ] **Check Stripe webhook logs:**
  ```bash
  railway logs --since 1h | grep "webhooks/stripe"
  # Verify: No 500 errors on webhook endpoint
  ```

### T+2 hours: Final Validation
- [ ] **Compare P95 latency to baseline:**
  - Baseline: ~6-8s (light search, 1 UF, 7 days)
  - Current: Should be <10s (includes +150ms quota overhead)

- [ ] **Error rate check:**
  ```bash
  railway logs --since 2h --json | jq -r 'select(.status >= 500) | .status' | sort | uniq -c
  # Expected: <5 total 500-series errors
  ```

- [ ] **No rollback triggers hit:**
  - ❌ Health check failures
  - ❌ Error rate >5%
  - ❌ P95 latency >25s
  - ❌ Critical customer complaints

---

## Rollback Procedure (If Needed)

### Rollback Decision Criteria
**EXECUTE ROLLBACK IF:**
- ✅ /health returns 503 for >5 consecutive minutes
- ✅ 500 error rate >5% of total requests in any 10-minute window
- ✅ Paid users blocked from Excel (capability enforcement broken)
- ✅ P95 latency >2x baseline (>25s for light searches)
- ✅ Quota check exceptions >10% of requests

### Rollback Steps (Target: <5 minutes)

#### Step 1: Rollback Backend
```bash
# List recent deployments
railway deployments list

# Identify previous stable deployment (look for commit before STORY-165)
# Should be commit: "test: add comprehensive test suite for STORY-165 [Task #6]" (previous)
railway rollback --to-deployment <previous-deployment-id>

# Monitor rollback completion
railway logs --follow
# Wait for: "Uvicorn running on"
```

#### Step 2: Rollback Frontend
```bash
# Option A: Vercel Dashboard
# 1. Navigate to https://vercel.com/your-project/deployments
# 2. Find previous stable deployment (before STORY-165 merge)
# 3. Click "..." → "Promote to Production"

# Option B: Vercel CLI
vercel rollback <previous-deployment-url>
```

#### Step 3: Validate Rollback
```bash
# Test backend health
curl https://smart-pncp-backend.up.railway.app/health | jq

# Test search (should work without quota check)
curl -X POST https://smart-pncp-backend.up.railway.app/buscar \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ufs":["SP"],"data_inicial":"2026-02-01","data_final":"2026-02-03","setor_id":"vestuario"}' | jq

# Verify: No "quota_used", "quota_remaining" fields in response (v0.2 behavior)
```

#### Step 4: Communication
- [ ] **Update team in Slack #alerts:**
  ```
  🚨 STORY-165 rollback executed at <timestamp>
  Reason: <brief description>
  Status: Production stable on v0.2
  Next steps: Root cause analysis, fix in progress
  ```

- [ ] **Create incident post-mortem:**
  - File: `docs/incidents/2026-02-03-story165-rollback.md`
  - Include: Timeline, root cause, lessons learned, prevention plan

---

## Success Criteria

### Deployment Considered Successful If:
- ✅ All smoke tests pass (backend + frontend)
- ✅ No 500 errors in first 2 hours
- ✅ P95 latency <15s (within 20% of baseline)
- ✅ Quota enforcement working correctly:
  - Free users: `excel_available=false`
  - Máquina users: `excel_available=true`
  - Quota exhaustion returns 403 with correct message
- ✅ No customer complaints about incorrect plan restrictions
- ✅ Upgrade modal displays when expected

### Metrics to Monitor Over Next 24 Hours:
1. **Error Rate:** <1% (target: <0.5%)
2. **P95 Latency:** <15s (target: <12.8s)
3. **Quota Check Success Rate:** >99%
4. **Upgrade Modal CTR:** >5% (of quota exhaustion events)
5. **Stripe Webhook Success:** 100% (any failure = critical)

---

## Emergency Contacts

**On-Call Engineer:** @oncall-dev (Slack)
**Database Admin:** @db-team (for Supabase issues)
**DevOps Lead:** @devops-lead (for Railway/Vercel issues)
**Product Owner:** @po (for rollback decision approval)

**Escalation Path:**
1. Minor issue (P95 latency spike) → @oncall-dev
2. Moderate issue (5% error rate) → @devops-lead
3. Critical issue (paid users blocked) → CTO + @po

---

## Appendix: Test User Credentials

### Free Trial User
```
Email: test-free@example.com
Password: Test123!
Expected: excel_available=false, quota_remaining=999999
```

### Consultor Ágil User
```
Email: test-consultor@example.com
Password: Test123!
Expected: excel_available=false, quota_remaining=50
```

### Máquina User
```
Email: test-maquina@example.com
Password: Test123!
Expected: excel_available=true, quota_remaining=300
```

### Sala de Guerra User
```
Email: test-sala@example.com
Password: Test123!
Expected: excel_available=true, quota_remaining=1000
```

---

**Checklist Version:** 1.0
**Last Updated:** 2026-02-03
**Next Review:** Post-deployment (T+24 hours)
