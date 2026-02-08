# Refund and Downgrade Policy - Annual Subscription Plans

**Effective Date:** March 1, 2026
**Last Updated:** February 7, 2026
**Governing Law:** Brazilian Consumer Defense Code (CDC - Lei 8.078/1990)

---

## Overview

This policy outlines the refund and downgrade procedures for SmartLic annual subscription plans in compliance with Brazilian consumer protection laws.

**Key Principles:**
1. **7-Day Full Refund Window** - Mandatory under Brazilian CDC Article 49
2. **No Refund After 7 Days** - Industry standard for SaaS, but benefits retained
3. **Exceptional Circumstances** - Full refund anytime for service failures
4. **Transparent Communication** - Clear expectations set at purchase

---

## 7-Day Full Refund (CDC Compliance)

### Legal Basis

**Brazilian Consumer Defense Code (Lei 8.078/1990), Article 49:**
> "The consumer may withdraw from a contract, without any penalty and with full reimbursement of any amounts paid, within 7 (seven) days from signature or receipt of the product or service, whenever the contract was concluded outside the commercial establishment, especially by telephone or at home."

This applies to all online purchases including SaaS subscriptions.

### Eligibility

**Who Qualifies:**
- Any customer who purchased an annual subscription
- Within 7 calendar days of the purchase date
- Regardless of reason (no justification required)

**Purchase Date Definition:**
- Date of successful payment (Stripe `invoice.paid` event timestamp)
- Not the date of account creation or trial start

### Refund Process

**Customer Initiated:**
1. Customer contacts support via:
   - Email: suporte@smartlic.tech
   - In-app support chat
   - Account settings → "Request Refund" button (visible only during 7-day window)

2. Support verifies eligibility:
   ```sql
   SELECT
     created_at,
     CURRENT_DATE - DATE(created_at) AS days_since_purchase
   FROM user_subscriptions
   WHERE user_id = 'xxx' AND billing_period = 'annual';
   ```

3. If eligible (≤7 days):
   - Issue full refund via Stripe API
   - Cancel subscription immediately
   - Revoke annual-exclusive features
   - Send confirmation email

**Timeline:**
- **Request to Approval:** Same business day (target: < 2 hours)
- **Approval to Refund Processing:** Immediate (Stripe API call)
- **Refund to Customer's Account:** 5-10 business days (bank/card issuer dependent)

### What Customer Receives

| Item | Amount | Timing |
|------|--------|--------|
| **Full Subscription Refund** | R$ 2,851 (Consultor Ágil) <br> R$ 5,731 (Máquina) <br> R$ 14,362 (Sala de Guerra) | 5-10 business days |
| **Access to Service** | Revoked immediately | Same day |
| **Previously Generated Reports** | Retained (read-only) | Permanent |

**Note:** Customer data (saved searches, search history) is retained for 30 days to allow re-subscription without data loss.

### Technical Implementation

```python
# backend/api/subscriptions/refund.py
from datetime import datetime, timedelta
import stripe

async def process_refund_request(user_id: str, reason: str = "requested_by_customer"):
    # 1. Fetch subscription
    subscription = await db.fetch_one("""
        SELECT
            stripe_subscription_id,
            stripe_customer_id,
            created_at,
            billing_period
        FROM user_subscriptions
        WHERE user_id = $1 AND billing_period = 'annual'
    """, user_id)

    if not subscription:
        raise ValueError("No annual subscription found")

    # 2. Check 7-day window
    purchase_date = subscription['created_at']
    days_since_purchase = (datetime.now() - purchase_date).days

    if days_since_purchase > 7:
        raise RefundWindowExpiredError(
            f"Refund window expired ({days_since_purchase} days since purchase). "
            "See downgrade policy for alternatives."
        )

    # 3. Retrieve latest invoice
    invoices = stripe.Invoice.list(
        subscription=subscription['stripe_subscription_id'],
        limit=1
    )
    latest_invoice = invoices.data[0]

    # 4. Issue refund
    refund = stripe.Refund.create(
        charge=latest_invoice.charge,
        amount=latest_invoice.amount_paid,  # Full amount
        reason=reason,
        metadata={
            'user_id': user_id,
            'refund_type': '7_day_cdc_compliance'
        }
    )

    # 5. Cancel subscription immediately
    stripe.Subscription.delete(subscription['stripe_subscription_id'])

    # 6. Update database
    await db.execute("""
        UPDATE user_subscriptions
        SET
            status = 'canceled',
            cancel_at_period_end = FALSE,
            canceled_at = NOW(),
            cancellation_reason = $1
        WHERE user_id = $2
    """, reason, user_id)

    # 7. Invalidate cache
    await redis.delete(f"features:{user_id}")
    await redis.delete(f"subscription:{user_id}")

    # 8. Send confirmation email
    await send_email(
        to=user_email,
        template="refund_confirmation",
        data={
            "refund_amount": latest_invoice.amount_paid / 100,
            "refund_timeline": "5-10 business days",
            "data_retention": "30 days"
        }
    )

    return {
        "success": True,
        "refund_id": refund.id,
        "amount": refund.amount / 100,
        "status": refund.status
    }
```

---

## Downgrade After 7 Days (No Refund)

### Policy Overview

**8+ Days After Purchase:**
- **No monetary refund offered**
- **Annual benefits retained** until the end of the current annual period
- **Automatic conversion** to monthly billing after annual period expires

**Rationale:**
- Industry standard for SaaS subscriptions
- Customer has already benefited from early access and other exclusive features
- Allows customers to extract full value from their purchase

### Downgrade Process

**Customer Initiated:**
1. Customer contacts support or uses "Change to Monthly" button in account settings
2. System verifies purchase date (must be 8+ days)
3. No refund issued, but subscription updated:
   - `billing_period` changed to `monthly` in database
   - Stripe subscription **not immediately changed** (keeps current price until period end)
   - `cancel_at_period_end = FALSE` (ensures continuity)
   - New monthly price ID scheduled for next billing cycle

4. Customer receives confirmation email:
   > "Your subscription will convert to monthly billing on {current_period_end}. Until then, you'll continue to enjoy all annual plan benefits including early access and proactive search. Your new monthly rate will be R$ {monthly_price}/month starting {next_billing_date}."

### What Customer Retains

**Until End of Annual Period:**
- ✨ Early Access to new features
- 🎯 Proactive Search (if launched)
- 🤖 AI Edital Analysis (Sala de Guerra annual only, if launched)
- All previously generated reports
- Saved searches and search history

**After Annual Period Expires:**
- Automatic switch to monthly billing at standard monthly rate
- Loss of annual-exclusive features (early access, proactive search, AI analysis)
- Core plan features remain based on plan tier (Consultor / Máquina / Sala de Guerra)

### Timeline Example

| Event | Date | Action |
|-------|------|--------|
| **Annual Purchase** | Jan 1, 2026 | R$ 2,851 charged for Consultor Ágil annual |
| **Downgrade Request** | Feb 15, 2026 (45 days later) | Customer requests monthly billing |
| **Request Processed** | Feb 15, 2026 | Database updated, no immediate Stripe change |
| **Benefits Continue** | Feb 15 - Dec 31, 2026 | Customer keeps annual benefits (early access, etc.) |
| **Auto-Convert to Monthly** | Jan 1, 2027 | Charged R$ 297/month, annual benefits revoked |

### Technical Implementation

```python
# backend/api/subscriptions/downgrade.py
async def downgrade_to_monthly(user_id: str):
    # 1. Fetch subscription
    subscription = await db.fetch_one("""
        SELECT
            stripe_subscription_id,
            created_at,
            current_period_end,
            billing_period
        FROM user_subscriptions
        WHERE user_id = $1
    """, user_id)

    # 2. Check if already monthly
    if subscription['billing_period'] == 'monthly':
        raise ValueError("Already on monthly billing")

    # 3. Check 7-day window (must be expired)
    days_since_purchase = (datetime.now() - subscription['created_at']).days
    if days_since_purchase <= 7:
        raise ValueError(
            "You're within the 7-day refund window. "
            "Please request a full refund instead of downgrading."
        )

    # 4. Get monthly price ID for current plan
    plan_id = await db.fetch_val("""
        SELECT plan_id FROM user_subscriptions WHERE user_id = $1
    """, user_id)
    monthly_price_id = PLAN_PRICE_IDS[plan_id]['monthly']

    # 5. Schedule change at period end (don't prorate)
    stripe.Subscription.modify(
        subscription['stripe_subscription_id'],
        items=[{
            'id': subscription['stripe_subscription_item_id'],
            'price': monthly_price_id
        }],
        proration_behavior='none',  # No immediate charge/refund
        billing_cycle_anchor='unchanged'  # Keep current period end
    )

    # 6. Update database
    await db.execute("""
        UPDATE user_subscriptions
        SET
            billing_period = 'monthly',
            updated_at = NOW()
        WHERE user_id = $1
    """, user_id)

    # 7. Invalidate cache (but features won't change until period end)
    await redis.delete(f"features:{user_id}")

    # 8. Send confirmation email
    await send_email(
        to=user_email,
        template="downgrade_confirmation",
        data={
            "current_period_end": subscription['current_period_end'],
            "monthly_price": PLAN_PRICES[plan_id]['monthly'],
            "benefits_retained": [
                "Early access",
                "Proactive search",
                "AI edital analysis (Sala de Guerra only)"
            ]
        }
    )

    return {
        "success": True,
        "billing_period": "monthly",
        "effective_date": subscription['current_period_end'],
        "benefits_until": subscription['current_period_end']
    }
```

---

## Exceptional Circumstances (Full Refund Anytime)

### Service Level Failures

**Condition:** Service downtime exceeding 72 consecutive hours

**Eligibility:**
- Any annual subscriber affected by the outage
- Downtime must be confirmed by internal monitoring (UptimeRobot, Pingdom)
- Excludes scheduled maintenance (notified 7+ days in advance)

**Refund Calculation:**
```python
# Prorated refund based on remaining annual period
days_remaining = (current_period_end - datetime.now()).days
daily_rate = annual_price / 365
refund_amount = daily_rate * days_remaining
```

**Example:**
- Sala de Guerra annual: R$ 14,362/year
- 180 days remaining in annual period
- Downtime: 75 hours (exceeds 72-hour threshold)
- Refund: (14,362 / 365) × 180 = R$ 7,076.71

---

### Feature Delay Beyond Promised Date

**Condition:** Promised feature delayed more than 6 months past stated availability date

**Eligible Features:**
- 🎯 Proactive Search (promised March 2026)
- 🤖 AI Edital Analysis (promised April 2026)

**Example Scenario:**
- Customer purchased annual plan in February 2026 for early access to "Proactive Search" (stated availability: March 2026)
- Feature is delayed to October 2026 (7 months after promised date)
- Customer qualifies for full annual refund

**Refund Type:**
- Full annual subscription refund
- Customer can choose to:
  1. Accept refund + cancel subscription, OR
  2. Accept refund + continue subscription at monthly rate until feature launches

**Prevention:**
- Conservative launch date estimates
- Monthly progress updates on upcoming features
- Early warning (60 days before promised date) if delays anticipated

---

### Unauthorized Charges / Fraud

**Condition:**
- Charge made without customer authorization
- Fraudulent use of payment method
- Duplicate charges

**Eligibility:**
- Immediate full refund regardless of purchase date
- Subscription canceled immediately
- Fraud investigation initiated

**Process:**
1. Customer reports unauthorized charge
2. Payment method verification (last 4 digits, billing address)
3. Stripe fraud analysis (IP, device fingerprint, behavioral patterns)
4. If confirmed fraudulent:
   - Full refund within 24 hours
   - Account suspended pending investigation
   - Law enforcement notified if necessary

---

## Communication Templates

### 7-Day Refund Confirmation Email

**Subject:** Refund Confirmed - SmartLic Annual Subscription

```
Olá {customer_name},

Your refund request has been approved.

**Refund Details:**
- Amount: R$ {refund_amount}
- Processing Time: 5-10 business days
- Refund Method: Original payment method

**Account Status:**
- Subscription: Canceled immediately
- Access: Revoked
- Data Retention: Saved for 30 days (re-subscribe anytime to restore)

If you change your mind within 30 days, you can reactivate your annual subscription and pick up right where you left off.

Questions? Reply to this email or contact suporte@smartlic.tech.

Obrigado,
Equipe SmartLic
```

---

### Downgrade Confirmation Email (8+ Days)

**Subject:** Subscription Updated - Converting to Monthly Billing

```
Olá {customer_name},

Your subscription has been updated to convert to monthly billing.

**What This Means:**
- **Until {current_period_end}:** You'll continue to enjoy all annual benefits:
  - ✨ Early access to new features
  - 🎯 Proactive search (launching March 2026)
  - 🤖 AI edital analysis (Sala de Guerra only, launching April 2026)

- **Starting {next_billing_date}:**
  - You'll be charged R$ {monthly_price}/month
  - Annual-exclusive benefits will no longer be available
  - Core plan features ({plan_name}) remain active

**No Action Required**
Your payment method on file will be charged automatically on {next_billing_date}.

Questions? Reply to this email or contact suporte@smartlic.tech.

Obrigado,
Equipe SmartLic
```

---

### Service Failure Refund Email

**Subject:** Service Credit - Apology for Recent Downtime

```
Olá {customer_name},

We sincerely apologize for the recent service disruption that affected your access to SmartLic.

**Incident Summary:**
- Duration: {downtime_hours} hours ({downtime_start} - {downtime_end})
- Cause: {brief_technical_explanation}

**Your Refund:**
- Amount: R$ {prorated_refund}
- Reason: Service downtime exceeded 72-hour threshold
- Processing: 5-10 business days to original payment method

Your subscription remains active. This refund is a service credit for the disruption.

We've implemented additional safeguards to prevent future incidents:
- {improvement_1}
- {improvement_2}

Thank you for your patience and understanding.

Atenciosamente,
{CEO_name}
CEO, SmartLic
```

---

## Internal Workflows

### Support Agent Checklist: Refund Request

**Step 1: Verify Eligibility**
- [ ] Confirm user has annual subscription (query `user_subscriptions`)
- [ ] Calculate days since purchase: `CURRENT_DATE - DATE(created_at)`
- [ ] Check if within 7-day window

**Step 2: Process Refund (If Eligible)**
- [ ] Retrieve Stripe subscription ID and latest invoice
- [ ] Issue refund via Stripe Dashboard or API
- [ ] Cancel subscription in Stripe
- [ ] Update `user_subscriptions` status to 'canceled'
- [ ] Invalidate Redis cache (`features:{user_id}`)
- [ ] Send confirmation email

**Step 3: Log Event**
- [ ] Create support ticket with refund details
- [ ] Add to `stripe_webhook_events` audit log
- [ ] Flag for monthly finance reconciliation

**Step 4: Follow-Up (Optional)**
- [ ] Send feedback survey (why did you cancel?)
- [ ] Offer assistance with alternative plans
- [ ] Add to re-engagement campaign (30-day email sequence)

---

### Support Agent Checklist: Downgrade Request (8+ Days)

**Step 1: Verify Eligibility**
- [ ] Confirm purchase date is 8+ days ago
- [ ] Verify current billing period is 'annual'

**Step 2: Explain Policy**
- [ ] Clearly communicate: No refund available
- [ ] Explain: Benefits retained until period end
- [ ] Confirm: Automatic conversion to monthly after period end

**Step 3: Process Downgrade (If Customer Agrees)**
- [ ] Update `user_subscriptions.billing_period = 'monthly'`
- [ ] Schedule Stripe subscription change at period end
- [ ] Send confirmation email with timeline
- [ ] Log event in support system

**Step 4: Alternatives (If Customer Unhappy)**
- [ ] Offer: Extended trial of upcoming features (proactive search)
- [ ] Offer: 1-month free extension of annual period (if requested by manager)
- [ ] Escalate to retention specialist if high-value customer

---

## Legal Disclaimers

### Governing Law
This policy is governed by:
- Brazilian Consumer Defense Code (Lei 8.078/1990)
- Brazilian Civil Code (Lei 10.406/2002)
- Marco Civil da Internet (Lei 12.965/2014)

### Dispute Resolution
Any disputes arising from this policy shall be resolved in:
- Jurisdiction: Comarca de São Paulo, Brazil
- Preferred Method: Mediation via consumidor.gov.br
- Small Claims: Juizado Especial Cível (claims < R$ 20,000)

### Changes to Policy
- SmartLic reserves the right to modify this policy with 30 days' notice
- Material changes require re-acceptance of Terms of Service
- Policy changes do not affect existing subscriptions retroactively

---

## Compliance Checklist

- [x] 7-day refund window implemented (CDC Art. 49)
- [x] Clear communication of refund policy on checkout page
- [x] Automated eligibility verification
- [x] Transparent downgrade process
- [ ] Legal review by Brazilian consumer law attorney (PENDING)
- [ ] LGPD compliance for data retention during refund window (PENDING)
- [ ] Integration with consumidor.gov.br for dispute resolution (PENDING)

---

**Policy Owner:** Legal & Compliance Team
**Technical Owner:** Backend Team (Subscription API)
**Review Frequency:** Quarterly
**Next Review:** May 1, 2026

---

## Related Documents

- **Feature Documentation:** `docs/features/annual-subscription.md`
- **Customer FAQs:** `docs/support/faq-annual-plans.md`
- **Terms of Service:** `docs/legal/terms-of-service.md` (see Annual Plans section)
- **Privacy Policy:** `docs/legal/privacy-policy.md` (see Data Retention section)
- **Story:** `docs/stories/STORY-171-*.md`

---

**Last Updated:** 2026-02-07
**Version:** 1.0
**Status:** Draft (Pending Legal Review)
