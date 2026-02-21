# Production Rollback Procedure

**Project:** BidIQ Uniformes
**Version:** 2.0
**Last Updated:** 2026-02-21
**Owner:** @devops

---

## Overview

This runbook provides step-by-step instructions for rolling back the BidIQ Uniformes application to a previous stable version in case of critical issues during or after deployment.

**Estimated Rollback Time:** < 5 min (backend + frontend, both on Railway)

**Rollback Authority:**
- Primary: @devops
- Secondary: @pm or @architect (if @devops unavailable)

---

## When to Rollback

### Automatic Rollback Triggers

Execute rollback **immediately** if any of these conditions are met:

1. **Error Rate >5%** for 5 consecutive minutes
2. **Health Check Failures >3** consecutive attempts
3. **Response Time >10s** (95th percentile) for 5 minutes
4. **Critical Feature Unavailable:**
   - Search functionality broken
   - Excel download failing
   - Backend API unreachable

### Manual Rollback Triggers

Consider rollback if:

1. **Data Integrity Issues:** Incorrect search results, corrupt Excel files
2. **Security Vulnerabilities:** Discovered in new deployment
3. **Unexpected Behavior:** Critical bug not caught in testing
4. **Performance Degradation:** >50% slower than previous version
5. **Stakeholder Request:** Critical business need

---

## Rollback Decision Process

### 1. Assess Severity

**CRITICAL (Immediate Rollback):**
- Application completely down
- Data loss or corruption
- Security breach
- Error rate >10%

**HIGH (Rollback within 15 minutes):**
- Error rate 5-10%
- Core feature unavailable
- Performance degradation >50%

**MEDIUM (Investigate, then decide):**
- Error rate 2-5%
- Non-critical feature broken
- Performance degradation 20-50%

**LOW (Monitor, fix forward):**
- Error rate <2%
- Minor UI glitch
- Performance degradation <20%

### 2. Communication

Before rollback, notify:

1. **Team Slack/Discord** (immediate):
   ```
   🚨 ROLLBACK INITIATED 🚨
   Reason: [error rate >5% / health check failing / etc.]
   ETA: 5 minutes
   Status updates: Every 2 minutes
   ```

2. **Stakeholders** (if applicable):
   ```
   Subject: [URGENT] BidIQ Production Issue - Rollback in Progress

   We've detected [issue] in production and are rolling back to the previous
   stable version. Estimated downtime: 5 minutes. Will update when resolved.
   ```

---

## Rollback Procedure

### Phase 1: Backend Rollback (Railway)

**Estimated Time:** 2 minutes

#### Option A: Railway Dashboard (Recommended)

1. **Open Railway Dashboard:**
   ```
   https://railway.app/dashboard
   ```

2. **Select Project:**
   - Navigate to `bidiq-backend` project
   - Click on the production service

3. **Access Deployments:**
   - Click "Deployments" tab
   - View deployment history

4. **Identify Last Stable Deployment:**
   - Look for the deployment **before** the current one
   - Check deployment time and commit SHA
   - Verify it has a **green checkmark** (successful)

5. **Execute Rollback:**
   - Click "•••" (three dots) on the stable deployment
   - Select "Redeploy"
   - Confirm: "Yes, redeploy this version"

6. **Monitor Redeployment:**
   - Watch logs in real-time
   - Wait for: `Application startup complete`
   - Expected time: ~90 seconds

7. **Verify Health:**
   ```bash
   curl https://bidiq-backend-production.up.railway.app/health
   # Expected: {"status":"healthy","timestamp":"..."}
   ```

#### Option B: Railway CLI (If Dashboard Unavailable)

1. **Login to Railway:**
   ```bash
   railway login
   ```

2. **Link to Project:**
   ```bash
   cd D:\pncp-poc\backend
   railway link
   # Select: bidiq-backend (production)
   ```

3. **Execute Rollback:**
   ```bash
   railway rollback
   # Select: Previous deployment from list
   ```

4. **Monitor Logs:**
   ```bash
   railway logs --tail
   # Wait for: Application startup complete
   ```

5. **Verify Health:**
   ```bash
   curl https://bidiq-backend-production.up.railway.app/health
   ```

**Backend Rollback Status:** ✅ Complete | ⏳ In Progress | ❌ Failed

---

### Phase 2: Frontend Rollback (Railway)

**Estimated Time:** 2 minutes

#### Option A: Railway Dashboard (Recommended)

1. **Open Railway Dashboard:**
   ```
   https://railway.app/dashboard
   ```

2. **Select Project:**
   - Navigate to the `bidiq-frontend` service
   - Click on the service name

3. **Access Deployments:**
   - Click "Deployments" tab
   - View deployment history

4. **Identify Last Stable Deployment:**
   - Look for the deployment **before** the current one
   - Check deployment time and commit SHA
   - Verify it has a **green checkmark** (successful)

5. **Execute Rollback:**
   - Click "•••" (three dots) on the stable deployment
   - Select "Redeploy"
   - Confirm: "Yes, redeploy this version"

6. **Monitor Redeployment:**
   - Watch logs in real-time
   - Wait for: `Listening on 0.0.0.0:3000`
   - Expected time: ~90 seconds

7. **Verify Health:**
   ```bash
   curl https://smartlic.tech
   # Expected: HTML content (200 OK)
   ```

#### Option B: Railway CLI (If Dashboard Unavailable)

1. **Login to Railway:**
   ```bash
   railway login
   ```

2. **Identify Previous Commit SHA:**
   ```bash
   # Find the last known good commit
   git log --oneline -10
   # Note the SHA of the previous stable version
   ```

3. **Execute Rollback:**
   ```bash
   railway redeploy --service bidiq-frontend -y
   # Or redeploy a specific commit:
   # railway service bidiq-frontend redeploy --commit <sha>
   ```

4. **Monitor Logs:**
   ```bash
   railway logs --service bidiq-frontend --tail
   # Wait for: Listening on 0.0.0.0:3000
   ```

5. **Verify Health:**
   ```bash
   curl https://smartlic.tech
   # Expected: HTML content (200 OK)
   ```

**Frontend Rollback Status:** ✅ Complete | ⏳ In Progress | ❌ Failed

---

### Phase 3: Verification & Smoke Tests

**Estimated Time:** 3 minutes

#### 3.1 Backend Verification

```bash
# Health Check
curl https://bidiq-backend-production.up.railway.app/health
# Expected: {"status":"healthy","timestamp":"..."}

# API Docs
curl https://bidiq-backend-production.up.railway.app/docs
# Expected: 200 OK (HTML)

# Test Search (1 state)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -d '{
    "ufs": ["SP"],
    "dataInicial": "2026-01-23",
    "dataFinal": "2026-01-30"
  }'
# Expected: 200 OK with results
```

#### 3.2 Frontend Verification

1. **Manual Browser Test:**
   - Open: https://smartlic.tech
   - ✅ Page loads in <2s
   - ✅ No JavaScript errors in console
   - ✅ All UI components render

2. **Integration Test:**
   - Select UF: SP
   - Click "Buscar Licitações"
   - ✅ Loading progress displays
   - ✅ Results appear
   - ✅ Download button functional

#### 3.3 Error Rate Verification

**Railway Dashboard (Backend):**
- Navigate to: Observability → Metrics
- Check: Error rate <1% over last 5 minutes
- Check: Response time <5s (95th percentile)

**Railway Dashboard (Frontend):**
- Navigate to: Observability → Metrics
- Check: Error rate <1% over last 5 minutes
- Check: No new error types

**Verification Status:** ✅ All Checks Passed | ⚠️ Partial Issues | ❌ Rollback Failed

---

## Post-Rollback Actions

### 1. Incident Report (Required)

Create incident report immediately:

**File:** `docs/incidents/incident-YYYY-MM-DD-HHmm.md`

**Template:**
```markdown
# Incident Report - Production Rollback

**Date:** YYYY-MM-DD HH:mm UTC
**Duration:** X minutes (from detection to resolution)
**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Owner:** @devops

## Summary
Brief description of what went wrong.

## Timeline
- HH:mm - Issue detected
- HH:mm - Rollback decision made
- HH:mm - Backend rollback initiated
- HH:mm - Frontend rollback initiated
- HH:mm - Verification complete
- HH:mm - Incident resolved

## Root Cause
What caused the issue?

## Impact
- Users affected: X
- Downtime: X minutes
- Error rate: X%
- Revenue impact (if applicable): $X

## Resolution
How was it fixed (i.e., rollback)?

## Action Items
1. [ ] Fix root cause in code
2. [ ] Add tests to prevent recurrence
3. [ ] Update deployment checklist
4. [ ] Improve monitoring/alerting

## Lessons Learned
What will we do differently next time?
```

### 2. Stakeholder Communication

**Team Notification:**
```
✅ ROLLBACK COMPLETE ✅
Duration: X minutes
Current status: Stable on previous version
Root cause: [brief description]
Next steps: [investigation / fix / etc.]
```

**Stakeholder Notification (if applicable):**
```
Subject: [RESOLVED] BidIQ Production Issue

The issue has been resolved by rolling back to the previous stable version.
Application is now fully operational. We are investigating the root cause
and will provide an update within [timeframe].

Downtime: X minutes
User impact: [description]
Next steps: [plan]
```

### 3. Root Cause Analysis

Within 24 hours, conduct RCA:

1. **Gather Data:**
   - Deployment logs (Railway backend + frontend)
   - Error logs (backend + frontend)
   - Monitoring metrics (before/during/after)
   - User reports (if any)

2. **Identify Root Cause:**
   - What changed? (code diff)
   - What broke? (specific component/function)
   - Why wasn't it caught? (testing gap)

3. **Create Fix:**
   - Write code to fix root cause
   - Add tests to prevent recurrence
   - Test thoroughly in staging

4. **Update Processes:**
   - Update pre-deployment checklist
   - Improve smoke tests
   - Add monitoring/alerting

### 4. Plan Next Deployment

**Timing:**
- Wait: 24-48 hours (allow time for thorough fix + testing)
- Avoid: Fridays, holidays, end-of-day

**Prerequisites:**
- [ ] Root cause fix implemented
- [ ] New tests added (prevent recurrence)
- [ ] Staging deployment successful
- [ ] Extended smoke testing (2x normal)
- [ ] Team available for 2 hours post-deploy

---

## Emergency Localhost Fallback

**Use Case:** Railway platform is completely down (extremely rare)

### Step 1: Run Backend Locally

```bash
# Navigate to backend
cd D:\pncp-poc\backend

# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Expected: Server running on http://0.0.0.0:8000
```

### Step 2: Run Frontend Locally

```bash
cd D:\pncp-poc\frontend
npm run dev
# Expected: Server running on http://localhost:3000
```

### Step 3: Notify Stakeholders

```
⚠️ EMERGENCY FALLBACK ACTIVATED ⚠️
Railway platform unavailable. Running on local infrastructure.
Access: http://<your-ip>:3000
Status: Investigating Railway platform issues
ETA: Unknown (dependent on Railway)
```

---

## Rollback Checklist Summary

### Pre-Rollback
- [ ] Severity assessed (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] Team notified via Slack/Discord
- [ ] Stakeholders notified (if applicable)
- [ ] Decision maker authorized rollback

### During Rollback
- [ ] Backend rolled back (Railway)
- [ ] Frontend rolled back (Railway)
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Error rate <1%

### Post-Rollback
- [ ] Incident report created
- [ ] Team notified of resolution
- [ ] Stakeholders notified (if applicable)
- [ ] Root cause analysis scheduled
- [ ] Next deployment planned

---

## Common Issues & Troubleshooting

### Issue: Railway Rollback Fails

**Symptom:** `railway rollback` command errors or deployment fails

**Solution:**
1. Check Railway status: https://railway.app/status
2. Verify project/service ID: `railway list`
3. Try dashboard rollback instead of CLI
4. Contact Railway support if platform issue

### Issue: Frontend (Railway) Rollback Fails

**Symptom:** Redeploy fails or deployment errors

**Solution:**
1. Check Railway status: https://railway.app/status
2. Verify service exists: `railway status`
3. Try dashboard rollback instead of CLI
4. Contact Railway support if platform issue

### Issue: Health Checks Still Failing After Rollback

**Symptom:** `curl /health` returns errors after rollback

**Solution:**
1. Check environment variables (may have been changed)
2. Verify OPENAI_API_KEY is valid
3. Check PNCP API status: https://pncp.gov.br
4. Review Railway logs for errors
5. Consider emergency localhost fallback

### Issue: Frontend Shows Errors After Rollback

**Symptom:** Page loads but shows errors or broken UI

**Solution:**
1. Hard refresh browser: Ctrl+Shift+R
2. Clear browser cache
3. Verify NEXT_PUBLIC_BACKEND_URL points to Railway URL
4. Check CORS configuration in backend
5. Review Railway frontend logs for errors

---

## Rollback Metrics

Track these metrics for each rollback:

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| Detection Time | <2 min | _____ | Time from issue to detection |
| Decision Time | <3 min | _____ | Time from detection to rollback decision |
| Execution Time | <5 min | _____ | Time from decision to rollback complete |
| Verification Time | <3 min | _____ | Time to verify rollback success |
| **Total Downtime** | **<10 min** | **_____** | **Total user-facing downtime** |

---

## Release Checklist

Follow these steps for every production release:

### 1. Update CHANGELOG.md

```bash
# Add new version entry at top of CHANGELOG.md
# Follow Keep a Changelog format
```

### 2. Create Git Tag

```bash
bash scripts/create-release.sh vX.Y.Z
# Idempotent: exits gracefully if tag exists
```

### 3. Verify Tag on GitHub

```bash
# Verify locally
git describe --tags HEAD

# Verify on GitHub
gh release list
# Or visit: https://github.com/tjsasakifln/PNCP-poc/tags
```

### 4. Deploy via CI

```bash
# Push to main triggers deploy.yml
git push origin main

# Or manual dispatch
gh workflow run deploy.yml
```

### 5. Verify /health

```bash
curl -s https://bidiq-backend-production.up.railway.app/health | python3 -m json.tool | grep version
# Expected: "version": "vX.Y.Z"
```

---

## Appendix: Contact Information

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| DevOps Lead | @devops | ____________ | 24/7 |
| Project Manager | @pm | ____________ | Business hours |
| Architect | @architect | ____________ | On-call rotation |
| QA Lead | @qa | ____________ | Business hours |

**Railway Support:** https://railway.app/help

---

**Document Version:** 2.0
**Created:** 2026-01-30
**Last Updated:** 2026-02-21
**Owner:** @devops
**Next Review:** After next production rollback event
