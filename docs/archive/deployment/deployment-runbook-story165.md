# Deployment Runbook - STORY-165: Plan Restructuring

**Story ID:** STORY-165
**Feature:** 3 Paid Tiers + FREE Trial with Plan Capabilities
**Version:** 1.0
**Created:** 2026-02-03
**Owner:** @devops
**Feature Flag:** `ENABLE_NEW_PRICING`
**Deployment Strategy:** Gradual Rollout (10% → 50% → 100%)

---

## Executive Summary

This runbook guides the production deployment of STORY-165, which introduces a new pricing structure (3 paid tiers + FREE trial) with plan-based capabilities enforcement. The deployment uses a **gradual rollout strategy** controlled by feature flag to minimize risk.

**Deployment Type:** Blue-Green + Feature Flag Gradual Rollout
**Estimated Duration:** 7 days (end-to-end)
**Critical Window:** First 48 hours after 100% rollout
**Rollback Mechanism:** Feature flag toggle (<30 seconds)

---

## Pre-Deployment Checklist

### Section 1: Development Readiness

- [ ] **All Tasks Complete:**
  - [ ] Task 1: Backend - Plan Capabilities (3 SP) ✅
  - [ ] Task 2: Backend - Date Range & Excel Validation (2 SP) ✅
  - [ ] Task 3: Backend - Quota & Rate Limiting (5 SP) ✅
  - [ ] Task 4: Backend - AI Summary Token Control (1 SP) ✅
  - [ ] Task 5: Backend - User Endpoint Enhancement (1 SP) ✅
  - [ ] Task 6: Frontend - Plan Badge & UI (2 SP) ✅
  - [ ] Task 7: Frontend - Excel & Date Range UX (3 SP) ✅
  - [ ] Task 8: Frontend - Quota Counter & Errors (2 SP) ✅
  - [ ] Task 9: Frontend - Upgrade Modal (2 SP) ✅
  - [ ] Task 10: Testing - Backend Suite (2 SP) ✅
  - [ ] Task 11: Testing - Frontend Suite (2 SP) ✅

- [ ] **Code Reviews:**
  - [ ] All PRs reviewed and approved
  - [ ] No outstanding comments/change requests
  - [ ] Security review complete (plan bypass vulnerabilities)

- [ ] **Git Status:**
  - [ ] All changes merged to `main` branch
  - [ ] Branch protection rules enabled
  - [ ] No uncommitted changes in `main`

### Section 2: Testing & Quality Assurance

- [ ] **Backend Testing:**
  - [ ] Unit test coverage ≥70% (target: 80% for STORY-165)
  - [ ] All 106 tests passing (STORY-165 test suite)
  - [ ] Integration tests passing (Supabase, Redis if enabled)
  - [ ] Edge cases tested:
    - [ ] Quota reset on 1st of month
    - [ ] Trial expiration (day 7)
    - [ ] Leap year date range
    - [ ] Timezone handling (UTC vs local)
    - [ ] Concurrent requests (race conditions)

- [ ] **Frontend Testing:**
  - [ ] Unit test coverage ≥60% (target: 70% for STORY-165)
  - [ ] All component tests passing
  - [ ] Integration tests passing (API calls)
  - [ ] UI/UX validation:
    - [ ] Plan badge renders correctly for all 4 tiers
    - [ ] Locked Excel button displays tooltip
    - [ ] Date range validation works in real-time
    - [ ] Quota counter updates correctly
    - [ ] Upgrade modal displays plan comparison

- [ ] **E2E Testing:**
  - [ ] Search flow (FREE trial user, 7-day limit)
  - [ ] Search flow (Consultor Ágil user, 30-day limit, no Excel)
  - [ ] Search flow (Máquina user, 1-year limit, Excel enabled)
  - [ ] Search flow (Sala de Guerra user, 5-year limit)
  - [ ] Quota exhaustion scenario
  - [ ] Trial expiration scenario
  - [ ] Upgrade CTA click tracking

- [ ] **Performance Testing:**
  - [ ] `/api/me` response time <500ms (quota check overhead)
  - [ ] `/api/buscar` response time unchanged (<6s for 1 state)
  - [ ] Database query performance acceptable (quota tracking)
  - [ ] Rate limiting does NOT degrade performance

### Section 3: Infrastructure Readiness

- [ ] **Backend (Railway):**
  - [ ] Environment variable configured: `ENABLE_NEW_PRICING=false` (start disabled)
  - [ ] Supabase connection verified (quota tracking table exists)
  - [ ] Redis connection verified (if enabled for rate limiting)
  - [ ] Health check endpoint passing: `/health`
  - [ ] Deployment successful in staging

- [ ] **Frontend (Vercel):**
  - [ ] No environment variable changes required (backend-driven)
  - [ ] Build successful
  - [ ] Deployment successful in staging

- [ ] **Database (Supabase):**
  - [ ] Migration applied:
    ```sql
    -- Users table updates
    ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_id VARCHAR(50) DEFAULT 'free_trial';
    ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP;

    -- Quota tracking table
    CREATE TABLE IF NOT EXISTS monthly_quota (
        user_id UUID REFERENCES users(id),
        month_year VARCHAR(7),  -- Format: "2026-02"
        searches_count INT DEFAULT 0,
        PRIMARY KEY (user_id, month_year)
    );
    ```
  - [ ] Database indexes created (if needed for performance)
  - [ ] Database backup created (pre-deployment snapshot)

### Section 4: Monitoring & Alerting

- [ ] **Railway Alerts Configured:**
  - [ ] CPU usage >80%
  - [ ] Memory usage >90%
  - [ ] Error rate >5%
  - [ ] Health check failures
  - [ ] Custom alert: 403 error rate >5%
  - [ ] Custom alert: 429 error rate >2%

- [ ] **Mixpanel Events Configured:**
  - [ ] `plan_limit_hit` (403 error tracking)
  - [ ] `quota_exhausted` (429 error tracking)
  - [ ] `upgrade_cta_clicked` (conversion tracking)
  - [ ] `trial_expiration_warning` (user engagement)

- [ ] **Alert Channels Tested:**
  - [ ] Slack notifications working
  - [ ] Email notifications working (if configured)
  - [ ] On-call schedule confirmed

### Section 5: Documentation

- [ ] **Technical Documentation:**
  - [ ] PRD.md updated with new pricing model
  - [ ] `docs/architecture/plan-capabilities.md` created
  - [ ] API documentation updated (`/api/me`, `/api/buscar` responses)
  - [ ] `docs/pricing.md` created (pricing comparison)

- [ ] **Operational Documentation:**
  - [ ] Rollback plan created: `docs/deployment/rollback-plan-story165.md` ✅
  - [ ] Deployment runbook created: `docs/deployment/deployment-runbook-story165.md` ✅
  - [ ] Monitoring guide updated (new metrics for STORY-165)

- [ ] **User-Facing Documentation:**
  - [ ] Help articles prepared (plan limits, upgrade process)
  - [ ] FAQ updated (trial period, quota limits, Excel export)
  - [ ] Onboarding materials updated (plan selection)

### Section 6: Stakeholder Communication

- [ ] **Internal Team:**
  - [ ] @pm briefed on deployment schedule
  - [ ] @qa briefed on post-deployment testing
  - [ ] @architect briefed on monitoring metrics
  - [ ] Support team briefed on new features (if applicable)

- [ ] **External Stakeholders:**
  - [ ] Users notified of upcoming changes (if applicable)
  - [ ] Marketing team briefed on new pricing (for launch)
  - [ ] Sales team briefed on plan features (for demos)

---

## Deployment Timeline & Milestones

### Overall Schedule (7 Days)

| Day | Phase | Activity | Duration | Go/No-Go |
|-----|-------|----------|----------|----------|
| **D+0** | Preparation | Pre-deployment checklist | 2 hours | ✅ |
| **D+0** | Staging | Deploy to staging, final validation | 2 hours | ✅ |
| **D+1** | Production | Blue-green deployment (feature flag OFF) | 30 min | ✅ |
| **D+1** | Rollout Phase 1 | Enable for 10% of users | Instant | ✅ Go/No-Go #1 |
| **D+2** | Monitoring | Monitor 10% rollout (24 hours) | 24 hours | - |
| **D+2** | Rollout Phase 2 | Increase to 50% of users | Instant | ✅ Go/No-Go #2 |
| **D+3** | Monitoring | Monitor 50% rollout (24 hours) | 24 hours | - |
| **D+3** | Rollout Phase 3 | Increase to 100% of users | Instant | ✅ Go/No-Go #3 |
| **D+4-5** | Critical Window | Intensive monitoring (48 hours) | 48 hours | - |
| **D+6** | Stabilization | Reduce monitoring frequency | Ongoing | - |
| **D+7** | Review | Post-deployment review meeting | 1 hour | - |

---

## Deployment Procedure

### Day 0: Pre-Deployment Preparation

#### Step 1: Final Staging Validation (2 hours)

**1.1 Deploy to Staging:**

```bash
# Backend (Railway staging)
cd D:\pncp-poc\backend
git checkout main
git pull origin main
railway link  # Select staging environment
railway up
railway logs --tail  # Monitor deployment

# Frontend (Vercel staging)
cd D:\pncp-poc\frontend
git checkout main
git pull origin main
vercel --prod  # Deploy to staging alias
```

**1.2 Run Smoke Tests:**

```bash
# Backend health check
curl https://bidiq-backend-staging.up.railway.app/health

# Test /api/me (feature flag OFF initially)
curl -X GET https://bidiq-backend-staging.up.railway.app/api/me \
  -H "Authorization: Bearer <staging-token>"
# Expected: No "capabilities" key

# Enable feature flag in staging
railway variables set ENABLE_NEW_PRICING=true

# Wait for redeployment (~90 seconds)
railway logs --tail

# Test /api/me again (feature flag ON)
curl -X GET https://bidiq-backend-staging.up.railway.app/api/me \
  -H "Authorization: Bearer <staging-token>"
# Expected: "capabilities" key present with plan limits

# Test date range validation (exceed 7-day limit for FREE trial)
curl -X POST https://bidiq-backend-staging.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <free-trial-token>" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2026-01-01",
    "dataFinal": "2026-01-30"
  }'
# Expected: 403 error with upgrade message
```

**1.3 Frontend Validation:**

1. Open staging URL: https://bidiq-uniformes-staging.vercel.app
2. Verify plan badge displays
3. Verify quota counter displays
4. Test locked Excel button (FREE trial user)
5. Test date range validation (warning appears)
6. Test upgrade modal (click locked Excel button)

**1.4 Rollback Test in Staging:**

```bash
# Toggle feature flag OFF
railway variables set ENABLE_NEW_PRICING=false

# Wait for redeployment (~90 seconds)
railway logs --tail

# Verify rollback
curl -X GET https://bidiq-backend-staging.up.railway.app/api/me
# Expected: No "capabilities" key (old behavior)

# Verify unlimited access restored
curl -X POST https://bidiq-backend-staging.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2025-01-01",  # 1+ year range
    "dataFinal": "2026-01-30"
  }'
# Expected: 200 OK (no 403 error)
```

**Staging Sign-Off:**
- [ ] All smoke tests passing
- [ ] Rollback tested successfully
- [ ] No errors in logs
- [ ] Approved by: _____________ Date: _____________

#### Step 2: Production Deployment Preparation (30 minutes)

**2.1 Database Backup:**

```bash
# Supabase dashboard
# Project → Database → Backups → Create Backup
# Label: "Pre-STORY-165-Deployment-YYYY-MM-DD"
```

**2.2 Verify Production Environment:**

```bash
# Check current feature flag status (should be OFF or not set)
railway variables --environment production
# ENABLE_NEW_PRICING should be "false" or absent
```

**2.3 Team Notification:**

```
📢 DEPLOYMENT NOTICE: STORY-165 (New Pricing)

Deployment Schedule:
- D+0 (Today): Blue-green deployment (feature flag OFF)
- D+1: Enable for 10% of users
- D+2: Increase to 50% (if 10% successful)
- D+3: Increase to 100% (if 50% successful)

Deployment Window: [HH:mm - HH:mm UTC]
On-Call: @devops (primary), @pm (backup)
Monitoring: Railway dashboard, Mixpanel, error logs

Rollback Plan: Feature flag toggle (<30 seconds)
See: docs/deployment/rollback-plan-story165.md

Questions: Tag @devops
```

---

### Day 1: Production Deployment (Blue-Green)

#### Step 1: Deploy Code to Production (30 minutes)

**1.1 Backend Deployment:**

```bash
cd D:\pncp-poc\backend
git checkout main
git pull origin main

# Link to production
railway link  # Select production environment

# Verify feature flag is OFF
railway variables
# ENABLE_NEW_PRICING=false (or not set)

# Deploy
railway up

# Monitor deployment
railway logs --tail
# Wait for: "Application startup complete"
```

**1.2 Verify Backend Health:**

```bash
# Health check
curl https://bidiq-backend-production.up.railway.app/health
# Expected: {"status":"healthy","timestamp":"..."}

# Test /api/me (feature flag OFF - should be old behavior)
curl -X GET https://bidiq-backend-production.up.railway.app/api/me \
  -H "Authorization: Bearer <production-token>"
# Expected: No "capabilities" key (old behavior)

# Test search (should work normally, no limits)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2025-01-01",  # 1+ year range
    "dataFinal": "2026-01-30"
  }'
# Expected: 200 OK (no 403 error)
```

**1.3 Frontend Deployment:**

```bash
cd D:\pncp-poc\frontend
git checkout main
git pull origin main

# Deploy to production
vercel --prod

# Monitor deployment
vercel inspect [deployment-url]
```

**1.4 Verify Frontend Health:**

1. Open production URL: https://bidiq-uniformes.vercel.app
2. ✅ Page loads in <2s
3. ✅ No JavaScript errors in console
4. ✅ All UI components render
5. ✅ No plan badge visible (feature flag OFF)
6. ✅ No quota counter visible (feature flag OFF)
7. ✅ Excel download button NOT locked (feature flag OFF)

**Production Deployment Status:**
- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] Health checks passing
- [ ] Feature flag OFF (verified)
- [ ] Old behavior confirmed (no plan limits)
- [ ] Approved by: _____________ Date: _____________

---

#### Step 2: Phase 1 Rollout - 10% of Users

**2.1 Enable Feature Flag for 10%:**

**Option A: Static 10% (All Users, Feature Flag Service)**

If using LaunchDarkly/Unleash:
```
1. Open feature flag dashboard
2. Find flag: "enable_new_pricing"
3. Set rollout: 10%
4. Target: All users (random 10%)
5. Save changes (instant propagation)
```

**Option B: Targeted 10% (Specific User Segments)**

```python
# Backend code (if not using feature flag service)
# backend/feature_flags.py

import hashlib

def is_feature_enabled_for_user(user_id: str, rollout_percentage: int = 10) -> bool:
    """
    Deterministic feature flag based on user_id hash.
    Same user_id always gets same result (consistent experience).
    """
    # Hash user_id to get a number between 0-99
    hash_val = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % 100

    # Enable for first X% of users
    return hash_val < rollout_percentage

# Usage in /api/buscar
ENABLE_NEW_PRICING = os.getenv("ENABLE_NEW_PRICING", "false").lower() == "true"
ROLLOUT_PERCENTAGE = int(os.getenv("ROLLOUT_PERCENTAGE", "0"))

if ENABLE_NEW_PRICING and is_feature_enabled_for_user(user_id, ROLLOUT_PERCENTAGE):
    # New behavior: Enforce plan limits
    quota_info = check_quota(user_id)
else:
    # Old behavior: No limits
    pass
```

**Deployment:**
```bash
# Set feature flag and rollout percentage
railway variables set ENABLE_NEW_PRICING=true
railway variables set ROLLOUT_PERCENTAGE=10

# Wait for redeployment (~90 seconds)
railway logs --tail
```

**2.2 Verify 10% Rollout:**

```bash
# Test with multiple user_ids (should see ~10% with new behavior)
for i in {1..10}; do
  user_id="test-user-$i"
  response=$(curl -s -X GET https://bidiq-backend-production.up.railway.app/api/me \
    -H "Authorization: Bearer <token-for-$user_id>")

  if echo "$response" | grep -q "capabilities"; then
    echo "User $user_id: NEW BEHAVIOR (plan limits)"
  else
    echo "User $user_id: OLD BEHAVIOR (no limits)"
  fi
done

# Expected: ~1 out of 10 users sees "NEW BEHAVIOR"
```

**2.3 Monitor 10% Rollout (24 hours):**

**Metrics to Track:**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Error rate (overall) | <2% | >5% (rollback) |
| 403 error rate | <1% | >5% (rollback) |
| 429 error rate | <0.5% | >2% (rollback) |
| Search success rate | >95% | <90% (rollback) |
| Upgrade CTA clicks | >1% | <0.5% (investigate) |
| Trial conversions | >5% | <2% (investigate) |
| Backend response time | <6s (95th %ile) | >10s (investigate) |
| Frontend load time | <2s | >4s (investigate) |

**Monitoring Checklist (Every 2 hours for 24h):**

- [ ] **Railway Dashboard:**
  - [ ] Error rate: _____% (target: <2%)
  - [ ] Response time: _____s (target: <6s)
  - [ ] CPU usage: _____% (target: <80%)
  - [ ] Memory usage: _____% (target: <90%)

- [ ] **Mixpanel Analytics:**
  - [ ] Search events: _____ total
  - [ ] 403 errors: _____ (target: <1% of searches)
  - [ ] 429 errors: _____ (target: <0.5% of searches)
  - [ ] Upgrade CTA clicks: _____ (target: >1% of limit hits)

- [ ] **Error Logs:**
  - [ ] No unexpected errors
  - [ ] 403/429 errors have correct messages
  - [ ] No database connection errors
  - [ ] No Redis connection errors (if enabled)

**Go/No-Go Decision #1 (After 24 hours):**

**GO Criteria (Increase to 50%):**
- [ ] Error rate <2%
- [ ] 403 error rate <1%
- [ ] 429 error rate <0.5%
- [ ] Search success rate >95%
- [ ] No P0/P1 bugs reported
- [ ] User feedback neutral or positive
- [ ] All monitoring targets met

**NO-GO Criteria (Stay at 10% or rollback):**
- [ ] Error rate ≥5% (immediate rollback)
- [ ] 403 error rate ≥5% (immediate rollback)
- [ ] Search success rate <90% (immediate rollback)
- [ ] P0 bug discovered (rollback, fix, re-deploy)
- [ ] Database integrity issues (rollback, investigate)

**Decision:**
- [ ] **GO** - Proceed to 50% rollout (Day 2)
- [ ] **NO-GO (Stay)** - Remain at 10%, investigate issues
- [ ] **NO-GO (Rollback)** - Rollback to 0%, fix critical issues

**Reason:** _________________________________

**Authorized By:** _____________ Date/Time: _____________

---

### Day 2: Phase 2 Rollout - 50% of Users

**Prerequisite:** Phase 1 (10%) successful for 24 hours

#### Step 1: Increase Rollout to 50%

**1.1 Update Feature Flag:**

```bash
# Update rollout percentage
railway variables set ROLLOUT_PERCENTAGE=50

# Wait for redeployment (~90 seconds)
railway logs --tail
```

**OR** (if using feature flag service):
```
1. Open feature flag dashboard
2. Find flag: "enable_new_pricing"
3. Set rollout: 50%
4. Save changes (instant propagation)
```

**1.2 Verify 50% Rollout:**

```bash
# Test with multiple user_ids (should see ~50% with new behavior)
for i in {1..10}; do
  user_id="test-user-$i"
  response=$(curl -s -X GET https://bidiq-backend-production.up.railway.app/api/me \
    -H "Authorization: Bearer <token-for-$user_id>")

  if echo "$response" | grep -q "capabilities"; then
    echo "User $user_id: NEW BEHAVIOR (plan limits)"
  else
    echo "User $user_id: OLD BEHAVIOR (no limits)"
  fi
done

# Expected: ~5 out of 10 users see "NEW BEHAVIOR"
```

**1.3 Monitor 50% Rollout (24 hours):**

Use same monitoring checklist as Phase 1 (10% rollout).

**Expected Changes:**
- 403/429 errors may increase proportionally (5x more users affected)
- Upgrade CTA clicks should increase proportionally
- Overall error rate should remain <2%
- Search success rate should remain >95%

**Go/No-Go Decision #2 (After 24 hours):**

**GO Criteria (Increase to 100%):**
- [ ] Error rate <2%
- [ ] 403 error rate <1%
- [ ] 429 error rate <0.5%
- [ ] Search success rate >95%
- [ ] No P0/P1 bugs reported
- [ ] User feedback neutral or positive
- [ ] All monitoring targets met
- [ ] Quota tracking accurate (spot-check Supabase)

**NO-GO Criteria (Stay at 50% or rollback):**
- [ ] Error rate ≥5% (immediate rollback)
- [ ] 403 error rate ≥5% (immediate rollback)
- [ ] Search success rate <90% (immediate rollback)
- [ ] P0 bug discovered (rollback, fix, re-deploy)
- [ ] Quota tracking issues (rollback, investigate)

**Decision:**
- [ ] **GO** - Proceed to 100% rollout (Day 3)
- [ ] **NO-GO (Stay)** - Remain at 50%, investigate issues
- [ ] **NO-GO (Rollback)** - Rollback to 10% or 0%, fix issues

**Reason:** _________________________________

**Authorized By:** _____________ Date/Time: _____________

---

### Day 3: Phase 3 Rollout - 100% of Users

**Prerequisite:** Phase 2 (50%) successful for 24 hours

#### Step 1: Increase Rollout to 100%

**1.1 Update Feature Flag:**

```bash
# Update rollout percentage to 100%
railway variables set ROLLOUT_PERCENTAGE=100

# Wait for redeployment (~90 seconds)
railway logs --tail
```

**OR** (if using feature flag service):
```
1. Open feature flag dashboard
2. Find flag: "enable_new_pricing"
3. Set rollout: 100%
4. Save changes (instant propagation)
```

**1.2 Verify 100% Rollout:**

```bash
# Test with multiple user_ids (ALL should see new behavior)
for i in {1..10}; do
  user_id="test-user-$i"
  response=$(curl -s -X GET https://bidiq-backend-production.up.railway.app/api/me \
    -H "Authorization: Bearer <token-for-$user_id>")

  if echo "$response" | grep -q "capabilities"; then
    echo "User $user_id: NEW BEHAVIOR (plan limits) ✅"
  else
    echo "User $user_id: OLD BEHAVIOR (no limits) ❌"
  fi
done

# Expected: 10 out of 10 users see "NEW BEHAVIOR"
```

**1.3 Post-Deployment Smoke Tests:**

```bash
# Test all 4 plan tiers

# 1. FREE Trial (7-day limit, no Excel)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <free-trial-token>" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2026-01-01",  # 30-day range (exceeds 7-day limit)
    "dataFinal": "2026-01-30"
  }'
# Expected: 403 error with upgrade message

# 2. Consultor Ágil (30-day limit, no Excel)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <consultor-agil-token>" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2026-01-01",  # 30-day range (at limit)
    "dataFinal": "2026-01-30"
  }'
# Expected: 200 OK, no Excel in response

# 3. Máquina (1-year limit, Excel enabled)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <maquina-token>" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2025-01-01",  # 1-year range
    "dataFinal": "2026-01-30"
  }'
# Expected: 200 OK, Excel included in response

# 4. Sala de Guerra (5-year limit, Excel enabled)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <sala-guerra-token>" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2021-01-01",  # 5-year range
    "dataFinal": "2026-01-30"
  }'
# Expected: 200 OK, Excel included in response
```

**Frontend Smoke Tests:**

1. Open production: https://bidiq-uniformes.vercel.app
2. Test FREE Trial User:
   - [ ] Plan badge displays: "FREE Trial (X dias restantes)"
   - [ ] Quota counter displays (if quota tracking enabled)
   - [ ] Excel button locked with 🔒 icon
   - [ ] Date range picker shows 7-day max warning
   - [ ] Upgrade modal opens on locked Excel click
3. Test Consultor Ágil User:
   - [ ] Plan badge displays: "Consultor Ágil"
   - [ ] Quota counter displays (50 searches/month)
   - [ ] Excel button locked with 🔒 icon
   - [ ] Date range picker shows 30-day max warning
4. Test Máquina User:
   - [ ] Plan badge displays: "Máquina"
   - [ ] Quota counter displays (300 searches/month)
   - [ ] Excel button functional (not locked)
   - [ ] Date range picker shows 1-year max warning
5. Test Sala de Guerra User:
   - [ ] Plan badge displays: "Sala de Guerra"
   - [ ] Quota counter displays (1000 searches/month)
   - [ ] Excel button functional (not locked)
   - [ ] Date range picker shows 5-year max warning

**100% Rollout Sign-Off:**
- [ ] All user tiers tested
- [ ] All smoke tests passing
- [ ] No errors in logs
- [ ] Approved by: _____________ Date: _____________

---

### Day 3-5: Critical Monitoring Window (48 Hours)

**Monitoring Intensity:** Every 2 hours for first 48 hours

**Key Metrics Dashboard:**

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Error Rate** | <2% | _____% | ✅ / ⚠️ / ❌ |
| **403 Error Rate** | <1% | _____% | ✅ / ⚠️ / ❌ |
| **429 Error Rate** | <0.5% | _____% | ✅ / ⚠️ / ❌ |
| **Search Success Rate** | >95% | _____% | ✅ / ⚠️ / ❌ |
| **Backend Response Time** | <6s | _____s | ✅ / ⚠️ / ❌ |
| **Frontend Load Time** | <2s | _____s | ✅ / ⚠️ / ❌ |
| **Upgrade CTA Clicks** | >1% | _____% | ✅ / ⚠️ / ❌ |
| **Trial Conversions** | >5% | _____% | ✅ / ⚠️ / ❌ |
| **Quota Tracking Accuracy** | 100% | _____% | ✅ / ⚠️ / ❌ |

**Monitoring Checklist (Every 2 hours):**

**Time: _____ (HH:mm UTC)**

- [ ] **Railway Dashboard:**
  - Error rate: _____% (target: <2%)
  - Response time: _____s (target: <6s)
  - CPU usage: _____% (target: <80%)
  - Memory usage: _____% (target: <90%)
  - Active requests: _____ (normal range)

- [ ] **Mixpanel Analytics:**
  - Search events: _____ (last 2 hours)
  - 403 errors: _____ (target: <1% of searches)
  - 429 errors: _____ (target: <0.5% of searches)
  - Upgrade CTA clicks: _____ (target: >1% of limit hits)
  - Conversion events: _____ (trial → paid)

- [ ] **Database Health (Supabase):**
  ```sql
  -- Check quota tracking
  SELECT COUNT(*) FROM monthly_quota;  -- Should increase over time

  -- Check trial expirations
  SELECT COUNT(*) FROM users WHERE trial_expires_at < NOW() AND plan_id = 'free_trial';

  -- Check plan distribution
  SELECT plan_id, COUNT(*) FROM users GROUP BY plan_id;
  ```

- [ ] **User Feedback:**
  - Support tickets: _____ (review for issues)
  - Social media mentions: _____ (sentiment analysis)
  - Feedback form submissions: _____ (review top complaints)

**Notes:** _________________________________

**On-Call Engineer:** _____________ Next Check: _____________

---

### Day 6: Stabilization

**Monitoring Intensity:** Reduce to every 4 hours

**Activities:**

1. **Review 48-Hour Metrics:**
   - Compile metrics from critical window
   - Identify trends (improving, stable, degrading)
   - Document any incidents or issues

2. **User Feedback Analysis:**
   - Review all support tickets related to new pricing
   - Categorize feedback (positive, neutral, negative)
   - Identify common pain points

3. **Performance Baseline:**
   - Establish new baseline for response times (with quota checks)
   - Establish new baseline for database query times
   - Document any performance impact

4. **Quota Tracking Audit:**
   ```sql
   -- Verify quota counters are accurate
   SELECT user_id, searches_count FROM monthly_quota WHERE month_year = '2026-02' ORDER BY searches_count DESC LIMIT 50;

   -- Check for anomalies (negative counts, impossibly high counts)
   SELECT COUNT(*) FROM monthly_quota WHERE searches_count < 0 OR searches_count > 10000;
   ```

5. **Plan for Long-Term Monitoring:**
   - Transition from intensive monitoring to normal cadence
   - Define long-term success metrics (conversion rate, churn, MRR)
   - Set up automated reports (weekly, monthly)

---

### Day 7: Post-Deployment Review

**Meeting Agenda (1 hour):**

**Attendees:** @devops, @pm, @qa, @architect, @dev

**1. Deployment Summary (10 min):**
- Timeline review (planned vs actual)
- Rollout phases (10% → 50% → 100%)
- Rollback events (if any)

**2. Metrics Review (15 min):**
- Error rates (overall, 403, 429)
- Search success rate
- Conversion metrics (upgrade CTA clicks, trial → paid)
- Performance impact (response times, load times)
- Quota tracking accuracy

**3. Issues & Incidents (15 min):**
- P0/P1 bugs discovered (if any)
- Rollback events (if any)
- User complaints (summary)
- Technical challenges

**4. Wins & Successes (10 min):**
- What went well?
- What exceeded expectations?
- Positive user feedback

**5. Lessons Learned (10 min):**
- What would we do differently?
- Process improvements
- Documentation gaps
- Monitoring gaps

**6. Action Items (10 min):**
- [ ] Bug fixes (if needed)
- [ ] UX improvements (based on feedback)
- [ ] Monitoring enhancements
- [ ] Documentation updates
- [ ] Next feature planning

**Meeting Notes:** _________________________________

**Action Items Owner:** _____________ Due Date: _____________

---

## Success Criteria

### Deployment Success

- [ ] **All Rollout Phases Complete:**
  - [ ] 10% rollout successful (24 hours)
  - [ ] 50% rollout successful (24 hours)
  - [ ] 100% rollout successful (48 hours)
  - [ ] No rollbacks required

- [ ] **Technical Metrics:**
  - [ ] Error rate <2% (overall)
  - [ ] 403 error rate <1% (plan limit hits)
  - [ ] 429 error rate <0.5% (quota exhaustion)
  - [ ] Search success rate >95%
  - [ ] Backend response time <6s (95th percentile)
  - [ ] Frontend load time <2s (median)

- [ ] **Feature Functionality:**
  - [ ] All 4 plan tiers working correctly
  - [ ] Date range validation enforced
  - [ ] Excel gating working correctly
  - [ ] Quota tracking accurate
  - [ ] Trial expiration logic correct
  - [ ] Upgrade modal functional

### Business Success (Week 1-4)

- [ ] **User Engagement:**
  - [ ] Trial signups increase ≥10%
  - [ ] Trial-to-paid conversion rate ≥5% (target: 10-15%)
  - [ ] Upgrade CTA click-through rate ≥1%
  - [ ] User churn rate unchanged or decreased

- [ ] **Revenue Metrics (Future):**
  - [ ] First paid user acquired (within 2 weeks)
  - [ ] MRR (Monthly Recurring Revenue) growing
  - [ ] Average revenue per user (ARPU) increasing

- [ ] **User Satisfaction:**
  - [ ] Net Promoter Score (NPS) ≥50
  - [ ] Support ticket rate unchanged or decreased
  - [ ] Positive sentiment in feedback (>70%)

### Long-Term Success (Month 1-3)

- [ ] **Conversion Optimization:**
  - [ ] Trial-to-paid conversion rate ≥10%
  - [ ] Upgrade from Consultor Ágil to Máquina ≥5%
  - [ ] Upgrade from Máquina to Sala de Guerra ≥2%

- [ ] **Retention:**
  - [ ] Monthly churn rate <10%
  - [ ] User lifetime value (LTV) increasing
  - [ ] Repeat searches per user increasing

- [ ] **Platform Stability:**
  - [ ] Uptime ≥99.9%
  - [ ] Error rate consistently <1%
  - [ ] No quota tracking errors
  - [ ] No trial expiration bugs

---

## Risk Assessment & Mitigation

### High-Risk Scenarios

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Quota tracking failure** | Medium | Critical | - Extensive testing before deployment<br>- Database indexes optimized<br>- Fallback to unlimited access if DB unavailable<br>- Real-time monitoring of quota queries |
| **Trial expiration bug** | Medium | High | - Edge case testing (timezone, leap year)<br>- Dry-run in staging with manipulated dates<br>- Grace period (1 day) for expired trials<br>- Manual override capability |
| **403/429 error rate spike** | Medium | High | - Gradual rollout (10% → 50% → 100%)<br>- Feature flag instant rollback<br>- Clear error messages with upgrade CTAs<br>- User support prepared for questions |
| **Performance degradation** | Low | Medium | - Database query optimization<br>- Redis caching for quota checks (optional)<br>- Load testing before deployment<br>- Rollback if response time >10s |
| **User confusion** | High | Low | - Clear UI/UX design (locked buttons, tooltips)<br>- Help articles and FAQs<br>- Onboarding materials updated<br>- Support team briefed |
| **Database migration failure** | Low | Critical | - Database backup before migration<br>- Migration tested in staging<br>- Rollback SQL prepared<br>- Migration can be re-run if needed |

### Known Issues (Accepted)

| Issue | Severity | Workaround | Fix Plan |
|-------|----------|------------|----------|
| **Redis not yet integrated** | P2 | Use in-memory rate limiting (or skip rate limiting) | Week 2 cleanup |
| **Payment integration TBD** | P2 | Upgrade modal shows plans but no payment (manual setup) | Future story (STORY-166) |
| **Quota reset logic not automated** | P2 | Quota resets on first search of new month (lazy reset) | Week 2 cleanup (add cron job) |

---

## Rollback Plan Reference

**See:** `docs/deployment/rollback-plan-story165.md`

**Quick Rollback Steps:**

1. **Toggle Feature Flag OFF:**
   ```bash
   railway variables set ENABLE_NEW_PRICING=false
   # OR: ROLLOUT_PERCENTAGE=0
   ```

2. **Verify Rollback:**
   ```bash
   curl https://bidiq-backend-production.up.railway.app/api/me
   # Expected: No "capabilities" key
   ```

3. **Notify Team:**
   ```
   🚨 FEATURE ROLLBACK: STORY-165
   Reason: [brief description]
   Status: Rollback complete (<30 seconds)
   Next Steps: [investigation / hotfix / etc.]
   ```

4. **Create Incident Report:**
   - File: `docs/incidents/story165-rollback-YYYY-MM-DD-HHmm.md`
   - See rollback plan for template

---

## Stakeholder Communication Plan

### Pre-Deployment (Day -1)

**Audience:** Internal team, early users (if applicable)

**Message:**
```
📢 NEW FEATURE LAUNCH: Smart Pricing

We're launching our new pricing structure:
- FREE Trial (7 days)
- Consultor Ágil (R$ 297/month)
- Máquina (R$ 597/month)
- Sala de Guerra (R$ 1497/month)

Launch Schedule:
- Day 1: 10% of users (test phase)
- Day 2: 50% of users (expansion)
- Day 3: 100% of users (full launch)

What to expect:
- Plan badge in header
- Quota counter for monthly searches
- Excel export gated (Máquina+ only)
- Date range limits by plan

Questions? Contact @pm or @devops.
```

### During Rollout (Day 1-3)

**Frequency:** Daily updates (if significant events)

**Message:**
```
📊 PRICING ROLLOUT UPDATE: Day X

Rollout Status: [10% / 50% / 100%]
Users Affected: [X total]
Success Metrics:
- Error rate: [X%] ✅
- Upgrade clicks: [X] ✅
- User feedback: [Positive / Neutral / Negative]

Next Steps:
- [Continue monitoring / Increase to 50% / etc.]

Issues: [None / See incident report]
```

### Post-Deployment (Day 7)

**Audience:** All stakeholders, marketing, sales

**Message:**
```
✅ PRICING ROLLOUT COMPLETE: STORY-165

100% rollout achieved successfully!

Final Metrics:
- Uptime: [99.X%]
- Error rate: [X%] (target: <2%)
- Conversion rate: [X%] (target: >5%)
- User feedback: [X% positive]

Key Learnings:
- [Lesson 1]
- [Lesson 2]

Next Steps:
- [Payment integration (STORY-166)]
- [Marketing launch]
- [Sales enablement]

Full Report: [link to post-deployment review doc]
```

---

## Appendix A: Environment Variables Reference

### Backend (Railway)

| Variable | Purpose | Default | Production Value |
|----------|---------|---------|------------------|
| `ENABLE_NEW_PRICING` | Master feature flag | `false` | `true` (after gradual rollout) |
| `ROLLOUT_PERCENTAGE` | Percentage of users with feature enabled | `0` | `100` (after gradual rollout) |
| `SUPABASE_URL` | Supabase connection | - | `https://[project-id].supabase.co` |
| `SUPABASE_KEY` | Supabase API key | - | `eyJ...` |
| `REDIS_URL` | Redis connection (optional) | - | `redis://...` (if enabled) |

### Frontend (Vercel)

No environment variable changes required. Frontend behavior driven by backend API responses.

---

## Appendix B: Database Schema Reference

### Users Table Updates

```sql
-- Add plan tracking columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_id VARCHAR(50) DEFAULT 'free_trial';
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMP;

-- Add index for trial expiration queries
CREATE INDEX IF NOT EXISTS idx_users_trial_expires ON users(trial_expires_at);
```

### Quota Tracking Table

```sql
-- Create monthly quota tracking table
CREATE TABLE IF NOT EXISTS monthly_quota (
    user_id UUID REFERENCES users(id),
    month_year VARCHAR(7),  -- Format: "2026-02"
    searches_count INT DEFAULT 0,
    last_search_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, month_year)
);

-- Add index for quota queries
CREATE INDEX IF NOT EXISTS idx_monthly_quota_month ON monthly_quota(month_year);
CREATE INDEX IF NOT EXISTS idx_monthly_quota_user ON monthly_quota(user_id);
```

---

## Appendix C: Contact Information

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| **DevOps Lead (Primary)** | @devops | ____________ | 24/7 during rollout (Day 1-5) |
| **Project Manager (Secondary)** | @pm | ____________ | Business hours + on-call |
| **Architect (Backup)** | @architect | ____________ | On-call rotation |
| **QA Lead** | @qa | ____________ | Business hours |

**External Support:**
- Railway: https://railway.app/help
- Vercel: https://vercel.com/support
- Supabase: support@supabase.io

---

## Document Metadata

**Document Version:** 1.0
**Created:** 2026-02-03
**Last Updated:** 2026-02-03
**Owner:** @devops
**Reviewed By:** @pm, @architect
**Next Review:** After deployment completion

**Related Documents:**
- Rollback Plan: `docs/deployment/rollback-plan-story165.md`
- Story: `docs/stories/STORY-165-plan-restructuring.md`
- Pre-Deployment Checklist: `docs/deployment/pre-deployment-checklist.md`
- Monitoring Guide: `docs/runbooks/monitoring-alerting-setup.md`

**Change Log:**
- 2026-02-03: Initial version created for STORY-165
