# Analytics Documentation - BidIQ Uniformes (DescompLicita) POC

**Last Updated:** 2026-01-30
**Owner:** @analyst
**Status:** Production-Ready ✅

---

## Overview

This directory contains comprehensive analytics documentation for the BidIQ Uniformes POC, including Mixpanel dashboard configurations, event tracking specifications, and troubleshooting guides.

---

## Documentation Files

### 1. **Mixpanel Dashboard Configuration** (`mixpanel-dashboard-configuration.md`)

**Purpose:** Complete configuration guide for 4 key Mixpanel dashboards

**Contents:**
- Dashboard 1: User Engagement (DAU/WAU/MAU, search frequency, session duration)
- Dashboard 2: Feature Usage (LLM summaries, multi-state searches, saved searches, onboarding)
- Dashboard 3: Performance (API response times, error rates, loading experience)
- Dashboard 4: Business Metrics (opportunities discovered, filter efficiency, conversion rates)
- Alert configuration (8 alerts: 4 critical, 4 warning)
- Implementation checklist
- Success criteria

**Audience:** Analytics team, Product Owner, DevOps

**Use When:**
- Setting up Mixpanel dashboards for the first time
- Understanding what metrics are being tracked
- Configuring alerts and thresholds
- Onboarding new team members to analytics

---

### 2. **Mixpanel Access Guide** (`mixpanel-access-guide.md`)

**Purpose:** User manual for accessing and using Mixpanel dashboards

**Contents:**
- How to get Mixpanel account access
- Dashboard navigation and URLs
- Filtering and segmenting data
- Creating custom reports (Insights, Funnels, Retention, Flows)
- Exporting data (CSV, PDF, scheduled exports)
- Sharing dashboards (team links, public links, embeds)
- Common tasks (daily monitoring, weekly reviews, investigating alerts)
- Troubleshooting (no data, slow charts, incorrect data)
- Best practices (data interpretation, dashboard hygiene)

**Audience:** All team members, stakeholders

**Use When:**
- First-time Mixpanel login
- Need to export data or create custom report
- Investigating an alert
- Preparing for weekly/monthly review

---

### 3. **Event Dictionary** (`event-dictionary.md`)

**Purpose:** Complete reference for all tracked events and their properties

**Contents:**
- Event naming convention (noun_verb format)
- Standard properties (timestamp, environment, distinct_id)
- 15 documented events across 6 categories:
  - Page Lifecycle: `page_load`, `page_exit`
  - Search: `search_started`, `search_completed`, `search_failed`, `search_progress_stage`
  - Download: `download_started`, `download_completed`, `download_failed`
  - Loading Progress: `loading_stage_reached`, `loading_abandoned`
  - Onboarding: `onboarding_completed`, `onboarding_dismissed`, `onboarding_step`
  - Saved Searches: `saved_search_created`
- Property definitions and examples
- Event flow examples (happy path, error path, abandonment)
- Testing instructions
- Privacy/LGPD compliance notes

**Audience:** Developers, QA, Analysts

**Use When:**
- Adding new event tracking code
- Debugging event tracking
- Understanding what data is collected
- Privacy/compliance questions

---

### 4. **Alert Runbook** (`alert-runbook.md`)

**Purpose:** Step-by-step troubleshooting guide for Mixpanel alerts

**Contents:**
- 8 alert definitions and thresholds
- Critical alerts (immediate response):
  1. Error Rate Spike (>10% for 1h)
  2. Search Success Rate Drop (<80% for 2h)
  3. Download Failure Spike (<85% for 1h)
  4. Response Time Degradation (P95 >40s for 30min)
- Warning alerts (investigation required):
  5. Bounce Rate High (>50% for 1 day)
  6. Loading Abandonment (>15% for 4h)
  7. Feature Adoption Low (<10% after 14 days)
  8. Onboarding Completion Low (<50% for 7 days)
- Troubleshooting steps for each alert
- Escalation matrix
- Post-incident checklist
- Useful commands (Railway CLI, Mixpanel debugging, PNCP API testing)

**Audience:** DevOps, Dev team, On-call engineers

**Use When:**
- Alert email received
- Investigating production issue
- Escalating incident
- Post-mortem documentation

---

### 5. **Early Metrics Report Template** (`early-metrics-report-template.md`)

**Purpose:** Template for analyzing first 24-48 hours of production data

**Contents:**
- Executive summary structure
- 11 metric categories:
  1. Usage Metrics (Active users, search activity, session behavior)
  2. Feature Usage (LLM summaries, multi-state searches, saved searches, onboarding, sector popularity)
  3. Performance (Response times, error rates, download performance, loading experience)
  4. Business Impact (Opportunities discovered, filter efficiency, user satisfaction, geographic distribution, temporal patterns)
  5. Success Criteria Validation (Issue #97 objectives)
  6. Anomalies & Issues
  7. Infrastructure & Costs
  8. User Feedback (Qualitative)
  9. Recommendations (Immediate, short-term, long-term)
  10. Next Sprint Priorities
  11. Appendix (Dashboards, data files, methodology)
- Target vs. actual comparison tables
- Status indicators (🟢/🟡/🔴)
- Visualization placeholders (screenshots)

**Audience:** Product Owner, Stakeholders, Sprint Review attendees

**Use When:**
- After production deployment (24-48h window)
- Preparing Sprint Review presentation
- Validating POC success
- Planning next sprint priorities

---

## Quick Start Guide

### For First-Time Users

1. **Get Access:** Request Mixpanel invitation from @devops
2. **Read Access Guide:** `mixpanel-access-guide.md` (20 min read)
3. **Bookmark Dashboards:** Save dashboard URLs in browser
4. **Join Slack Channels:**
   - #bidiq-analytics (questions, discussions)
   - #bidiq-alerts (alert notifications)

### For Daily Monitoring

1. Open User Engagement Dashboard
2. Check: DAU, search success rate, error rate
3. If anomaly: Follow Alert Runbook

### For Weekly Reviews

1. Review all 4 dashboards (30 min)
2. Note trends week-over-week
3. Document insights in Slack #bidiq-analytics

### For Sprint Review

1. Generate Early Metrics Report (use template)
2. Export dashboard screenshots
3. Prepare recommendations

---

## Event Tracking Status

### ✅ Production-Ready Events (15 total)

All events are currently being tracked in production:

- **Page Lifecycle:** page_load, page_exit
- **Search:** search_started, search_completed, search_failed, search_progress_stage
- **Download:** download_started, download_completed, download_failed
- **Loading:** loading_stage_reached, loading_abandoned
- **Onboarding:** onboarding_completed, onboarding_dismissed, onboarding_step
- **Saved Searches:** saved_search_created

### 🔄 Future Events (Roadmap)

Events to add in future versions:

- `llm_fallback_triggered` (when LLM API fails and fallback is used)
- `cache_hit` / `cache_miss` (if caching is implemented)
- `filter_too_broad` / `filter_too_narrow` (user feedback on filters)
- `user_feedback_submitted` (if feedback form is added)
- `contract_value_analyzed` (if we extract valor from PNCP data)

---

## Dashboard Configuration Status

### Task #8: Configure Mixpanel Dashboards ✅

**Status:** Documentation Complete (2026-01-30)
**Next Steps:**
1. Obtain Mixpanel project token
2. Add `NEXT_PUBLIC_MIXPANEL_TOKEN` to environment variables
3. Deploy to production
4. Wait 24-48h for data collection
5. Create dashboards in Mixpanel following configuration guide
6. Configure 8 alerts
7. Grant team access

**Timeline:**
- Documentation: ✅ Complete
- Dashboard Creation: ⏳ Pending production deployment
- Alert Configuration: ⏳ Pending dashboard creation
- Team Training: ⏳ Pending access setup

---

## Support & Contact

**Analytics Owner:** @analyst
- Questions about metrics or dashboards
- Interpreting data or trends
- Custom report requests

**Technical Issues:** @devops
- Mixpanel access problems
- Alert configuration
- MCP/infrastructure issues

**Product Questions:** @pm or @po
- Metric targets and goals
- Feature prioritization
- Success criteria validation

**Slack Channels:**
- #bidiq-analytics - General analytics discussions
- #bidiq-alerts - Alert notifications and incident response

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | @analyst | Initial documentation created (Task #8) |
| | | | - Dashboard configuration guide |
| | | | - Access guide |
| | | | - Event dictionary |
| | | | - Alert runbook |
| | | | - Early metrics report template |

---

## Related Documentation

**Project Documentation:**
- `D:\pncp-poc\PRD.md` - Product Requirements Document
- `D:\pncp-poc\ROADMAP.md` - Project roadmap and progress
- `D:\pncp-poc\.env.example` - Environment variables (includes MIXPANEL_TOKEN)

**AIOS Framework:**
- `.aios-core/development/tasks/` - Task definitions
- `docs/stories/` - Development stories

**Frontend Analytics Code:**
- `frontend/app/components/AnalyticsProvider.tsx` - Mixpanel initialization
- `frontend/hooks/useAnalytics.ts` - Event tracking hook
- `frontend/app/page.tsx` - Main search page with event tracking

**Backend (Future):**
- `backend/app/api/routes.py` - API endpoints (could add server-side tracking)

---

**Last Updated:** 2026-01-30 by @analyst
**Next Review:** After production deployment + 48h (Task #9)
