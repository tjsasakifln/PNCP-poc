# Terms of Service - Annual Plans Amendments

**Document Type:** Legal Requirements Summary
**Purpose:** Outline required changes to Terms of Service for annual subscription plans
**Status:** Draft - Requires Legal Review
**Target Effective Date:** March 1, 2026
**Last Updated:** February 7, 2026

---

## ⚠️ IMPORTANT LEGAL NOTICE

This document is a **technical requirements summary** prepared by the engineering team. It is **NOT a legal document** and does **NOT constitute legal advice.

**REQUIRED ACTIONS BEFORE PRODUCTION:**
1. [ ] Review by qualified Brazilian consumer law attorney
2. [ ] LGPD (Lei Geral de Proteção de Dados) compliance audit
3. [ ] CDC (Código de Defesa do Consumidor) compliance verification
4. [ ] Approval by Legal & Compliance Team
5. [ ] Final review by CEO/General Counsel
6. [ ] User notification of ToS changes (30-day notice required)

**DO NOT deploy annual subscription feature to production until legal review is complete.**

---

## Overview of Required Changes

The introduction of annual subscription plans requires amendments to the following sections of SmartLic's Terms of Service:

1. **Billing & Payment Terms** - Add annual billing option and pricing structure
2. **Refund Policy** - Add 7-day CDC compliance provision
3. **Cancellation & Downgrade Policy** - Explain benefit retention after downgrade
4. **Feature Availability** - Define annual-exclusive features and early access
5. **Data Retention** - Clarify data retention during 7-day refund window
6. **Modification of Terms** - How ToS changes affect existing subscribers
7. **Dispute Resolution** - Add reference to consumidor.gov.br

---

## Section 1: Billing & Payment Terms

### Current Text (Monthly Only)

> **4.1 Subscription Plans**
>
> SmartLic offers three subscription tiers: Consultor Ágil, Máquina, and Sala de Guerra. All subscriptions are billed monthly in Brazilian Reais (BRL) and renew automatically on the same day each month unless canceled.
>
> **4.2 Payment Methods**
>
> We accept credit cards, debit cards, PIX, and boleto bancário. Payment is due at the time of subscription or renewal.

### Proposed Amendments (Add Annual Option)

> **4.1 Subscription Plans**
>
> SmartLic offers three subscription tiers: Consultor Ágil, Máquina, and Sala de Guerra. Subscriptions are available in two billing periods:
>
> - **Monthly Billing:** Charged monthly in Brazilian Reais (BRL) on the same day each month
> - **Annual Billing:** Charged annually in Brazilian Reais (BRL) on the anniversary of subscription
>
> Annual subscriptions receive a 20% discount compared to monthly billing (equivalent to 2.4 months free) plus exclusive features as described in Section 4.3.
>
> **4.2 Payment Methods**
>
> We accept credit cards, debit cards, PIX, and boleto bancário. Payment is due at the time of subscription or renewal.
>
> - **Monthly Plans:** First payment due at subscription, subsequent payments due monthly
> - **Annual Plans:** Full year payment due upfront at subscription, renewal payment due annually
>
> **4.3 Annual Subscription Exclusive Features**
>
> Annual subscribers receive access to exclusive features not available to monthly subscribers:
>
> - **Early Access:** New features available 2-4 weeks before monthly subscribers
> - **Proactive Search:** AI-powered automatic bid discovery with daily summaries (available March 2026)
> - **AI Edital Analysis (Sala de Guerra Annual Only):** Advanced AI analysis of bid documents with risk assessment (available April 2026)
>
> Feature availability dates are estimates and may be subject to reasonable delays. See Section 9.2 (Delayed Feature Refund Policy) for compensation in case of significant delays.

**Legal Review Points:**
- [ ] Verify pricing structure complies with Brazilian consumer protection laws
- [ ] Ensure feature availability disclaimers are sufficient
- [ ] Confirm payment timing language is clear and enforceable

---

## Section 2: Refund Policy (CDC Compliance)

### Current Text (Pro-Rated Refunds)

> **5.1 Refund Policy**
>
> Monthly subscriptions may be canceled at any time with a pro-rated refund for unused time in the current billing period.

### Proposed Amendments (Add 7-Day CDC Window)

> **5.1 Refund Policy**
>
> **5.1.1 Monthly Subscriptions**
>
> Monthly subscriptions may be canceled at any time with a pro-rated refund for unused time in the current billing period. Refunds are processed within 5-10 business days to the original payment method.
>
> **5.1.2 Annual Subscriptions - 7-Day Full Refund (CDC Article 49)**
>
> In accordance with Brazilian Consumer Defense Code (Lei 8.078/1990, Article 49), annual subscription purchasers may request a full refund within **7 (seven) calendar days** of the date of purchase, without penalty and without needing to provide a reason.
>
> - **Calculation of 7-Day Period:** Begins at the date and time of successful payment (invoice.paid event)
> - **Refund Amount:** 100% of the annual subscription fee
> - **Processing Time:** Refund issued immediately upon request; funds returned to original payment method within 5-10 business days
> - **Access:** Subscription and access to service revoked immediately upon refund
> - **Data Retention:** User data retained for 30 days to allow re-subscription without data loss (see Section 7.3)
>
> **5.1.3 Annual Subscriptions - After 7 Days (No Monetary Refund)**
>
> Annual subscriptions purchased more than 7 days ago are **not eligible for monetary refunds** unless covered by Section 5.2 (Exceptional Circumstances).
>
> Users who wish to cancel after the 7-day window will:
> - **Retain all annual benefits** (early access, proactive search, AI analysis) until the end of the current annual period
> - **Automatically convert to monthly billing** at the conclusion of the annual period, unless the subscription is fully canceled
> - **Not receive a pro-rated refund** for unused annual time
>
> This policy aligns with industry standards for SaaS subscriptions while ensuring users extract full value from their annual commitment.
>
> **5.2 Exceptional Circumstances - Full Refund Anytime**
>
> Annual subscribers are eligible for a full refund regardless of purchase date in the following circumstances:
>
> **5.2.1 Service Level Failure**
> - SmartLic service is unavailable for more than 72 consecutive hours
> - Refund calculated on a pro-rated basis for remaining annual time
> - Excludes scheduled maintenance with 7+ days advance notice
>
> **5.2.2 Delayed Features**
> - An annual-exclusive feature (proactive search, AI analysis) is delayed more than 6 months past the stated availability date
> - User may choose: (a) full refund + subscription cancellation, OR (b) full refund + continuation at monthly rate until feature launches
>
> **5.2.3 Unauthorized Charges**
> - Fraudulent charge or billing error
> - Full refund processed within 24 hours of confirmation
> - Fraud investigation initiated per Section 10.4 (Security & Fraud Prevention)
>
> **5.3 Refund Request Process**
>
> To request a refund:
> 1. **Within 7 days of annual purchase:** Click "Request Refund" in Account Settings → Billing, OR contact suporte@smartlic.tech
> 2. **Exceptional circumstances:** Email suporte@smartlic.tech with details and supporting documentation
>
> All refund requests are reviewed and processed within 2 business hours during business hours (9 AM - 6 PM BRT, Monday-Friday).

**Legal Review Points:**
- [ ] Verify 7-day CDC window calculation methodology (calendar vs business days)
- [ ] Confirm "service level failure" definitions are reasonable and measurable
- [ ] Ensure "feature delay" thresholds (6 months) are fair and defensible
- [ ] Review unauthorized charge procedures for compliance with payment card industry standards

---

## Section 3: Cancellation & Downgrade Policy

### Current Text (Immediate Cancellation)

> **6.1 Cancellation**
>
> You may cancel your subscription at any time from Account Settings. Cancellation takes effect at the end of the current billing period. You will retain access until the end of the paid period.

### Proposed Amendments (Add Downgrade Process)

> **6.1 Cancellation**
>
> **6.1.1 Monthly Subscriptions**
>
> You may cancel your monthly subscription at any time from Account Settings. Cancellation takes effect immediately with a pro-rated refund for unused time in the current billing period (see Section 5.1.1).
>
> **6.1.2 Annual Subscriptions**
>
> You may cancel your annual subscription at any time, subject to the refund policy in Section 5.1.2-5.1.3:
>
> - **Within 7 days of purchase:** Full refund + immediate cancellation
> - **After 7 days:** No refund, but subscription remains active until the end of the current annual period
>
> To prevent automatic renewal, cancellation must be requested at least 24 hours before the annual renewal date.
>
> **6.2 Downgrade: Annual to Monthly**
>
> Annual subscribers may request to downgrade to monthly billing at any time:
>
> **6.2.1 Downgrade Within 7 Days of Purchase**
> - If requested within 7 days, user should instead request a full refund (Section 5.1.2) and re-subscribe to a monthly plan
>
> **6.2.2 Downgrade After 7 Days**
> - No monetary refund provided
> - User retains all annual-exclusive features (early access, proactive search, AI analysis) until the end of the current annual period
> - Subscription automatically converts to monthly billing at the end of the annual period
> - Monthly billing begins at the standard monthly rate for the user's plan tier
> - User loses access to annual-exclusive features when converting to monthly
>
> **Example Timeline:**
> - Jan 1, 2026: Subscribe to Consultor Ágil Annual (R$ 2,851/year)
> - March 1, 2026: Request downgrade to monthly (60 days after purchase)
> - March 1 - Dec 31, 2026: Retain annual benefits (early access, proactive search)
> - Jan 1, 2027: Automatic conversion to monthly billing (R$ 297/month), annual benefits revoked
>
> To request a downgrade, use the "Change to Monthly" button in Account Settings → Billing, or contact suporte@smartlic.tech.
>
> **6.3 Upgrade: Monthly to Annual**
>
> Monthly subscribers may upgrade to annual billing at any time:
>
> - Unused monthly time is credited on a pro-rated basis toward the annual charge
> - Annual-exclusive features activate immediately
> - Next billing date resets to 12 months from upgrade date
>
> **Example:**
> - Current plan: Consultor Ágil Monthly (R$ 297/month)
> - 15 days remaining in current monthly period
> - Pro-rated credit: R$ 148.50 (15/30 × 297)
> - You pay: R$ 2,851 - R$ 148.50 = R$ 2,702.50
> - Next billing date: 12 months from today

**Legal Review Points:**
- [ ] Verify downgrade process complies with Brazilian consumer protection laws
- [ ] Confirm benefit retention until period end is clearly communicated
- [ ] Ensure upgrade pro-rata calculations are transparent and accurate
- [ ] Review auto-renewal notice requirements (24-hour vs 7-day vs 30-day)

---

## Section 4: Feature Availability & Early Access

### Current Text (No Early Access)

> **7.1 Service Features**
>
> SmartLic provides procurement opportunity discovery, filtering, reporting, and notifications based on your subscription tier. Features and functionality may be updated from time to time.

### Proposed Amendments (Add Annual-Exclusive Features)

> **7.1 Service Features**
>
> SmartLic provides procurement opportunity discovery, filtering, reporting, and notifications based on your subscription tier and billing period.
>
> **7.1.1 Core Features (All Plans)**
>
> Available to all subscribers regardless of billing period:
> - Unlimited searches across PNCP database
> - Excel/CSV export of results
> - Email notifications for new opportunities
> - Saved searches (quantity varies by plan tier)
>
> **7.1.2 Annual-Exclusive Features**
>
> Available only to annual subscribers:
>
> **Early Access (All Annual Plans):**
> - New features released 2-4 weeks before monthly subscribers
> - Opportunity to provide feedback during early access period
> - Early access period may vary by feature complexity
>
> **Proactive Search (All Annual Plans - Available March 2026):**
> - AI-powered automatic bid discovery based on saved search criteria
> - Daily email summaries of relevant opportunities
> - Customizable delivery frequency and filters
>
> **AI Edital Analysis (Sala de Guerra Annual Only - Available April 2026):**
> - Advanced AI analysis of bid documents (editais)
> - Risk assessment and win probability scoring
> - Compliance checklist generation
> - Competitive analysis
>
> **7.1.3 Feature Availability Dates**
>
> Availability dates for upcoming features are estimates based on current development plans. SmartLic will make commercially reasonable efforts to meet stated dates but cannot guarantee exact launch timing.
>
> - **Acceptable Delay:** Up to 6 months past stated availability date
> - **Significant Delay:** More than 6 months past stated availability date (triggers refund eligibility per Section 5.2.2)
>
> **7.1.4 Feature Updates & Changes**
>
> SmartLic reserves the right to:
> - Add new features to any plan tier at any time
> - Modify or discontinue features with 30 days' notice
> - Convert annual-exclusive features to monthly plan features after 12 months (early access period ends)
>
> If an annual-exclusive feature becomes available to monthly subscribers within 12 months of your annual purchase, you are entitled to a pro-rated refund for the remaining annual period (calculated as: [annual_price - monthly_price × 12] × [months_remaining / 12]).

**Legal Review Points:**
- [ ] Verify "acceptable delay" window (6 months) is reasonable
- [ ] Ensure feature modification/discontinuation notice period complies with consumer laws
- [ ] Confirm pro-rated refund calculation for feature de-exclusivity is fair
- [ ] Review whether "commercially reasonable efforts" language is sufficient

---

## Section 5: Data Retention & Privacy

### Current Text (General Data Retention)

> **8.1 Data Retention**
>
> Upon cancellation, your data is retained for 30 days to allow re-subscription without data loss. After 30 days, data is permanently deleted.

### Proposed Amendments (Clarify Refund Window Retention)

> **8.1 Data Retention**
>
> **8.1.1 Standard Cancellation (Monthly Plans & Annual After 7 Days)**
>
> Upon cancellation, your data is retained for 30 days to allow re-subscription without data loss:
>
> - **Saved searches:** Read-only access for 30 days
> - **Search history:** Read-only access for 30 days
> - **Generated reports:** Available for download for 30 days
> - **Account information:** Login available, subscription features disabled
>
> After 30 days, all data is permanently deleted in accordance with LGPD (Lei Geral de Proteção de Dados).
>
> **8.1.2 7-Day Refund Window (Annual Plans)**
>
> If you request a full refund within 7 days of annual subscription purchase:
>
> - Your subscription and access are revoked immediately
> - Your data is retained for 30 days (same as Section 8.1.1)
> - You may re-subscribe within 30 days to restore full access without data loss
>
> **8.1.3 Data Export**
>
> You may export your data at any time via Account Settings → Export Data. This option remains available:
> - During active subscription
> - During 30-day retention period after cancellation
> - During 7-day refund window (before refund request)
>
> Exported data is provided in CSV and JSON formats.
>
> **8.1.4 LGPD Compliance**
>
> All data retention, processing, and deletion practices comply with Brazilian LGPD (Lei Geral de Proteção de Dados, Lei 13.709/2018). For details, see our Privacy Policy at smartlic.tech/privacy.

**Legal Review Points:**
- [ ] Verify LGPD compliance for 30-day retention period
- [ ] Confirm data export formats meet LGPD "data portability" requirements
- [ ] Ensure immediate access revocation upon refund complies with consumer laws
- [ ] Review whether 30-day retention applies to personal data vs usage data

---

## Section 6: Modification of Terms

### Current Text (30-Day Notice)

> **9.1 Changes to Terms**
>
> We may modify these Terms at any time with 30 days' notice. Continued use of the service after changes take effect constitutes acceptance of the new Terms.

### Proposed Amendments (Grandfather Clause for Pricing)

> **9.1 Changes to Terms**
>
> **9.1.1 General Modifications**
>
> We may modify these Terms at any time with 30 days' notice via:
> - Email notification to your registered email address
> - Banner notification in the SmartLic application
> - Publication at smartlic.tech/terms
>
> Continued use of the service after changes take effect constitutes acceptance of the new Terms.
>
> **9.1.2 Pricing Changes**
>
> Price changes are announced with at least 30 days' notice and apply as follows:
>
> **Monthly Subscriptions:**
> - Price changes take effect at your next monthly billing date (minimum 30 days after announcement)
> - You may cancel before the price increase to avoid the new rate
>
> **Annual Subscriptions (Grandfather Clause):**
> - Your annual price is **locked in** for the duration of your subscription
> - Price increases do NOT affect your current annual period
> - Price increases apply to your first renewal after the announcement
> - You will be notified of the new renewal price at least 30 days before your renewal date
>
> **Example:**
> - You subscribe on Feb 1, 2026 at R$ 2,851/year
> - We announce price increase to R$ 3,200/year on July 1, 2026
> - Your first renewal (Feb 1, 2027) is still R$ 2,851
> - Your second renewal (Feb 1, 2028) is R$ 3,200 (if you don't cancel)
>
> **9.1.3 Material Changes**
>
> Material changes to Terms (changes to refund policy, data retention, core features) require re-acceptance:
> - You will be prompted to accept updated Terms upon next login
> - If you decline, your subscription will be canceled with a pro-rated refund (monthly) or full refund if within 7 days (annual)
>
> **9.1.4 Non-Material Changes**
>
> Non-material changes (clarifications, formatting, minor corrections) do not require re-acceptance and take effect after 30 days' notice.

**Legal Review Points:**
- [ ] Verify grandfather clause for annual pricing is enforceable
- [ ] Confirm 30-day notice period meets Brazilian consumer law requirements
- [ ] Ensure "material change" definition is clear and comprehensive
- [ ] Review whether forced re-acceptance for material changes is compliant

---

## Section 7: Dispute Resolution

### Current Text (Court Jurisdiction)

> **10.1 Governing Law**
>
> These Terms are governed by Brazilian law. Disputes shall be resolved in the Comarca de São Paulo, Brazil.

### Proposed Amendments (Add consumidor.gov.br Option)

> **10.1 Governing Law**
>
> These Terms are governed by Brazilian law, including:
> - Brazilian Consumer Defense Code (Lei 8.078/1990)
> - Brazilian Civil Code (Lei 10.406/2002)
> - Marco Civil da Internet (Lei 12.965/2014)
> - LGPD - Lei Geral de Proteção de Dados (Lei 13.709/2018)
>
> **10.2 Dispute Resolution**
>
> We encourage users to contact suporte@smartlic.tech first to resolve any disputes informally. If informal resolution fails, you may pursue the following options:
>
> **10.2.1 Consumidor.gov.br (Preferred)**
>
> For consumer disputes, we recommend using the Brazilian government's official dispute resolution platform:
> - Website: consumidor.gov.br
> - Free mediation service
> - Average resolution time: 7 days
> - SmartLic is registered and responds to all consumidor.gov.br complaints within 5 business days
>
> **10.2.2 Juizado Especial Cível (Small Claims Court)**
>
> For disputes involving amounts up to R$ 20,000:
> - No attorney required
> - Low filing fees
> - Fast resolution (typically 60-90 days)
>
> **10.2.3 Standard Court Jurisdiction**
>
> For disputes not resolved through the above methods or exceeding small claims thresholds:
> - Jurisdiction: Comarca de São Paulo, Brazil
> - Governing Law: Brazilian federal and São Paulo state law
> - Consumer disputes may be filed in the consumer's local jurisdiction per CDC Article 101
>
> **10.3 Class Action Waiver (Not Applicable to Brazilian Consumers)**
>
> Brazilian consumer protection law (CDC) permits collective actions ("ações coletivas"). Nothing in these Terms waives your right to participate in collective consumer actions.

**Legal Review Points:**
- [ ] Verify consumidor.gov.br registration is complete and active
- [ ] Confirm jurisdiction provisions comply with CDC Article 101 (consumer's local jurisdiction)
- [ ] Ensure class action language does not conflict with Brazilian collective action rights
- [ ] Review LGPD reference is accurate and complete

---

## Section 8: Additional Provisions for Annual Plans

### New Section (Not in Current ToS)

> **11. Annual Subscription Specific Provisions**
>
> **11.1 Billing Cycle**
>
> Annual subscriptions bill on a yearly cycle:
> - First payment: Due immediately upon subscription
> - Subsequent payments: Due on the anniversary of the subscription date
> - Example: Subscribe on Feb 15, 2026 → Next billing Feb 15, 2027
>
> **11.2 Pro-Rata Calculations**
>
> When upgrading from monthly to annual:
> - Unused monthly time is calculated on a daily basis (days_remaining / days_in_period × monthly_price)
> - Credit is applied to the annual charge immediately
> - Example: 15 days remaining in a 30-day monthly period for R$ 297 plan = R$ 148.50 credit
>
> **11.3 Auto-Renewal Notice**
>
> Annual subscriptions auto-renew unless canceled:
> - **First notice:** 30 days before renewal (informational)
> - **Second notice:** 7 days before renewal (renewal amount and date)
> - **Final notice:** 24 hours before renewal (last chance to cancel)
>
> To cancel auto-renewal, use Account Settings → Billing → Cancel Auto-Renewal at least 24 hours before renewal date.
>
> **11.4 Payment Failure**
>
> If annual renewal payment fails:
> - **Day 0:** Payment attempted, email notification sent
> - **Day 3:** Second payment attempt, email notification
> - **Day 7:** Third payment attempt, email + SMS notification
> - **Day 14:** Final payment attempt, account suspended if failed
> - **Day 30:** Subscription canceled, data retention begins (30 days)
>
> Update your payment method in Account Settings → Billing to avoid suspension.
>
> **11.5 Currency and Taxes**
>
> All annual subscription prices are listed in Brazilian Reais (BRL) and are inclusive of any applicable taxes:
> - Prices include Brazilian sales tax when applicable
> - International customers may be subject to additional local taxes
> - Prices exclude payment processing fees (charged by payment processor, not SmartLic)
>
> **11.6 No Partial Periods**
>
> Annual subscriptions are sold in 12-month increments only. We do not offer 6-month or other partial annual periods.

**Legal Review Points:**
- [ ] Verify auto-renewal notice timing complies with Brazilian auto-renewal laws
- [ ] Confirm payment failure timeline is reasonable and clearly communicated
- [ ] Ensure tax disclosure is accurate (consult with Brazilian tax attorney)
- [ ] Review whether pro-rata calculation methodology is fair and transparent

---

## Implementation Checklist

Before deploying annual subscription feature:

### Legal Review
- [ ] Brazilian consumer law attorney review (CDC compliance)
- [ ] LGPD compliance audit (data retention during refund window)
- [ ] Tax compliance review (annual billing, cross-border if applicable)
- [ ] Terms of Service updated and approved by legal team
- [ ] Privacy Policy updated (if data retention practices change)

### User Communication
- [ ] Existing users notified of ToS changes (30-day notice)
- [ ] ToS acceptance flow implemented for material changes
- [ ] Help Center / FAQ updated with annual plan details
- [ ] Support team trained on refund and downgrade policies
- [ ] Email templates created for:
  - 7-day refund confirmation
  - Downgrade confirmation
  - Annual renewal reminders (30d, 7d, 24h)
  - Payment failure notifications

### Technical Implementation
- [ ] 7-day refund eligibility check implemented
- [ ] Pro-rata calculation logic tested
- [ ] Annual-exclusive feature flags working
- [ ] Stripe webhook handling for annual subscriptions
- [ ] Data retention during refund window tested
- [ ] Auto-renewal notice emails scheduled
- [ ] consumidor.gov.br integration (if available via API)

### Compliance Monitoring
- [ ] Refund request tracking (7-day vs 8+ day)
- [ ] Feature launch date monitoring (trigger refunds if 6+ month delay)
- [ ] Service uptime monitoring (trigger refunds if 72+ hour outage)
- [ ] Quarterly compliance audits scheduled

---

## Open Legal Questions

The following questions require input from legal counsel:

1. **7-Day CDC Window:**
   - Does the 7-day window start from payment success or service activation?
   - Should we offer a 24-hour grace period (making it effectively 8 days) for customer satisfaction?
   - What constitutes "use" of the service for CDC purposes (does logging in = "use")?

2. **Feature Delay Compensation:**
   - Is 6 months a legally defensible "acceptable delay" period?
   - Should we offer partial refunds for delays of 3-6 months?
   - What if a feature is delayed indefinitely - full refund or conversion to monthly?

3. **Price Lock (Grandfather Clause):**
   - Can we enforce price locks for annual subscriptions in Brazil?
   - What if our costs increase significantly (e.g., 100% inflation) - can we raise prices mid-contract?
   - How long can a price lock last (1 year, 2 years, indefinitely)?

4. **Auto-Renewal Disclosure:**
   - Is 24-hour advance notice sufficient for auto-renewal cancellation?
   - Should we require explicit opt-in for auto-renewal (vs default opt-in)?
   - Do we need a separate "auto-renewal agreement" or is ToS inclusion sufficient?

5. **Dispute Resolution:**
   - Does our consumidor.gov.br language waive any mandatory court rights?
   - Can we specify São Paulo jurisdiction for annual contracts, or must we allow consumer's local jurisdiction always?
   - Is arbitration permitted for annual B2C SaaS contracts in Brazil?

6. **LGPD Data Retention:**
   - Does 30-day retention apply to all data types or only account data?
   - Can we retain anonymized usage analytics after refund/cancellation?
   - What constitutes proper "data export" under LGPD for SaaS?

---

## Recommended Legal Counsel

**Firm Specialization Needed:**
- Brazilian consumer law (CDC expertise)
- SaaS / technology contracts
- LGPD / data privacy
- Subscription billing models
- E-commerce regulations

**Recommended Firms (Placeholder - To Be Researched):**
1. [Brazilian Tech Law Firm 1]
2. [Consumer Law Specialist 2]
3. [LGPD Compliance Firm 3]

**Budget Estimate:** R$ 15,000 - R$ 30,000 for comprehensive ToS review and amendments

---

## Timeline

| Milestone | Target Date | Owner |
|-----------|-------------|-------|
| **Legal firm selection** | Feb 10, 2026 | CEO / Legal |
| **Initial legal review** | Feb 20, 2026 | External counsel |
| **Draft ToS amendments** | Feb 25, 2026 | Legal + Engineering |
| **Internal review & approval** | Feb 28, 2026 | CEO / General Counsel |
| **User notification (30-day notice)** | March 1, 2026 | Marketing / Compliance |
| **ToS acceptance flow deployed** | March 15, 2026 | Engineering |
| **Annual plans go live** | March 31, 2026 | Product / Engineering |

---

## Related Documentation

- **Feature Spec:** `docs/features/annual-subscription.md`
- **Refund Policy:** `docs/legal/downgrade-policy.md`
- **Support FAQs:** `docs/support/faq-annual-plans.md`
- **Story:** `docs/stories/STORY-171-*.md`
- **Current ToS:** `docs/legal/terms-of-service.md` (if exists)
- **Current Privacy Policy:** `docs/legal/privacy-policy.md` (if exists)

---

**Document Owner:** Legal & Compliance Team
**Technical Contact:** Backend Team (Subscription API)
**Last Updated:** 2026-02-07
**Version:** 1.0 (Draft)
**Status:** ⚠️ Pending Legal Review - NOT APPROVED FOR PRODUCTION USE

---

## Approval Sign-Off

- [ ] **Legal Counsel Approval:** _______________________ Date: _______
- [ ] **General Counsel / CEO Approval:** _______________________ Date: _______
- [ ] **Compliance Officer Approval:** _______________________ Date: _______
- [ ] **Engineering Lead Acknowledgment:** _______________________ Date: _______

**DO NOT PROCEED WITH ANNUAL SUBSCRIPTION DEPLOYMENT UNTIL ALL APPROVALS ARE OBTAINED.**
