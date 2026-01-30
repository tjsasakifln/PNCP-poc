# Mixpanel Alert Runbook

**Version:** 1.0
**Last Updated:** 2026-01-30
**Purpose:** Troubleshooting guide for Mixpanel analytics alerts

---

## Alert Overview

This runbook documents the 8 configured Mixpanel alerts, their thresholds, and step-by-step troubleshooting procedures.

**Alert Categories:**
- **Critical:** Immediate response required (< 1 hour)
- **Warning:** Investigation required (< 4 hours)

---

## Alert Notification Channels

**Primary:**
- Email notifications to configured recipients
- Slack #bidiq-alerts channel (via webhook)

**Escalation:**
- Critical: Tag @devops and @dev in Slack
- Warning: Tag @analyst and @pm

**On-Call Rotation:**
- **Business Hours (9am-6pm BRT):** Dev team
- **After Hours:** DevOps (critical only)

---

## Critical Alerts

### 🚨 ALERT 1: Error Rate Spike

**Severity:** Critical ⚠️
**Trigger Condition:** Error rate > 10% for 1 hour
**Metric:** `(search_failed / search_started) * 100`
**Dashboard:** Performance Dashboard
**Recipients:** @dev, @devops

#### Symptoms

- Many users encountering search errors
- Error messages displayed frequently
- Potential complete service outage

#### Possible Causes

1. **PNCP API Down/Unstable**
   - PNCP service outage
   - Network connectivity issues
   - Rate limiting (429 errors)

2. **Backend Server Issues**
   - Railway deployment failure
   - Memory/CPU exhaustion
   - Database connection loss

3. **Code Bugs**
   - Uncaught exception in new deployment
   - Regression in search logic
   - Invalid input validation

#### Troubleshooting Steps

**Step 1: Verify Scope (5 minutes)**

1. Open Mixpanel Performance Dashboard
2. Check error rate trend (last 24 hours)
3. Break down by `error_type` to identify pattern
4. Check if errors affect all UFs or specific states

**Step 2: Check Backend Health (5 minutes)**

```bash
# 1. Check Railway backend status
railway status

# 2. Check recent logs
railway logs --tail 100

# 3. Check health endpoint
curl https://bidiq-backend.railway.app/health

# 4. Check error logs
railway logs | grep "ERROR" | tail -50
```

**Step 3: Check PNCP API (5 minutes)**

```bash
# Test PNCP API directly
curl "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=2026-01-23&dataFinal=2026-01-30&uf=SC&pagina=1&tamanhoPagina=10"

# Expected: 200 OK with JSON response
# If 5xx: PNCP is down
# If 429: Rate limited (unlikely for direct test)
# If timeout: Network/connectivity issue
```

**Step 4: Analyze Specific Error Types**

**If `error_type = NetworkError`:**
- Backend can't reach PNCP
- Check Railway network settings
- Verify DNS resolution
- Check for firewall/security rules

**If `error_type = TypeError` or `ReferenceError`:**
- Code bug (likely recent deployment)
- Check recent commits: `git log --oneline -10`
- Review changed files
- Rollback if necessary: `railway rollback`

**If `error_type = TimeoutError`:**
- PNCP responding slowly (>30s)
- Increase timeout threshold
- Check PNCP status page
- Temporary issue likely

**If `error_type = ValidationError`:**
- Invalid user input bypassing frontend validation
- Review frontend validation logic
- Check for malicious requests

**Step 5: Immediate Mitigation**

**If PNCP is down:**
- No immediate fix possible (external dependency)
- Post status update in Slack
- Enable maintenance banner on frontend
- Set up PNCP status monitoring

**If backend is down:**
- Restart Railway service: `railway restart`
- Scale up if resource exhaustion: `railway scale`
- Rollback if recent deployment: `railway rollback`
- Check logs for stack traces

**If code bug:**
- Identify breaking commit: `git bisect`
- Revert commit: `git revert <commit-hash>`
- Deploy hotfix: `git push origin main`
- Railway auto-deploys

#### Post-Incident

1. **Document in Slack:** Post-mortem summary in #bidiq-alerts
2. **Update Runbook:** Add new error pattern if novel
3. **Prevent Recurrence:**
   - Add test case for bug
   - Improve monitoring
   - Add PNCP status check before search

---

### 🚨 ALERT 2: Search Success Rate Drop

**Severity:** Critical ⚠️
**Trigger Condition:** Search success rate < 80% for 2 hours
**Metric:** `(search_completed / search_started) * 100`
**Dashboard:** User Engagement Dashboard
**Recipients:** @dev, @po

#### Symptoms

- High percentage of failed searches
- Users reporting inability to search
- Reduced download activity

#### Possible Causes

1. **Partial Backend Outage**
   - Backend running but degraded
   - Database read/write failures
   - Cache unavailable

2. **PNCP API Degradation**
   - Intermittent PNCP failures
   - Increased latency causing timeouts
   - Partial data corruption

3. **Input Validation Issues**
   - New validation rules too strict
   - Invalid default date ranges
   - UF selection bugs

#### Troubleshooting Steps

**Step 1: Differentiate from Alert 1**

- If error rate is also >10%, follow Alert 1 runbook first
- If error rate is <10% but success rate <80%, continue here

**Step 2: Analyze Success Rate Breakdown**

1. Open User Engagement Dashboard
2. Break down success rate by:
   - `setor_id` (does one sector fail more?)
   - `uf_count` (do multi-state searches fail more?)
   - Hour of day (time-based pattern?)

**Step 3: Sample Failed Searches**

```bash
# Check recent search logs
railway logs | grep "search_started" | tail -20
railway logs | grep "search_failed" | tail -20

# Look for patterns:
# - Specific UFs failing consistently?
# - Specific date ranges causing errors?
# - Specific sectors broken?
```

**Step 4: Test Manually**

1. Go to production site: https://bidiq.vercel.app
2. Perform test search:
   - UF: SC
   - Date range: Last 7 days
   - Sector: Vestuário
3. If fails: Note exact error message
4. Try different combinations to isolate

**Step 5: Check Backend Validation**

```python
# If certain inputs are failing, review validation logic
# backend/app/schemas.py - BuscaRequest validation

# Example: Check date range validation
# Are users selecting >30 day ranges?
# Is date format validation too strict?
```

#### Immediate Mitigation

**If specific UF is broken:**
- Investigate UF-specific PNCP data issues
- Temporarily disable UF in frontend (last resort)
- Add skip logic in backend for problematic UF

**If specific sector is broken:**
- Review sector keyword list
- Check for regex errors in filter logic
- Temporarily remove problematic keywords

**If validation is too strict:**
- Relax validation rules
- Add better error messages to guide users
- Log validation failures for analysis

#### Post-Incident

1. **Root Cause Analysis:** Why did validation fail?
2. **Improve Error Handling:** Better user-facing errors
3. **Add Monitoring:** Track validation failures separately

---

### 🚨 ALERT 3: Download Failure Spike

**Severity:** Critical ⚠️
**Trigger Condition:** Download completion rate < 85% for 1 hour
**Metric:** `(download_completed / download_started) * 100`
**Dashboard:** User Engagement Dashboard
**Recipients:** @dev

#### Symptoms

- Users clicking "Download Excel" but file not downloading
- Error messages on download
- Reduced business value delivery

#### Possible Causes

1. **File Generation Errors**
   - Excel generation library (openpyxl) failure
   - Invalid data causing openpyxl crash
   - Memory exhaustion on large files

2. **Storage Issues**
   - Disk full on Railway server
   - Temp directory cleanup failure
   - Permission issues

3. **Cache Expiration**
   - Download ID expired (>10min TTL)
   - Cache cleared prematurely
   - Cache eviction due to memory pressure

#### Troubleshooting Steps

**Step 1: Check Download Error Types**

1. Open Mixpanel → Events → `download_failed`
2. Break down by `error_type`
3. Sample error messages

**Step 2: Check Backend Logs**

```bash
# Check Excel generation errors
railway logs | grep "Excel" | tail -50

# Check download endpoint errors
railway logs | grep "/api/download" | tail -50

# Check for disk space issues
railway logs | grep "No space left" | tail -20
```

**Step 3: Test Download Manually**

1. Perform search on production
2. Click "Download Excel"
3. Open browser DevTools → Network tab
4. Check `/api/download?id=...` request:
   - Status code (200 OK expected)
   - Response headers (Content-Type, Content-Disposition)
   - Response body (Excel binary or error JSON)

**Step 4: Check Storage**

```bash
# Check Railway disk usage
railway run df -h

# Check temp directory
railway run ls -lh /tmp | head -20

# Check memory usage
railway run free -h
```

**Step 5: Isolate Issue**

**If `error_type = NotFoundError`:**
- Download ID not in cache (expired or never created)
- Check cache TTL (should be 10 minutes)
- Check if `search_completed` event has `download_id` property

**If `error_type = FileGenerationError`:**
- Excel creation failed
- Check openpyxl logs
- Review data that failed to export
- Limit file size if too large

**If `error_type = NetworkError`:**
- File transfer interrupted
- Check client-side network issues
- Increase download timeout

#### Immediate Mitigation

**If cache expiration too short:**
```bash
# Increase cache TTL from 10min to 30min (temporary)
# Edit backend/app/api/routes.py
# Change DOWNLOAD_CACHE_TTL = 600 to 1800
git commit -am "temp: increase download cache TTL"
git push origin main
```

**If disk full:**
```bash
# Clear temp files
railway run rm -rf /tmp/*.xlsx

# Increase disk size (Railway dashboard)
# Or upgrade Railway plan
```

**If openpyxl bug:**
- Add try-except around Excel generation
- Return CSV as fallback
- Log failing data for debugging

#### Post-Incident

1. **Implement File Cleanup:** Cron job to clean old temp files
2. **Add Storage Monitoring:** Alert if disk >80% full
3. **Optimize Excel Generation:** Stream large files instead of in-memory

---

### 🚨 ALERT 4: Response Time Degradation

**Severity:** Critical ⚠️
**Trigger Condition:** P95 response time > 40 seconds for 30 minutes
**Metric:** `P95(search_completed.time_elapsed_ms)`
**Dashboard:** Performance Dashboard
**Recipients:** @devops, @dev

#### Symptoms

- Searches taking very long to complete
- Users abandoning searches (loading_abandoned spike)
- Poor user experience

#### Possible Causes

1. **PNCP API Slowness**
   - PNCP servers under load
   - Increased latency from PNCP
   - Network congestion

2. **Backend Performance Issues**
   - Inefficient filtering logic
   - Memory swap (out of RAM)
   - CPU throttling

3. **Large Result Sets**
   - Users searching all 27 UFs (national search)
   - 30-day date ranges
   - High volume of raw PNCP data

#### Troubleshooting Steps

**Step 1: Check Performance Distribution**

1. Open Performance Dashboard
2. View Search Duration Distribution histogram
3. Identify if all searches are slow or just a few outliers
4. Check if P50 is also slow (vs just P95)

**Step 2: Correlate with Search Parameters**

1. Break down slow searches by:
   - `uf_count` (multi-state searches slower?)
   - `date_range_days` (longer ranges slower?)
   - `total_raw` (more raw data slower?)

**Step 3: Check Backend Resources**

```bash
# Check CPU and memory usage
railway run top -b -n 1

# Check Railway metrics dashboard
# Look for CPU/memory spikes

# Check if backend is being throttled
railway logs | grep "throttle" | tail -20
```

**Step 4: Profile Search Performance**

```bash
# Add timing logs to backend (if not present)
# Check time spent in each phase:
# 1. PNCP API call
# 2. Filtering
# 3. LLM summary
# 4. Excel generation

railway logs | grep "time_elapsed" | tail -20
```

**Step 5: Test PNCP API Directly**

```bash
# Measure PNCP API response time directly
time curl "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=2026-01-23&dataFinal=2026-01-30&uf=SC&pagina=1&tamanhoPagina=500"

# If >10s, PNCP is slow
# If <5s, backend processing is slow
```

#### Immediate Mitigation

**If PNCP is slow:**
- No immediate fix (external dependency)
- Communicate to users via banner
- Consider caching common searches
- Add PNCP status check and fail-fast

**If backend is slow:**
```bash
# Scale up Railway instance
railway scale --memory 1GB --cpu 1vCPU

# Or restart to clear memory
railway restart
```

**If large searches are slow:**
- Add frontend warning for national searches (all 27 UFs)
- Limit date range to 15 days max
- Add pagination for large result sets

**If filtering is slow:**
- Optimize keyword matching (use compiled regex)
- Parallelize filtering across UFs
- Add early-exit logic

#### Post-Incident

1. **Optimize Filtering:** Profile and improve bottleneck
2. **Add Caching:** Cache PNCP results for 5 minutes
3. **Set Timeouts:** Enforce 60s max search time
4. **Improve UX:** Show progress estimates, allow cancellation

---

## Warning Alerts

### ⚠️ ALERT 5: Bounce Rate High

**Severity:** Warning
**Trigger Condition:** Bounce rate > 50% for 1 day
**Metric:** `(page_exit with session_duration_ms < 30000 AND no search_started) / page_load * 100`
**Dashboard:** User Engagement Dashboard
**Recipients:** @ux-design-expert, @po

#### Symptoms

- Many users leaving within 30 seconds
- Low search initiation rate
- Poor first impression

#### Possible Causes

1. **UX/UI Issues**
   - Confusing interface
   - Unclear value proposition
   - Broken onboarding tour

2. **Performance Issues**
   - Page loads slowly (>5s)
   - Unresponsive UI
   - White screen on load

3. **Wrong Audience**
   - Traffic from irrelevant sources
   - Misleading marketing
   - Bot traffic

#### Troubleshooting Steps

**Step 1: Segment Bounces**

1. Break down bounce rate by:
   - `referrer` (where are users coming from?)
   - `user_agent` (device/browser issues?)
   - Hour of day (time-based pattern?)

**Step 2: Check for Bots**

```javascript
// In Mixpanel Insights:
// Filter page_load events where user_agent contains "bot" or "crawler"
// Count bot traffic vs. human traffic
```

**Step 3: User Journey Analysis**

1. Mixpanel → Reports → Flows
2. Start event: `page_load`
3. See what users do (or don't do) next
4. Identify common drop-off points

**Step 4: Onboarding Analysis**

1. Check onboarding tour metrics:
   - `onboarding_step` (are users seeing tour?)
   - `onboarding_completed` vs `onboarding_dismissed`
2. If tour not triggering, check Shepherd.js logs

**Step 5: Performance Check**

```bash
# Check page load performance
# Use Lighthouse or WebPageTest
# Target: <3s Time to Interactive

# Check frontend build size
cd frontend
npm run build
# Look for large bundles (>300KB)
```

#### Immediate Actions

**If UX issue:**
- Conduct user testing with 5-10 users
- Gather qualitative feedback
- Prioritize UX improvements

**If onboarding broken:**
- Test tour in production
- Fix Shepherd.js configuration
- Simplify tour (reduce steps)

**If performance issue:**
- Optimize frontend bundle size
- Enable CDN caching
- Compress images/assets

**If bot traffic:**
- Add bot detection (frontend/backend)
- Filter bots from analytics
- No immediate user impact

#### Post-Incident

1. **UX Improvements:** Redesign based on user feedback
2. **Onboarding V2:** A/B test simplified tour
3. **Performance Optimization:** Code splitting, lazy loading

---

### ⚠️ ALERT 6: Loading Abandonment

**Severity:** Warning
**Trigger Condition:** Abandonment rate > 15% for 4 hours
**Metric:** `(loading_abandoned / loading_stage_reached) * 100`
**Dashboard:** Performance Dashboard
**Recipients:** @ux-design-expert, @dev

#### Symptoms

- Users navigating away during search
- High drop-off during loading stages
- Poor patience/tolerance

#### Possible Causes

1. **Long Wait Times**
   - Search taking >30 seconds
   - No perceived progress
   - Uncertainty about completion

2. **Loading UX Issues**
   - Progress indicator not updating
   - Stages advancing too slowly
   - No cancel button

3. **User Impatience**
   - Unrealistic expectations (<10s)
   - Competing urgent tasks
   - Mobile users (shorter attention span)

#### Troubleshooting Steps

**Step 1: Identify Abandonment Stage**

1. Break down `loading_abandoned` by `last_stage`
2. Which stage do most users abandon at?
   - Stage 1-2: Immediate abandonment (too slow to start)
   - Stage 3-4: Mid-search abandonment (lost patience)
   - Stage 5: Near-completion abandonment (timeout?)

**Step 2: Check Actual Search Times**

1. Compare abandonment rate to actual search duration
2. If searches are <20s but abandonment is high:
   - UX issue (perceived slowness)
3. If searches are >40s and abandonment is high:
   - Performance issue (actual slowness)

**Step 3: Analyze Loading Stage Times**

1. Break down `loading_stage_reached` by `time_in_stage_ms`
2. Identify slowest stage (bottleneck)
3. Correlate with `search_completed.time_elapsed_ms`

**Step 4: User Device Analysis**

1. Parse `user_agent` to detect mobile vs desktop
2. Check if mobile users abandon more
3. If yes: Mobile UX needs improvement

#### Immediate Actions

**If UX issue (perceived slowness):**
- Improve progress indicator (show exact percentages)
- Add time estimates ("About 15 seconds remaining")
- Add animations to show activity
- Add cancel button

**If performance issue (actual slowness):**
- Follow Alert 4 runbook (Response Time Degradation)
- Optimize slowest loading stage
- Set timeout and fail-fast

**If mobile-specific:**
- Optimize mobile loading UX
- Simplify mobile search flow
- Consider mobile-specific optimizations

#### Post-Incident

1. **Loading UX V2:** Add progress estimates, cancel button
2. **Performance Optimization:** Reduce slowest stage time
3. **User Testing:** Validate UX improvements

---

### ⚠️ ALERT 7: Feature Adoption Low

**Severity:** Warning
**Trigger Condition:** Saved searches adoption < 10% after 14 days
**Metric:** `(Unique users with saved_search_created / DAU) * 100`
**Dashboard:** Feature Usage Dashboard
**Recipients:** @po, @ux-design-expert

#### Symptoms

- Very few users saving searches
- Feature not being discovered
- Low repeat usage

#### Possible Causes

1. **Discoverability**
   - Feature hidden in UI
   - No prompts to use feature
   - Not included in onboarding tour

2. **Value Proposition Unclear**
   - Users don't understand benefit
   - Feature seems unnecessary
   - No use case demonstrated

3. **UX Friction**
   - Too many clicks to save search
   - Naming search is cumbersome
   - Editing saved searches is hard

#### Troubleshooting Steps

**Step 1: Check Feature Visibility**

1. Go to production site
2. Perform search
3. How obvious is "Save Search" button?
4. Is it visible above the fold?

**Step 2: Onboarding Tour Check**

1. Trigger onboarding tour
2. Does it mention saved searches?
3. If not, add to tour

**Step 3: User Feedback**

1. Contact 5-10 active users
2. Ask: "Have you noticed the Save Search feature?"
3. Ask: "Would you use it if X?"
4. Gather qualitative insights

**Step 4: Competitor Analysis**

1. Check how other tools implement saved searches
2. Identify best practices
3. Note differences in UX

#### Immediate Actions

**If discoverability issue:**
- Make "Save Search" button more prominent
- Add tooltip on first search result
- Include in onboarding tour (add step)

**If value proposition unclear:**
- Add explanatory text: "Save this search to quickly repeat it later"
- Show example use case
- Add "New Feature" badge temporarily

**If UX friction:**
- Auto-generate search name (e.g., "Vestuário - SC, PR")
- Allow quick save without naming
- Simplify edit/delete flow

#### Post-Incident

1. **A/B Test:** Test different Save button placements
2. **User Education:** In-app tips, tutorial video
3. **Feature Iteration:** Based on user feedback

---

### ⚠️ ALERT 8: Onboarding Completion Low

**Severity:** Warning
**Trigger Condition:** Tour completion < 50% for 7 days
**Metric:** `(onboarding_completed / onboarding_step) * 100`
**Dashboard:** Feature Usage Dashboard
**Recipients:** @ux-design-expert, @po

#### Symptoms

- Many users starting tour but not finishing
- High dismissal rate
- Onboarding ineffective

#### Possible Causes

1. **Tour Too Long**
   - Too many steps (>5)
   - Each step too wordy
   - User fatigue

2. **Tour Not Relevant**
   - Steps don't apply to user's goal
   - Feature-focused instead of task-focused
   - Power users don't need basics

3. **Tour UX Issues**
   - Hard to dismiss/skip
   - Blocks critical UI elements
   - Confusing navigation (back/forward)

#### Troubleshooting Steps

**Step 1: Analyze Dismissal Patterns**

1. Break down `onboarding_dismissed` by `step_id`
2. Which step do users quit at?
3. Is there a consistent drop-off point?

**Step 2: Step-by-Step Analysis**

1. For each step, calculate:
   - `onboarding_step[N]` (users who saw step N)
   - `onboarding_step[N+1]` (users who advanced)
   - Drop-off rate: `1 - (N+1 / N)`
2. Identify highest drop-off step

**Step 3: Tour Testing**

1. Go through tour as first-time user
2. Note any issues:
   - Confusing wording?
   - Too much text?
   - Step doesn't make sense?
3. Get external user to test

**Step 4: Completion Time Analysis**

1. Calculate average tour duration:
   - `onboarding_completed.completion_time - page_load.timestamp`
2. If >2 minutes, tour is too long

#### Immediate Actions

**If tour too long:**
- Reduce to 3-5 steps max
- Simplify wording (50 words per step max)
- Remove non-essential steps

**If tour not relevant:**
- Add "Skip Tour" button (make it obvious)
- Show tour only to first-time users
- Offer "Quick Tour" (3 steps) vs "Full Tour" (7 steps)

**If specific step is problematic:**
- Rewrite confusing step
- Add visual highlighting to guide user
- Test with users again

#### Post-Incident

1. **Tour V2:** Simplified 3-step tour
2. **A/B Test:** Test different tour lengths
3. **Contextual Help:** Replace tour with in-context tooltips

---

## Escalation Matrix

| Alert | Initial Owner | Escalation (1h) | Escalation (2h) | Escalation (4h) |
|-------|---------------|-----------------|-----------------|-----------------|
| 1. Error Rate Spike | @dev | @devops | @architect | @pm |
| 2. Search Success Drop | @dev | @po | @devops | @pm |
| 3. Download Failure | @dev | @devops | - | @pm |
| 4. Response Time Degradation | @devops | @dev | @architect | @pm |
| 5. Bounce Rate High | @ux-design-expert | @po | @pm | - |
| 6. Loading Abandonment | @ux-design-expert | @dev | @po | - |
| 7. Feature Adoption Low | @po | @ux-design-expert | @pm | - |
| 8. Onboarding Completion Low | @ux-design-expert | @po | @pm | - |

**Escalation Rules:**
- If unresolved after 1 hour, escalate to next level
- Tag all previous escalation levels in Slack
- Document actions taken before escalating

---

## Post-Incident Checklist

After resolving any alert:

- [ ] **Document Incident**
  - What happened (summary)
  - Root cause identified
  - Actions taken
  - Resolution time

- [ ] **Post-Mortem** (for critical alerts)
  - Timeline of events
  - What went well
  - What went wrong
  - Action items to prevent recurrence

- [ ] **Update Runbook**
  - Add new troubleshooting steps if applicable
  - Update thresholds if too sensitive/lenient
  - Add known issues section

- [ ] **Communicate**
  - Slack #bidiq-alerts: Incident resolved
  - Stakeholder email: If customer-facing impact
  - Team retrospective: Lessons learned

- [ ] **Implement Fixes**
  - Create GitHub issues for long-term fixes
  - Prioritize in backlog
  - Assign owners

---

## Appendix: Useful Commands

### Railway CLI

```bash
# Check service status
railway status

# View logs (last 100 lines)
railway logs --tail 100

# Follow logs in real-time
railway logs --follow

# Restart service
railway restart

# Rollback to previous deployment
railway rollback

# Scale resources
railway scale --memory 512MB --cpu 0.5vCPU

# Run command in Railway container
railway run <command>

# SSH into container
railway shell
```

### Mixpanel Debugging

```javascript
// In browser console (production):

// Check if Mixpanel is initialized
mixpanel.get_distinct_id();

// View last tracked events
mixpanel.get_config('debug'); // Should be false in production

// Manually trigger test event
mixpanel.track('test_event', { test: true });

// View Mixpanel configuration
mixpanel.get_config();
```

### PNCP API Testing

```bash
# Test PNCP API directly
curl -w "\nTime: %{time_total}s\n" \
  "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=2026-01-23&dataFinal=2026-01-30&uf=SC&pagina=1&tamanhoPagina=10"

# Expected: 200 OK, <5s response time
# If >10s: PNCP is slow
# If 5xx: PNCP is down
# If 429: Rate limited
```

---

**Questions?** Contact @analyst (analytics) or @devops (infrastructure)
