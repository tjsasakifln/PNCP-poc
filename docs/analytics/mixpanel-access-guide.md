# Mixpanel Access Guide

**Version:** 1.0
**Last Updated:** 2026-01-30
**Audience:** All team members and stakeholders

---

## Overview

This guide explains how to access and use the Mixpanel analytics dashboards for the BidIQ Uniformes (DescompLicita) POC.

---

## Getting Access

### Step 1: Account Setup

1. **Receive Invitation Email**
   - Project admin will send Mixpanel invitation
   - Email subject: "You've been invited to join [Project Name] on Mixpanel"

2. **Create Account**
   - Click "Accept Invitation" in email
   - Set password (min 8 characters)
   - Complete profile (name, role)

3. **Verify Access**
   - Log in at: https://mixpanel.com/
   - You should see "BidIQ Uniformes POC" project

### Step 2: Role Permissions

**Admin:**
- Full access to all features
- Can create/edit dashboards
- Can invite team members
- Can manage billing

**Member:**
- Can view and create dashboards
- Can create reports
- Cannot invite users or manage billing

**Viewer (Consumer):**
- Read-only access
- Can view dashboards
- Cannot create or edit

**Typical Assignments:**
- Dev Team: Member
- Product/Business: Member
- Stakeholders: Viewer
- DevOps: Admin

---

## Accessing Dashboards

### Dashboard URLs (Bookmarks)

Once logged in, bookmark these URLs:

1. **User Engagement Dashboard**
   - URL: `https://mixpanel.com/project/[PROJECT_ID]/view/[BOARD_ID]/app/boards#id=[DASHBOARD_1_ID]`
   - Quick access: Dashboards > User Engagement

2. **Feature Usage Dashboard**
   - URL: `https://mixpanel.com/project/[PROJECT_ID]/view/[BOARD_ID]/app/boards#id=[DASHBOARD_2_ID]`
   - Quick access: Dashboards > Feature Usage

3. **Performance Dashboard**
   - URL: `https://mixpanel.com/project/[PROJECT_ID]/view/[BOARD_ID]/app/boards#id=[DASHBOARD_3_ID]`
   - Quick access: Dashboards > Performance

4. **Business Metrics Dashboard**
   - URL: `https://mixpanel.com/project/[PROJECT_ID]/view/[BOARD_ID]/app/boards#id=[DASHBOARD_4_ID]`
   - Quick access: Dashboards > Business Metrics

**Note:** Project admin will share exact URLs after dashboard creation.

### Navigation Tips

**From Homepage:**
1. Log in → Click project name → Dashboards (left sidebar)
2. Select desired dashboard from list
3. Use tabs to switch between dashboards

**Keyboard Shortcuts:**
- `Ctrl + K` (Windows) or `Cmd + K` (Mac): Quick search
- `Ctrl + /`: Show keyboard shortcuts
- `Esc`: Close modal/panel

---

## Using Dashboards

### Basic Operations

#### Viewing Data

1. **Date Range Selector** (Top right)
   - Default: Last 7 days
   - Presets: Today, Yesterday, Last 7/30/90 days, Custom
   - Click to change range
   - All charts update automatically

2. **Refresh Data**
   - Auto-refresh: Every 5 minutes (configurable)
   - Manual refresh: Click refresh icon (top right)
   - Last updated time shown below each chart

3. **Chart Interactions**
   - **Hover:** See exact values
   - **Click:** Drill down into details
   - **Drag:** Zoom into time range (line charts)
   - **Legend Click:** Show/hide series

#### Filtering Data

1. **Global Filters** (Top bar)
   - Filter entire dashboard by property
   - Examples:
     - Environment: production (exclude development data)
     - Setor: vestuario (only uniform searches)
     - UF: SC (only Santa Catarina)

2. **Chart-Specific Filters**
   - Hover over chart → Click "Filter" icon
   - Add filter → Select property → Choose value
   - Temporary filter (doesn't affect other charts)

3. **Breakdown/Segmentation**
   - Most charts support "Breakdown by" property
   - Examples:
     - Break down searches by `setor_id`
     - Break down errors by `error_type`
   - Limit: 10 segments displayed

### Advanced Features

#### Creating Custom Reports

1. **Insights (Ad-Hoc Analysis)**
   - Navigation: Reports > Insights
   - Select event: `search_started`, `download_completed`, etc.
   - Choose metric: Total, Unique, Average, etc.
   - Add filters/breakdowns
   - Save as new report

2. **Funnels**
   - Navigation: Reports > Funnels
   - Define steps (ordered events)
   - Example: page_load → search_started → search_completed → download_completed
   - See conversion rates between steps
   - Identify drop-off points

3. **Retention**
   - Navigation: Reports > Retention
   - Track user return behavior
   - Example: Users who searched on Day 0, returned to search on Day 7?
   - Cohort analysis

4. **Flows**
   - Navigation: Reports > Flows
   - Visualize user journey paths
   - See most common event sequences
   - Identify unexpected paths

#### Exporting Data

**Export Chart Data:**
1. Hover over chart → Click "..." (more options)
2. Select "Export" → Choose format:
   - **CSV:** Raw data table
   - **PNG:** Chart image
   - **PDF:** Formatted report
3. Download file

**Export Dashboard:**
1. Click "..." (top right) → "Export Dashboard"
2. Choose format: PDF (all charts)
3. Select date range
4. Download

**Scheduled Exports:**
1. Click "..." (top right) → "Schedule Export"
2. Set frequency: Daily, Weekly, Monthly
3. Set recipients (email addresses)
4. Mixpanel emails report automatically

#### Sharing Dashboards

**Share Link (Team Members):**
1. Click "Share" button (top right)
2. Copy URL
3. Share via Slack, email, etc.
4. Recipient must have Mixpanel access

**Public Link (External Stakeholders):**
1. Click "Share" → "Create Public Link"
2. Set expiration date
3. Copy link
4. Anyone with link can view (no login required)
5. **Security Note:** Public links are view-only, no sensitive data exposed

**Embed Dashboard:**
1. Click "Share" → "Embed"
2. Copy iframe code
3. Paste into internal wiki/portal
4. Refresh periodically

---

## Common Tasks

### Daily Monitoring (5 minutes)

**For Product/Business:**
1. Open User Engagement Dashboard
2. Check DAU (Daily Active Users)
3. Check search success rate
4. Review any anomalies

**For Dev/DevOps:**
1. Open Performance Dashboard
2. Check error rate (should be <5%)
3. Check P95 response time (should be <30s)
4. Investigate any alerts

### Weekly Reviews (30 minutes)

1. **User Engagement:**
   - WAU trend (up or down?)
   - Top UFs searched
   - Search frequency

2. **Feature Usage:**
   - Saved searches adoption
   - Onboarding completion rate
   - Multi-state search usage

3. **Performance:**
   - Average response time
   - Error rate trend
   - Loading abandonment

4. **Business Metrics:**
   - Total searches (week-over-week growth)
   - Opportunities discovered
   - Filter efficiency

### Investigating Alerts

**When you receive an alert email:**

1. **Click Alert Link**
   - Goes directly to relevant chart
   - Shows current value vs. threshold

2. **Check Context**
   - Is this a real issue or noise?
   - Check related metrics (e.g., error rate + response time)
   - Look at breakdown (which UF? which sector?)

3. **Gather Evidence**
   - Export chart as PNG
   - Note exact time of anomaly
   - Check backend logs (if applicable)

4. **Report/Escalate**
   - Slack: #bidiq-alerts channel
   - Tag relevant team (@dev, @devops)
   - Share Mixpanel chart link

5. **Follow Alert Runbook**
   - See: `docs/analytics/alert-runbook.md`
   - Each alert has specific troubleshooting steps

---

## Troubleshooting

### Issue: "No data available"

**Causes:**
- No events tracked in selected date range
- Filter too restrictive (e.g., UF that was never searched)
- Production deployment not yet live

**Solutions:**
- Check date range (expand to "All Time")
- Remove filters
- Verify events in Live View (see below)

### Issue: "Chart loading slowly"

**Causes:**
- Large date range (e.g., 1 year of data)
- Complex breakdown (e.g., breakdown by `user_agent`)
- High cardinality property

**Solutions:**
- Reduce date range (try 7 days first)
- Simplify breakdown (use fewer segments)
- Contact admin to optimize query

### Issue: "Data looks incorrect"

**Causes:**
- Mixed production + development data
- Event tracking bug
- Mixpanel caching

**Solutions:**
- Add global filter: `environment = production`
- Check event dictionary: `docs/analytics/event-dictionary.md`
- Hard refresh: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- Contact dev team to verify event tracking

### Verifying Events (Live View)

1. Navigation: Reports > Live View
2. See real-time events as they're tracked
3. Click event to see properties
4. Useful for debugging event tracking
5. Filter by event name to focus

---

## Best Practices

### Data Interpretation

1. **Look for Trends, Not Absolutes**
   - One day of high error rate ≠ crisis
   - Week-over-week trend matters more

2. **Correlate Metrics**
   - High error rate + slow response time = backend issue
   - High bounce rate + low onboarding completion = UX problem

3. **Consider Context**
   - Monday traffic differs from Saturday
   - Holiday periods may show anomalies
   - Marketing campaigns cause spikes

4. **Avoid Vanity Metrics**
   - Total page views alone doesn't mean success
   - Focus on engagement, conversion, satisfaction

### Dashboard Hygiene

1. **Use Consistent Date Ranges**
   - Default to "Last 7 days" for operational dashboards
   - Use "Last 30 days" for strategic reviews

2. **Annotate Anomalies**
   - Mixpanel allows chart annotations
   - Mark deployments, incidents, campaigns
   - Example: "2026-01-30: Production launch"

3. **Review Access Quarterly**
   - Remove team members who left
   - Adjust roles as needed
   - Audit public links

4. **Keep Dashboards Focused**
   - Each dashboard serves 1 purpose
   - Too many charts = analysis paralysis
   - Archive unused dashboards

---

## Getting Help

### Internal Resources

1. **Documentation:**
   - Event Dictionary: `docs/analytics/event-dictionary.md`
   - Dashboard Configuration: `docs/analytics/mixpanel-dashboard-configuration.md`
   - Alert Runbook: `docs/analytics/alert-runbook.md`

2. **Team Channels:**
   - Slack: #bidiq-analytics (questions, discussions)
   - Slack: #bidiq-alerts (alert notifications)

3. **Point of Contact:**
   - Analytics Owner: @analyst
   - Mixpanel Admin: @devops
   - Business Questions: @pm or @po

### Mixpanel Support

1. **Help Center:**
   - URL: https://help.mixpanel.com/
   - Search documentation
   - Video tutorials

2. **Community:**
   - URL: https://community.mixpanel.com/
   - Ask questions
   - See common solutions

3. **Support Tickets:**
   - Free plan: Email support (48h response)
   - Paid plan: Priority support (4h response)

---

## Appendix: Quick Reference

### Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Quick search | Ctrl + K | Cmd + K |
| Refresh dashboard | Ctrl + R | Cmd + R |
| Open help | Ctrl + / | Cmd + / |
| Close modal | Esc | Esc |
| Fullscreen chart | F | F |

### Common Filters

| Filter | Purpose |
|--------|---------|
| `environment = production` | Exclude development/test data |
| `setor_id = vestuario` | Focus on uniform sector |
| `uf_count > 1` | Multi-state searches only |
| `time_elapsed_ms > 30000` | Slow searches (>30s) |
| `error_type is set` | Failed operations only |

### Date Range Presets

| Preset | Use Case |
|--------|----------|
| Today | Real-time monitoring |
| Last 7 days | Weekly operational review |
| Last 30 days | Monthly strategic review |
| Last 90 days | Quarterly trend analysis |
| Custom | Specific incident investigation |

---

**Questions?** Contact @analyst or post in #bidiq-analytics Slack channel.
