# STORY-171 Documentation Index

**Quick Navigation Guide for Annual Subscription Documentation**

---

## 📂 Documentation Structure

```
docs/
├── features/
│   └── annual-subscription.md          # 🔧 Technical implementation guide
├── legal/
│   ├── downgrade-policy.md             # ⚖️ Refund and downgrade procedures
│   └── tos-annual-plans-diff.md        # 📜 Terms of Service amendments
├── support/
│   └── faq-annual-plans.md             # ❓ Customer FAQs
└── stories/
    ├── STORY-171-documentation-summary.md   # 📊 Summary of all docs
    └── STORY-171-documentation-index.md     # 🗂️ This file (navigation)
```

---

## 🎯 Quick Links by Role

### 👨‍💻 Developers

**Start Here:** [`docs/features/annual-subscription.md`](../features/annual-subscription.md)

**What You Need:**
- Architecture diagram (line 19)
- API endpoint specs (line 77)
  - `POST /api/subscriptions/update-billing-period`
  - `GET /api/features/me`
- Database schema (line 155)
  - `user_subscriptions` table
  - `plan_features` table
  - `stripe_webhook_events` table
- Redis caching strategy (line 250)
- Pro-rata calculation examples (line 310)
- Troubleshooting guide (line 465)

**Also Review:**
- Environment configuration: `backend/.env` (Redis, Stripe, feature flags)
- Testing checklist (line 600)

---

### ⚖️ Legal Team

**Start Here:** [`docs/legal/tos-annual-plans-diff.md`](../legal/tos-annual-plans-diff.md)

**What You Need:**
- Section 2: Refund Policy / CDC Compliance (line 110)
- Section 3: Cancellation & Downgrade Policy (line 230)
- Section 7: Dispute Resolution (line 490)
- Open Legal Questions (line 680)
- Implementation Checklist (line 750)

**Also Review:**
- [`docs/legal/downgrade-policy.md`](../legal/downgrade-policy.md) - Full refund policy
- 7-Day Full Refund section (line 25)
- Downgrade After 7 Days section (line 125)
- Exceptional Circumstances section (line 270)

**Action Items:**
- Legal counsel selection (by Feb 10)
- Review refund policy for CDC compliance
- Draft ToS amendments
- Obtain CEO/General Counsel approval

---

### 🎧 Customer Support

**Start Here:** [`docs/support/faq-annual-plans.md`](../support/faq-annual-plans.md)

**What You Need:**
- Billing & Pricing FAQs (line 15)
- Refunds & Cancellations FAQs (line 95)
- Features & Benefits FAQs (line 185)
- Switching Plans FAQs (line 275)
- Quick Reference Table (line 575)

**Also Review:**
- [`docs/legal/downgrade-policy.md`](../legal/downgrade-policy.md)
  - Communication templates (line 380)
  - Support agent checklists (line 480)

**Common Scenarios:**
1. **Customer requests refund (within 7 days):**
   - Check eligibility: `CURRENT_DATE - DATE(created_at) <= 7`
   - Process full refund via Stripe
   - Use email template: "7-Day Refund Confirmation" (downgrade-policy.md, line 385)

2. **Customer requests downgrade (after 7 days):**
   - Explain: No refund, but benefits retained until period end
   - Use checklist: "Support Agent Checklist: Downgrade Request" (downgrade-policy.md, line 540)
   - Use email template: "Downgrade Confirmation Email" (downgrade-policy.md, line 420)

---

### 📊 Product/Marketing

**Start Here:** [`docs/features/annual-subscription.md`](../features/annual-subscription.md)

**What You Need:**
- Overview & Benefits (line 10)
- Pricing Structure (line 45)
  - 20% discount = 2.4 months free
  - Exact prices for all 3 plans
- Premium Benefits (line 60)
  - Tier 1: All annual plans
  - Tier 2: Sala de Guerra annual only

**Also Review:**
- [`docs/support/faq-annual-plans.md`](../support/faq-annual-plans.md)
  - Customer value propositions
  - Objection handling (refunds, feature delays)

**Marketing Copy Source:**
- Headline: "Save 20% with Annual Billing"
- Subhead: "Lock in your rate + get exclusive early access to new features"
- Benefits:
  - ✨ Early access (2-4 weeks before monthly subscribers)
  - 🎯 Proactive search (March 2026)
  - 🤖 AI edital analysis (Sala de Guerra, April 2026)
  - 💰 20% discount

---

### 🔧 DevOps/Infrastructure

**Start Here:** `backend/.env` and [`docs/features/annual-subscription.md`](../features/annual-subscription.md)

**What You Need:**
- Redis configuration (backend/.env, line 47)
  - `REDIS_URL`, `REDIS_PASSWORD`, `REDIS_TLS`
- Cache TTL settings (backend/.env, line 54)
- Redis cache strategy (annual-subscription.md, line 250)
  - Cache keys: `features:{user_id}`, `subscription:{user_id}`
  - TTLs: 5 minutes (features), 5 minutes (subscriptions)

**Setup Tasks:**
1. Provision Redis instance (Redis Cloud, Upstash, or Railway)
2. Set `REDIS_URL` in production environment
3. Enable TLS: `REDIS_TLS=true` for production
4. Configure Stripe webhooks:
   - URL: `https://api.smartlic.tech/webhooks/stripe`
   - Events: `customer.subscription.updated`, `invoice.paid`, `invoice.payment_failed`
5. Set feature flag: `ENABLE_ANNUAL_PLANS=false` (until legal review complete)

---

### 🎯 Executives/Leadership

**Start Here:** [`docs/stories/STORY-171-documentation-summary.md`](STORY-171-documentation-summary.md)

**What You Need:**
- Overview of all documentation (line 10)
- Coverage analysis (line 270)
- Next steps and timeline (line 370)
- Success metrics (line 480)

**Key Decisions Required:**
1. **Legal Review Budget:** R$ 15,000 - R$ 30,000 (ToS amendments, CDC compliance)
2. **Launch Timeline:** March 31, 2026 (requires legal approval by Feb 28)
3. **Feature Roadmap:**
   - Proactive Search: March 2026 (annual-exclusive)
   - AI Edital Analysis: April 2026 (Sala de Guerra annual only)
4. **Policy Approval:**
   - 7-day CDC refund window
   - No refund after 7 days (benefits retained)
   - 6-month feature delay threshold

**Risk Assessment:**
- Legal: Requires attorney review (CDC, LGPD compliance)
- Financial: 7-day refund rate (target <5%)
- Technical: Redis caching, Stripe integration, pro-rata calculations
- Customer Support: Potential spike in refund/downgrade requests

---

## 📋 Document Summaries

### 1. Feature Documentation
**File:** `docs/features/annual-subscription.md`
**Length:** 850+ lines
**Purpose:** Technical implementation guide for developers

**Key Sections:**
- Architecture & data flow
- API specifications
- Database schema
- Redis caching
- Pro-rata calculations
- Troubleshooting

**When to Use:**
- Implementing backend endpoints
- Setting up Redis caching
- Writing tests
- Debugging production issues

---

### 2. Legal Policy
**File:** `docs/legal/downgrade-policy.md`
**Length:** 700+ lines
**Purpose:** Refund and downgrade procedures (legal + operational)

**Key Sections:**
- 7-day CDC refund (Article 49)
- Downgrade after 7 days (no refund)
- Exceptional circumstances
- Email templates
- Support workflows

**When to Use:**
- Processing refund requests
- Handling downgrades
- Customer communication
- Legal compliance verification

---

### 3. Customer FAQs
**File:** `docs/support/faq-annual-plans.md`
**Length:** 650+ lines
**Purpose:** Customer-facing support content

**Key Sections:**
- Billing & pricing
- Refunds & cancellations
- Features & benefits
- Switching plans
- Payment & invoicing

**When to Use:**
- Answering customer questions
- Creating help center articles
- Training support agents
- Marketing/sales enablement

---

### 4. ToS Amendments
**File:** `docs/legal/tos-annual-plans-diff.md`
**Length:** 1,000+ lines
**Purpose:** Legal requirements for Terms of Service updates

**Key Sections:**
- 7 ToS sections requiring amendments
- Open legal questions
- Implementation checklist
- Timeline and budget

**When to Use:**
- Legal review process
- Drafting ToS updates
- Compliance verification
- CEO/General Counsel approval

---

### 5. Documentation Summary
**File:** `docs/stories/STORY-171-documentation-summary.md`
**Length:** 700+ lines
**Purpose:** Overview of all documentation created

**Key Sections:**
- All deliverables summary
- Coverage analysis
- Usage guide by role
- Next steps and timeline

**When to Use:**
- Project status updates
- Handoff to other teams
- Executive briefings
- Onboarding new team members

---

## 🔍 Find Information Fast

### "How much do customers save with annual plans?"
**Answer:** 20% (equivalent to 2.4 months free)
**Source:** `docs/features/annual-subscription.md`, line 45

---

### "What's the refund policy?"
**Answer:**
- **0-7 days:** Full refund, no questions asked (CDC Article 49)
- **8+ days:** No refund, but benefits retained until period end
- **Exceptions:** Service failure (72+ hours), feature delay (6+ months), fraud

**Source:** `docs/legal/downgrade-policy.md`, line 25

---

### "What are annual-exclusive features?"
**Answer:**
- ✨ Early Access (2-4 weeks before monthly)
- 🎯 Proactive Search (March 2026)
- 🤖 AI Edital Analysis - Sala de Guerra only (April 2026)

**Source:** `docs/features/annual-subscription.md`, line 60

---

### "How does pro-rata calculation work?"
**Answer:** Monthly → Annual upgrade example:
- Monthly plan: R$ 297
- 15 days remaining
- Credit: (15/30) × 297 = R$ 148.50
- You pay: R$ 2,851 - R$ 148.50 = R$ 2,702.50

**Source:** `docs/features/annual-subscription.md`, line 310

---

### "What Redis cache keys are used?"
**Answer:**
- `features:{user_id}` - TTL: 5 minutes
- `subscription:{user_id}` - TTL: 5 minutes
- `stripe:customer:{email}` - TTL: 60 minutes
- `plan:features:{plan_id}` - TTL: 24 hours

**Source:** `docs/features/annual-subscription.md`, line 250

---

### "What if a feature is delayed?"
**Answer:**
- **0-6 months delay:** No compensation
- **6+ months delay:** Full refund OR keep subscription at monthly rate

**Source:** `docs/legal/downgrade-policy.md`, line 290

---

### "How do I request a refund as a customer?"
**Answer:**
1. **Within 7 days:** Account Settings → Billing → "Request Refund" button
2. **Exceptional cases:** Email suporte@smartlic.tech

**Source:** `docs/support/faq-annual-plans.md`, line 105

---

### "What Stripe price IDs do I need?"
**Answer:** 6 total (3 plans × 2 billing periods):
- `STRIPE_PRICE_CONSULTOR_AGIL_MENSAL` (R$ 297/month)
- `STRIPE_PRICE_CONSULTOR_AGIL_ANUAL` (R$ 2,851/year)
- `STRIPE_PRICE_MAQUINA_MENSAL` (R$ 597/month)
- `STRIPE_PRICE_MAQUINA_ANUAL` (R$ 5,731/year)
- `STRIPE_PRICE_SALA_GUERRA_MENSAL` (R$ 1,497/month)
- `STRIPE_PRICE_SALA_GUERRA_ANUAL` (R$ 14,362/year)

**Source:** `backend/.env`, line 34

---

### "What legal approvals are needed?"
**Answer:**
1. Brazilian consumer law attorney review (CDC, LGPD)
2. Compliance officer approval
3. CEO / General Counsel sign-off
4. 30-day user notice before ToS changes

**Source:** `docs/legal/tos-annual-plans-diff.md`, line 750

---

## 📅 Timeline Reference

| Date | Milestone | Document Reference |
|------|-----------|-------------------|
| **Feb 7, 2026** | Documentation complete | This document |
| **Feb 10, 2026** | Legal firm selection | `tos-annual-plans-diff.md`, line 870 |
| **Feb 20, 2026** | Initial legal review | `tos-annual-plans-diff.md`, line 870 |
| **Feb 25, 2026** | Draft ToS amendments | `tos-annual-plans-diff.md`, line 870 |
| **Feb 28, 2026** | Internal approval | `tos-annual-plans-diff.md`, line 870 |
| **March 1, 2026** | User notification (30-day notice) | `tos-annual-plans-diff.md`, line 870 |
| **March 15, 2026** | ToS acceptance flow deployed | `tos-annual-plans-diff.md`, line 870 |
| **March 31, 2026** | Annual plans go live | `tos-annual-plans-diff.md`, line 870 |

---

## ✅ Pre-Launch Checklist

Use this checklist to verify readiness before production deployment.

### Legal & Compliance
- [ ] Brazilian consumer law attorney review complete
- [ ] LGPD compliance audit complete
- [ ] ToS amendments approved by legal team
- [ ] CEO / General Counsel sign-off obtained
- [ ] 30-day user notice sent (ToS changes)
- [ ] consumidor.gov.br registration verified

### Technical Implementation
- [ ] Backend API endpoints implemented (`/api/subscriptions/update-billing-period`)
- [ ] Frontend billing period toggle UI built
- [ ] Redis caching configured (development + production)
- [ ] Stripe price IDs created and configured
- [ ] Stripe webhooks configured and tested
- [ ] Pro-rata calculation logic tested (upgrade/downgrade)
- [ ] 7-day refund eligibility check implemented
- [ ] Feature flags working (`ENABLE_ANNUAL_PLANS`)

### Testing
- [ ] Unit tests passing (pro-rata, refund eligibility)
- [ ] Integration tests passing (Stripe, Redis)
- [ ] E2E tests passing (upgrade, downgrade, refund flows)
- [ ] Load testing complete (Redis performance)
- [ ] Security review complete (payment handling, data retention)

### Customer Communication
- [ ] Help Center updated with FAQ content
- [ ] Support team trained on refund/downgrade workflows
- [ ] Email templates configured (refund, downgrade, renewal reminders)
- [ ] Marketing materials prepared (pricing page, feature announcements)

### Monitoring & Support
- [ ] Refund request tracking dashboard configured
- [ ] Feature launch date alerts set (March 2026, April 2026)
- [ ] Uptime monitoring configured (72-hour threshold)
- [ ] Support ticket escalation workflows defined

### Final Approval
- [ ] Product team go/no-go decision
- [ ] Engineering team deployment approval
- [ ] Legal team final sign-off
- [ ] Executive leadership approval

---

## 🆘 Support Resources

### Internal Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| **Legal Team** | legal@smartlic.tech | ToS amendments, CDC compliance |
| **Compliance Officer** | compliance@smartlic.tech | LGPD, regulatory compliance |
| **Backend Lead** | dev-backend@smartlic.tech | API implementation, Redis |
| **Frontend Lead** | dev-frontend@smartlic.tech | UI/UX implementation |
| **DevOps Lead** | devops@smartlic.tech | Redis setup, Stripe webhooks |
| **Support Lead** | support-lead@smartlic.tech | Customer workflows, training |
| **Product Manager** | pm@smartlic.tech | Feature roadmap, prioritization |

### External Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| **Stripe Dashboard** | dashboard.stripe.com | Price IDs, webhooks, payments |
| **Redis Cloud** | redis.com | Redis instance management |
| **consumidor.gov.br** | consumidor.gov.br | Dispute resolution platform |
| **Brazilian CDC** | planalto.gov.br/ccivil_03/leis/l8078.htm | Consumer protection law |
| **LGPD** | planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm | Data protection law |

---

## 📝 Document Maintenance

### Version Control

All documentation is version-controlled in the Git repository:
- **Location:** `docs/` directory
- **Branch Strategy:** Feature branches for updates, merge to main after review
- **Commit Convention:** `docs: update annual subscription FAQ with new pricing`

### Review Schedule

| Document | Review Frequency | Next Review |
|----------|------------------|-------------|
| **Feature Documentation** | Quarterly | May 1, 2026 |
| **Legal Policy** | Annually | Feb 1, 2027 |
| **Customer FAQs** | Monthly | March 7, 2026 |
| **ToS Amendments** | As needed | After legal review |

### Update Triggers

Update documentation when:
- API endpoints change
- Pricing structure changes
- Legal requirements change (new laws, court rulings)
- Customer feedback identifies gaps or confusion
- Features launch (March 2026 proactive search, April 2026 AI analysis)

---

## 🎓 Onboarding Guide

### New Team Member? Start Here:

1. **Read This:** `docs/stories/STORY-171-documentation-summary.md` (10 min)
2. **Skim Your Role Section:** See "Quick Links by Role" above (5 min)
3. **Deep Dive:** Read the full document for your role (30-60 min)
4. **Ask Questions:** Contact the document owner (see Support Resources above)

### New Developer?

1. Read: `docs/features/annual-subscription.md` (architecture, API, database)
2. Review: `backend/.env` (environment configuration)
3. Set up: Local Redis instance
4. Test: Run existing unit tests for subscription logic
5. Build: Start with small feature (e.g., refund eligibility check)

### New Support Agent?

1. Read: `docs/support/faq-annual-plans.md` (all sections)
2. Review: `docs/legal/downgrade-policy.md` (refund policy, email templates)
3. Practice: Role-play common scenarios (refund request, downgrade request)
4. Shadow: Observe experienced agent handling annual plan tickets
5. Solo: Handle tickets with supervision for first week

---

## 🔗 Cross-References

### Related Stories
- **STORY-171 Track 1:** Frontend UI implementation
- **STORY-171 Track 2:** Backend API implementation
- **STORY-171 Track 3:** Testing (unit, integration, E2E)
- **STORY-172:** Proactive Search (annual-exclusive, March 2026)
- **STORY-173:** AI Edital Analysis (Sala de Guerra annual, April 2026)

### Related Documentation
- **Terms of Service:** `docs/legal/terms-of-service.md` (base document to be amended)
- **Privacy Policy:** `docs/legal/privacy-policy.md` (LGPD compliance, data retention)
- **Stripe Integration:** `docs/integrations/stripe.md` (if exists)
- **Redis Caching:** `docs/architecture/caching-strategy.md` (if exists)

---

## 📊 Metrics Dashboard (Post-Launch)

Track these metrics after annual plans launch:

| Metric | Target | Data Source |
|--------|--------|-------------|
| **7-Day Refund Rate** | <5% | Stripe + Supabase |
| **8+ Day Downgrade Rate** | <10% | Supabase `user_subscriptions` |
| **Annual Conversion Rate** | >15% | Monthly → Annual upgrades |
| **Support Ticket Volume** | Baseline + 20% (first week) | Support system |
| **Feature Delay Refunds** | 0 | Manual tracking |
| **Service Failure Refunds** | 0 | Uptime monitoring |
| **Customer Satisfaction** | >4.5/5 | Post-interaction surveys |

**Dashboard Location:** [TBD - Set up in analytics platform]

---

## 🚀 Quick Start Commands

### Developers

```bash
# Set up local environment
cd backend
cp .env .env.local  # Copy and update with local Redis
docker run -d -p 6379:6379 redis:latest  # Start local Redis

# Run backend
uvicorn main:app --reload

# Run tests
pytest --cov  # Check coverage (target: 70%+)

# Frontend
cd frontend
npm install
npm run dev

# Run E2E tests
npm run test:e2e
```

### DevOps

```bash
# Check Redis connection
redis-cli -u $REDIS_URL ping  # Should return PONG

# Test Stripe webhook
stripe listen --forward-to localhost:8000/webhooks/stripe

# Deploy feature flag
railway variables set ENABLE_ANNUAL_PLANS=true

# Check production logs
railway logs --tail
```

---

## 📧 Feedback

This documentation index is maintained by the Engineering Team. If you:
- Can't find information you need
- Notice outdated content
- Have suggestions for improvement

**Contact:** docs@smartlic.tech or create a GitHub issue with label `documentation`

---

**Last Updated:** 2026-02-07
**Maintained By:** Backend Team
**Version:** 1.0
**Next Review:** March 1, 2026 (before annual plans launch)
