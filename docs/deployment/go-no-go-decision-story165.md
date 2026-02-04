# Go/No-Go Decision Framework - STORY-165

**Feature:** Plan Restructuring & Quota Enforcement
**Story ID:** STORY-165
**Version:** 1.0
**Created:** February 4, 2026
**Owner:** @pm (Parker)

---

## Overview

This document defines the decision criteria, approval authority, and escalation paths for each stage of STORY-165 deployment (Staging → Production 10% → 50% → 100%).

---

## Decision Gates

### Gate 1: Staging Deployment
**Decision Point:** February 4, 2026
**Approvers Required:** @devops-lead + @qa
**Timeline:** 2-3 hours for validation

### Gate 2: Production 10% Rollout
**Decision Point:** February 6, 2026 (T+2 days after staging)
**Approvers Required:** @devops-lead + @qa + @pm
**Timeline:** 24 hours monitoring

### Gate 3: Production 50% Rollout
**Decision Point:** February 7, 2026 (T+3 days)
**Approvers Required:** @devops-lead + @pm
**Timeline:** 24 hours monitoring

### Gate 4: Production 100% Rollout
**Decision Point:** February 8, 2026 (T+4 days)
**Approvers Required:** @devops-lead + @pm + CTO (optional)
**Timeline:** Permanent deployment

---

## Gate 1: Staging Deployment (GO/NO-GO)

### GO Criteria (ALL must be met)

#### Code Quality
- [x] Backend tests: 106 passing (≥70% coverage)
- [x] Frontend tests: 69 passing (≥60% coverage)
- [x] E2E tests: 60 passing (Playwright)
- [x] Linting: No errors (backend + frontend)
- [x] Security scan: No critical vulnerabilities (CodeQL)

#### Infrastructure Readiness
- [ ] Staging environment provisioned (Railway)
- [ ] Database indexes created (Supabase)
  - `idx_subscriptions_user_active`
  - `idx_monthly_quota_user_month`
  - `idx_search_sessions_user_created`
- [ ] Test users created (free, consultor, maquina, sala)
- [ ] Environment variables configured (staging)
- [ ] Feature flag implemented (`ENABLE_NEW_PRICING`)

#### Team Readiness
- [ ] QA team trained (test scenarios reviewed)
- [ ] On-call engineer assigned (24-hour coverage)
- [ ] Rollback procedure tested (dry run completed)
- [ ] Monitoring dashboards configured (Railway + Supabase)

#### Success Metrics Defined
- [ ] Error rate baseline recorded (<0.5% current)
- [ ] P95 latency baseline recorded (3.2s light search)
- [ ] Quota exhaustion target set (5-20 events/day)
- [ ] Upgrade modal CTR target set (>5%)

### NO-GO Triggers (ANY triggers NO-GO)

- ❌ Backend coverage <70% (current: 80.8%)
- ❌ Frontend coverage <60% (current: 91.5%)
- ❌ >5 P1/P2 bugs in backlog (critical blockers)
- ❌ Database indexes not created (performance risk)
- ❌ Rollback procedure untested (safety concern)
- ❌ No on-call engineer assigned (incident response gap)

### Decision Authority
**Primary:** @devops-lead
**Advisory:** @qa, @architect
**Escalation:** If 2+ NO-GO triggers → Defer to CTO

### Post-Deployment Validation (Within 2 hours)
- [ ] Health check returns `status=healthy`
- [ ] Smoke tests pass (6/6 scenarios)
- [ ] No 500 errors in logs
- [ ] Quota check success rate >99%
- [ ] Supabase connection pool <15 active connections

---

## Gate 2: Production 10% Rollout (GO/NO-GO)

### GO Criteria (ALL must be met)

#### Staging Success
- [ ] Staging stable for 48+ hours (no P0/P1 incidents)
- [ ] All 6 test scenarios passing (100% success rate)
- [ ] No outstanding P1 bugs (P2/P3 acceptable if documented)
- [ ] Performance within targets (P95 <15s)
- [ ] QA sign-off received (formal approval)

#### Metrics Thresholds
- [ ] Error rate <1% (staging)
- [ ] P95 latency <15s (light search)
- [ ] Quota check latency <200ms (P95)
- [ ] Supabase query time <50ms (avg)
- [ ] No timeout errors (PNCP API + Supabase)

#### Business Readiness
- [ ] Upgrade modal messaging approved (@pm)
- [ ] Analytics tracking verified (upgrade clicks logged)
- [ ] Customer support briefed (potential quota complaints)
- [ ] Rollback plan communicated to stakeholders

#### Risk Mitigation
- [ ] Feature flag at 10% (canary rollout)
- [ ] On-call engineer assigned (24-hour watch)
- [ ] Rollback SLA confirmed (5 minutes)
- [ ] Incident response plan activated

### NO-GO Triggers (ANY triggers NO-GO)

- ❌ Staging unstable (<48 hours uptime)
- ❌ Any P0 bug found (system down, data loss)
- ❌ >3 P1 bugs unresolved (major feature broken)
- ❌ Error rate >1.5% (staging)
- ❌ Performance degradation >20% (P95 >18s)
- ❌ Quota enforcement inaccurate (any false positives/negatives)
- ❌ Excel blocking inaccurate (any FREE user gets Excel)
- ❌ QA veto (formal NO-GO from @qa)

### Decision Authority
**Primary:** @devops-lead + @pm
**Required Approvals:**
- Technical: @devops-lead (infrastructure readiness)
- Quality: @qa (test coverage, bug count)
- Business: @pm (customer impact assessment)

**Escalation:** If conflicting approvals → CTO decides

### Post-Deployment Monitoring (24 hours)
- [ ] Error rate <1% (production 10%)
- [ ] No customer complaints (support tickets = 0)
- [ ] Quota exhaustion events logged (5-20/day expected)
- [ ] Upgrade modal impressions tracked (analytics)
- [ ] No rollbacks executed

### Success Criteria for Gate 3 Advancement
- [ ] 24 hours stable (error rate <1%)
- [ ] Zero P0/P1 incidents
- [ ] Customer complaints <3 (non-critical issues)
- [ ] Upgrade modal CTR >5% (preliminary data)

---

## Gate 3: Production 50% Rollout (GO/NO-GO)

### GO Criteria (ALL must be met)

#### 10% Rollout Success
- [ ] 10% deployment stable for 24+ hours
- [ ] Error rate <1% (production)
- [ ] Zero P0 incidents (critical bugs)
- [ ] Customer complaints <3 (acceptable threshold)
- [ ] Performance within SLA (P95 <15s)

#### Business Metrics Validated
- [ ] Quota exhaustion events: 5-20/day (expected behavior)
- [ ] Upgrade modal CTR >5% (preliminary conversion)
- [ ] No false positives (FREE users blocked incorrectly)
- [ ] No false negatives (Máquina users missing Excel)

#### Infrastructure Health
- [ ] Supabase connection pool stable (<15 connections)
- [ ] No database deadlocks (quota upsert conflicts)
- [ ] Redis cache (if deployed) hit rate >80%
- [ ] No memory leaks (backend container stable)

#### Team Confidence
- [ ] On-call engineer reports no concerns
- [ ] @devops-lead confident in infrastructure
- [ ] @pm satisfied with business metrics
- [ ] No escalations to CTO (smooth deployment)

### NO-GO Triggers (ANY triggers NO-GO)

- ❌ Error rate >1.5% (production 10%)
- ❌ Any P0 incident (even if resolved quickly)
- ❌ >5 customer complaints (quota restrictions backlash)
- ❌ Conversion rate <2% (business decision to abort)
- ❌ Performance degradation >25% (P95 >18.75s)
- ❌ Database performance issues (query time >100ms avg)
- ❌ On-call engineer veto (operational concern)

### Decision Authority
**Primary:** @devops-lead + @pm
**Required Approvals:**
- Infrastructure: @devops-lead (capacity, performance)
- Business: @pm (conversion metrics, customer feedback)

**Escalation:** If business metrics weak → Discuss with CTO

### Post-Deployment Monitoring (24 hours)
- [ ] Error rate <1%
- [ ] Upgrade modal CTR >5% (stable or improving)
- [ ] Customer complaints <5
- [ ] Performance stable (P95 <15s)
- [ ] No rollbacks executed

### Success Criteria for Gate 4 Advancement
- [ ] 48 hours stable (10% + 50% combined)
- [ ] Conversion metrics healthy (CTR >5%, early conversions)
- [ ] Customer feedback neutral or positive
- [ ] Infrastructure scaled appropriately (if needed)

---

## Gate 4: Production 100% Rollout (GO/NO-GO)

### GO Criteria (ALL must be met)

#### 50% Rollout Success
- [ ] 50% deployment stable for 24+ hours
- [ ] Error rate <0.5% (target: production-grade)
- [ ] Zero P0/P1 incidents (entire deployment window)
- [ ] Customer complaints <5 (acceptable for GTM)
- [ ] Performance meets SLA (P95 <12.8s ideal, <15s max)

#### Business KPIs Achieved
- [ ] Quota exhaustion → Upgrade CTR >5%
- [ ] Early conversions (≥1 paid plan upgrade)
- [ ] Excel blocking 100% accurate (no support tickets)
- [ ] Trial expiration enforced (no bypasses)

#### Infrastructure Maturity
- [ ] Database indexes optimized (query time <50ms avg)
- [ ] Connection pool scaled (no 503 errors under load)
- [ ] Monitoring dashboards complete (business + technical)
- [ ] Alerts configured (P0/P1 trigger Slack notifications)

#### Documentation Complete
- [ ] PRD.md updated (new pricing model)
- [ ] docs/architecture/plan-capabilities.md created
- [ ] API documentation updated (/api/me, /api/buscar)
- [ ] Pricing comparison page published (docs/pricing.md)

#### Stakeholder Alignment
- [ ] CTO sign-off (optional but recommended)
- [ ] Product Owner satisfied (GTM readiness)
- [ ] Customer Support trained (quota FAQs)
- [ ] Marketing ready (pricing page live)

### NO-GO Triggers (ANY triggers NO-GO)

- ❌ Error rate >1% (production 50%)
- ❌ Any P0/P1 incident (unresolved)
- ❌ >10 customer complaints (quota backlash)
- ❌ Conversion rate <3% (business threshold)
- ❌ Performance regression >15% (P95 >13.8s)
- ❌ Outstanding P1 bugs (must fix before 100%)
- ❌ CTO veto (strategic concern)

### Decision Authority
**Primary:** @pm + @devops-lead
**Required Approvals:**
- Business: @pm (GTM readiness, conversion metrics)
- Infrastructure: @devops-lead (production stability)
- Optional: CTO (strategic alignment)

**Escalation:** If conversion weak but stable → CTO decides

### Post-Deployment Actions (Week 1)
- [ ] Remove feature flag code (cleanup)
- [ ] Announce GTM readiness to stakeholders
- [ ] Publish pricing page (marketing site)
- [ ] Monitor conversion funnel (quota → upgrade → checkout)
- [ ] Weekly review (error rate, conversion, feedback)

### Long-Term Success Criteria (Month 1)
- [ ] Error rate <0.5% (sustained)
- [ ] Conversion rate >10% (quota exhaustion → paid plan)
- [ ] Customer churn <5% (trial → paid retention)
- [ ] Performance improved (Redis cache deployed)

---

## Rollback Decision Tree

### When to Rollback?

```
┌─────────────────────────────────────┐
│ Is system down or data loss?        │
│ (P0 Severity)                        │
└─────────────┬───────────────────────┘
              │ YES → IMMEDIATE ROLLBACK (no approval needed)
              │ NO ↓
┌─────────────────────────────────────┐
│ Error rate >2% OR                   │
│ >5 P1 bugs unresolved?               │
└─────────────┬───────────────────────┘
              │ YES → ROLLBACK (DevOps Lead approves)
              │ NO ↓
┌─────────────────────────────────────┐
│ Performance degradation >30% OR     │
│ >10 customer complaints?             │
└─────────────┬───────────────────────┘
              │ YES → ROLLBACK (PM + DevOps Lead decide)
              │ NO ↓
┌─────────────────────────────────────┐
│ Conversion rate <2% (business)?     │
└─────────────┬───────────────────────┘
              │ YES → DISCUSS (PM + CTO decide)
              │ NO ↓
┌─────────────────────────────────────┐
│ Minor issues (P2/P3)?               │
└─────────────┬───────────────────────┘
              │ FIX FORWARD (no rollback)
              ↓
```

### Rollback Authority Matrix

| Severity | Decision Maker | Approval Time | Rollback SLA |
|----------|----------------|---------------|--------------|
| **P0 (Critical)** | @oncall-dev (solo decision) | Immediate | 5 minutes |
| **P1 (High)** | @devops-lead + @oncall-dev | <15 minutes | 10 minutes |
| **P2 (Medium)** | @devops-lead + @pm | <1 hour | 30 minutes |
| **P3 (Low)** | @pm (business decision) | <4 hours | Fix forward |

### Rollback Procedure
**See:** `docs/deployment/rollback-plan-story165.md`

**Quick Steps:**
1. Set feature flag: `ENABLE_NEW_PRICING=0%`
2. Verify old pricing active (check /api/me)
3. Monitor error rate (should return to <0.5%)
4. Notify team (#smart-pncp-incidents)
5. Post-mortem within 24 hours

---

## Escalation Paths

### Technical Escalation
```
Issue Detected (monitoring alert)
    ↓
@oncall-dev (first responder, 5 min SLA)
    ↓
P3 → Create ticket (backlog)
P2 → Investigate (4-hour SLA)
P1 → Escalate to @devops-lead + war room
P0 → IMMEDIATE ROLLBACK + CTO notification
```

### Business Escalation
```
Conversion Metrics Weak (<5% CTR)
    ↓
@pm analyzes data (24-hour assessment)
    ↓
If trend continues (48 hours)
    ↓
Discuss with CTO (strategic decision)
    ↓
Options:
- Rollback (abort pricing change)
- Fix forward (improve messaging, A/B test)
- Extend monitoring (wait for more data)
```

### Customer Complaint Escalation
```
Customer Complaint Received (support ticket)
    ↓
Support categorizes (P0-P3 + tags: quota, excel, trial)
    ↓
>10 complaints in 24 hours → Escalate to @pm
    ↓
@pm reviews:
- Are complaints valid bugs? → Fix or rollback
- Are complaints UX friction? → Improve messaging
- Are complaints expected? → Document FAQ
```

---

## Metrics Dashboard (Live Monitoring)

### Technical Health
**Dashboard:** Railway Metrics (https://railway.app/project/{project-id}/metrics)

| Metric | Target | Yellow Alert | Red Alert (Rollback) |
|--------|--------|--------------|----------------------|
| Error Rate | <0.5% | >1% | >2% |
| P95 Latency | <12.8s | >15s | >20s |
| Health Check Uptime | 100% | <99.9% | <99% |
| Quota Check Latency | <200ms | >300ms | >500ms |

### Business Health
**Dashboard:** Custom Analytics (TBD)

| Metric | Target | Yellow Alert | Red Alert |
|--------|--------|--------------|-----------|
| Quota Exhaustion Events | 5-20/day | >30/day | >50/day |
| Upgrade Modal CTR | >5% | <4% | <2% |
| Excel Enforcement Accuracy | 100% | <99% | <95% |
| Customer Complaints | <5/day | >8/day | >15/day |

### Infrastructure Health
**Dashboard:** Supabase Metrics (https://app.supabase.com/project/{project-id}/database/query-performance)

| Metric | Target | Yellow Alert | Red Alert |
|--------|--------|--------------|-----------|
| Connection Pool Usage | <15 connections | >20 | >30 |
| Avg Query Time (check_quota) | <50ms | >100ms | >200ms |
| Database CPU | <50% | >70% | >90% |
| Database Deadlocks | 0 | >1/hour | >5/hour |

---

## Communication Templates

### GO Decision Announcement (Slack #smart-pncp-dev)
```
🚀 STORY-165 Gate {N} - GO Decision Approved

**Gate:** {Staging / Production 10% / 50% / 100%}
**Decision:** GO ✅
**Approvers:**
- Technical: @devops-lead ✅
- Quality: @qa ✅
- Business: @pm ✅

**Success Criteria Met:**
✅ Error rate: {0.4%} (target: <1%)
✅ Test coverage: Backend 80.8%, Frontend 91.5%
✅ All smoke tests passing (6/6)
✅ Performance: P95 {12.3s} (target: <15s)

**Next Steps:**
- Deployment: {Date/Time}
- Monitoring: {On-call engineer assigned}
- Rollback SLA: 5 minutes

**Timeline:** {Duration} monitoring period
**War Room:** #smart-pncp-war-room (if needed)
```

### NO-GO Decision Announcement (Slack #smart-pncp-dev)
```
🚫 STORY-165 Gate {N} - NO-GO Decision

**Gate:** {Staging / Production 10% / 50% / 100%}
**Decision:** NO-GO ❌
**Decision Maker:** @{role}

**Blockers:**
❌ {Blocker 1: Error rate >1.5%}
❌ {Blocker 2: P1 bug unresolved}

**Remediation Plan:**
1. {Action 1: Fix quota logic bug #234}
2. {Action 2: Re-run regression tests}
3. {Action 3: Re-evaluate in 24 hours}

**Next Gate Review:** {Date/Time}
**Owner:** @{responsible person}
```

### Rollback Announcement (Slack #smart-pncp-incidents)
```
🔥 EMERGENCY ROLLBACK - STORY-165

**Severity:** P{0/1/2}
**Reason:** {Brief description of issue}
**Decision Maker:** @{role}
**Rollback Status:** IN PROGRESS ⏳

**Actions Taken:**
✅ Feature flag set to 0%
⏳ Verifying old pricing active
⏳ Monitoring error rate

**Expected Recovery:** {5 minutes}
**Impact:** {Users affected, if any}

**Post-Mortem:** Scheduled for {Date/Time}
**Owner:** @oncall-dev
```

---

## Post-Deployment Review (Retrospective)

### Within 48 Hours of 100% Rollout
**Attendees:** @devops-lead, @pm, @qa, @oncall-dev, @architect

**Agenda:**
1. **What Went Well:**
   - Deployment velocity (time per gate)
   - Test coverage effectiveness
   - Rollback readiness (if tested)
   - Team coordination

2. **What Went Wrong:**
   - Bugs found in production (root cause)
   - Metrics that missed expectations
   - Customer complaints (valid vs. expected)
   - Performance issues

3. **Action Items:**
   - Process improvements (deployment checklist updates)
   - Monitoring enhancements (missing alerts)
   - Documentation gaps (runbooks, FAQs)
   - Technical debt (optimization opportunities)

4. **Success Metrics:**
   - Conversion rate (quota → paid plan)
   - Error rate (sustained <0.5%)
   - Customer satisfaction (complaints = 0)
   - GTM readiness (pricing page live)

**Output:** Retrospective document in `docs/retrospectives/story165-deployment.md`

---

## Appendix: Decision Checklist (Print & Sign-Off)

### Gate 1: Staging Deployment
```
☐ Code quality: Tests passing, coverage >70%
☐ Infrastructure: Staging provisioned, DB indexes created
☐ Team readiness: QA trained, on-call assigned
☐ Metrics: Baselines recorded

Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@qa)           Date: __________
```

### Gate 2: Production 10% Rollout
```
☐ Staging success: 48+ hours stable
☐ Metrics: Error rate <1%, latency <15s
☐ Business: Upgrade modal approved, support briefed
☐ Risk: Feature flag at 10%, rollback plan ready

Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@qa)           Date: __________
Approver: _________________ (@pm)           Date: __________
```

### Gate 3: Production 50% Rollout
```
☐ 10% success: 24+ hours stable, error rate <1%
☐ Business: CTR >5%, customer complaints <3
☐ Infrastructure: Connection pool stable, no deadlocks

Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@pm)           Date: __________
```

### Gate 4: Production 100% Rollout
```
☐ 50% success: 24+ hours stable, error rate <0.5%
☐ Business: Conversion metrics healthy, GTM ready
☐ Documentation: PRD updated, pricing page published
☐ Stakeholder: CTO sign-off (optional)

Approver: _________________ (@devops-lead)  Date: __________
Approver: _________________ (@pm)           Date: __________
Approver: _________________ (CTO, optional) Date: __________
```

---

**Document Owner:** @pm (Parker)
**Last Updated:** February 4, 2026
**Next Review:** Post-deployment (February 10, 2026)

**Questions?** Slack #smart-pncp-dev or email dev-team@smartpncp.com
