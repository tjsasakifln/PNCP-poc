# Annual Subscription Feature

## Overview

The annual subscription feature allows users to commit to a 12-month billing period and receive a 20% discount plus exclusive premium benefits. This feature integrates with Stripe for payment processing, Supabase for data persistence, and Redis for high-performance caching.

**Key Benefits:**
- 💰 20% discount (equivalent to 2.4 months free)
- ✨ Early Access to new features (2-4 weeks before monthly subscribers)
- 🎯 Proactive Search (STORY-172 - launching March 2026)
- 🤖 AI Edital Analysis for Sala de Guerra annual plans only (STORY-173 - launching April 2026)

**Implementation Status:** STORY-171 (In Progress)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Interface (Next.js)                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  BillingPeriodToggle Component                                │  │
│  │  - Monthly/Annual switch                                      │  │
│  │  - Price display with 20% discount badge                     │  │
│  │  - Premium benefits tooltip                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
                    POST /api/subscriptions/update-billing-period
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       Backend API (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  1. Validate user authentication (JWT)                        │  │
│  │  2. Retrieve current subscription from Supabase               │  │
│  │  3. Calculate pro-rata credit/charge                          │  │
│  │  4. Update Stripe subscription                                │  │
│  │  5. Update Supabase user_subscriptions table                  │  │
│  │  6. Invalidate Redis cache (features:{user_id})               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
        ┌───────────────────────┐      ┌──────────────────────┐
        │   Stripe API          │      │  Supabase PostgreSQL │
        │  - Update subscription│      │  - user_subscriptions│
        │  - Apply pro-rata     │      │  - plan_features     │
        │  - Handle 3D Secure   │      │  - Feature flags     │
        └───────────────────────┘      └──────────────────────┘
                    ↓                               ↓
        ┌───────────────────────┐      ┌──────────────────────┐
        │  Stripe Webhooks      │      │  Redis Cache         │
        │  - invoice.paid       │      │  Key: features:{id}  │
        │  - customer.updated   │      │  TTL: 5 minutes      │
        │  - subscription.*     │      │  Invalidate on update│
        └───────────────────────┘      └──────────────────────┘
```

**Data Flow:**
1. User toggles monthly ↔ annual in frontend
2. Frontend sends update request to backend
3. Backend validates and calculates pro-rata
4. Stripe subscription updated with new price ID
5. Supabase `user_subscriptions.billing_period` updated
6. Redis cache invalidated to reflect new features
7. Stripe webhook confirms successful update
8. Frontend displays confirmation and new benefits

---

## Pricing Structure

### Pricing Formula
```
Annual Price = Monthly Price × 9.6
```

This yields exactly 20% discount: `(12 - 2.4) / 12 = 0.80 = 20% off`

### Plan Pricing Table

| Plan | Monthly | Annual | Savings | Effective Monthly |
|------|---------|--------|---------|-------------------|
| **Consultor Ágil** | R$ 297 | R$ 2,851 | R$ 713 (20%) | R$ 237.58 |
| **Máquina** | R$ 597 | R$ 5,731 | R$ 1,433 (20%) | R$ 477.58 |
| **Sala de Guerra** | R$ 1,497 | R$ 14,362 | R$ 3,590 (20%) | R$ 1,196.83 |

### Stripe Price IDs (Production)

```bash
# Consultor Ágil
PRICE_CONSULTOR_MONTHLY=price_1XXXXXXXXXXXX
PRICE_CONSULTOR_ANNUAL=price_1YYYYYYYYYYYY

# Máquina
PRICE_MAQUINA_MONTHLY=price_1ZZZZZZZZZZZZZ
PRICE_MAQUINA_ANNUAL=price_1AAAAAAAAAAAAAA

# Sala de Guerra
PRICE_SALA_MONTHLY=price_1BBBBBBBBBBBBBB
PRICE_SALA_ANNUAL=price_1CCCCCCCCCCCCCC
```

---

## Premium Benefits

### Tier 1: All Annual Plans (Consultor, Máquina, Sala de Guerra)

| Benefit | Description | Availability |
|---------|-------------|--------------|
| **✨ Early Access** | Access new features 2-4 weeks before monthly subscribers | Live |
| **🎯 Proactive Search** | AI automatically searches for relevant bids and sends daily summaries | March 2026 (STORY-172) |
| **💰 20% Discount** | Pay for 9.6 months, get 12 months | Live |

### Tier 2: Sala de Guerra Annual Only

| Benefit | Description | Availability |
|---------|-------------|--------------|
| **🤖 AI Edital Analysis** | Advanced AI analysis of bid documents with risk assessment and win probability | April 2026 (STORY-173) |

### Feature Availability Matrix

```typescript
// Backend: plan_features table
{
  plan_id: "sala_de_guerra",
  billing_period: "annual",
  features: {
    early_access: true,          // Live
    proactive_search: true,      // March 2026
    ai_edital_analysis: true,    // April 2026
    priority_support: true       // Live
  }
}

// Monthly plans (all tiers)
{
  billing_period: "monthly",
  features: {
    early_access: false,
    proactive_search: false,
    ai_edital_analysis: false
  }
}
```

---

## API Endpoints

### POST /api/subscriptions/update-billing-period

Update user's billing period between monthly and annual.

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "billing_period": "annual"  // "monthly" | "annual"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "billing_period": "annual",
  "next_billing_date": "2027-02-07T00:00:00Z",
  "pro_rata_amount": -150.50,  // Negative = credit, Positive = charge
  "new_price": 2851.00,
  "new_features": [
    "early_access",
    "proactive_search",
    "ai_edital_analysis"
  ],
  "message": "Successfully upgraded to annual billing. You'll receive R$ 150.50 credit on your next invoice."
}
```

**Error Responses:**

```json
// 401 Unauthorized
{
  "error": "Authentication required",
  "code": "UNAUTHORIZED"
}

// 404 Not Found
{
  "error": "No active subscription found",
  "code": "NO_SUBSCRIPTION"
}

// 400 Bad Request
{
  "error": "Invalid billing period. Must be 'monthly' or 'annual'",
  "code": "INVALID_BILLING_PERIOD"
}

// 409 Conflict
{
  "error": "Already on annual billing",
  "code": "ALREADY_ANNUAL"
}

// 500 Stripe Error
{
  "error": "Failed to update Stripe subscription",
  "code": "STRIPE_ERROR",
  "details": "Stripe error message here"
}
```

**Rate Limiting:** 5 requests per minute per user

**Idempotency:** Safe to retry within 5 minutes (cached result)

---

### GET /api/features/me

Retrieve current user's available features based on plan and billing period.

**Authentication:** Required (JWT Bearer token)

**Success Response (200):**
```json
{
  "user_id": "uuid-here",
  "plan_id": "sala_de_guerra",
  "billing_period": "annual",
  "features": {
    "early_access": true,
    "proactive_search": true,
    "ai_edital_analysis": true,
    "priority_support": true,
    "max_saved_searches": 50,
    "export_formats": ["excel", "csv", "pdf"]
  },
  "cached": true,
  "cache_expires_at": "2026-02-07T12:35:00Z"
}
```

**Caching Strategy:**
- **Cache Key:** `features:{user_id}`
- **TTL:** 5 minutes
- **Invalidation:** On billing period update, plan upgrade/downgrade, Stripe webhook
- **Stale-While-Revalidate:** Return cached data while fetching fresh data in background

**Cache Miss Behavior:**
1. Query Supabase `user_subscriptions` + `plan_features`
2. Store in Redis with 5-minute TTL
3. Return fresh data

---

## Database Schema

### user_subscriptions Table

```sql
CREATE TABLE user_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id VARCHAR(50) NOT NULL,  -- 'consultor_agil', 'maquina', 'sala_de_guerra'
  billing_period VARCHAR(20) NOT NULL DEFAULT 'monthly',  -- 'monthly' | 'annual'
  stripe_subscription_id VARCHAR(100) UNIQUE NOT NULL,
  stripe_customer_id VARCHAR(100) NOT NULL,
  stripe_price_id VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'canceled', 'past_due'
  current_period_start TIMESTAMPTZ NOT NULL,
  current_period_end TIMESTAMPTZ NOT NULL,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT valid_billing_period CHECK (billing_period IN ('monthly', 'annual')),
  CONSTRAINT valid_plan_id CHECK (plan_id IN ('consultor_agil', 'maquina', 'sala_de_guerra'))
);

CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_stripe_sub ON user_subscriptions(stripe_subscription_id);
CREATE INDEX idx_user_subscriptions_billing_period ON user_subscriptions(billing_period);
```

### plan_features Table

```sql
CREATE TABLE plan_features (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id VARCHAR(50) NOT NULL,
  billing_period VARCHAR(20) NOT NULL,
  feature_key VARCHAR(100) NOT NULL,
  feature_value JSONB,  -- Can store boolean, number, string, or object
  available_from TIMESTAMPTZ,  -- NULL = available now
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(plan_id, billing_period, feature_key),
  CONSTRAINT valid_billing_period CHECK (billing_period IN ('monthly', 'annual'))
);

-- Seed data for annual plan benefits
INSERT INTO plan_features (plan_id, billing_period, feature_key, feature_value, available_from) VALUES
-- All annual plans
('consultor_agil', 'annual', 'early_access', 'true', NOW()),
('consultor_agil', 'annual', 'proactive_search', 'true', '2026-03-01'),
('maquina', 'annual', 'early_access', 'true', NOW()),
('maquina', 'annual', 'proactive_search', 'true', '2026-03-01'),
('sala_de_guerra', 'annual', 'early_access', 'true', NOW()),
('sala_de_guerra', 'annual', 'proactive_search', 'true', '2026-03-01'),
-- Sala de Guerra annual exclusive
('sala_de_guerra', 'annual', 'ai_edital_analysis', 'true', '2026-04-01');
```

### stripe_webhook_events Table (Audit Log)

```sql
CREATE TABLE stripe_webhook_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stripe_event_id VARCHAR(100) UNIQUE NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  subscription_id VARCHAR(100),
  payload JSONB NOT NULL,
  processed BOOLEAN DEFAULT FALSE,
  processed_at TIMESTAMPTZ,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stripe_events_type ON stripe_webhook_events(event_type);
CREATE INDEX idx_stripe_events_user ON stripe_webhook_events(user_id);
CREATE INDEX idx_stripe_events_processed ON stripe_webhook_events(processed);
```

---

## Redis Cache Strategy

### Cache Keys

```
features:{user_id}           # User's available features (5 min TTL)
subscription:{user_id}       # User's subscription data (5 min TTL)
stripe:customer:{email}      # Stripe customer ID by email (60 min TTL)
plan:features:{plan_id}      # Plan feature definitions (24 hour TTL)
```

### Cache Invalidation Triggers

1. **Manual Billing Period Update**
   ```python
   await redis.delete(f"features:{user_id}")
   await redis.delete(f"subscription:{user_id}")
   ```

2. **Stripe Webhook: `customer.subscription.updated`**
   ```python
   user_id = get_user_by_stripe_subscription(subscription_id)
   await redis.delete(f"features:{user_id}")
   await redis.delete(f"subscription:{user_id}")
   ```

3. **Plan Feature Update (Admin)**
   ```python
   await redis.delete(f"plan:features:{plan_id}")
   # Invalidate all users on this plan
   user_ids = get_users_by_plan(plan_id)
   for uid in user_ids:
       await redis.delete(f"features:{uid}")
   ```

### Cache-Aside Pattern (Lazy Loading)

```python
async def get_user_features(user_id: str) -> dict:
    # Try cache first
    cache_key = f"features:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss - fetch from database
    features = await db.fetch_user_features(user_id)

    # Store in cache
    await redis.setex(
        cache_key,
        300,  # 5 minutes
        json.dumps(features)
    )

    return features
```

---

## Pro-Rata Calculation

### Scenario 1: Monthly → Annual (Upgrade)

**Situation:** User pays R$ 297/month, wants to switch to R$ 2,851/year. 15 days remain in current monthly period.

**Calculation:**
```python
# 1. Calculate unused monthly time value
days_remaining = 15
days_in_period = 30
monthly_price = 297.00
unused_monthly_value = (days_remaining / days_in_period) * monthly_price
# unused_monthly_value = 148.50

# 2. Annual charge
annual_price = 2851.00

# 3. Net charge (Stripe handles this automatically)
# Stripe credits the unused monthly amount and charges full annual
# User pays: 2851.00 - 148.50 = 2702.50 immediately
```

**Implementation:**
```python
# Update Stripe subscription
stripe.Subscription.modify(
    subscription_id,
    items=[{
        'id': subscription_item_id,
        'price': PRICE_CONSULTOR_ANNUAL
    }],
    proration_behavior='always_invoice',  # Create immediate invoice
    billing_cycle_anchor='now'  # Reset billing cycle to today
)
```

### Scenario 2: Annual → Monthly (Downgrade)

**Situation:** User on annual plan (R$ 2,851/year) wants to downgrade to monthly (R$ 297/month). 180 days remain in annual period.

**Brazilian CDC Compliance:**
- **0-7 days since purchase:** Full refund (R$ 2,851)
- **8+ days since purchase:** No refund, but keep benefits until period end

**Implementation:**
```python
purchase_date = subscription.start_date
days_since_purchase = (datetime.now() - purchase_date).days

if days_since_purchase <= 7:
    # Full refund via Stripe
    stripe.Refund.create(
        charge=charge_id,
        amount=285100,  # Full amount in cents
        reason='requested_by_customer'
    )
    # Cancel subscription immediately
    stripe.Subscription.delete(subscription_id)
else:
    # No refund - schedule downgrade at period end
    stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=False,
        items=[{
            'id': subscription_item_id,
            'price': PRICE_CONSULTOR_MONTHLY
        }],
        proration_behavior='none',  # No immediate charge
        billing_cycle_anchor='unchanged'  # Keep current period end
    )
    # Update database
    await db.execute("""
        UPDATE user_subscriptions
        SET billing_period = 'monthly',
            updated_at = NOW()
        WHERE user_id = $1
    """, user_id)
```

### Edge Cases

#### Timezone Handling
```python
# Always use UTC for calculations
from datetime import timezone
period_end = subscription.current_period_end.replace(tzinfo=timezone.utc)
now = datetime.now(timezone.utc)
days_remaining = (period_end - now).days
```

#### Failed Payment During Pro-Rata
```python
# Stripe webhook: invoice.payment_failed
# Revert billing_period change in database
await db.execute("""
    UPDATE user_subscriptions
    SET billing_period = (
        SELECT billing_period FROM user_subscriptions_history
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1 OFFSET 1
    )
    WHERE user_id = $1
""", user_id)

# Invalidate cache
await redis.delete(f"features:{user_id}")
```

#### 3D Secure / SCA Authentication
```python
# If payment requires authentication
if invoice.payment_intent.status == 'requires_action':
    return {
        "success": False,
        "requires_action": True,
        "client_secret": invoice.payment_intent.client_secret,
        "message": "Additional authentication required"
    }
```

---

## Troubleshooting

### Issue: Pro-rata calculation shows wrong amount

**Symptoms:** User reports unexpected charge when switching billing periods

**Diagnosis:**
```python
# Check Stripe invoice line items
invoice = stripe.Invoice.retrieve(invoice_id, expand=['lines.data.proration_details'])
for line in invoice.lines.data:
    print(f"Description: {line.description}")
    print(f"Amount: {line.amount / 100}")
    print(f"Proration: {line.proration}")
```

**Solution:**
- Verify `proration_behavior='always_invoice'` is set
- Check `billing_cycle_anchor` (should be 'now' for immediate change)
- Ensure Stripe subscription has correct `current_period_end`

---

### Issue: Features not updating after billing period change

**Symptoms:** User switched to annual but still sees monthly features

**Diagnosis:**
```bash
# Check Redis cache
redis-cli GET "features:{user_id}"

# Check database
psql -c "SELECT billing_period, updated_at FROM user_subscriptions WHERE user_id = 'xxx';"
```

**Solution:**
```python
# Manually invalidate cache
await redis.delete(f"features:{user_id}")
await redis.delete(f"subscription:{user_id}")

# Force feature refresh
features = await get_user_features(user_id, force_refresh=True)
```

---

### Issue: Stripe webhook not processing

**Symptoms:** Subscription updated in Stripe but not reflected in Supabase

**Diagnosis:**
```sql
-- Check webhook events table
SELECT * FROM stripe_webhook_events
WHERE processed = FALSE
ORDER BY created_at DESC
LIMIT 10;
```

**Solution:**
```python
# Retry failed webhook
event = await db.fetch_one("""
    SELECT * FROM stripe_webhook_events
    WHERE stripe_event_id = $1
""", event_id)

await process_stripe_webhook(json.loads(event['payload']))

# Mark as processed
await db.execute("""
    UPDATE stripe_webhook_events
    SET processed = TRUE, processed_at = NOW()
    WHERE stripe_event_id = $1
""", event_id)
```

---

### Issue: User can't downgrade (7-day window expired)

**Symptoms:** User requests refund after 7-day CDC window

**Policy:** No refund, but user retains annual benefits until period end, then converts to monthly.

**Customer Support Response Template:**
> "According to Brazilian CDC regulations, refunds are available within 7 days of purchase. Since your annual plan was purchased on {date} ({days} days ago), we cannot process a refund. However, you will continue to enjoy all annual plan benefits including early access and proactive search until {period_end_date}. After that, your subscription will automatically convert to monthly billing at R$ {monthly_price}/month."

**Exception Cases (Full Refund Anytime):**
1. Service downtime > 72 consecutive hours
2. Promised feature (proactive search, AI analysis) delayed > 6 months past stated date
3. Unauthorized charge / fraud investigation

---

## Testing Checklist

### Unit Tests
- [ ] Pro-rata calculation (monthly → annual)
- [ ] Pro-rata calculation (annual → monthly)
- [ ] 7-day refund eligibility check
- [ ] Feature availability based on plan + billing period
- [ ] Cache invalidation on billing period change

### Integration Tests
- [ ] Stripe subscription update (monthly → annual)
- [ ] Stripe subscription update (annual → monthly)
- [ ] Stripe webhook processing (`customer.subscription.updated`)
- [ ] Database state consistency after billing change
- [ ] Redis cache consistency

### E2E Tests
- [ ] User toggles monthly → annual in UI
- [ ] Correct price displayed with 20% discount badge
- [ ] Payment succeeds and features update immediately
- [ ] User receives email confirmation
- [ ] User toggles annual → monthly (7+ days after purchase)
- [ ] Benefits retained until period end
- [ ] Automatic conversion to monthly after annual expires

---

## Related Documentation

- **Legal:** `docs/legal/downgrade-policy.md` - Refund and downgrade policies
- **Support:** `docs/support/faq-annual-plans.md` - Customer FAQs
- **Stories:** `docs/stories/STORY-171-*.md` - Implementation details
- **Architecture:** `docs/architecture/billing-system.md` - Overall billing architecture
- **API Spec:** `docs/api/subscriptions.yaml` - OpenAPI specification

---

**Last Updated:** 2026-02-07
**Story:** STORY-171
**Status:** In Progress
**Next Review:** March 2026 (before Proactive Search launch)
