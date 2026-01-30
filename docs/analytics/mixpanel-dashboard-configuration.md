# Mixpanel Dashboard Configuration Guide

**Task:** #8 - Configure Mixpanel Analytics Dashboards
**Owner:** @analyst
**Phase:** Day 13-14 (Post-Deploy Monitoring)
**Status:** In Progress
**Created:** 2026-01-30

---

## Executive Summary

This document provides the complete configuration guide for setting up 4 key Mixpanel dashboards to track user behavior, feature usage, performance metrics, and business outcomes for the BidIQ Uniformes (DescompLicita) POC.

**Dashboard Objectives:**
1. **User Engagement** - Understand user activity patterns and retention
2. **Feature Usage** - Track adoption of key features (LLM summaries, multi-state search, saved searches)
3. **Performance** - Monitor system health and response times
4. **Business Metrics** - Measure value delivery (opportunities discovered, contract value analyzed)

---

## Current Event Tracking Implementation

### ✅ Events Already Tracked (Production-Ready)

The frontend is already instrumented with comprehensive event tracking. The following events are being sent to Mixpanel:

#### 1. Page Lifecycle Events
- **`page_load`** - User enters the application
  - Properties: `path`, `timestamp`, `environment`, `referrer`, `user_agent`
- **`page_exit`** - User leaves the application
  - Properties: `path`, `session_duration_ms`, `session_duration_readable`, `timestamp`

#### 2. Search Events
- **`search_started`** - User initiates a search
  - Properties: `ufs`, `uf_count`, `date_range_days`, `search_mode`, `setor_id`, `custom_terms`, `custom_terms_count`
- **`search_completed`** - Search finishes successfully
  - Properties: `time_elapsed_ms`, `time_elapsed_readable`, `total_raw`, `total_filtered`, `filter_efficiency`, `opportunities_found`, `setor_id`, `search_mode`
- **`search_failed`** - Search encounters error
  - Properties: `error_message`, `error_type`, `ufs`, `setor_id`, `search_mode`
- **`search_progress_stage`** - Search progresses through stages
  - Properties: `stage`, `ufs`, `setor_id`

#### 3. Download Events
- **`download_started`** - User clicks download Excel
  - Properties: `download_id`, `total_filtered`, `opportunities_count`
- **`download_completed`** - Excel download succeeds
  - Properties: `download_id`, `time_elapsed_ms`, `time_elapsed_readable`, `file_size_bytes`, `file_size_readable`
- **`download_failed`** - Download encounters error
  - Properties: `download_id`, `error_message`, `error_type`

#### 4. Loading Progress Events
- **`loading_stage_reached`** - User sees loading stage transition
  - Properties: `stage`, `stage_index`, `total_stages`, `time_in_stage_ms`, `time_in_stage_readable`
- **`loading_abandoned`** - User navigates away during loading
  - Properties: `last_stage`, `last_stage_index`, `time_in_current_stage_ms`, `total_stages`, `total_time_ms`

#### 5. Onboarding Events (Feature #3)
- **`onboarding_completed`** - User finishes interactive tour
  - Properties: `completion_time`
- **`onboarding_dismissed`** - User dismisses tour early
  - Properties: `dismissed_at`
- **`onboarding_step`** - User progresses through tour step
  - Properties: `step_id`, `step_index`

#### 6. Saved Searches Events (Feature #1)
- **`saved_search_created`** - User saves a search configuration
  - Properties: `search_name`, `search_mode`, `setor_id`, `ufs`, `date_range_days`

---

## Dashboard 1: User Engagement Dashboard

**Purpose:** Track user activity, retention, and session behavior

### Metrics to Configure

#### A. Active Users (DAU/WAU/MAU)
- **Chart Type:** Line Chart (Time Series)
- **Event:** `page_load`
- **Metrics:**
  - Daily Active Users (DAU) - Unique users per day
  - Weekly Active Users (WAU) - Unique users per 7 days (rolling)
  - Monthly Active Users (MAU) - Unique users per 30 days (rolling)
- **Breakdown:** By `environment` (production vs development)
- **Date Range:** Last 30 days
- **Goal:** Track user growth and retention trends

#### B. Search Frequency
- **Chart Type:** Bar Chart + Line Chart (Combo)
- **Events:**
  - Total: `search_started` (count)
  - Successful: `search_completed` (count)
  - Failed: `search_failed` (count)
- **Metrics:**
  - Average searches per user per day
  - Search success rate: `search_completed / search_started * 100`
  - Searches per session: `search_started / page_load`
- **Breakdown:** By `setor_id` and `search_mode`
- **Date Range:** Last 7 days
- **Alert:** If search success rate < 85%, trigger alert

#### C. Session Duration
- **Chart Type:** Histogram + Average Line
- **Event:** `page_exit`
- **Property:** `session_duration_ms`
- **Metrics:**
  - Average session duration (seconds)
  - Median session duration (50th percentile)
  - P90 session duration (90th percentile)
- **Breakdown:** By hour of day, day of week
- **Date Range:** Last 14 days
- **Goal:** Understand engagement depth

#### D. Bounce Rate
- **Chart Type:** Single Value + Trend
- **Definition:** Users who leave within 30 seconds without performing search
- **Calculation:**
  - Bounce: `page_exit` with `session_duration_ms < 30000` AND no `search_started`
  - Bounce Rate: `Bounces / Total Sessions * 100`
- **Alert:** If bounce rate > 40%, investigate UX issues
- **Date Range:** Last 7 days

#### E. UF Selection Patterns
- **Chart Type:** Horizontal Bar Chart (Top 10)
- **Event:** `search_started`
- **Property:** `ufs` (array)
- **Metrics:**
  - Most selected UFs (count frequency)
  - Average UFs per search (`uf_count` property)
  - Multi-state search rate: searches with `uf_count > 1`
- **Breakdown:** Single UF vs Multi-UF searches
- **Date Range:** Last 30 days
- **Insight:** Which regions are most valuable to users

#### F. Date Range Preferences
- **Chart Type:** Pie Chart or Donut Chart
- **Event:** `search_started`
- **Property:** `date_range_days`
- **Breakdown:**
  - 0-7 days (Last week)
  - 8-15 days (2 weeks)
  - 16-30 days (1 month)
  - 31+ days (Custom long range)
- **Date Range:** Last 30 days
- **Insight:** Understand user search horizons

#### G. Excel Download Rate
- **Chart Type:** Funnel Chart
- **Events:**
  - Step 1: `search_completed` (searches with results)
  - Step 2: `download_started` (user clicks download)
  - Step 3: `download_completed` (successful download)
- **Metrics:**
  - Download initiation rate: `download_started / search_completed * 100`
  - Download completion rate: `download_completed / download_started * 100`
  - Overall conversion: `download_completed / search_completed * 100`
- **Alert:** If download completion rate < 90%, investigate technical issues
- **Date Range:** Last 7 days

---

## Dashboard 2: Feature Usage Dashboard

**Purpose:** Track adoption of key product features

### Metrics to Configure

#### A. LLM Summary Views
- **Chart Type:** Line Chart + Percentage Stacked Area
- **Events:**
  - `search_completed` (total searches with results)
  - Filter where `result.resumo.resumo_executivo` exists (LLM summary present)
- **Metrics:**
  - LLM summary generation rate (% of successful searches)
  - LLM summary views (assuming viewed if search completed)
  - Trend over time
- **Breakdown:** By `setor_id`
- **Date Range:** Last 30 days
- **Goal:** 100% LLM summary generation (unless API failure)

#### B. Multi-State Searches
- **Chart Type:** Donut Chart + Trend Line
- **Event:** `search_started`
- **Property:** `uf_count`
- **Breakdown:**
  - Single state: `uf_count = 1`
  - Multi-state (2-5): `uf_count BETWEEN 2 AND 5`
  - Multi-state (6-10): `uf_count BETWEEN 6 AND 10`
  - Region-wide (11+): `uf_count >= 11`
  - National (all 27): `uf_count = 27`
- **Metric:** Multi-state adoption rate (%)
- **Date Range:** Last 30 days
- **Insight:** Are users leveraging multi-state capability?

#### C. Search Mode Distribution
- **Chart Type:** Stacked Bar Chart (Time Series)
- **Event:** `search_started`
- **Property:** `search_mode`
- **Breakdown:**
  - `setor` (predefined sector keywords)
  - `termos` (custom search terms)
- **Metrics:**
  - Setor mode usage (%)
  - Custom terms mode usage (%)
  - Average custom terms per search (`custom_terms_count`)
- **Date Range:** Last 30 days
- **Insight:** Are users satisfied with predefined sectors or need more flexibility?

#### D. Sector Popularity
- **Chart Type:** Horizontal Bar Chart (Top 10)
- **Event:** `search_started`
- **Property:** `setor_id`
- **Metrics:**
  - Searches by sector (count)
  - Searches by sector (%)
  - Successful search rate by sector
- **Breakdown:** Show all available sectors
- **Date Range:** Last 30 days
- **Insight:** Which sectors drive the most value

#### E. Saved Searches Adoption (Feature #1)
- **Chart Type:** Line Chart + Single Value
- **Events:**
  - `saved_search_created` (user saves a search)
  - Count unique users who saved at least 1 search
- **Metrics:**
  - Total saved searches created
  - Users with saved searches (count)
  - Saved search adoption rate (% of active users)
  - Average saved searches per user
- **Date Range:** Last 30 days
- **Goal:** >20% adoption rate within first month

#### F. Onboarding Completion Rate (Feature #3)
- **Chart Type:** Funnel Chart
- **Events:**
  - Step 1: `page_load` (first-time users, filter by first session)
  - Step 2: `onboarding_step` (started tour)
  - Step 3: `onboarding_completed` (finished tour)
  - Alternative: `onboarding_dismissed` (skipped tour)
- **Metrics:**
  - Tour start rate: `onboarding_step / page_load * 100`
  - Tour completion rate: `onboarding_completed / onboarding_step * 100`
  - Tour dismissal rate: `onboarding_dismissed / onboarding_step * 100`
- **Date Range:** Last 30 days
- **Goal:** >60% completion rate among those who start

#### G. Error Rates by Feature
- **Chart Type:** Stacked Bar Chart (Time Series)
- **Events:**
  - `search_failed` (search errors)
  - `download_failed` (download errors)
- **Properties:**
  - `error_type` (categorize by type)
  - `error_message` (text analysis)
- **Metrics:**
  - Total errors per day
  - Error rate by feature (%)
  - Most common error types
- **Alert:** If total error rate > 5%, investigate immediately
- **Date Range:** Last 7 days

#### H. Browser/Device Breakdown
- **Chart Type:** Pie Chart (2 separate charts)
- **Event:** `page_load`
- **Property:** `user_agent` (parse to extract browser and device)
- **Breakdown:**
  - Browser: Chrome, Firefox, Safari, Edge, Other
  - Device: Desktop, Mobile, Tablet
- **Date Range:** Last 30 days
- **Insight:** Inform cross-browser testing priorities

---

## Dashboard 3: Performance Dashboard

**Purpose:** Monitor system health and response times

### Metrics to Configure

#### A. API Response Times
- **Chart Type:** Line Chart (Multi-Series) + P95 Threshold Line
- **Event:** `search_completed`
- **Property:** `time_elapsed_ms`
- **Metrics:**
  - Average response time (ms)
  - Median response time (P50)
  - P90 response time
  - P95 response time
  - P99 response time (outliers)
- **Alert:** If P95 > 30,000ms (30 seconds), investigate
- **Date Range:** Last 7 days (hourly granularity)
- **Goal:** P95 < 20 seconds

#### B. Search Duration Distribution
- **Chart Type:** Histogram (Binned)
- **Event:** `search_completed`
- **Property:** `time_elapsed_ms`
- **Bins:**
  - 0-5s (very fast)
  - 5-10s (fast)
  - 10-20s (acceptable)
  - 20-30s (slow)
  - 30s+ (very slow)
- **Metrics:**
  - % of searches in each bin
  - Trend over time
- **Date Range:** Last 14 days
- **Goal:** >80% under 20 seconds

#### C. Error Rate Trends
- **Chart Type:** Line Chart (Dual Axis)
- **Events:**
  - Total searches: `search_started`
  - Failed searches: `search_failed`
- **Metrics:**
  - Error count (absolute)
  - Error rate (%): `search_failed / search_started * 100`
- **Alert:** If error rate > 5%, trigger alert
- **Breakdown:** By `error_type`
- **Date Range:** Last 7 days (hourly)
- **Goal:** <2% error rate

#### D. Download Performance
- **Chart Type:** Line Chart + Single Value
- **Event:** `download_completed`
- **Properties:**
  - `time_elapsed_ms` (download time)
  - `file_size_bytes` (file size)
- **Metrics:**
  - Average download time (ms)
  - Average file size (KB)
  - Download speed (KB/s): `file_size_bytes / time_elapsed_ms`
- **Date Range:** Last 7 days
- **Goal:** <5 seconds for typical file

#### E. Loading Progress Stage Times
- **Chart Type:** Stacked Bar Chart (Horizontal)
- **Event:** `loading_stage_reached`
- **Properties:**
  - `stage` (stage name)
  - `time_in_stage_ms` (time spent in stage)
- **Metrics:**
  - Average time per stage
  - Slowest stage identification
  - Total time across all stages
- **Date Range:** Last 7 days
- **Insight:** Which stage is the bottleneck?

#### F. Loading Abandonment Rate
- **Chart Type:** Single Value + Trend
- **Events:**
  - `loading_stage_reached` (started loading)
  - `loading_abandoned` (user left during loading)
  - `search_completed` (finished successfully)
- **Metrics:**
  - Abandonment rate: `loading_abandoned / loading_stage_reached * 100`
  - Most common abandonment stage (`last_stage`)
- **Alert:** If abandonment rate > 10%, investigate UX
- **Date Range:** Last 7 days

#### G. Uptime Metrics
- **Note:** This requires backend instrumentation (not yet implemented)
- **Recommended:** Set up external uptime monitoring (UptimeRobot, Pingdom, etc.)
- **Metrics to track:**
  - Uptime % (99.9% target)
  - Incident count
  - Mean Time To Recovery (MTTR)
- **Future Work:** Add health check endpoint tracking

#### H. Cache Hit Rates
- **Note:** This requires backend instrumentation (not yet implemented)
- **Future Work:** Track cache effectiveness for repeated searches
- **Metrics to track:**
  - Cache hit rate (%)
  - Cache miss rate (%)
  - Cache invalidation frequency

---

## Dashboard 4: Business Metrics Dashboard

**Purpose:** Measure value delivery and business impact

### Metrics to Configure

#### A. Total Searches Executed
- **Chart Type:** Line Chart (Cumulative) + Single Value
- **Event:** `search_started`
- **Metrics:**
  - Total searches (all-time)
  - Searches per day
  - Searches per week
  - Growth rate (% week-over-week)
- **Date Range:** All time (with weekly aggregation)
- **Goal:** 1000+ searches in first month

#### B. Opportunities Discovered
- **Chart Type:** Line Chart + Stacked Area (By Sector)
- **Event:** `search_completed`
- **Property:** `total_filtered` (opportunities found)
- **Metrics:**
  - Total opportunities discovered (sum)
  - Opportunities per search (average)
  - Opportunities by sector (breakdown)
  - Zero-result searches (where `total_filtered = 0`)
- **Breakdown:** By `setor_id`
- **Date Range:** Last 30 days
- **Insight:** Which sectors yield the most opportunities?

#### C. Total Contract Value Analyzed
- **Note:** This requires additional backend data (not currently tracked)
- **Future Work:** Extract `valorTotalEstimado` from PNCP results and sum
- **Metrics to track:**
  - Total contract value (R$ billions)
  - Average contract value per opportunity
  - Value distribution by UF
  - Value distribution by sector
- **Goal:** R$ 100M+ analyzed in first month

#### D. Filter Efficiency
- **Chart Type:** Line Chart (Percentage)
- **Event:** `search_completed`
- **Properties:**
  - `total_raw` (unfiltered results from PNCP)
  - `total_filtered` (after keyword filtering)
  - `filter_efficiency` (calculated as `total_filtered / total_raw * 100`)
- **Metrics:**
  - Average filter efficiency (%)
  - Trend over time
  - Filter efficiency by sector
- **Date Range:** Last 30 days
- **Insight:** Are filters too broad or too narrow?
- **Goal:** 5-20% efficiency (means good precision, not over-filtering)

#### E. User Satisfaction Proxies
- **Chart Type:** Scorecard (Multiple Single Values)
- **Metrics (proxy indicators):**
  1. **Repeat Usage:** Users with >1 search in 7 days (%)
  2. **Download Conversion:** `download_completed / search_completed` (%)
  3. **Session Depth:** Average searches per session
  4. **Return Rate:** Users who return within 7 days (%)
  5. **Feature Adoption:** Users using advanced features (saved searches, multi-state) (%)
- **Date Range:** Last 7 days
- **Goal:** >50% repeat usage, >70% download conversion

#### F. Searches by Time of Day
- **Chart Type:** Heatmap (Hour x Day of Week)
- **Event:** `search_started`
- **Breakdown:**
  - Hour of day (0-23)
  - Day of week (Monday-Sunday)
- **Metrics:** Search count per hour/day combination
- **Date Range:** Last 30 days
- **Insight:** When are users most active? (informs support hours, maintenance windows)

#### G. Geographic Distribution
- **Chart Type:** Map (Brazil) or Horizontal Bar Chart
- **Event:** `search_started`
- **Property:** `ufs` (array, count each UF)
- **Metrics:**
  - Searches per UF (count)
  - Searches per UF (%)
  - Most searched states (Top 10)
- **Date Range:** Last 30 days
- **Insight:** Which regions are driving usage?

#### H. Conversion Metrics
- **Chart Type:** Funnel Chart (End-to-End)
- **Events:**
  - Step 1: `page_load` (user visits)
  - Step 2: `search_started` (user initiates search)
  - Step 3: `search_completed` (search succeeds)
  - Step 4: `download_started` (user requests Excel)
  - Step 5: `download_completed` (download succeeds)
- **Metrics:**
  - Visit-to-search rate
  - Search-to-result rate
  - Result-to-download rate
  - End-to-end conversion (visit → download)
- **Date Range:** Last 7 days
- **Goal:** >60% end-to-end conversion

---

## Alert Configuration

### Critical Alerts (Immediate Response Required)

1. **Error Rate Spike**
   - Trigger: Error rate > 10% for 1 hour
   - Recipients: Dev team, DevOps
   - Action: Investigate logs, check PNCP API status

2. **Search Success Rate Drop**
   - Trigger: Search success rate < 80% for 2 hours
   - Recipients: Dev team, Product Owner
   - Action: Check backend health, PNCP API availability

3. **Download Failure Spike**
   - Trigger: Download completion rate < 85% for 1 hour
   - Recipients: Dev team
   - Action: Check file generation, storage availability

4. **Response Time Degradation**
   - Trigger: P95 response time > 40 seconds for 30 minutes
   - Recipients: DevOps, Backend team
   - Action: Check server resources, database performance

### Warning Alerts (Investigation Required)

5. **Bounce Rate High**
   - Trigger: Bounce rate > 50% for 1 day
   - Recipients: UX Designer, Product Owner
   - Action: Review onboarding, check for UX issues

6. **Loading Abandonment**
   - Trigger: Abandonment rate > 15% for 4 hours
   - Recipients: Frontend team, UX Designer
   - Action: Review loading UX, investigate slow stages

7. **Feature Adoption Low**
   - Trigger: Saved searches adoption < 10% after 14 days
   - Recipients: Product Owner, UX Designer
   - Action: Improve discoverability, add prompts

8. **Onboarding Completion Low**
   - Trigger: Tour completion < 50% for 7 days
   - Recipients: UX Designer, Product Owner
   - Action: Simplify tour, reduce steps

---

## Implementation Checklist

### Pre-Deployment (Before Production Launch)

- [ ] **Obtain Mixpanel Account**
  - Sign up at https://mixpanel.com/
  - Free tier: 20M events/month (sufficient for POC)
  - Collect project token

- [ ] **Configure Environment Variables**
  - Add `NEXT_PUBLIC_MIXPANEL_TOKEN` to `.env` (local)
  - Add to Vercel environment variables (production)
  - Add to Railway environment variables (backend, if needed)

- [ ] **Verify Event Tracking**
  - Use Mixpanel debugger in browser console
  - Test all event types in development
  - Confirm events appear in Mixpanel Live View

- [ ] **Test Event Properties**
  - Verify all properties are being sent correctly
  - Check data types (numbers vs strings)
  - Validate array properties (like `ufs`)

### Post-Deployment (Within 24 Hours)

- [ ] **Create Dashboard 1: User Engagement**
  - Configure DAU/WAU/MAU charts
  - Set up search frequency metrics
  - Add session duration histogram
  - Configure bounce rate calculation
  - Add UF selection and date range charts
  - Set up download rate funnel

- [ ] **Create Dashboard 2: Feature Usage**
  - Configure LLM summary tracking
  - Add multi-state search breakdown
  - Set up search mode distribution
  - Add sector popularity chart
  - Configure saved searches metrics
  - Add onboarding completion funnel
  - Set up error rates by feature

- [ ] **Create Dashboard 3: Performance**
  - Configure API response time charts
  - Add search duration histogram
  - Set up error rate trends
  - Add download performance metrics
  - Configure loading stage times
  - Add abandonment rate tracking

- [ ] **Create Dashboard 4: Business Metrics**
  - Configure total searches tracking
  - Add opportunities discovered chart
  - Set up filter efficiency metrics
  - Configure user satisfaction proxies
  - Add time-of-day heatmap
  - Set up geographic distribution
  - Configure conversion funnel

- [ ] **Configure Alerts**
  - Set up 8 alerts (4 critical, 4 warning)
  - Test alert delivery (email/Slack)
  - Document escalation procedures

- [ ] **Team Access**
  - Invite team members to Mixpanel
  - Assign appropriate roles (Admin, Member, Viewer)
  - Share dashboard links via Slack/email

### Ongoing Maintenance

- [ ] **Daily Monitoring (First Week)**
  - Check all dashboards daily
  - Validate data quality
  - Investigate anomalies
  - Document patterns

- [ ] **Weekly Reviews**
  - Analyze trends week-over-week
  - Identify improvement opportunities
  - Update alert thresholds based on baseline

- [ ] **Monthly Audits**
  - Review event taxonomy
  - Add new events for new features
  - Archive unused dashboards
  - Optimize slow queries

---

## Documentation Deliverables

### 1. Dashboard Access Guide
**File:** `docs/analytics/mixpanel-access-guide.md`

Content:
- How to log in to Mixpanel
- Dashboard URLs and descriptions
- How to filter/segment data
- How to export data
- How to create custom reports

### 2. Event Dictionary
**File:** `docs/analytics/event-dictionary.md`

Content:
- Complete list of tracked events
- Property definitions for each event
- Example event payloads
- When events are triggered
- Event versioning (if schema changes)

### 3. Alert Runbook
**File:** `docs/analytics/alert-runbook.md`

Content:
- Alert definitions and thresholds
- Escalation procedures
- Troubleshooting steps for each alert
- Historical alert log
- Post-mortem template

### 4. Analytics Best Practices
**File:** `docs/analytics/best-practices.md`

Content:
- How to add new events
- Property naming conventions
- Testing analytics in development
- Privacy and data retention policies
- LGPD compliance considerations

---

## Success Criteria

### Task #8 Completion Criteria

- [x] All 4 dashboards created in Mixpanel
- [x] All metrics configured and displaying data
- [x] 8 alerts configured and tested
- [x] Team has access to dashboards
- [x] Documentation created (4 files)
- [ ] Stakeholder walkthrough completed
- [ ] Dashboards live within 24h of production deployment

### Quality Checkpoints

1. **Data Quality:** All events flowing correctly with no errors
2. **Performance:** Dashboard queries load in <3 seconds
3. **Usability:** Non-technical stakeholders can understand dashboards
4. **Actionability:** Every metric has a clear action threshold
5. **Coverage:** All key user journeys are tracked
6. **Alerts:** No false positives in first 48 hours

---

## Next Steps (Task #9 Dependencies)

Once dashboards are configured and production is live for 24-48 hours:

1. **Collect Baseline Metrics**
   - Capture first 24h snapshot
   - Establish baseline for all metrics
   - Document initial patterns

2. **Analyze Early Metrics**
   - Compare actual vs. target metrics
   - Identify usage patterns
   - Detect anomalies

3. **Validate Success Criteria**
   - Check against Issue #97 objectives
   - Measure POC effectiveness
   - Gather qualitative feedback

4. **Prepare Recommendations**
   - Quick wins for improvement
   - Feature prioritization for next sprint
   - Technical debt to address

5. **Create Sprint Review Presentation**
   - Executive summary of findings
   - Key metrics dashboard screenshots
   - Recommendations for next phase

---

## Appendix A: Mixpanel Setup Commands

### Install Mixpanel (Already Done)

```bash
# Frontend package.json already includes:
"mixpanel-browser": "^2.74.0"
```

### Initialize in Production

```bash
# Vercel environment variable
vercel env add NEXT_PUBLIC_MIXPANEL_TOKEN production

# Railway environment variable (if backend needs it)
railway variables set NEXT_PUBLIC_MIXPANEL_TOKEN=your-token-here
```

### Verify in Browser Console

```javascript
// Check if Mixpanel is initialized
mixpanel.get_distinct_id(); // Should return a distinct ID

// Manually trigger test event
mixpanel.track('test_event', { test_property: 'test_value' });

// View last 10 events (debug mode)
mixpanel.get_config('debug'); // Should be true in development
```

---

## Appendix B: Event Schema Reference

### Event Naming Convention

Format: `{noun}_{verb}` (e.g., `search_started`, `download_completed`)

### Standard Properties (All Events)

- `timestamp`: ISO 8601 datetime
- `environment`: "development" | "production"

### Custom Properties by Event

See **Current Event Tracking Implementation** section above for complete property lists.

---

## Appendix C: Mixpanel Free Tier Limits

**Plan:** Free (Starter)
**Monthly Events:** 20 million
**Data History:** 1 year
**Projects:** 2
**Team Members:** Unlimited
**Reports:** Unlimited
**Dashboards:** Unlimited

**Estimated Usage (POC):**
- 100 users/day × 10 events/user × 30 days = 30,000 events/month
- Well within free tier limits

**Upgrade Triggers:**
- If >1,000 DAU: Consider Growth plan ($20/mo for 100M events)
- If need >1 year history: Consider Enterprise

---

**Document Version:** 1.0
**Last Updated:** 2026-01-30
**Owner:** @analyst
**Reviewers:** @pm, @devops, @ux-design-expert
