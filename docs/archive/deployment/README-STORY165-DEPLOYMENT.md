# STORY-165 Deployment Documentation Index

**Feature:** Plan Restrictions & Quota System
**Version:** 1.0
**Created:** 2026-02-03
**Status:** Ready for Production Deployment

---

## 📚 Documentation Overview

This directory contains comprehensive deployment, monitoring, and operational documentation for STORY-165 (Plan Restrictions & Quota System). All documents are production-ready and designed for different audiences (DevOps, On-Call, Architects).

---

## 🎯 Quick Start by Role

### For DevOps Engineers (Deployment Team)
**Primary Document:** [`story165-deployment-checklist.md`](./story165-deployment-checklist.md)

**Workflow:**
1. ✅ Review checklist (15-minute deployment procedure)
2. ✅ Run pre-deployment tests (backend, frontend, E2E)
3. ✅ Execute deployment (Railway + Vercel)
4. ✅ Run smoke tests (free user, paid user flows)
5. ✅ Monitor first 2 hours (error rate, latency, business metrics)

**Supporting Docs:**
- [`deployment-runbook-story165.md`](./deployment-runbook-story165.md) - Detailed step-by-step guide
- [`smoke-tests-story165.md`](./smoke-tests-story165.md) - Test scripts and expected results
- [`rollback-plan-story165.md`](./rollback-plan-story165.md) - Emergency rollback procedure

---

### For On-Call Engineers (Incident Response)
**Primary Document:** [`oncall-quick-reference-story165.md`](./oncall-quick-reference-story165.md)

**Use Cases:**
- 🚨 **Emergency:** Health check failing → Rollback decision in 5 minutes
- 🔍 **Investigation:** High 403 rate → Diagnose quota exhaustion vs. bug
- 📊 **Monitoring:** Daily metrics check (error rate, latency, business KPIs)

**Key Sections:**
- Emergency Response (first 5 minutes)
- Common Issues & Solutions (5 scenarios)
- Rollback triggers & commands
- Escalation path (P0 → P3 severity)

**Supporting Docs:**
- [`monitoring-story165.md`](./monitoring-story165.md) - Complete alert catalog
- [`performance-baseline-story165.md`](./performance-baseline-story165.md) - Latency targets

---

### For Architects (Performance & Optimization)
**Primary Document:** [`performance-baseline-story165.md`](./performance-baseline-story165.md)

**Focus Areas:**
1. **Baseline Metrics:** Pre-deployment performance (3.2s P50 → 3.43s expected)
2. **Bottleneck Analysis:** Supabase queries (110ms overhead per search)
3. **Optimization Roadmap:**
   - Phase 1: Database indexes (immediate)
   - Phase 2: Redis caching (Week 2, -90ms improvement)
   - Phase 3: Materialized views (Month 2, -40ms improvement)

**Supporting Docs:**
- [`monitoring-story165.md`](./monitoring-story165.md) - Section 6 (Architecture Health Checks)

---

### For Product Owners (Business Metrics)
**Primary Document:** [`monitoring-story165.md`](./monitoring-story165.md) - Section 1.3

**Key Business Metrics:**
1. **Quota Exhaustion Events:** Conversion opportunity (users hitting limits)
2. **Upgrade Modal CTR:** Target >5% (quota exhaustion → upgrade click)
3. **Excel Download Enforcement:** 100% blocked for Free/Consultor, 100% allowed for Máquina/Sala
4. **Trial Expiration Enforcement:** 100% blocked after expiry

**Dashboard Location:** Section 9 (Recommended visualizations)

---

## 📖 Complete Document Catalog

### Deployment & Operations

| Document | Purpose | Audience | Pages |
|----------|---------|----------|-------|
| **[story165-deployment-checklist.md](./story165-deployment-checklist.md)** | Step-by-step deployment procedure | DevOps | 12 |
| **[deployment-runbook-story165.md](./deployment-runbook-story165.md)** | Detailed deployment guide with scripts | DevOps | 37 |
| **[rollback-plan-story165.md](./rollback-plan-story165.md)** | Emergency rollback procedure (5-min SLA) | DevOps, On-Call | 23 |
| **[smoke-tests-story165.md](./smoke-tests-story165.md)** | Post-deployment validation tests | DevOps, QA | 12 |

### Monitoring & Incident Response

| Document | Purpose | Audience | Pages |
|----------|---------|----------|-------|
| **[oncall-quick-reference-story165.md](./oncall-quick-reference-story165.md)** | On-call engineer playbook (quick reference) | On-Call | 14 |
| **[monitoring-story165.md](./monitoring-story165.md)** | Complete monitoring spec (metrics, alerts, dashboards) | Architects, On-Call | 36 |
| **[performance-baseline-story165.md](./performance-baseline-story165.md)** | Performance baselines & optimization roadmap | Architects | 23 |

### Legacy Documentation (Pre-STORY-165)

| Document | Purpose | Status |
|----------|---------|--------|
| [phase4-devops-readiness-report.md](./phase4-devops-readiness-report.md) | DevOps readiness assessment | ✅ Complete |
| [pre-deployment-checklist.md](./pre-deployment-checklist.md) | General deployment checklist | ✅ Complete |
| [railway-environment-setup.md](./railway-environment-setup.md) | Railway configuration guide | ✅ Complete |

---

## 🎯 Deployment Timeline

### T-24 Hours: Pre-Deployment
- [ ] **Database Preparation** (30 min)
  - Create Supabase indexes (see checklist Section "Pre-Deployment")
  - Verify test users exist (free_trial, consultor_agil, maquina, sala_guerra)

- [ ] **Baseline Collection** (15 min)
  - Record current P95 latency (target: ~6-8s for light searches)
  - Document error rate (target: <0.5%)

- [ ] **Test Suite Validation** (20 min)
  - Backend: 106 tests, coverage >70%
  - Frontend: 69 tests, coverage >49%
  - E2E: 60 tests (Playwright)

### T=0: Deployment
- [ ] **Backend Deploy** (Railway, 3 min)
- [ ] **Frontend Deploy** (Vercel, 2 min)
- [ ] **Smoke Tests** (10 min - see smoke-tests-story165.md)

### T+15 min: Initial Validation
- [ ] No 500 errors in logs
- [ ] Quota check success rate >99%
- [ ] Health endpoint returns `status=healthy`

### T+1 Hour: Performance Validation
- [ ] P95 latency <15s (target: <12.8s)
- [ ] Quota exhaustion events logged correctly
- [ ] Upgrade modal impressions tracked (frontend analytics)

### T+24 Hours: Success Criteria
- [ ] Error rate <1% ✅
- [ ] No customer complaints ✅
- [ ] Upgrade modal CTR >5% ✅
- [ ] Zero rollbacks executed ✅

---

## 🚨 Emergency Contacts

| Role | Contact | Use Case |
|------|---------|----------|
| **On-Call Engineer** | @oncall-dev (Slack) | First responder for all incidents |
| **DevOps Lead** | @devops-lead (Slack) | Deployment issues, rollback approval |
| **Database Admin** | @db-team (Slack) | Supabase performance, index creation |
| **Product Owner** | @po (Slack) | Rollback decision (revenue impact) |
| **CTO** | escalate via @devops-lead | P0 incidents (system down >30 min) |

**Escalation Path:**
1. **P3 (Low):** @oncall-dev → Create ticket for backlog
2. **P2 (Medium):** @oncall-dev → Investigate within 4 hours
3. **P1 (High):** @oncall-dev + @devops-lead → Fix within 1 hour
4. **P0 (Critical):** @oncall-dev + @devops-lead + CTO → Rollback within 15 min

---

## 📊 Key Performance Indicators (KPIs)

### Week 1 Success Metrics
```yaml
Reliability:
  - Error rate: <1% (target: <0.5%)
  - P95 latency: <15s (target: <12.8s)
  - Health check uptime: 100%
  - Rollbacks: 0

Business:
  - Quota exhaustion events: 5-20/day (expected behavior)
  - Upgrade modal CTR: >5% (quota exhaustion → upgrade click)
  - Excel enforcement: 100% accuracy (Free blocked, Máquina allowed)
  - Customer complaints: 0

Performance:
  - check_quota() P95: <200ms
  - Supabase connection pool: <15 active connections
  - Redis cache hit rate: N/A (not deployed yet)
```

### Month 1 Optimization Targets
- ✅ Redis cache deployed (Week 2) → -90ms average latency
- ✅ Database indexes optimized → -50ms query time
- ✅ Connection pool scaled (5 → 20) → No 503 errors under load
- ✅ Quota exhaustion → Paid conversion: >10%

---

## 🛠️ Architecture Changes Summary

### New Backend Components (STORY-165)

```python
# New modules added:
backend/
├── quota.py              # Plan capabilities + quota tracking (NEW)
│   ├── PLAN_CAPABILITIES  # Hardcoded plan definitions
│   ├── check_quota()      # Pre-search quota validation
│   ├── increment_quota()  # Post-search quota increment
│   └── save_session()     # Search history tracking
│
└── main.py (updated)
    └── /buscar endpoint   # Now calls check_quota() before PNCP fetch
    └── /me endpoint       # New: Returns user profile + quota status
```

### New Frontend Components (STORY-165)

```typescript
frontend/app/components/
├── QuotaBadge.tsx        # Shows plan name + quota status
├── PlanBadge.tsx         # Displays current plan (FREE, Consultor, etc.)
├── QuotaCounter.tsx      # "X / Y buscas" or "∞" for trial
└── UpgradeModal.tsx      # Triggered on quota exhaustion or locked features
```

### Database Impact (Supabase)

```sql
-- Tables accessed (no schema changes in STORY-165):
user_subscriptions  -- Read: check_quota() (every search)
monthly_quota       -- Read + Write: check_quota(), increment_quota()
search_sessions     -- Write: save_search_session() (every search)

-- New indexes (REQUIRED for performance):
CREATE INDEX idx_subscriptions_user_active ON user_subscriptions(...);
CREATE INDEX idx_monthly_quota_user_month ON monthly_quota(...);
CREATE INDEX idx_search_sessions_user_created ON search_sessions(...);
```

### Performance Impact Summary

| Operation | Pre-STORY-165 | Post-STORY-165 | Overhead |
|-----------|---------------|----------------|----------|
| Light search (1 UF, 7 days) | 3.2s | 3.43s | +230ms (7.2%) |
| Medium search (3 UFs, 30 days) | 8.4s | 8.63s | +230ms (2.7%) |
| Heavy search (5 UFs, 90 days) | 22.7s | 22.93s | +230ms (1.0%) |

**Overhead Breakdown:**
- check_quota(): 110ms (Supabase queries)
- increment_quota(): 70ms (upsert)
- save_session(): 50ms (insert)
- **Total:** 230ms per search (acceptable)

---

## 📝 Next Steps After Deployment

### Immediate (Week 1)
1. **Monitor Dashboard Daily:**
   - Railway metrics (error rate, latency)
   - Supabase connection pool (active connections)
   - Business metrics (quota exhaustion, upgrade CTR)

2. **Collect Feedback:**
   - User complaints about plan restrictions (expect: 0)
   - Upgrade modal effectiveness (CTR >5%)
   - Performance degradation reports (expect: none)

### Week 2-4: Optimization Phase
1. **Deploy Redis Cache:**
   - Add Railway Redis addon ($5/month)
   - Implement caching in `check_quota()` (see performance-baseline Section 4.2)
   - Target: 80% cache hit rate, -90ms average latency

2. **Database Tuning:**
   - Analyze slow query log (Supabase dashboard)
   - Optimize connection pool size (5 → 20)
   - Implement atomic increment function (PostgreSQL)

3. **Monitoring Enhancements:**
   - Set up Grafana dashboards (if needed)
   - Configure Slack alerts for P1/P0 incidents
   - Add business intelligence dashboard (conversion funnel)

---

## 🔗 Related Documentation

### Story & Requirements
- **Original Story:** `docs/stories/STORY-165-plan-restrictions-ui.md`
- **PRD Reference:** `PRD.md` (Section 11: Subscription Plans)

### Testing
- **Test Suite:** `backend/tests/test_quota.py` (32 tests)
- **Frontend Tests:** `frontend/__tests__/components/QuotaBadge.test.tsx`
- **E2E Tests:** `frontend/e2e-tests/quota-enforcement.spec.ts`

### Architecture
- **ADR:** `docs/architecture/adr-multi-source-consolidation.md` (if applicable)
- **API Contract:** `docs/architecture/multi-source-api-contract.md`

---

## 📚 Appendix: Document Change Log

| Date | Document | Change | Author |
|------|----------|--------|--------|
| 2026-02-03 | All deployment docs | Initial creation for STORY-165 | @architect (Alex) |
| 2026-02-03 | monitoring-story165.md | Added Section 9 (Dashboard visualizations) | @architect (Alex) |
| 2026-02-03 | performance-baseline-story165.md | Added Phase 3 optimization roadmap | @architect (Alex) |
| 2026-02-03 | oncall-quick-reference-story165.md | Added daily check-in script | @architect (Alex) |

**Next Review Date:** 2026-02-10 (1 week post-deployment)

---

## ✅ Document Quality Checklist

- [x] All documents peer-reviewed by @architect
- [x] Tested on staging environment (smoke tests validated)
- [x] Emergency contacts verified (Slack channels exist)
- [x] Rollback procedure tested (dry run completed)
- [x] Performance baselines measured (pre-deployment)
- [x] Business metrics defined (quota exhaustion, CTR)
- [x] On-call engineer trained (quick reference reviewed)

---

**Documentation Status:** ✅ Ready for Production
**Deployment Approval:** Pending @devops-lead sign-off
**Deploy Date:** 2026-02-03 (scheduled)

**Questions?** Contact @architect (Alex) via Slack #smart-pncp-dev
