# Production Rollout Checklist - STORY-165

**Feature:** Plan Restructuring & Quota Enforcement
**Story ID:** STORY-165
**Version:** 1.0
**Created:** February 4, 2026
**Owner:** @devops-lead

---

## Overview

This checklist guides the phased production rollout of STORY-165 from 10% → 50% → 100% deployment. Each phase has validation gates, success criteria, and rollback triggers.

**Phases:**
1. Pre-Rollout Validation (before 10%)
2. 10% Rollout Checklist
3. 50% Rollout Checklist
4. 100% Rollout Checklist
5. Post-Rollout Validation

---

## Phase 0: Pre-Rollout Validation

### ✅ Staging Success Validation
**Timeline:** February 4-5, 2026 (2 days minimum)
**Owner:** @qa + @devops-lead

#### Code Quality
- [ ] **Backend Tests:** 106 passing (≥70% coverage)
  - Command: `cd backend && pytest --cov`
  - Expected: All tests pass, coverage report shows >70%
  - Location: `backend/htmlcov/index.html`

- [ ] **Frontend Tests:** 69 passing (≥60% coverage)
  - Command: `cd frontend && npm test -- --coverage`
  - Expected: All tests pass, coverage >60%
  - Location: `frontend/coverage/index.html`

- [ ] **E2E Tests:** 60 passing (Playwright)
  - Command: `cd frontend && npm run test:e2e`
  - Expected: All flows pass (search, quota, excel, upgrade)

- [ ] **Linting:** No errors
  - Backend: `cd backend && ruff check .`
  - Frontend: `cd frontend && npm run lint`

#### Staging Environment Health
- [ ] **Staging URL accessible:** https://bidiq-frontend-staging.railway.app
  - Manual check: Open URL, verify homepage loads

- [ ] **Backend health check passing:**
  - Command: `curl https://bidiq-uniformes-staging.railway.app/health`
  - Expected: `{"status":"healthy"}`

- [ ] **Database indexes created:**
  ```sql
  -- Run in Supabase SQL Editor (Production DB)
  CREATE INDEX IF NOT EXISTS idx_subscriptions_user_active
    ON user_subscriptions(user_id, status)
    WHERE status = 'active';

  CREATE INDEX IF NOT EXISTS idx_monthly_quota_user_month
    ON monthly_quota(user_id, month_year);

  CREATE INDEX IF NOT EXISTS idx_search_sessions_user_created
    ON search_sessions(user_id, created_at DESC);
  ```
  - Verify: `SELECT * FROM pg_indexes WHERE tablename IN ('user_subscriptions', 'monthly_quota', 'search_sessions');`

- [ ] **Test users exist in production:**
  - Login with: free@test.com, consultor@test.com, maquina@test.com, sala@test.com
  - Verify: Each user has correct `plan_id` in database

#### Smoke Tests (All 6 Scenarios Pass)
- [ ] **Scenario 1:** FREE Trial user can search 7-day range, Excel blocked
- [ ] **Scenario 2:** Consultor Ágil quota exhaustion triggers 429 error
- [ ] **Scenario 3:** Máquina user can download Excel
- [ ] **Scenario 4:** Date range validation blocks 62-day search on 30-day plan
- [ ] **Scenario 5:** Rate limiting enforces 10 req/min for Consultor Ágil
- [ ] **Scenario 6:** Upgrade modal opens when clicking locked Excel button

**Validation Script:**
```bash
# Run comprehensive smoke tests
cd docs/deployment
bash smoke-tests-story165.sh
# Expected output: "✅ All 6 smoke tests passed"
```

#### Performance Baseline
- [ ] **Record current metrics:**
  - Error rate: ___% (target: <0.5%)
  - P95 latency (light search): ___s (target: ~3.2s)
  - P95 latency (medium search): ___s (target: ~8.4s)
  - Health check uptime: ___% (target: 100%)

- [ ] **Supabase baseline:**
  - Connection pool usage: ___ connections (target: <10)
  - Avg query time (searches table): ___ms (target: <50ms)

**Collection Method:**
```bash
# Railway metrics (last 24 hours)
railway metrics --project bidiq-uniformes-production --json > baseline.json

# Supabase metrics
# Navigate to: https://app.supabase.com/project/{project-id}/database/query-performance
# Export last 24 hours as CSV
```

#### Team Readiness
- [ ] **On-call engineer assigned:** @_____ (24-hour coverage)
  - Contact: Slack @oncall-dev
  - Backup: @devops-lead

- [ ] **War room created:** Slack #smart-pncp-war-room
  - Members: @oncall-dev, @devops-lead, @pm, @qa, @architect

- [ ] **Rollback procedure tested:**
  - Dry run: Set feature flag to 0%, verify old pricing active
  - Document results: `docs/deployment/rollback-dry-run-results.md`

- [ ] **Stakeholders notified:**
  - Announcement sent to #smart-pncp-general
  - Email sent to: Product, Support, Marketing teams
  - Timeline shared: 10% (Feb 6) → 50% (Feb 7) → 100% (Feb 8)

#### Documentation
- [ ] **Runbooks updated:**
  - `docs/deployment/deployment-runbook-story165.md`
  - `docs/deployment/oncall-quick-reference-story165.md`
  - `docs/deployment/rollback-plan-story165.md`

- [ ] **Monitoring dashboards configured:**
  - Railway: Error rate, latency, CPU, memory
  - Supabase: Connection pool, query performance
  - Custom: Quota exhaustion events, upgrade CTR (if available)

#### GO/NO-GO Decision
- [ ] **All checklist items above complete:** ☐ YES / ☐ NO
- [ ] **No P0/P1 bugs in backlog:** ☐ YES / ☐ NO
- [ ] **QA sign-off received:** @qa ___________
- [ ] **DevOps sign-off received:** @devops-lead ___________
- [ ] **PM sign-off received:** @pm ___________

**Decision:** ☐ GO ☐ NO-GO
**Date/Time:** _____________
**Next Gate:** Production 10% Rollout (February 6, 2026)

---

## Phase 1: Production 10% Rollout

### ✅ Pre-Deployment (T-1 hour)
**Timeline:** February 6, 2026, 9:00 AM BRT
**Owner:** @devops-lead

#### Environment Preparation
- [ ] **Railway production environment ready:**
  - Backend: https://bidiq-uniformes-production.up.railway.app
  - Frontend: https://bidiq-frontend-production.up.railway.app

- [ ] **Feature flag configured:**
  - Set: `ENABLE_NEW_PRICING=0%` (disabled, pre-deployment)
  - Verify: `curl https://bidiq-uniformes-production.up.railway.app/api/feature-flags`
  - Expected: `{"ENABLE_NEW_PRICING": 0}`

- [ ] **Monitoring dashboards open:**
  - Railway metrics: https://railway.app/project/{project-id}/metrics
  - Supabase dashboard: https://app.supabase.com/project/{project-id}
  - Slack #smart-pncp-war-room: Ready for alerts

- [ ] **Rollback script ready:**
  ```bash
  # Create rollback script (save as rollback-10pct.sh)
  #!/bin/bash
  echo "Rolling back STORY-165 (10% → 0%)..."
  railway variables --set ENABLE_NEW_PRICING=0
  echo "Waiting 30s for rollout..."
  sleep 30
  curl https://bidiq-uniformes-production.up.railway.app/health
  echo "Rollback complete. Verify old pricing active."
  ```
  - Make executable: `chmod +x rollback-10pct.sh`

#### Team Communication
- [ ] **War room announcement:**
  ```
  🚀 STORY-165 Production 10% Rollout - STARTING

  **Timeline:**
  - T+0: Enable feature flag (10%)
  - T+15min: Initial validation
  - T+1hr: Performance check
  - T+24hr: Decision for 50% rollout

  **On-Call:** @oncall-dev
  **Rollback SLA:** 5 minutes
  **War Room:** #smart-pncp-war-room
  ```

### ✅ Deployment (T=0, ~5 minutes)
**Timeline:** 10:00 AM BRT (exact time)

- [ ] **Enable feature flag (10%):**
  ```bash
  # Set feature flag via Railway CLI
  railway variables --set ENABLE_NEW_PRICING=10

  # Verify deployment
  sleep 30  # Wait for config propagation
  curl https://bidiq-uniformes-production.up.railway.app/api/feature-flags
  # Expected: {"ENABLE_NEW_PRICING": 10}
  ```

- [ ] **Verify deployment:**
  - Backend restarted: Check Railway logs for "Uvicorn running"
  - Frontend reloaded: Check Railway logs for "Next.js started"
  - Health check passing: `curl .../health` returns `{"status":"healthy"}`

- [ ] **Announce deployment complete:**
  ```
  ✅ STORY-165 10% Rollout - DEPLOYED

  **Status:** Feature flag enabled at 10%
  **Time:** {timestamp}
  **Next Check:** T+15min (initial validation)

  Monitoring in progress...
  ```

### ✅ Initial Validation (T+15 minutes)
**Timeline:** 10:15 AM BRT
**Owner:** @oncall-dev

#### Technical Health
- [ ] **No 500 errors in logs:**
  ```bash
  railway logs --project bidiq-uniformes-production --filter "500" --since 15m
  # Expected: No results
  ```

- [ ] **Quota check success rate >99%:**
  - Check Railway metrics: Error rate for `/api/buscar` endpoint
  - Expected: <1% error rate

- [ ] **Health endpoint healthy:**
  ```bash
  curl https://bidiq-uniformes-production.up.railway.app/health
  # Expected: {"status":"healthy", "database":"connected"}
  ```

- [ ] **Supabase connection pool normal:**
  - Navigate to Supabase dashboard → Database → Connections
  - Expected: <15 active connections

#### User Experience
- [ ] **Test FREE trial user flow:**
  1. Login as free@test.com
  2. Verify plan badge shows "FREE Trial"
  3. Attempt 10-day search (should warn about 7-day limit)
  4. Click locked Excel button (should open upgrade modal)

- [ ] **Test Máquina user flow:**
  1. Login as maquina@test.com
  2. Verify Excel button enabled (no lock icon)
  3. Execute search, download Excel
  4. Verify file downloads successfully

#### Rollback Decision Point
- [ ] **All validation items passing:** ☐ YES / ☐ NO
- [ ] **Error rate <1%:** ☐ YES / ☐ NO
- [ ] **No customer complaints (support tickets):** ☐ YES / ☐ NO

**Decision:** ☐ CONTINUE ☐ ROLLBACK
**If ROLLBACK:** Execute `./rollback-10pct.sh` immediately

### ✅ Performance Check (T+1 hour)
**Timeline:** 11:00 AM BRT
**Owner:** @oncall-dev

#### Latency Metrics
- [ ] **P95 latency <15s (light search):**
  - Railway metrics: Check /api/buscar endpoint latency
  - Expected: <15s (ideal: <12.8s)

- [ ] **Quota check latency <200ms:**
  - Backend logs: Search for "check_quota duration"
  - Expected: P95 <200ms

- [ ] **Supabase query time <100ms:**
  - Supabase dashboard → Query Performance
  - Check: `monthly_quota` and `user_subscriptions` tables

#### Business Metrics (If Available)
- [ ] **Quota exhaustion events logged:**
  - Backend logs: Search for "quota_exhausted"
  - Expected: 0-5 events (10% traffic, early data)

- [ ] **Upgrade modal impressions tracked:**
  - Frontend analytics: Check console logs for "upgrade_modal_shown"
  - Expected: >0 impressions (if any FREE users in 10%)

- [ ] **Excel enforcement working:**
  - Backend logs: Search for "excel_blocked"
  - Expected: >0 events (if any FREE/Consultor users tried)

#### Incident Check
- [ ] **No incidents reported:**
  - Slack #smart-pncp-incidents: 0 messages
  - Support tickets: 0 related to STORY-165
  - On-call pager: 0 alerts

### ✅ 24-Hour Monitoring (T+24 hours)
**Timeline:** February 7, 2026, 10:00 AM BRT
**Owner:** @oncall-dev → @devops-lead (handoff)

#### Reliability Metrics
- [ ] **Error rate <1%:** ___% (Railway metrics)
- [ ] **P95 latency <15s:** ___s (Railway metrics)
- [ ] **Health check uptime 100%:** ___% (Railway uptime)
- [ ] **Zero rollbacks executed:** ☐ YES / ☐ NO

#### Business Metrics
- [ ] **Quota exhaustion events:** ___ events (expected: 5-20/day for 10% traffic)
- [ ] **Upgrade modal CTR:** ___% (expected: >5% if data available)
- [ ] **Customer complaints:** ___ tickets (expected: 0-2 max)

#### GO/NO-GO Decision for 50% Rollout
- [ ] **All metrics within targets:** ☐ YES / ☐ NO
- [ ] **Zero P0/P1 incidents:** ☐ YES / ☐ NO
- [ ] **Customer feedback neutral/positive:** ☐ YES / ☐ NO
- [ ] **DevOps confidence high:** ☐ YES / ☐ NO
- [ ] **PM approval for 50% rollout:** @pm ___________

**Decision:** ☐ GO to 50% ☐ NO-GO (investigate issues)
**Date/Time:** _____________
**Next Gate:** Production 50% Rollout (February 7, 2026)

---

## Phase 2: Production 50% Rollout

### ✅ Pre-Deployment (T-30 minutes)
**Timeline:** February 7, 2026, 10:00 AM BRT
**Owner:** @devops-lead

#### Validation from 10% Rollout
- [ ] **10% deployment stable for 24+ hours:** ☐ YES / ☐ NO
- [ ] **Error rate from 10%:** ___% (must be <1%)
- [ ] **Customer complaints from 10%:** ___ (must be <3)
- [ ] **Performance from 10%:** P95 ___s (must be <15s)

#### Environment Check
- [ ] **Railway production healthy:**
  ```bash
  curl https://bidiq-uniformes-production.up.railway.app/health
  # Expected: {"status":"healthy"}
  ```

- [ ] **Supabase healthy:**
  - Connection pool: ___ connections (<15)
  - CPU usage: ___% (<50%)
  - No deadlocks: ☐ YES / ☐ NO

- [ ] **Feature flag current state:**
  ```bash
  railway variables --get ENABLE_NEW_PRICING
  # Expected: 10
  ```

#### Team Readiness
- [ ] **On-call engineer ready:** @_____ (same or new?)
- [ ] **War room active:** #smart-pncp-war-room
- [ ] **Rollback script updated:**
  ```bash
  # rollback-50pct.sh
  #!/bin/bash
  echo "Rolling back STORY-165 (50% → 10%)..."
  railway variables --set ENABLE_NEW_PRICING=10
  sleep 30
  curl .../health
  echo "Rollback to 10% complete."
  ```

### ✅ Deployment (T=0, ~5 minutes)
**Timeline:** 10:30 AM BRT

- [ ] **Enable feature flag (50%):**
  ```bash
  railway variables --set ENABLE_NEW_PRICING=50
  sleep 30
  curl .../api/feature-flags
  # Expected: {"ENABLE_NEW_PRICING": 50}
  ```

- [ ] **Verify deployment:**
  - Backend restarted: ☐ YES
  - Health check passing: ☐ YES
  - Logs show no errors: ☐ YES

- [ ] **Announce deployment:**
  ```
  ✅ STORY-165 50% Rollout - DEPLOYED

  **Status:** Feature flag enabled at 50%
  **Time:** {timestamp}
  **Monitoring:** Next 24 hours

  @oncall-dev monitoring...
  ```

### ✅ Initial Validation (T+15 minutes)
**Timeline:** 10:45 AM BRT
**Owner:** @oncall-dev

- [ ] **No 500 errors:** Railway logs clean
- [ ] **Error rate <1%:** Railway metrics
- [ ] **Quota check success rate >99%:** ☐ YES / ☐ NO
- [ ] **Supabase connection pool <15:** ☐ YES / ☐ NO
- [ ] **No customer complaints:** Support tickets = 0

**Decision:** ☐ CONTINUE ☐ ROLLBACK to 10%

### ✅ Performance Check (T+1 hour)
**Timeline:** 11:30 AM BRT

- [ ] **P95 latency <15s:** ___s (Railway metrics)
- [ ] **Quota check latency <200ms:** ___ms (backend logs)
- [ ] **Supabase query time <100ms:** ___ms (Supabase dashboard)
- [ ] **No performance degradation vs. 10%:** ☐ YES / ☐ NO

### ✅ 24-Hour Monitoring (T+24 hours)
**Timeline:** February 8, 2026, 10:30 AM BRT

#### Reliability Metrics
- [ ] **Error rate <1%:** ___% (target: <0.5% for 100%)
- [ ] **P95 latency <15s:** ___s
- [ ] **Health check uptime 100%:** ___%
- [ ] **Zero rollbacks executed:** ☐ YES / ☐ NO

#### Business Metrics
- [ ] **Quota exhaustion events:** ___ events (expected: 25-100/day for 50% traffic)
- [ ] **Upgrade modal CTR:** ___% (expected: >5%)
- [ ] **Early conversions:** ___ paid upgrades (expected: ≥1)
- [ ] **Customer complaints:** ___ tickets (expected: <5)

#### GO/NO-GO Decision for 100% Rollout
- [ ] **All metrics within targets:** ☐ YES / ☐ NO
- [ ] **Conversion metrics healthy:** ☐ YES / ☐ NO (CTR >5%)
- [ ] **Customer feedback acceptable:** ☐ YES / ☐ NO (<5 complaints)
- [ ] **Infrastructure stable:** ☐ YES / ☐ NO (no scaling issues)
- [ ] **DevOps + PM approval:** @devops-lead _____ @pm _____

**Decision:** ☐ GO to 100% ☐ NO-GO (extend monitoring or rollback)
**Date/Time:** _____________
**Next Gate:** Production 100% Rollout (February 8, 2026)

---

## Phase 3: Production 100% Rollout

### ✅ Pre-Deployment (T-30 minutes)
**Timeline:** February 8, 2026, 10:00 AM BRT
**Owner:** @devops-lead + @pm

#### Validation from 50% Rollout
- [ ] **50% deployment stable for 24+ hours:** ☐ YES / ☐ NO
- [ ] **Error rate from 50%:** ___% (must be <0.5%)
- [ ] **Conversion metrics from 50%:** CTR ___% (must be >5%)
- [ ] **Customer complaints from 50%:** ___ (must be <5)
- [ ] **Performance from 50%:** P95 ___s (must be <15s)

#### Final Checks
- [ ] **Railway production healthy:** Health check passing
- [ ] **Supabase healthy:** Connection pool <15, CPU <50%
- [ ] **Feature flag current state:** ENABLE_NEW_PRICING=50

#### Stakeholder Alignment
- [ ] **PM approval:** @pm ___________ (business readiness)
- [ ] **DevOps approval:** @devops-lead ___________ (technical stability)
- [ ] **CTO awareness:** @cto notified (optional sign-off)

#### Documentation Ready
- [ ] **PRD.md updated:** New pricing model documented
- [ ] **docs/architecture/plan-capabilities.md:** Created
- [ ] **API docs updated:** /api/me and /api/buscar responses
- [ ] **Pricing page ready:** Marketing site (or docs/pricing.md)

### ✅ Deployment (T=0, ~5 minutes)
**Timeline:** 10:30 AM BRT

- [ ] **Enable feature flag (100%):**
  ```bash
  railway variables --set ENABLE_NEW_PRICING=100
  sleep 30
  curl .../api/feature-flags
  # Expected: {"ENABLE_NEW_PRICING": 100}
  ```

- [ ] **Verify deployment:**
  - Backend restarted: ☐ YES
  - Frontend reloaded: ☐ YES
  - Health check passing: ☐ YES
  - Logs show no errors: ☐ YES

- [ ] **Announce deployment:**
  ```
  🎉 STORY-165 100% Rollout - COMPLETE

  **Status:** Feature flag enabled at 100%
  **Time:** {timestamp}
  **Milestone:** New pricing model fully deployed

  Monitoring for next 48 hours...
  ```

### ✅ Initial Validation (T+30 minutes)
**Timeline:** 11:00 AM BRT
**Owner:** @oncall-dev

#### Technical Health
- [ ] **No 500 errors:** Railway logs clean (last 30 min)
- [ ] **Error rate <1%:** ___% (Railway metrics)
- [ ] **Quota check success rate >99%:** ☐ YES / ☐ NO
- [ ] **Supabase connection pool <20:** ___ connections
- [ ] **No timeout errors:** Logs show no DB timeouts

#### User Experience
- [ ] **FREE trial flow working:** Test with free@test.com
- [ ] **Consultor Ágil quota enforcing:** Test quota exhaustion
- [ ] **Máquina Excel export working:** Download successful
- [ ] **Upgrade modal functional:** Triggers on locked features

#### Business Metrics (Early Data)
- [ ] **Quota exhaustion events:** ___ events (first hour)
- [ ] **Upgrade modal impressions:** ___ impressions
- [ ] **No critical customer complaints:** Support tickets = 0

**Decision:** ☐ CONTINUE ☐ ROLLBACK to 50%

### ✅ Performance Check (T+2 hours)
**Timeline:** 12:30 PM BRT

- [ ] **P95 latency <15s:** ___s (must be <15s)
- [ ] **Error rate <0.5%:** ___% (long-term target)
- [ ] **Quota check latency <200ms:** ___ms
- [ ] **Supabase query time <50ms:** ___ms (avg)
- [ ] **No performance degradation vs. 50%:** ☐ YES / ☐ NO

### ✅ 48-Hour Monitoring (T+48 hours)
**Timeline:** February 10, 2026, 10:30 AM BRT

#### Reliability Metrics (Week 1 Targets)
- [ ] **Error rate <0.5%:** ___% (sustained)
- [ ] **P95 latency <12.8s:** ___s (ideal target)
- [ ] **Health check uptime 100%:** ___%
- [ ] **Zero rollbacks executed:** ☐ YES / ☐ NO

#### Business Metrics (Week 1 Targets)
- [ ] **Quota exhaustion events:** ___ events/day (expected: 50-200/day for 100% traffic)
- [ ] **Upgrade modal CTR:** ___% (target: >5%)
- [ ] **Conversions (quota → paid):** ___ conversions (target: ≥5 in first week)
- [ ] **Customer complaints:** ___ tickets (target: <10 total)

#### Infrastructure Health
- [ ] **Supabase connection pool:** ___ avg connections (<15 target)
- [ ] **Database CPU:** ___% avg (<50% target)
- [ ] **No database deadlocks:** ☐ YES / ☐ NO
- [ ] **Backend memory stable:** No leaks detected

#### Documentation Complete
- [ ] **PRD.md updated:** ✅ New pricing model section added
- [ ] **docs/architecture/plan-capabilities.md:** ✅ Created
- [ ] **API documentation:** ✅ Updated (Swagger/OpenAPI)
- [ ] **Pricing page published:** ✅ Live on marketing site

#### Success Criteria Met
- [ ] **All metrics within targets:** ☐ YES / ☐ NO
- [ ] **No P0/P1 incidents:** ☐ YES / ☐ NO
- [ ] **Customer satisfaction acceptable:** ☐ YES / ☐ NO
- [ ] **GTM readiness confirmed:** ☐ YES / ☐ NO

**FINAL DECISION:** ☐ SUCCESS ☐ PARTIAL SUCCESS ☐ ROLLBACK NEEDED

---

## Phase 4: Post-Rollout Validation

### ✅ Week 1 Review (T+7 days)
**Timeline:** February 15, 2026
**Owner:** @pm + @devops-lead

#### Retrospective Meeting
- [ ] **Meeting scheduled:** Attendees (@devops, @pm, @qa, @oncall, @architect)
- [ ] **Agenda prepared:**
  1. What went well (deployment velocity, test coverage)
  2. What went wrong (bugs, performance issues, complaints)
  3. Action items (process improvements, tech debt)
  4. Success metrics review (conversion, error rate, satisfaction)

#### Success Metrics Summary
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Error rate | <0.5% | ___% | ☐ ✅ ☐ ⚠️ |
| P95 latency | <12.8s | ___s | ☐ ✅ ☐ ⚠️ |
| Conversion rate (quota → paid) | >10% | ___% | ☐ ✅ ☐ ⚠️ |
| Customer complaints | <10 | ___ | ☐ ✅ ☐ ⚠️ |
| Rollbacks executed | 0 | ___ | ☐ ✅ ☐ ⚠️ |

#### Action Items
- [ ] **Performance optimizations identified:**
  - Priority 1: _______________
  - Priority 2: _______________
  - Priority 3: _______________

- [ ] **Monitoring enhancements:**
  - Missing alerts: _______________
  - Dashboard improvements: _______________

- [ ] **Documentation updates:**
  - FAQs needed: _______________
  - Runbook gaps: _______________

#### Next Steps
- [ ] **Deploy Redis cache (Week 2):** Expected -90ms latency improvement
- [ ] **Optimize database indexes (Week 2):** Expected -50ms query time
- [ ] **Scale connection pool (if needed):** 5 → 20 connections
- [ ] **Implement business intelligence dashboard:** Conversion funnel tracking

### ✅ Month 1 Review (T+30 days)
**Timeline:** March 8, 2026
**Owner:** @pm

#### Business KPIs (Month 1)
- [ ] **Conversion rate (quota → paid):** ___% (target: >10%)
- [ ] **Trial → Paid retention:** ___% (target: >20%)
- [ ] **Customer churn:** ___% (target: <5%)
- [ ] **Average upgrade time:** ___ days (FREE → Paid)

#### Technical KPIs (Month 1)
- [ ] **Error rate sustained:** ___% (target: <0.5%)
- [ ] **Performance improvement:** ___s P95 (target: <10s after Redis)
- [ ] **Uptime:** ___% (target: 99.9%)

#### GTM Readiness
- [ ] **Pricing page live:** ☐ YES / ☐ NO
- [ ] **Marketing campaign launched:** ☐ YES / ☐ NO
- [ ] **Customer support trained:** ☐ YES / ☐ NO (FAQs, objection handling)
- [ ] **Payment gateway integrated:** ☐ YES / ☐ NO (Stripe/PayPal)

#### Long-Term Roadmap
- [ ] **Feature flag removal:** Remove `ENABLE_NEW_PRICING` code (cleanup)
- [ ] **Legacy pricing cleanup:** Archive old plan logic (6-plan system)
- [ ] **Optimization Phase 2:** Materialized views (Month 2, -40ms)
- [ ] **Business intelligence:** Advanced funnel analytics (Month 2)

---

## Rollback Procedures

### Emergency Rollback (P0 Incident)
**SLA:** 5 minutes from decision to traffic restored

```bash
# rollback-emergency.sh
#!/bin/bash

echo "🚨 EMERGENCY ROLLBACK - STORY-165"
echo "Setting feature flag to 0%..."

railway variables --set ENABLE_NEW_PRICING=0

echo "Waiting 30s for rollout..."
sleep 30

echo "Verifying health..."
curl https://bidiq-uniformes-production.up.railway.app/health

echo "Checking old pricing active..."
curl https://bidiq-uniformes-production.up.railway.app/api/me \
  -H "Authorization: Bearer {test-token}"
# Expected: Old pricing structure (6 plans)

echo "✅ Rollback complete. Monitor error rate for 10 minutes."
echo "Post-mortem required within 24 hours."
```

### Partial Rollback (50% → 10%)
**Use Case:** Business metrics weak, but no critical incident

```bash
railway variables --set ENABLE_NEW_PRICING=10
sleep 30
curl .../health
echo "Partial rollback complete. Extended monitoring at 10%."
```

### Full Rollback (100% → 0%)
**Use Case:** Major issues discovered, abort deployment

```bash
railway variables --set ENABLE_NEW_PRICING=0
sleep 30
curl .../health
echo "Full rollback complete. Reverting to old pricing model."
# Schedule post-mortem, analyze root cause, re-plan deployment
```

---

## Communication Templates

### Deployment Announcement (Slack #smart-pncp-general)
```
🚀 STORY-165 Production Rollout - {Phase}

**Feature:** Plan Restructuring (3 Paid Tiers + FREE Trial)
**Phase:** {10% / 50% / 100%}
**Date:** {Date/Time}
**Status:** DEPLOYED ✅

**What Changed:**
- New pricing model: FREE Trial, Consultor Ágil, Máquina, Sala de Guerra
- Quota enforcement system (monthly limits)
- Excel export restrictions (Máquina+ only)
- Date range validation (plan-based history limits)

**Impact:**
- {10% / 50% / 100%} of users will see new pricing
- Expected quota exhaustion events: {5-20 / 25-100 / 50-200} per day
- Upgrade modal will trigger on locked features

**Monitoring:**
- War Room: #smart-pncp-war-room
- On-Call: @oncall-dev
- Dashboards: Railway + Supabase

**Questions?** Contact @pm or @devops-lead
```

### Success Announcement (Slack #smart-pncp-general)
```
🎉 STORY-165 100% Rollout - SUCCESS

**Milestone:** New pricing model fully deployed
**Date:** {Date}
**Uptime:** {99.9%}
**Error Rate:** {0.4%} (target: <0.5%)

**Success Metrics:**
✅ Zero rollbacks executed
✅ Conversion rate: {12%} (target: >10%)
✅ Customer complaints: {3} (target: <10)
✅ Performance: P95 {11.2s} (target: <12.8s)

**GTM Readiness:** ✅ Complete
- Pricing page live
- Payment gateway integrated
- Customer support trained

**Next Steps:**
- Week 2: Deploy Redis cache (-90ms latency)
- Month 2: Business intelligence dashboard
- Month 3: A/B testing for conversion optimization

**Thank you to:** @oncall-dev, @qa, @devops-lead, @pm, @architect

Questions? Contact @pm (Parker)
```

---

## Appendix: Sign-Off Sheet

### Phase 1: 10% Rollout
```
Pre-Deployment Validation:
☐ Code quality: Tests passing, coverage >70%
☐ Staging success: 48+ hours stable
☐ Team ready: On-call assigned, rollback tested

Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@qa)           Date: __________
Approver: _________________ (@pm)           Date: __________

Post-Deployment (24hr):
☐ Error rate <1%: ___%
☐ No incidents: ☐ YES
☐ Customer complaints: ___

Decision for 50%: ☐ GO ☐ NO-GO
Approver: _________________ (@devops-lead)  Date: __________
```

### Phase 2: 50% Rollout
```
Pre-Deployment Validation:
☐ 10% stable: 24+ hours
☐ Error rate <1%: ___%
☐ Customer feedback acceptable: ___ complaints

Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@pm)           Date: __________

Post-Deployment (24hr):
☐ Error rate <1%: ___%
☐ Conversion metrics: CTR ___%
☐ Customer complaints: ___

Decision for 100%: ☐ GO ☐ NO-GO
Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@pm)           Date: __________
```

### Phase 3: 100% Rollout
```
Pre-Deployment Validation:
☐ 50% stable: 24+ hours
☐ Error rate <0.5%: ___%
☐ Conversion healthy: CTR ___%
☐ Documentation complete: ☐ YES

Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@pm)           Date: __________
Approver: _________________ (CTO, optional) Date: __________

Post-Deployment (48hr):
☐ Error rate <0.5%: ___%
☐ Conversions: ___ paid upgrades
☐ Customer satisfaction: ___ NPS

FINAL STATUS: ☐ SUCCESS ☐ PARTIAL SUCCESS ☐ ROLLBACK

Project Manager: _________________ (@pm)    Date: __________
```

---

**Document Owner:** @devops-lead
**Last Updated:** February 4, 2026
**Next Review:** February 15, 2026 (Week 1 retrospective)

**Questions?** Slack #smart-pncp-dev or email dev-team@smartpncp.com
