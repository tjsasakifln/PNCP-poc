# Rollback Plan - STORY-165: Plan Restructuring

**Story ID:** STORY-165
**Feature:** 3 Paid Tiers + FREE Trial with Plan Capabilities
**Version:** 1.0
**Created:** 2026-02-03
**Owner:** @devops
**Feature Flag:** `ENABLE_NEW_PRICING`

---

## Executive Summary

This document outlines the rollback strategy for STORY-165, which introduces a new pricing structure (3 paid tiers + FREE trial) with plan-based capabilities enforcement. Unlike standard rollbacks that revert entire deployments, this rollback leverages **feature flag toggling** for instant rollback with zero downtime.

**Rollback Mechanism:** Feature flag toggle (`ENABLE_NEW_PRICING = false`)
**Estimated Rollback Time:** <30 seconds (instant flag toggle)
**Downtime Required:** None (feature flag enables/disables feature in real-time)
**Rollback Authority:** @devops (primary), @pm (secondary)

---

## Rollback Trigger Conditions

### Automatic Rollback Triggers (Immediate Action)

Execute rollback **immediately** if any of these conditions are met:

| Trigger | Threshold | Monitoring Source |
|---------|-----------|-------------------|
| **HTTP 403 Error Spike** | >10% of requests return 403 | Railway logs, Mixpanel errors |
| **HTTP 429 Error Spike** | >5% of requests return 429 | Railway logs |
| **Search Failure Rate** | >10% of searches fail | Mixpanel funnel analysis |
| **User Upgrade Click Rate** | <1% after 1000 impressions | Mixpanel conversion tracking |
| **Backend Error Rate** | >5% overall error rate | Railway dashboard |
| **Database Connection Failures** | Supabase connection errors | Backend logs |
| **Redis Connection Failures** | Rate limiting unavailable | Backend logs (if Redis enabled) |
| **Feature Flag Service Down** | Unable to toggle feature flag | Backend health check |

### Manual Rollback Triggers (Decision Required)

Consider rollback if:

1. **User Feedback:**
   - Multiple complaints about blocked features (Excel, date range)
   - Confusion about quota limits or plan restrictions
   - Negative sentiment spike in support channels

2. **Business Impact:**
   - Trial-to-paid conversion rate <5% (target: 10-15%)
   - User churn rate increases >20%
   - Upgrade CTA click-through rate <1%

3. **Technical Issues:**
   - Quota tracking inconsistencies (users charged incorrectly)
   - Trial expiration logic errors (users blocked prematurely)
   - Plan capability mismatches (wrong limits applied)

4. **Data Integrity:**
   - Incorrect plan assignments in database
   - Quota counter resets failing
   - Trial expiration dates corrupted

5. **Performance Degradation:**
   - `/api/buscar` response time increases >50%
   - `/api/me` response time >2s (slow quota checks)
   - Database query timeout errors

---

## Rollback Decision Process

### Step 1: Assess Severity

**CRITICAL (Immediate Rollback - <5 minutes):**
- Application unusable for majority of users
- Data loss or corruption (quota tracking, plan assignments)
- Security vulnerability (bypassing plan limits)
- Error rate >10%
- Database connection failures

**HIGH (Rollback within 15 minutes):**
- Error rate 5-10%
- Core feature blocked for FREE/Consultor Ágil users
- Quota tracking failures (users incorrectly limited)
- Trial expiration logic broken

**MEDIUM (Investigate, then decide within 30 minutes):**
- Error rate 2-5%
- Non-critical UX issues (locked button tooltip incorrect)
- Upgrade modal not displaying correctly
- Minor quota counter display errors

**LOW (Monitor, fix forward):**
- Error rate <2%
- Minor UI glitches (badge color incorrect)
- Non-blocking analytics tracking issues
- Plan name typos

### Step 2: Gather Evidence

Before rollback, collect:

1. **Error Logs (Railway):**
   ```bash
   railway logs --tail 500 | grep -E "(403|429|ERROR)"
   ```

2. **Mixpanel Analytics:**
   - Search success rate (last 1 hour)
   - 403/429 error event counts
   - Upgrade CTA click events
   - Conversion funnel drop-off points

3. **Database State (Supabase):**
   ```sql
   -- Check plan distribution
   SELECT plan_id, COUNT(*) FROM users GROUP BY plan_id;

   -- Check quota usage
   SELECT AVG(searches_count) FROM monthly_quota WHERE month_year = '2026-02';

   -- Check trial expirations
   SELECT COUNT(*) FROM users WHERE trial_expires_at < NOW() AND plan_id = 'free_trial';
   ```

4. **User Reports:**
   - Support tickets (if any)
   - Social media mentions
   - Feedback form submissions

### Step 3: Make Decision

**Decision Maker:** @devops (primary), @pm (secondary)

**Decision Criteria:**
- [ ] Is the issue blocking >10% of users?
- [ ] Is the issue causing data corruption?
- [ ] Is the issue a security risk?
- [ ] Can the issue be fixed forward in <30 minutes?
- [ ] Is the rollback risk lower than leaving feature enabled?

**Decision:**
- [ ] **ROLLBACK** - Toggle feature flag to `false`
- [ ] **FIX FORWARD** - Deploy hotfix while monitoring
- [ ] **MONITOR** - Observe for 30 more minutes, then re-assess

**Reason:** _________________________________

**Authorized By:** _____________ Date/Time: _____________

---

## Rollback Procedure

### Feature Flag Rollback (Preferred Method)

**Estimated Time:** <30 seconds
**Downtime:** None (zero-downtime toggle)

#### Step 1: Toggle Feature Flag

**Option A: Environment Variable (Railway)**

1. **Open Railway Dashboard:**
   ```
   https://railway.app/dashboard → bidiq-backend → Variables
   ```

2. **Update Feature Flag:**
   ```
   ENABLE_NEW_PRICING=false
   ```

3. **Save Changes:**
   - Railway will automatically redeploy (takes ~90 seconds)
   - No code changes required

4. **Monitor Redeployment:**
   ```bash
   railway logs --tail
   # Wait for: "Application startup complete"
   ```

**Option B: In-Code Toggle (if dynamic flag system)**

If using a feature flag service (e.g., LaunchDarkly, Unleash):

1. **Open Feature Flag Dashboard:**
   ```
   [Feature Flag Service URL]
   ```

2. **Find Flag:**
   - Search for: `enable_new_pricing`
   - Current environment: Production

3. **Toggle OFF:**
   - Set to: `false` or `0%`
   - Save changes

4. **Verify Toggle (instant):**
   ```bash
   curl https://bidiq-backend-production.up.railway.app/api/feature-flags
   # Expected: {"enable_new_pricing": false}
   ```

#### Step 2: Verify Rollback (Backend)

```bash
# Test /api/me endpoint (should NOT return capabilities)
curl -X GET https://bidiq-backend-production.up.railway.app/api/me \
  -H "Authorization: Bearer <test-token>"

# Expected Response (OLD behavior):
{
  "user_id": "...",
  "email": "...",
  # NO capabilities, quota_used, quota_remaining, etc.
}

# Test /api/buscar (should NOT enforce date range limits)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2025-01-01",  # 1+ year range
    "dataFinal": "2026-01-30"
  }'

# Expected: 200 OK (no 403 error for date range)
```

#### Step 3: Verify Rollback (Frontend)

1. **Manual Browser Test:**
   - Open: https://bidiq-uniformes.vercel.app
   - ✅ No plan badge displayed in header
   - ✅ No quota counter visible
   - ✅ Excel download button NOT locked (no 🔒 icon)
   - ✅ Date range picker has no max limit warning

2. **Test Search Flow:**
   - Select UF: SP
   - Set date range: 1+ year (e.g., 2025-01-01 to 2026-01-30)
   - Click "Buscar Licitações"
   - ✅ Search succeeds (no 403 error)
   - ✅ Excel download functional (not blocked)

**Rollback Status:** ✅ Complete | ⏳ In Progress | ❌ Failed

---

### Full Deployment Rollback (Fallback Method)

**Use Case:** Feature flag toggle fails OR codebase issues require code rollback

**Estimated Time:** <5 minutes

See `docs/runbooks/rollback-procedure.md` for full deployment rollback steps.

**Quick Steps:**

1. **Identify Last Stable Deployment (before STORY-165):**
   - Railway: Deployments tab → Find deployment before STORY-165 merge
   - Vercel: Deployments tab → Find deployment before STORY-165 merge

2. **Execute Rollback:**
   - Railway: Click "•••" → Redeploy
   - Vercel: Click "•••" → Promote to Production

3. **Verify Health Checks:**
   ```bash
   curl https://bidiq-backend-production.up.railway.app/health
   curl https://bidiq-uniformes.vercel.app
   ```

---

## Post-Rollback Actions

### 1. Immediate Communication (Within 2 minutes)

**Team Notification (Slack/Discord):**
```
🚨 FEATURE ROLLBACK: STORY-165 (New Pricing)
Reason: [error rate >10% / quota tracking failures / etc.]
Action: Feature flag toggled to OFF
Status: Rollback complete in <30 seconds
Impact: Users reverted to unlimited access (old behavior)
Next Steps: [investigation / hotfix / re-deployment schedule]
```

**Stakeholder Notification (if applicable):**
```
Subject: [ALERT] STORY-165 Feature Rollback

The new pricing feature (STORY-165) has been rolled back due to [reason].
Users have reverted to unlimited access (previous behavior).

Rollback Time: <30 seconds
User Impact: Minimal (instant feature toggle)
Current Status: Stable on previous feature set
Next Steps: [investigation timeline]
```

### 2. Incident Report (Within 1 hour)

**File:** `docs/incidents/story165-rollback-YYYY-MM-DD-HHmm.md`

**Template:**
```markdown
# Incident Report - STORY-165 Rollback

**Date:** YYYY-MM-DD HH:mm UTC
**Duration:** X minutes (from detection to rollback complete)
**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Owner:** @devops

## Summary
[Brief description of what triggered rollback]

## Rollback Timeline
- HH:mm - Issue detected ([monitoring source])
- HH:mm - Rollback decision made (by [decision maker])
- HH:mm - Feature flag toggled to OFF
- HH:mm - Backend verification complete
- HH:mm - Frontend verification complete
- HH:mm - Incident resolved

## Trigger Metrics
- Error rate: X% (threshold: Y%)
- Affected users: X (estimated)
- Failed requests: X total
- Specific errors: [403, 429, etc.]

## Root Cause (Preliminary)
[What caused the issue? Code bug, logic error, data issue, etc.]

## Impact Assessment
- Users affected: X (estimated)
- Rollback duration: X seconds
- User-facing downtime: None (feature flag toggle)
- Revenue impact: N/A (no paying users yet)
- Trial users impacted: X (reverted to unlimited access)

## Resolution Method
Feature flag toggle: ENABLE_NEW_PRICING = false
Rollback mechanism: Railway environment variable update
Verification: Backend + frontend smoke tests

## Data Integrity Check
- [ ] User plan assignments intact (no corruption)
- [ ] Quota counters preserved (for re-enablement)
- [ ] Trial expiration dates unchanged
- [ ] Database state consistent

## Action Items
1. [ ] Fix root cause in code ([specific issue])
2. [ ] Add tests to prevent recurrence ([specific tests])
3. [ ] Update deployment checklist ([specific item])
4. [ ] Improve monitoring/alerting ([specific metric])
5. [ ] Re-test in staging with extended test suite
6. [ ] Schedule re-deployment ([target date])

## Lessons Learned
[What will we do differently next time?]

## Re-Deployment Plan
Target Date: [YYYY-MM-DD]
Prerequisites:
- [ ] Root cause fix merged and tested
- [ ] Extended staging tests (2x normal suite)
- [ ] Additional monitoring alerts configured
- [ ] Team available for 2 hours post-deploy
```

### 3. Root Cause Analysis (Within 24 hours)

**Investigation Areas:**

1. **Code Review:**
   - Review quota check logic (`backend/quota.py`)
   - Review date range validation (`backend/main.py`)
   - Review Excel gating logic
   - Review trial expiration handling

2. **Data Analysis:**
   ```sql
   -- Users affected by incorrect plan limits
   SELECT * FROM users WHERE plan_id = 'free_trial' AND trial_expires_at < NOW();

   -- Quota tracking anomalies
   SELECT user_id, searches_count FROM monthly_quota WHERE searches_count > 1000;

   -- Failed requests (from logs)
   SELECT COUNT(*), error_type FROM error_logs
   WHERE timestamp > [rollback_time - 1h]
   GROUP BY error_type;
   ```

3. **Test Gap Analysis:**
   - Were edge cases tested? (quota reset, trial expiration, leap year)
   - Was integration testing sufficient?
   - Were error scenarios covered?

4. **Monitoring Gap Analysis:**
   - Were appropriate alerts configured?
   - Were thresholds set correctly?
   - Was detection time acceptable (<2 min)?

**RCA Output:**
- Root cause identified: [specific issue]
- Fix required: [code change, config update, data migration]
- Prevention measures: [tests, monitoring, process changes]

### 4. Re-Deployment Planning

**Minimum Wait Time:** 24-48 hours (allow time for thorough fix + testing)

**Prerequisites for Re-Deployment:**

- [ ] **Root Cause Fixed:**
  - [ ] Code changes merged to `main`
  - [ ] Unit tests added (prevent recurrence)
  - [ ] Integration tests expanded
  - [ ] Edge cases covered

- [ ] **Extended Testing:**
  - [ ] Backend test coverage ≥80% (increased from 70%)
  - [ ] Frontend test coverage ≥70% (increased from 60%)
  - [ ] All STORY-165 test scenarios pass
  - [ ] Additional edge case testing (quota reset, trial expiration)

- [ ] **Staging Validation:**
  - [ ] Deployed to staging for 48 hours
  - [ ] Smoke tests passing continuously
  - [ ] No errors in staging logs
  - [ ] Performance benchmarks met

- [ ] **Monitoring Enhanced:**
  - [ ] Additional alerts configured:
    - 403 error rate >5%
    - 429 error rate >2%
    - Quota tracking failures
    - Trial expiration logic errors
  - [ ] Alert channels tested (Slack, email)
  - [ ] On-call schedule confirmed

- [ ] **Gradual Rollout Plan:**
  - [ ] Phase 1: 10% of users (monitor 24h)
  - [ ] Phase 2: 50% of users (monitor 24h)
  - [ ] Phase 3: 100% of users (monitor 48h)
  - [ ] Automatic rollback triggers defined (same as above)

- [ ] **Team Readiness:**
  - [ ] @devops available for 2 hours post-deploy
  - [ ] @qa available for verification
  - [ ] @pm informed of deployment schedule
  - [ ] No conflicting deployments scheduled

**Re-Deployment Timeline:**

| Day | Activity |
|-----|----------|
| D+0 | Rollback occurred, incident report created |
| D+1 | Root cause analysis complete, fix identified |
| D+2 | Fix implemented, tests added |
| D+3 | Staging deployment, extended testing begins |
| D+4 | Staging validation continues |
| D+5 | Production re-deployment (10% rollout) |
| D+6 | 50% rollout (if 10% successful) |
| D+7 | 100% rollout (if 50% successful) |

---

## Rollback Verification Checklist

### Pre-Rollback
- [ ] Severity assessed (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] Evidence gathered (logs, metrics, user reports)
- [ ] Rollback decision made by authorized person
- [ ] Team notified via Slack/Discord
- [ ] Stakeholders notified (if applicable)

### During Rollback
- [ ] Feature flag toggled to OFF (`ENABLE_NEW_PRICING=false`)
- [ ] Backend redeployment monitored (if env var change)
- [ ] Rollback time recorded (start → complete)

### Post-Rollback Verification
- [ ] **Backend Checks:**
  - [ ] `/api/me` does NOT return `capabilities` object
  - [ ] `/api/buscar` does NOT enforce date range limits (old behavior)
  - [ ] `/api/buscar` does NOT enforce quota limits (old behavior)
  - [ ] Excel generation works for all users (no gating)
  - [ ] Health check passing: `/health` returns 200 OK

- [ ] **Frontend Checks:**
  - [ ] No plan badge displayed in header
  - [ ] No quota counter visible
  - [ ] Excel download button NOT locked (no 🔒 icon)
  - [ ] Date range picker has no max limit warning
  - [ ] Search flow works (select UF → search → download)

- [ ] **Error Rate Verification:**
  - [ ] Error rate <1% (Railway dashboard)
  - [ ] No 403 errors in last 5 minutes
  - [ ] No 429 errors in last 5 minutes
  - [ ] Response time <5s (95th percentile)

- [ ] **Data Integrity:**
  - [ ] User plan assignments unchanged (no data loss)
  - [ ] Quota counters preserved (for future re-enablement)
  - [ ] Trial expiration dates intact
  - [ ] Database state consistent

### Post-Rollback Actions
- [ ] Incident report created
- [ ] Team notified of resolution
- [ ] Stakeholders notified (if applicable)
- [ ] Root cause analysis scheduled (within 24h)
- [ ] Re-deployment plan drafted

---

## Known Risks & Mitigations

### Risk 1: Feature Flag Toggle Delay

**Risk:** Railway environment variable change requires redeployment (~90 seconds)

**Mitigation:**
- Use dynamic feature flag service (LaunchDarkly, Unleash) for instant toggle
- OR: Implement in-code flag check with API endpoint to toggle without redeploy

**Fallback:**
- If instant toggle unavailable, use full deployment rollback (<5 minutes)

### Risk 2: Database State Inconsistency

**Risk:** Users may have quota counters, trial expirations set during feature enablement

**Mitigation:**
- Feature flag toggle does NOT delete data (preserves for re-enablement)
- Old code path ignores `capabilities`, `quota_used`, etc. (graceful degradation)
- Database state remains consistent (no migrations during rollback)

**Verification:**
```sql
-- After rollback, verify data intact
SELECT COUNT(*) FROM users WHERE plan_id IS NOT NULL;  -- Should match pre-rollback count
SELECT COUNT(*) FROM monthly_quota;  -- Should match pre-rollback count
```

### Risk 3: Frontend Caching Issues

**Risk:** Users may see cached version with plan badges/locked buttons after rollback

**Mitigation:**
- Vercel automatically purges cache on new deployment
- Next.js ISR (Incremental Static Regeneration) will update within seconds
- Users can hard refresh (Ctrl+Shift+R) to clear browser cache

**Verification:**
- Test in incognito browser (no cache)
- Check multiple browsers/devices
- Monitor user reports for lingering UI issues

### Risk 4: Partial Rollback (Backend Only or Frontend Only)

**Risk:** Feature flag toggles backend but frontend still shows plan UI

**Mitigation:**
- Frontend checks feature flag via API response (`/api/me`)
- If backend returns NO capabilities, frontend hides plan UI
- No frontend-only feature flag needed (backend drives behavior)

**Verification:**
- Frontend makes `/api/me` call on load
- If `capabilities` key missing, hide PlanBadge, QuotaCounter, locked Excel button

---

## Communication Templates

### Team Notification (Slack/Discord)

**Rollback Initiated:**
```
🚨 FEATURE ROLLBACK: STORY-165 (New Pricing)
Reason: [brief description]
Method: Feature flag toggle (ENABLE_NEW_PRICING=false)
ETA: 30 seconds
Status Updates: Every 2 minutes
```

**Rollback Complete:**
```
✅ ROLLBACK COMPLETE: STORY-165
Duration: X seconds
Method: Feature flag toggle
Current Status: Stable (reverted to unlimited access)
Impact: Users reverted to old behavior (no plan limits)
Next Steps:
1. Incident report: [link]
2. Root cause analysis: Within 24h
3. Re-deployment plan: TBD
Questions: Tag @devops
```

### Stakeholder Notification (Email)

**Subject: [ALERT] STORY-165 Feature Rollback - New Pricing**

```
Hi [Stakeholder],

We've rolled back the new pricing feature (STORY-165) due to [reason].

ROLLBACK SUMMARY:
- Feature: 3 Paid Tiers + FREE Trial
- Rollback Time: [HH:mm UTC]
- Duration: <30 seconds (feature flag toggle)
- User Impact: Minimal (instant revert to unlimited access)

CURRENT STATUS:
- Application stable and fully operational
- Users reverted to previous behavior (no plan limits)
- All features accessible (Excel download, unlimited date range)

NEXT STEPS:
1. Root cause analysis: [timeframe]
2. Fix implementation: [timeframe]
3. Re-deployment plan: [target date]

We'll provide updates every [frequency] until resolution.

Questions? Contact @devops or @pm.

Best,
DevOps Team
```

---

## Rollback Success Metrics

Track these metrics for each rollback:

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| **Detection Time** | <2 min | _____ | Time from issue to detection |
| **Decision Time** | <3 min | _____ | Time from detection to rollback decision |
| **Execution Time** | <30 sec | _____ | Time from decision to feature flag toggle |
| **Verification Time** | <2 min | _____ | Time to verify rollback success |
| **Total Incident Time** | **<5 min** | **_____** | **Total time from detection to resolution** |
| **User-Facing Downtime** | **0 min** | **_____** | **Zero-downtime feature toggle** |
| **Error Rate Post-Rollback** | <1% | _____% | Error rate after rollback |
| **Users Affected** | TBD | _____ | Estimated users impacted by issue |

---

## Appendix A: Feature Flag Configuration

### Environment Variable Method (Current)

**Railway Dashboard:**
```
Settings → Variables → ENABLE_NEW_PRICING
Values: "true" (enabled) | "false" (disabled)
```

**Backend Code:**
```python
# backend/config.py
import os

ENABLE_NEW_PRICING = os.getenv("ENABLE_NEW_PRICING", "false").lower() == "true"
```

**Usage in Code:**
```python
# backend/main.py
from config import ENABLE_NEW_PRICING

@app.post("/api/buscar")
async def buscar(request: BuscaRequest):
    if ENABLE_NEW_PRICING:
        # New behavior: Enforce plan limits
        quota_info = check_quota(user_id)
        if not quota_info.allowed:
            raise HTTPException(status_code=403, detail=quota_info.error_message)
    else:
        # Old behavior: No limits (unlimited access)
        pass

    # Continue with search logic...
```

### Dynamic Feature Flag Method (Future Enhancement)

**Recommended Service:** LaunchDarkly, Unleash, or custom API

**Benefits:**
- Instant toggle (no redeployment)
- Gradual rollout (10% → 50% → 100%)
- User-based targeting (beta users, internal testing)
- A/B testing capability

**Implementation Example:**
```python
# backend/feature_flags.py
from launchdarkly import LDClient

ld_client = LDClient(os.getenv("LAUNCHDARKLY_SDK_KEY"))

def is_feature_enabled(feature_key: str, user_id: str) -> bool:
    user = {"key": user_id}
    return ld_client.variation(feature_key, user, default=False)

# Usage
if is_feature_enabled("enable_new_pricing", user_id):
    # New behavior
else:
    # Old behavior
```

---

## Appendix B: Contact Information

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| **DevOps Lead (Primary)** | @devops | ____________ | 24/7 during rollout |
| **Project Manager (Secondary)** | @pm | ____________ | Business hours |
| **Architect (Backup)** | @architect | ____________ | On-call rotation |
| **QA Lead** | @qa | ____________ | Business hours |

**External Support:**
- Railway Support: https://railway.app/help
- Vercel Support: https://vercel.com/support
- Supabase Support: support@supabase.io (if DB issues)

---

## Document Metadata

**Document Version:** 1.0
**Created:** 2026-02-03
**Last Updated:** 2026-02-03
**Owner:** @devops
**Reviewed By:** @pm, @architect
**Next Review:** After first production deployment or rollback event

**Change Log:**
- 2026-02-03: Initial version created for STORY-165
