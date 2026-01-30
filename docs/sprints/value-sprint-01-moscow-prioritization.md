# Value Sprint 01 - MoSCoW Prioritization

**Product Owner:** @po (Sarah)
**Date:** 2026-01-29
**Sprint:** Value Sprint 01 (2 weeks / 14 days)
**Input:** Baseline Analysis Report by @analyst (Atlas)

---

## Executive Summary

Reviewed @analyst's baseline report and **CONFIRMED** MoSCoW prioritization with **ONE CRITICAL ADDITION:** Analytics tracking is now **MUST HAVE Priority #0** (foundational).

**Sprint Capacity:** ~50-55 story points (realistic for 9-agent squad over 2 weeks)

**MUST HAVE Total:** 30 story points (60% of capacity)
**SHOULD HAVE Total:** 26 story points (full sprint if aggressive)
**COULD HAVE Total:** 8 story points (stretch goals)

**Recommendation:** Lock MUST HAVE scope, be selective with SHOULD HAVE based on velocity after Week 1.

---

## Business Context

### Why This Sprint Matters

**Current State:**
- UX Score: 52/100 (precário)
- No retention features (users abandon after 2-3 uses)
- No differentiation (just a search wrapper)
- No data to inform decisions

**Desired State After Sprint:**
- User retention +50% (saved searches prevent abandonment)
- Perceived performance improved (better loading feedback)
- First impression optimized (onboarding reduces bounce rate)
- Data-driven iteration enabled (analytics foundation)

**Business Impact:**
- **Retention:** Currently losing 40-60% of users after 3 sessions
- **Competitive Advantage:** Proactive notifications differentiate us
- **Product-Market Fit:** Must prove value quickly or lose momentum

---

## MoSCoW Framework

### Priority #0: FOUNDATIONAL (MUST HAVE) 🟢

**Before ANY features, we need measurement capability.**

#### 0. Analytics Tracking Infrastructure
**Owner:** @dev + @analyst
**Effort:** 2 days (1 story point)
**Business Value:** CRITICAL (foundational for all metrics)

**Acceptance Criteria:**
- [ ] Google Analytics 4 OR Mixpanel integrated in frontend
- [ ] Track 8 critical events:
  - `search_started` (params: UFs, date_range, setor/termos)
  - `search_completed` (time_elapsed, total_raw, total_filtered)
  - `search_failed` (error_type, error_message)
  - `download_started`
  - `download_completed` (time_elapsed)
  - `download_failed` (error_type)
  - `page_load`
  - `page_exit` (session_duration)
- [ ] Backend performance metrics logged (latency, PNCP response times)
- [ ] Dashboard created for real-time monitoring (Mixpanel/GA4)
- [ ] 6 success metrics trackable:
  - Time to Download
  - Download Conversion Rate
  - Bounce Rate (First Search)
  - Search Repeat Rate
  - Time on Task (First Search)
  - NPS (collect via survey)

**Why Priority #0:**
- Without data, we can't measure impact of other features
- Baselines are estimates; need real data ASAP
- Informs SHOULD HAVE decisions after Week 1

**Technical Approach:**
- Frontend: `useAnalytics` custom hook
- Mixpanel recommended (better product analytics than GA4)
- Lightweight: <5KB bundle impact

**Risk:** None (proven technology, low complexity)

---

### MUST HAVE (Sprint-Critical) 🔴

**These DIRECTLY address the top 3 user pain points and are NON-NEGOTIABLE for sprint success.**

#### 1. Saved Searches & History
**Owner:** @dev + @architect
**Effort:** 5 days (13 story points)
**Business Value:** CRITICAL - Fixes Pain #1 (Repetitive Work Wasted)

**User Story:**
> "As a returning user, I want my recent searches saved automatically so I don't waste 60s re-configuring every time I visit."

**Acceptance Criteria:**
- [ ] Automatically save last 10 searches in localStorage (or backend DB if time permits)
- [ ] UI to access search history (dropdown or sidebar panel)
- [ ] Re-execute past search with 1 click
- [ ] Show search metadata: date executed, # of results, UFs selected
- [ ] Option to "pin" favorite searches (max 3 pinned)
- [ ] Option to clear history
- [ ] Mobile-friendly interface
- [ ] Persist across browser sessions (localStorage minimum)

**Why MUST HAVE:**
- Analyst evidence: 100% of returning users affected
- Retention impact: 40-60% churn after 3 sessions (this fixes it)
- Heuristic score: Fixes critical Heuristic #6 (Recognition vs. Recall = 1/10)
- Quick ROI: High value, moderate effort

**Technical Approach:**
- Phase 1 (MVP): localStorage (simpler, no backend changes)
- Phase 2 (future): Backend persistence + sync across devices
- Schema: `{ id, timestamp, ufs, dateRange, sector, termos, resultCount }`

**Risk:** LOW (localStorage is proven, no backend dependency)

---

#### 2. Performance Improvements + Visible Feedback
**Owner:** @dev + @ux-design-expert
**Effort:** 3 days (8 story points)
**Business Value:** HIGH - Fixes Pain #3 (Uncertainty During Search)

**User Story:**
> "As a user searching multiple states, I want to see real-time progress so I know the system isn't frozen and can estimate time remaining."

**Acceptance Criteria:**
- [ ] Replace generic "Buscando..." with detailed progress:
  - "Buscando licitações em SP... (5/27 estados)"
  - Progress bar showing % complete
  - Accurate time estimate (based on actual UF processing time)
- [ ] Loading skeleton instead of blank screen
- [ ] Optimizations:
  - Debounce filter inputs (300ms)
  - Lazy load results if >100 items (pagination or virtual scrolling)
  - Cache PNCP metadata (5min TTL) to avoid redundant calls
  - Parallel PNCP requests where possible (investigate API limits)
- [ ] Backend: Log per-UF processing time for accurate estimates
- [ ] Error recovery: If 1 UF fails, show partial results + warning

**Why MUST HAVE:**
- Analyst evidence: 100% of searches affected
- Perception matters: Users think it's slow even if backend is fast
- Heuristic score: Improves Heuristic #1 (Visibility of System Status = 6/10 → 9/10)
- Low effort, high impact

**Technical Approach:**
- Frontend: WebSocket OR SSE for real-time updates (if backend supports)
- Fallback: Polling backend for progress (every 2s)
- Backend: Emit progress events after each UF processed

**Risk:** MEDIUM (WebSocket/SSE adds complexity; fallback to polling if needed)

---

#### 3. Interactive Onboarding Flow
**Owner:** @ux-design-expert + @dev
**Effort:** 3 days (8 story points)
**Business Value:** HIGH - Reduces Bounce Rate, Improves First Impression

**User Story:**
> "As a first-time user, I want a guided tour so I understand how to use BidIQ and get value quickly, not fumble around confused."

**Acceptance Criteria:**
- [ ] 3-step wizard on first visit (localStorage flag to track)
- [ ] **Step 1:** "Welcome to DescompLicita - Find government contracts easily"
  - Explain what tool does in 1 sentence
  - Show example screenshot
  - CTA: "Let me show you how" button
- [ ] **Step 2:** Interactive demo with REAL data
  - Pre-fill search form (e.g., "Uniformes em SC/PR/RS, últimos 7 dias")
  - Trigger actual search
  - Show results + summary
  - Highlight key UI elements (download button, filters, summary)
- [ ] **Step 3:** "Now try your own search"
  - Clear demo search
  - Prompt user to select their states/sector
  - Celebrate first successful search
- [ ] Skip option ("I already know how to use this")
- [ ] Never show again (localStorage: `onboardingCompleted: true`)
- [ ] Mobile-responsive
- [ ] Optional: Tooltip overlays for each UI element (alternative to wizard)

**Why MUST HAVE:**
- Analyst evidence: Heuristic #10 (Help & Documentation = 1/10) is CRITICAL
- Bounce rate: 40% of users leave after first search (onboarding fixes this)
- Time on Task target: 120s → 60s (50% reduction)
- First impression is EVERYTHING in SaaS

**Technical Approach:**
- Use library: Intro.js OR Shepherd.js (lightweight onboarding libraries)
- Alternative: Custom modal-based wizard
- localStorage: `{ onboardingCompleted: boolean, timestamp: ISO }`

**Risk:** LOW (proven pattern, many libs available)

---

**MUST HAVE Summary:**
- **Total Effort:** 30 story points (1 + 13 + 8 + 8)
- **Duration:** ~9 days (if sequential) or ~6 days (if parallelized)
- **Sprint % Used:** 60% of capacity
- **Business Impact:** Fixes all 3 critical pain points + enables data-driven iteration

---

### SHOULD HAVE (High Value, Time Permitting) 🟡

**These add PROACTIVE VALUE and DIFFERENTIATION but are not sprint-critical.**

**Decision Point:** After Day 7, assess velocity:
- If MUST HAVE on track → Start SHOULD HAVE items
- If MUST HAVE delayed → Cut SHOULD HAVE, focus on quality

---

#### 4. Opportunity Notifications (Alerts)
**Owner:** @dev + @architect + @devops
**Effort:** 5 days (13 story points)
**Business Value:** HIGH - Fixes Pain #2 (Lack of Proactive Value)

**User Story:**
> "As a regular user, I want to be notified when new matching licitações are published so I don't miss opportunities while my competitors find them first."

**Acceptance Criteria:**
- [ ] Create "Alert" from saved search
  - UI: "Create alert from this search" button
  - Form: Name, email (pre-filled), frequency (daily/instant)
- [ ] Background job (cron or Celery):
  - Runs daily (or hourly for "instant" alerts)
  - Re-executes saved search against PNCP
  - Detects NEW results (not in previous run)
- [ ] Email notification when new results found:
  - Subject: "🔔 [N] new licitações matching [Alert Name]"
  - Body: Summary + top 3 results + link to full results
  - CTA: "View all [N] new opportunities"
- [ ] Alert management UI:
  - List all active alerts
  - Edit alert (criteria, frequency)
  - Pause/resume alert
  - Delete alert
- [ ] Limit: 3 active alerts per user (MVP constraint)
- [ ] Unsubscribe link in email (required by anti-spam laws)

**Why SHOULD HAVE:**
- Analyst evidence: Pain #2 is HIGH severity (competitive disadvantage)
- Differentiation: Makes tool PROACTIVE, not reactive
- Retention: "Set and forget" → users stay engaged
- BUT: Requires backend job + email infrastructure (higher complexity)

**Technical Approach:**
- Backend: APScheduler OR Celery for background jobs
- Email: SendGrid OR AWS SES (transactional emails)
- Database: Store alerts (user_id, search_criteria, last_run, frequency)
- Dedupe logic: Track `seen_pncp_ids` to avoid re-notifying

**Risk:** HIGH
- Email deliverability (spam filters)
- Background job reliability (need monitoring)
- PNCP API rate limits (daily polling for all alerts)
- **Mitigation:** Start with "daily" frequency only (easier than "instant")

**Fallback:** If too complex, punt to next sprint, keep MUST HAVE quality high

---

#### 5. Personal Analytics Dashboard
**Owner:** @dev + @analyst
**Effort:** 3 days (8 story points)
**Business Value:** MEDIUM-HIGH - Shows Value Generated (Retention Boost)

**User Story:**
> "As a user, I want to see statistics on my searches and downloads so I understand how much value I'm getting from DescompLicita."

**Acceptance Criteria:**
- [ ] Dashboard page (`/dashboard` route)
- [ ] Key metrics (cards):
  - Total searches performed
  - Total downloads
  - Total opportunities found (sum of all search results)
  - Estimated time saved vs. manual PNCP search (heuristic calculation)
- [ ] Chart: Searches per day/week (last 30 days)
- [ ] Top states searched (pie chart or bar chart)
- [ ] Top sectors searched
- [ ] "Your most valuable search" (highest # of results)
- [ ] Export analytics as CSV

**Why SHOULD HAVE:**
- Shows tangible value ("You found 150 opportunities in 30 days!")
- Gamification potential (badges, streaks - future)
- Retention: Users who see value stats are more likely to return
- BUT: Requires analytics data (depends on Priority #0 being done FIRST)

**Technical Approach:**
- Frontend: Chart.js OR Recharts (React charting library)
- Data source: Analytics events (from Priority #0)
- Aggregation: Frontend (if data volume low) OR backend API (if high)

**Risk:** LOW (frontend-heavy, minimal backend)

**Dependency:** Priority #0 (Analytics Tracking) must be complete

---

#### 6. Multi-Format Export (CSV, PDF)
**Owner:** @dev
**Effort:** 2 days (5 story points)
**Business Value:** MEDIUM - Flexibility for Different Workflows

**User Story:**
> "As a user, I want to download results in CSV or PDF format (not just Excel) so I can integrate with my existing workflows."

**Acceptance Criteria:**
- [ ] Export dropdown (instead of single "Download Excel" button)
  - Option 1: Excel (.xlsx) - current default
  - Option 2: CSV (.csv) - raw data, all columns
  - Option 3: PDF (.pdf) - formatted report with LLM summary
- [ ] CSV export:
  - All columns from Excel
  - UTF-8 encoding (handles Portuguese characters)
  - Comma-separated (not semicolon)
- [ ] PDF export:
  - Header: DescompLicita branding
  - Section 1: LLM executive summary
  - Section 2: Table of results (top 50 if >50 results)
  - Footer: "Generated on [date]"
  - Library: ReportLab (Python) OR pdfmake (Node.js)
- [ ] Same download ID system (10min cache TTL)

**Why SHOULD HAVE:**
- User flexibility (some prefer CSV for data analysis, PDF for reports)
- Low effort (backend logic exists, just different formatters)
- NOT critical (Excel works for 90% of users)

**Technical Approach:**
- Backend:
  - CSV: Built-in `csv` module (Python)
  - PDF: ReportLab OR WeasyPrint (HTML → PDF)
- Reuse existing `licitacoes_filtradas` data

**Risk:** LOW (well-supported libraries)

---

**SHOULD HAVE Summary:**
- **Total Effort:** 26 story points (13 + 8 + 5)
- **Duration:** ~8 days (if sequential)
- **Sprint % Used:** 52% of capacity (on top of MUST HAVE = 112% total → OVERCOMMIT)
- **Decision Rule:** Pick 1-2 based on Week 1 velocity

**Recommended SHOULD HAVE Selection (if forced to choose):**
1. **Opportunity Notifications** (highest differentiation, but riskiest)
2. **Personal Analytics Dashboard** (lower risk, good retention value)
3. Multi-Format Export (lowest priority, defer to next sprint)

---

### COULD HAVE (Nice to Have, Likely Deferred) 🟢

**These are incremental improvements that DON'T address critical pain points.**

---

#### 7. Persistent Filters
**Owner:** @dev
**Effort:** 1 day (3 story points)
**Business Value:** LOW - Convenience, Not Critical

**User Story:**
> "As a user, I want my last filter selections (UFs, date range, sector) remembered so I don't have to re-select them every visit."

**Acceptance Criteria:**
- [ ] Save last search parameters to localStorage:
  - `lastSelectedUFs`
  - `lastDateRange`
  - `lastSector`
- [ ] Pre-fill form on page load
- [ ] Checkbox: "Remember my selections" (opt-in)
- [ ] Clear button to reset to defaults

**Why COULD HAVE:**
- Overlaps with MUST HAVE #1 (Saved Searches) - if that exists, persistent filters are redundant
- Low impact compared to other features
- Easy to add later

**Risk:** NONE (trivial)

**Recommendation:** DEFER to next sprint or combine with Saved Searches

---

**COULD HAVE Summary:**
- **Total Effort:** 3 story points
- **Sprint % Used:** 6% of capacity
- **Recommendation:** Skip for this sprint, revisit after MUST HAVE + SHOULD HAVE delivered

---

## Final MoSCoW Breakdown

| Priority | Features | Total Points | % of Sprint | Decision |
|----------|----------|--------------|-------------|----------|
| **Priority #0 (Foundation)** | Analytics Tracking | 1 | 2% | ✅ LOCK |
| **MUST HAVE** | Saved Searches, Performance, Onboarding | 29 | 58% | ✅ LOCK |
| **SHOULD HAVE** | Notifications, Dashboard, Multi-Export | 26 | 52% | ⚠️ PICK 1-2 |
| **COULD HAVE** | Persistent Filters | 3 | 6% | ❌ DEFER |
| **TOTAL (if all)** | All | 59 | 118% | ⚠️ OVERCOMMIT |

---

## Scope Lock Decision (Product Owner)

### LOCKED SCOPE (Non-Negotiable)

**Week 1 Focus:**
1. ✅ Analytics Tracking (Day 1-2) - @dev + @analyst
2. ✅ Saved Searches & History (Day 1-7) - @dev + @architect
3. ✅ Performance + Visible Feedback (Day 3-7) - @dev + @ux-design-expert
4. ✅ Interactive Onboarding (Day 5-7) - @ux-design-expert + @dev

**Total:** 30 story points (realistic for Week 1 with parallelization)

---

### FLEXIBLE SCOPE (Velocity-Dependent)

**Week 2 Decision (Day 7 Checkpoint):**

**IF Week 1 velocity ≥ 90% (27+ points completed):**
- ✅ Add **Personal Analytics Dashboard** (lower risk, 8 points)
- ✅ Add **Multi-Format Export** (lowest risk, 5 points)
- **Total Week 2:** 13 points (safe buffer)

**IF Week 1 velocity 70-89% (21-26 points completed):**
- ✅ Add **Personal Analytics Dashboard** ONLY (8 points)
- ❌ Defer Notifications (too risky for Week 2)

**IF Week 1 velocity <70% (<21 points completed):**
- ❌ Defer ALL SHOULD HAVE
- ✅ Focus on quality, testing, and polish of MUST HAVE

---

### DEFERRED SCOPE (Next Sprint)

**Guaranteed Deferral:**
- ❌ Opportunity Notifications (13 points, too complex for this sprint)
  - **Reason:** Requires backend job + email + monitoring (high risk)
  - **Future Sprint:** Value Sprint 02 or Q2 Roadmap
- ❌ Persistent Filters (3 points, redundant with Saved Searches)
  - **Reason:** Low impact, overlaps with delivered features
  - **Future Sprint:** Polish sprint or bundle with other small enhancements

---

## Success Criteria (Definition of Done)

### Sprint Success = MUST HAVE Delivered

**Minimum Viable Success:**
1. ✅ Analytics tracking live and collecting data
2. ✅ Users can save and replay searches (10x history)
3. ✅ Loading feedback is detailed and accurate
4. ✅ New users experience guided onboarding

**Metrics Targets (2 weeks post-deploy):**
- Time to Download: -30% (from baseline)
- Bounce Rate: -25%
- Search Repeat Rate: +50%
- NPS: Collect baseline (target +15 points vs. baseline)

**Quality Gates:**
- All features pass QA (@qa sign-off)
- Test coverage ≥70% (backend), ≥60% (frontend)
- No P0/P1 bugs in production
- Performance: Page load <2s, search <120s (99th percentile)

---

## Risks & Mitigation

### Risk #1: Overcommitment (118% of capacity)

**Likelihood:** HIGH
**Impact:** HIGH (quality suffers, burnout, missed deadline)

**Mitigation:**
- ✅ LOCK only MUST HAVE scope (60% capacity)
- ✅ SHOULD HAVE is explicitly conditional (Day 7 checkpoint)
- ✅ @sm tracks velocity daily, alerts @po if <90%

**Contingency:**
- If Week 1 behind → Cut Onboarding to "minimal" (tooltip-only, defer wizard)
- If Week 2 behind → Cut all SHOULD HAVE, deliver MUST HAVE with high quality

---

### Risk #2: Analytics Delay Blocks Dashboard

**Likelihood:** LOW
**Impact:** MEDIUM (can't deliver Dashboard without data)

**Mitigation:**
- ✅ Analytics is Priority #0 (Day 1-2, before anything else)
- ✅ @dev + @analyst pair on this (knowledge sharing)
- ✅ If delayed → Dashboard automatically deferred (dependency clear)

**Contingency:**
- Mock data for Dashboard UI (deliver frontend, connect data later)

---

### Risk #3: User Validation Invalidates Priorities

**Likelihood:** MEDIUM
**Impact:** MEDIUM (wasted effort on wrong features)

**Mitigation:**
- ✅ Heuristic analysis is strong (52/100 score, clear critical issues)
- ✅ Optional user interviews Day 2-3 (validate top pains)
- ✅ Analytics data will confirm/deny after 3 days

**Contingency:**
- If interviews reveal different pains → @po adjusts SHOULD HAVE priorities
- MUST HAVE scope stays locked (based on code analysis, not assumptions)

---

## User Interviews Decision (Optional)

### Recommendation: SKIP for this sprint

**Reasoning:**
1. Heuristic analysis is comprehensive (code-based, objective)
2. Top 3 pains are evident (no persistence, no proactive value, poor feedback)
3. User interviews take 3-4 hours (diverts focus from implementation)
4. Analytics will provide BETTER data after Day 3 (actual usage patterns)

**Alternative:**
- Collect qualitative feedback AFTER sprint (post-deploy survey)
- Ask: "What feature had the biggest impact?" to validate priorities

**If stakeholder insists:**
- Limit to 3 interviews (not 5-7)
- Focus script: Validate top 3 pains ONLY (don't explore new pains)
- Owner: @pm (not @analyst) to free up analyst for dashboard work

---

## Communication Plan

### Stakeholder Updates

**Daily (Internal):**
- @sm runs standup (9am, 15min)
- Burn-down chart updated
- Blockers escalated to @po immediately

**Weekly (External):**
- End of Week 1 (Day 7): Sprint review with stakeholders
  - Demo: Saved Searches, Performance, Onboarding (if done)
  - Decision: Go/No-Go on SHOULD HAVE scope
- End of Week 2 (Day 14): Final sprint review
  - Demo: All delivered features
  - Metrics: Early results (if 3+ days of data)
  - Retrospective: What worked, what to improve

---

## Next Steps (Handoff)

### Immediate Actions (Day 1):

1. **@sm:** Kickoff sprint planning meeting
   - Present this MoSCoW doc
   - Create stories for MUST HAVE items
   - Assign owners and define DoD

2. **@dev:** Start Analytics Tracking (Priority #0)
   - Choose tool: Mixpanel (recommended) vs. GA4
   - Integrate in frontend
   - Test 8 events

3. **@architect:** Review Saved Searches architecture
   - localStorage vs. backend DB decision
   - Schema design
   - API contracts (if backend needed)

4. **@ux-design-expert:** Start Onboarding wireframes
   - 3-step wizard flow
   - Mockups for review (by EOD Day 1)

---

### Day 2-3 Actions:

5. **@analyst:** Set up analytics dashboard
   - Mixpanel board OR GA4 custom reports
   - Track 6 success metrics

6. **@pm:** Validate technical feasibility
   - Review architecture with @architect
   - Identify risks/blockers
   - Allocate dev work (who does what)

7. **@qa:** Prepare test plan
   - Test cases for each MUST HAVE feature
   - Automation strategy (where possible)
   - Staging environment setup

---

### Day 7 Checkpoint:

8. **@sm + @po:** Velocity review
   - Actual vs. planned story points
   - Burn-down trend
   - **GO/NO-GO decision on SHOULD HAVE scope**

9. **@devops:** Prepare deployment pipeline
   - CI/CD for staging
   - Rollback strategy
   - Monitoring alerts

---

## Approval & Sign-Off

**Product Owner Decision:** ✅ APPROVED

**Scope:**
- ✅ LOCK: Priority #0 + MUST HAVE (30 points)
- ⚠️ CONDITIONAL: SHOULD HAVE (pick 1-2 based on Day 7 velocity)
- ❌ DEFER: COULD HAVE (next sprint)

**Success Criteria:**
- Deliver MUST HAVE with HIGH QUALITY (>70% coverage, no P0 bugs)
- Metrics tracked from Day 1 (analytics live)
- User retention improved (validate post-deploy)

**Next Agent:** @sm (Scrum Master) for Sprint Planning

---

**Document Status:** ✅ FINAL
**Signed:** @po (Sarah)
**Date:** 2026-01-29
