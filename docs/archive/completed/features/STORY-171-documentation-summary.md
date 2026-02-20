# STORY-171 Documentation Summary

**Story:** STORY-171 - Annual Subscription Toggle
**Track:** Track 4 - Documentation + Legal
**Created:** 2026-02-07
**Status:** ✅ Complete

---

## Documentation Deliverables

This document summarizes all documentation created for the annual subscription feature (STORY-171, Track 4).

---

## 1. Feature Documentation

**File:** `docs/features/annual-subscription.md`

**Length:** 850+ lines (comprehensive technical documentation)

**Sections:**
1. **Overview** - Feature benefits, implementation status
2. **Architecture** - Full system diagram (User → Frontend → Backend → Stripe → Supabase → Redis)
3. **Pricing Structure** - Formula (Annual = Monthly × 9.6), pricing table for all 3 plans
4. **Premium Benefits** - Tier 1 (all annual), Tier 2 (Sala de Guerra only)
5. **API Endpoints** - Full specs with request/response examples
   - `POST /api/subscriptions/update-billing-period`
   - `GET /api/features/me`
6. **Database Schema** - Complete SQL for 3 tables:
   - `user_subscriptions`
   - `plan_features`
   - `stripe_webhook_events`
7. **Redis Cache Strategy** - Cache keys, TTLs, invalidation triggers
8. **Pro-Rata Calculation** - Detailed examples for upgrade/downgrade scenarios
9. **Troubleshooting** - Common issues with diagnosis and solutions
10. **Testing Checklist** - Unit, integration, E2E tests

**Key Technical Details:**
- Architecture diagram showing complete data flow
- Redis caching strategy with 5-minute TTL
- Pro-rata calculation examples (monthly → annual, annual → monthly)
- 7-day CDC refund window implementation
- Stripe webhook handling
- Feature flag system (`features:{user_id}`)
- Edge cases: timezone handling, failed payments, 3D Secure

**Audience:** Developers, architects, QA engineers

---

## 2. Legal Documentation

**File:** `docs/legal/downgrade-policy.md`

**Length:** 700+ lines (legal policy document)

**Sections:**
1. **Overview** - 3 key principles (7-day refund, no refund after 7 days, exceptional circumstances)
2. **7-Day Full Refund (CDC Compliance)**
   - Legal basis: Brazilian CDC Lei 8.078/1990, Article 49
   - Eligibility criteria
   - Refund process (customer-initiated, support-initiated)
   - Timeline (5-10 business days)
   - Technical implementation (Python code example)
3. **Downgrade After 7 Days (No Refund)**
   - Policy overview (benefits retained until period end)
   - Downgrade process
   - Timeline example (Jan 1 purchase → March 1 downgrade → Dec 31 benefits expire)
   - Technical implementation (Python code example)
4. **Exceptional Circumstances (Full Refund Anytime)**
   - Service level failures (72+ hour downtime)
   - Feature delays (6+ months past promised date)
   - Unauthorized charges / fraud
5. **Communication Templates**
   - 7-day refund confirmation email
   - Downgrade confirmation email (8+ days)
   - Service failure refund email
6. **Internal Workflows**
   - Support agent checklists (refund request, downgrade request)
7. **Legal Disclaimers**
   - Governing law (CDC, Civil Code, Marco Civil)
   - Dispute resolution (consumidor.gov.br, small claims, standard courts)
8. **Compliance Checklist** - Implementation status tracking

**Key Legal Points:**
- CDC Article 49 compliance (7-day withdrawal right)
- Pro-rata refund calculations for service failures
- Data retention during refund window (30 days)
- Dispute resolution via consumidor.gov.br
- LGPD compliance notes

**Audience:** Legal team, compliance, customer support, executives

---

## 3. Support FAQs

**File:** `docs/support/faq-annual-plans.md`

**Length:** 650+ lines (customer-facing FAQ)

**Sections:**
1. **Billing & Pricing** (5 Q&A)
   - Savings calculation (20% = 2.4 months free)
   - Upfront payment vs monthly
   - Mid-cycle upgrade with pro-rata credit
   - Renewal process
   - No hidden fees
2. **Refunds & Cancellations** (6 Q&A)
   - 7-day full refund policy
   - Cancellation after 7 days (benefits retained)
   - Exceptional refund circumstances
   - Data retention (30 days)
3. **Features & Benefits** (6 Q&A)
   - Annual-only benefits (early access, proactive search, AI analysis)
   - Early access definition (2-4 weeks)
   - Feature delay refunds (6+ months)
   - Monthly vs annual feature access
   - Benefit retention during downgrade
4. **Switching Plans** (3 Q&A)
   - Plan tier upgrades (Consultor → Máquina)
   - Annual ↔ monthly switching
   - Subscription pausing (not available yet)
5. **Payment & Invoicing** (5 Q&A)
   - Accepted payment methods
   - Installment payments (not available yet)
   - Invoice generation
   - Payment failure handling
   - Price lock (grandfather clause)
6. **Technical Questions** (4 Q&A)
   - Feature access checking (UI, API)
   - Data transfer on upgrade
   - Team member management
   - 7-day window calculation (calendar days + 24h grace period)

**Quick Reference Table:** Annual vs Monthly comparison

**Key Customer-Facing Details:**
- Clear pricing examples with real numbers
- Timeline examples (purchase → downgrade → expiration)
- Step-by-step instructions (how to request refund, how to downgrade)
- Contact information (email, chat, phone)
- Self-service resources (help center, tutorials, roadmap)

**Audience:** Customers, customer support agents, sales team

---

## 4. Environment Configuration Updates

### Backend: `backend/.env`

**Updates Made:**
1. **Feature Flag:**
   ```bash
   ENABLE_ANNUAL_PLANS=false  # Default off until legal review complete
   ```

2. **Stripe Price IDs:**
   ```bash
   # Consultor Ágil
   STRIPE_PRICE_CONSULTOR_AGIL_MENSAL=price_xxx  # R$ 297/month
   STRIPE_PRICE_CONSULTOR_AGIL_ANUAL=price_yyy   # R$ 2,851/year

   # Máquina
   STRIPE_PRICE_MAQUINA_MENSAL=price_xxx         # R$ 597/month
   STRIPE_PRICE_MAQUINA_ANUAL=price_yyy          # R$ 5,731/year

   # Sala de Guerra
   STRIPE_PRICE_SALA_GUERRA_MENSAL=price_xxx     # R$ 1,497/month
   STRIPE_PRICE_SALA_GUERRA_ANUAL=price_yyy      # R$ 14,362/year
   ```

3. **Redis Configuration:**
   ```bash
   REDIS_URL=redis://localhost:6379/0
   REDIS_PASSWORD=  # Empty for local, set for production
   REDIS_TLS=false  # Set to true for production (Redis Cloud, Upstash)
   ```

4. **Cache TTL Settings:**
   ```bash
   CACHE_TTL_FEATURES=300          # 5 minutes - user feature flags
   CACHE_TTL_SUBSCRIPTIONS=300     # 5 minutes - subscription data
   CACHE_TTL_STRIPE_CUSTOMERS=3600 # 60 minutes - Stripe customer ID cache
   CACHE_TTL_PLAN_FEATURES=86400   # 24 hours - plan feature definitions
   ```

### Frontend: `frontend/.env.local`

**Updates Made:**
1. **Stripe Public Key:**
   ```bash
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
   ```

2. **Feature Flag:**
   ```bash
   NEXT_PUBLIC_ENABLE_ANNUAL_PLANS=false  # Frontend feature flag
   ```

**Purpose:** Allow gradual rollout, A/B testing, and easy on/off toggle for production deployment.

---

## 5. Terms of Service Update Requirements

**File:** `docs/legal/tos-annual-plans-diff.md`

**Length:** 1,000+ lines (legal requirements summary)

**Status:** ⚠️ **DRAFT - REQUIRES LEGAL REVIEW BEFORE PRODUCTION**

**Sections:**
1. **Legal Notice** - Disclaimer that this is NOT legal advice, requires attorney review
2. **Overview of Required Changes** - 7 ToS sections that need amendments
3. **Section 1: Billing & Payment Terms**
   - Add annual billing option
   - Define annual-exclusive features
   - Feature availability disclaimers
4. **Section 2: Refund Policy (CDC Compliance)**
   - 7-day full refund (CDC Article 49)
   - After 7 days: no refund, benefits retained
   - Exceptional circumstances (service failure, feature delay, fraud)
5. **Section 3: Cancellation & Downgrade Policy**
   - Monthly vs annual cancellation
   - Downgrade process (annual → monthly)
   - Upgrade process (monthly → annual)
6. **Section 4: Feature Availability & Early Access**
   - Core features (all plans)
   - Annual-exclusive features
   - Feature availability dates (estimates)
   - Feature de-exclusivity refund policy
7. **Section 5: Data Retention & Privacy**
   - 30-day retention after cancellation
   - 7-day refund window data retention
   - LGPD compliance
8. **Section 6: Modification of Terms**
   - Grandfather clause for annual pricing
   - Material vs non-material changes
9. **Section 7: Dispute Resolution**
   - consumidor.gov.br (preferred)
   - Small claims court
   - Standard court jurisdiction
   - Class action rights preserved (CDC)
10. **Section 8: Annual Subscription Specific Provisions** (NEW)
    - Billing cycle
    - Pro-rata calculations
    - Auto-renewal notices (30d, 7d, 24h)
    - Payment failure timeline
    - Currency and taxes
11. **Implementation Checklist** - 30+ items before production deployment
12. **Open Legal Questions** - 6 categories requiring legal counsel input
13. **Recommended Legal Counsel** - Firm specialization requirements
14. **Timeline** - From legal review to production (30-day user notice period)

**Critical Legal Points:**
- CDC Article 49 compliance (7-day withdrawal)
- LGPD data retention compliance
- Grandfather clause for annual pricing
- Auto-renewal notice requirements
- Dispute resolution via consumidor.gov.br
- Feature delay compensation (6-month threshold)

**Open Legal Questions:**
1. 7-day window: payment success vs service activation?
2. Feature delay: is 6 months defensible?
3. Price lock: enforceable in Brazil?
4. Auto-renewal: 24-hour notice sufficient?
5. Dispute resolution: mandatory arbitration allowed?
6. LGPD: 30-day retention applies to all data types?

**Implementation Checklist Categories:**
- Legal review (CDC, LGPD, tax compliance)
- User communication (30-day notice, ToS acceptance flow)
- Technical implementation (refund checks, pro-rata logic, webhooks)
- Compliance monitoring (refund tracking, feature launch dates, uptime)

**Timeline:** Feb 10 (legal firm selection) → March 31 (annual plans go live)

**Budget Estimate:** R$ 15,000 - R$ 30,000 for comprehensive legal review

**Audience:** Legal team, compliance officer, CEO, general counsel

---

## Documentation Metrics

| Document | Lines | Word Count (est.) | Audience | Purpose |
|----------|-------|-------------------|----------|---------|
| **Feature Documentation** | 850+ | ~8,000 | Developers | Technical implementation guide |
| **Legal Policy** | 700+ | ~7,000 | Legal / Support | Refund and downgrade procedures |
| **Customer FAQs** | 650+ | ~6,500 | Customers | Self-service support |
| **ToS Amendments** | 1,000+ | ~10,000 | Legal / Executives | Terms of Service updates |
| **Total** | **3,200+** | **~31,500** | Mixed | Complete feature documentation |

---

## Coverage Analysis

### Technical Documentation Coverage: ✅ 100%

- [x] Architecture diagram with all system components
- [x] API endpoint specifications (request/response)
- [x] Database schema with indexes and constraints
- [x] Redis caching strategy with invalidation triggers
- [x] Pro-rata calculation examples (upgrade/downgrade)
- [x] Stripe webhook handling
- [x] Edge cases (timezones, failed payments, 3D Secure)
- [x] Troubleshooting guide (diagnosis + solutions)
- [x] Testing checklist (unit, integration, E2E)

### Legal Documentation Coverage: ✅ 100%

- [x] 7-day CDC refund policy (Article 49)
- [x] Downgrade policy (8+ days, no refund)
- [x] Exceptional refund circumstances (service failure, feature delay, fraud)
- [x] Communication templates (refund, downgrade, service failure)
- [x] Support agent workflows (checklists)
- [x] Legal disclaimers (governing law, dispute resolution)
- [x] LGPD compliance notes
- [x] ToS amendment requirements (7 sections)
- [x] Open legal questions (6 categories)
- [x] Implementation checklist (30+ items)

### Customer Support Coverage: ✅ 100%

- [x] Pricing and savings calculations
- [x] Billing frequency and timing
- [x] Refund eligibility (7-day window)
- [x] Cancellation procedures
- [x] Annual-exclusive features (early access, proactive search, AI analysis)
- [x] Upgrade/downgrade processes
- [x] Payment methods and invoicing
- [x] Data retention and export
- [x] Contact information and self-service resources
- [x] Quick reference table (annual vs monthly)

### Environment Configuration Coverage: ✅ 100%

- [x] Feature flags (backend + frontend)
- [x] Stripe price IDs (6 placeholders: 3 plans × 2 billing periods)
- [x] Redis connection variables
- [x] Cache TTL settings (4 categories)
- [x] Clear comments and documentation

---

## Usage Guide for Each Document

### For Developers (Backend/Frontend Implementation)

**Primary Document:** `docs/features/annual-subscription.md`

**Use Cases:**
1. Implementing `/api/subscriptions/update-billing-period` endpoint
2. Setting up Redis caching for feature flags
3. Integrating Stripe subscription updates
4. Handling pro-rata calculations
5. Processing Stripe webhooks
6. Writing unit/integration tests

**Key Sections:**
- Architecture (understand full system)
- API Endpoints (exact request/response formats)
- Database Schema (SQL to copy/paste)
- Redis Cache Strategy (cache keys and invalidation)
- Pro-Rata Calculation (edge cases)
- Troubleshooting (common issues)

---

### For Legal/Compliance Team

**Primary Documents:**
1. `docs/legal/downgrade-policy.md` - Refund and downgrade procedures
2. `docs/legal/tos-annual-plans-diff.md` - ToS amendment requirements

**Use Cases:**
1. Reviewing CDC compliance for 7-day refund window
2. Approving refund and downgrade policies
3. Drafting ToS amendments
4. Identifying open legal questions
5. Preparing for legal counsel review
6. Ensuring LGPD compliance

**Key Sections:**
- 7-Day Full Refund (CDC Article 49 implementation)
- Exceptional Circumstances (full refund anytime)
- Open Legal Questions (6 categories requiring attorney input)
- Implementation Checklist (legal review tasks)
- ToS Amendment Sections (what needs to change)

---

### For Customer Support Team

**Primary Documents:**
1. `docs/support/faq-annual-plans.md` - Customer FAQs
2. `docs/legal/downgrade-policy.md` - Internal workflows

**Use Cases:**
1. Answering customer questions about annual plans
2. Processing refund requests (7-day window check)
3. Handling downgrade requests (8+ days)
4. Explaining annual-exclusive features
5. Troubleshooting billing issues
6. Escalating exceptional refund cases

**Key Sections:**
- FAQ sections (copy/paste answers to customers)
- Communication Templates (email responses)
- Support Agent Checklists (step-by-step workflows)
- Quick Reference Table (annual vs monthly comparison)

---

### For Product/Marketing Team

**Primary Documents:**
1. `docs/features/annual-subscription.md` - Feature overview
2. `docs/support/faq-annual-plans.md` - Customer messaging

**Use Cases:**
1. Writing marketing copy for annual plans
2. Creating product launch materials
3. Designing pricing page
4. Planning feature rollout (early access, proactive search, AI analysis)
5. Communicating value proposition (20% savings, exclusive features)

**Key Sections:**
- Overview (benefits and value props)
- Pricing Structure (exact numbers and savings)
- Premium Benefits (tier 1 and tier 2)
- FAQ Sections (customer objection handling)

---

### For DevOps/Infrastructure Team

**Primary Documents:**
1. `docs/features/annual-subscription.md` - Redis setup
2. `backend/.env` - Environment configuration

**Use Cases:**
1. Setting up Redis instance (Redis Cloud, Upstash, Railway)
2. Configuring Stripe webhooks
3. Environment variable management (staging vs production)
4. Monitoring cache performance
5. Troubleshooting production issues

**Key Sections:**
- Redis Cache Strategy (TTLs, invalidation)
- Environment Configuration (.env variables)
- Troubleshooting (Redis cache issues, Stripe webhooks)

---

## Next Steps

### Immediate (Before Development)

1. **Legal Review** (REQUIRED)
   - [ ] Select Brazilian consumer law attorney (by Feb 10)
   - [ ] Initial legal review of refund/downgrade policy (by Feb 20)
   - [ ] Draft ToS amendments with legal counsel (by Feb 25)
   - [ ] Obtain CEO/General Counsel approval (by Feb 28)

2. **Environment Setup**
   - [ ] Create Stripe price IDs for 6 plans (3 tiers × 2 billing periods)
   - [ ] Set up Redis instance (development + staging + production)
   - [ ] Update `.env` files with real Stripe price IDs
   - [ ] Configure Stripe webhooks for subscription events

3. **Technical Planning**
   - [ ] Review architecture diagram with team
   - [ ] Estimate development effort (backend, frontend, testing)
   - [ ] Create implementation tasks for STORY-171 (Tracks 1-3)
   - [ ] Set up feature flags in codebase

---

### During Development

4. **Backend Implementation**
   - [ ] Follow `docs/features/annual-subscription.md` API specs
   - [ ] Implement pro-rata calculation logic
   - [ ] Set up Redis caching
   - [ ] Add Stripe webhook handlers
   - [ ] Write unit tests for refund eligibility check

5. **Frontend Implementation**
   - [ ] Build billing period toggle component
   - [ ] Display annual-exclusive features
   - [ ] Show 20% discount badge
   - [ ] Add refund request button (visible only during 7-day window)

6. **Testing**
   - [ ] Unit tests (pro-rata, refund eligibility)
   - [ ] Integration tests (Stripe API, Redis cache)
   - [ ] E2E tests (upgrade, downgrade, refund flows)
   - [ ] Load testing (Redis cache performance)

---

### Before Production Launch

7. **Customer Communication** (30-Day Notice Required)
   - [ ] Send ToS change notification to all users (March 1)
   - [ ] Update Help Center with FAQ content
   - [ ] Train support team on refund/downgrade workflows
   - [ ] Prepare marketing materials for annual plans

8. **Compliance & Monitoring**
   - [ ] Set up refund request tracking dashboard
   - [ ] Configure alerts for feature launch dates (March 2026, April 2026)
   - [ ] Set up uptime monitoring (72-hour threshold for service failure refunds)
   - [ ] Create quarterly compliance audit checklist

9. **Final Approvals**
   - [ ] Legal sign-off on ToS amendments
   - [ ] Compliance officer approval
   - [ ] CEO/General Counsel approval
   - [ ] Product team go/no-go decision

10. **Launch** (Target: March 31, 2026)
    - [ ] Deploy feature flags (set `ENABLE_ANNUAL_PLANS=true`)
    - [ ] Monitor first 24 hours for issues
    - [ ] Review first week refund requests
    - [ ] Collect user feedback

---

## Success Metrics

### Documentation Quality Metrics

- **Completeness:** ✅ 100% coverage of all STORY-171 Track 4 requirements
- **Clarity:** Technical + legal + customer-facing docs all written in appropriate language for audience
- **Actionability:** Includes code examples, SQL schemas, support workflows, legal checklists
- **Maintainability:** Structured with clear sections, tables, examples

### Feature Launch Metrics (To Track After Production)

- **7-Day Refund Rate:** Target <5% of annual subscriptions
- **8+ Day Downgrade Rate:** Target <10% of annual subscriptions
- **Support Ticket Volume:** Expect spike in first week, then normalize
- **Feature Delay Refunds:** 0 refunds due to feature delays (implies on-time launches)
- **Service Failure Refunds:** 0 refunds due to 72+ hour downtime (implies 99.9%+ uptime)

---

## Document Maintenance

### Review Frequency

| Document | Review Frequency | Trigger Events |
|----------|------------------|----------------|
| **Feature Documentation** | Quarterly | API changes, new features, architecture updates |
| **Legal Policy** | Annually + as needed | Law changes, policy updates, customer feedback |
| **Customer FAQs** | Monthly | Support ticket trends, new questions |
| **ToS Amendments** | As needed | Legal requirements, material policy changes |
| **Environment Config** | On every deployment | New env variables, infrastructure changes |

### Ownership

| Document | Owner | Backup |
|----------|-------|--------|
| **Feature Documentation** | Backend Lead | Architect |
| **Legal Policy** | Legal Team | Compliance Officer |
| **Customer FAQs** | Support Lead | Product Manager |
| **ToS Amendments** | Legal Team | General Counsel |
| **Environment Config** | DevOps Lead | Backend Lead |

---

## Related Stories

- **STORY-171 Track 1:** Frontend UI (billing period toggle, premium benefits display)
- **STORY-171 Track 2:** Backend API (subscription updates, feature flags, Redis caching)
- **STORY-171 Track 3:** Testing (unit, integration, E2E)
- **STORY-172:** Proactive Search (annual-exclusive feature, March 2026)
- **STORY-173:** AI Edital Analysis (Sala de Guerra annual-exclusive, April 2026)

---

## Conclusion

All required documentation for STORY-171 Track 4 (Documentation + Legal) has been created:

1. ✅ **Feature Documentation** - 850+ lines of technical specs
2. ✅ **Legal Policy** - 700+ lines of refund/downgrade procedures
3. ✅ **Customer FAQs** - 650+ lines of support content
4. ✅ **ToS Amendments** - 1,000+ lines of legal requirements
5. ✅ **Environment Configuration** - Backend + Frontend .env updates

**Total:** 3,200+ lines, ~31,500 words of comprehensive documentation covering technical implementation, legal compliance, customer support, and environment configuration.

**Status:** Ready for legal review and implementation.

**Next Step:** Legal team review of refund policy and ToS amendments (by Feb 20, 2026).

---

**Created By:** Claude Code (AI Development Assistant)
**Story:** STORY-171 Track 4
**Date:** 2026-02-07
**Last Updated:** 2026-02-07
**Version:** 1.0
