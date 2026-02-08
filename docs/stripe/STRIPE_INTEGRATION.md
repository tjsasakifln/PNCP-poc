# Stripe Integration - Annual Subscriptions (STORY-171)

**Status:** Prepared (awaiting Price IDs from Stripe Dashboard)
**Created:** 2026-02-07
**Track:** Track 3 (Stripe Integration Preparation)

---

## Overview

This document covers the Stripe integration for annual subscription billing in STORY-171.

**Key Features:**
1. **Idempotent Webhook Handler** - Prevents duplicate event processing
2. **Signature Validation** - Rejects unsigned/forged webhooks
3. **Atomic DB Updates** - Race condition protection
4. **Cache Invalidation** - Redis features cache updated
5. **Audit Trail** - All webhook events logged

---

## Architecture

### Components

```
┌─────────────┐
│   Stripe    │ (Webhook Events)
│  Dashboard  │
└──────┬──────┘
       │ customer.subscription.updated
       ▼
┌──────────────────────────────────────┐
│  Backend Webhook Handler             │
│  /webhooks/stripe                    │
│                                      │
│  1. Verify signature                 │
│  2. Check idempotency (DB)          │
│  3. Update user_subscriptions       │
│  4. Invalidate Redis cache          │
│  5. Log event                        │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Database (Supabase)                 │
│                                      │
│  - stripe_webhook_events             │
│  - user_subscriptions                │
└──────────────────────────────────────┘
```

### Files Created

#### Backend Files

| File | Purpose |
|------|---------|
| `backend/webhooks/stripe.py` | Webhook handler (idempotent, signature validation) |
| `backend/webhooks/__init__.py` | Webhooks package init |
| `backend/models/stripe_webhook_event.py` | SQLAlchemy model for webhook events |
| `backend/models/user_subscription.py` | SQLAlchemy model for subscriptions |
| `backend/models/__init__.py` | Models package init |
| `backend/cache.py` | Redis client with in-memory fallback |
| `backend/database.py` | SQLAlchemy engine and session factory |
| `backend/tests/test_stripe_webhook.py` | Unit tests (95%+ coverage target) |

#### Database Migrations

| File | Purpose |
|------|---------|
| `supabase/migrations/008_stripe_webhook_events.sql` | Create webhook events table |

#### Scripts & Documentation

| File | Purpose |
|------|---------|
| `backend/scripts/test-stripe-webhooks.sh` | Local webhook testing script |
| `docs/stripe/create-annual-prices.md` | Step-by-step price creation guide |
| `docs/stripe/STRIPE_INTEGRATION.md` | This document |

#### Configuration

| File | Changes |
|------|---------|
| `backend/.env` | Added Stripe Price IDs, webhook secret |
| `backend/requirements.txt` | Added `sqlalchemy`, `psycopg2-binary` |

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New dependencies:**
- `sqlalchemy==2.0.36` - ORM for webhook events and subscriptions
- `psycopg2-binary==2.9.10` - PostgreSQL adapter
- `stripe==11.4.1` (already installed)
- `redis==5.2.1` (already installed)

---

### 2. Apply Database Migration

```bash
# Using Supabase CLI
npx supabase db push

# Or manually via Supabase Dashboard SQL Editor
# Copy contents of: supabase/migrations/008_stripe_webhook_events.sql
```

**Verification:**
```sql
-- Should show stripe_webhook_events table
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name = 'stripe_webhook_events';

-- Should return: stripe_webhook_events
```

---

### 3. Create Stripe Annual Prices

**Follow:** `docs/stripe/create-annual-prices.md`

**Summary:**
1. Log in to Stripe Dashboard (Test mode)
2. Navigate to Products
3. Create 3 annual prices:
   - Consultor Ágil: R$ 2,851/year (285100 centavos)
   - Máquina: R$ 5,731/year (573100 centavos)
   - Sala de Guerra: R$ 14,362/year (1436200 centavos)
4. Copy Price IDs to `.env`

---

### 4. Configure Environment Variables

Update `backend/.env`:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here

# Stripe Webhook Secret (from Stripe CLI or Dashboard)
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Stripe Annual Plan Price IDs
STRIPE_PRICE_CONSULTOR_AGIL_ANUAL=price_xxxxxxxxxxxxx
STRIPE_PRICE_MAQUINA_ANUAL=price_xxxxxxxxxxxxx
STRIPE_PRICE_SALA_GUERRA_ANUAL=price_xxxxxxxxxxxxx
```

---

### 5. Test Webhook Locally

**Prerequisites:**
- Stripe CLI installed ([Download](https://stripe.com/docs/stripe-cli))
- Backend running on `http://localhost:8000`

**Run Test Script:**
```bash
# Terminal 1: Start backend
uvicorn main:app --reload --port 8000

# Terminal 2: Run webhook test
bash backend/scripts/test-stripe-webhooks.sh
```

**Expected Output:**
```
✅ Stripe CLI found
✅ Backend is running
✅ Stripe listener started
✅ Webhook processed successfully
✅ Idempotency working (duplicate event rejected)
```

---

## Webhook Event Flow

### Event: `customer.subscription.updated`

**Trigger:** User upgrades from monthly to annual (or vice versa)

**Processing Steps:**

1. **Receive Event**
   ```json
   {
     "id": "evt_1234567890",
     "type": "customer.subscription.updated",
     "data": {
       "object": {
         "id": "sub_abcdefgh",
         "plan": { "interval": "year" },
         "customer": "cus_xyz123"
       }
     }
   }
   ```

2. **Verify Signature**
   ```python
   stripe.Webhook.construct_event(
       payload, sig_header, STRIPE_WEBHOOK_SECRET
   )
   ```
   - ❌ Invalid signature → HTTP 400 "Invalid signature"
   - ✅ Valid signature → Continue

3. **Idempotency Check**
   ```sql
   SELECT id FROM stripe_webhook_events WHERE id = 'evt_1234567890';
   ```
   - ✅ Exists → Return `{"status": "already_processed"}`
   - ❌ Not found → Continue

4. **Determine Billing Period**
   ```python
   interval = event.data.object.plan.interval
   billing_period = 'annual' if interval == 'year' else 'monthly'
   ```

5. **Atomic DB Update**
   ```sql
   INSERT INTO user_subscriptions (stripe_subscription_id, billing_period, updated_at)
   VALUES ('sub_abcdefgh', 'annual', NOW())
   ON CONFLICT (stripe_subscription_id)
   DO UPDATE SET billing_period = 'annual', updated_at = NOW();
   ```

6. **Invalidate Cache**
   ```python
   redis_client.delete(f"features:{user_id}")
   ```

7. **Log Event**
   ```sql
   INSERT INTO stripe_webhook_events (id, type, processed_at, payload)
   VALUES ('evt_1234567890', 'customer.subscription.updated', NOW(), {...});
   ```

8. **Return Success**
   ```json
   {"status": "success", "event_id": "evt_1234567890"}
   ```

---

## Security

### Signature Validation

**Critical:** ALWAYS verify webhook signatures to prevent fake webhooks.

```python
try:
    event = stripe.Webhook.construct_event(
        payload, sig_header, STRIPE_WEBHOOK_SECRET
    )
except stripe.error.SignatureVerificationError:
    raise HTTPException(400, "Invalid signature")
```

**Why This Matters:**
- Without validation, attackers can forge webhooks
- Could manipulate billing_period without payment
- Could trigger unauthorized refunds

**Environment Variable:**
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

---

### Idempotency

**Problem:** Stripe may retry webhooks if your endpoint times out.

**Solution:** Check `stripe_webhook_events` table before processing.

```python
existing = db.query(StripeWebhookEvent).filter(
    StripeWebhookEvent.id == event.id
).first()

if existing:
    return {"status": "already_processed"}
```

**Benefits:**
- Prevents duplicate billing_period updates
- Prevents duplicate cache invalidations
- Prevents race conditions with concurrent webhooks

---

## Testing

### Unit Tests

**File:** `backend/tests/test_stripe_webhook.py`

**Coverage Target:** 95%+

**Test Cases:**
1. ✅ Valid signature accepted
2. ❌ Missing signature header rejected (HTTP 400)
3. ❌ Invalid signature rejected (HTTP 400)
4. ❌ Malformed payload rejected (HTTP 400)
5. ✅ Duplicate event returns "already_processed"
6. ✅ New event processed and recorded
7. ✅ Billing period updated (year → annual, month → monthly)
8. ✅ Cache invalidated after update
9. ✅ Event logged to stripe_webhook_events table
10. ⚠️ Database error triggers rollback

**Run Tests:**
```bash
cd backend
pytest tests/test_stripe_webhook.py -v --cov=webhooks/stripe
```

---

### Integration Testing

**File:** `backend/scripts/test-stripe-webhooks.sh`

**Steps:**
1. Start Stripe CLI listener
2. Trigger `customer.subscription.updated` event
3. Verify webhook received (HTTP 200)
4. Verify event recorded in DB
5. Verify idempotency (retry returns "already_processed")

**Manual Verification:**
```sql
-- Check webhook events
SELECT * FROM stripe_webhook_events ORDER BY processed_at DESC LIMIT 5;

-- Check billing_period updated
SELECT user_id, billing_period, updated_at
FROM user_subscriptions
WHERE stripe_subscription_id IS NOT NULL
ORDER BY updated_at DESC LIMIT 5;
```

---

## Monitoring

### Key Metrics

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| **Webhook error rate** | > 5% | Check logs, verify STRIPE_WEBHOOK_SECRET |
| **Signature verification failures** | > 10/hour | Possible attack, rotate webhook secret |
| **Duplicate events** | > 20% | Normal (Stripe retries), ensure idempotency works |
| **Cache invalidation failures** | > 1% | Check Redis connection |

### Logging

**Log Levels:**
- `INFO`: Successful webhook processing
- `WARNING`: Missing signature header
- `ERROR`: Signature verification failed, database errors
- `DEBUG`: Full event payload (disabled in production)

**Log Format:**
```
[INFO] Webhook processed successfully: event_id=evt_123, type=customer.subscription.updated
[ERROR] Webhook signature verification failed: event_id=evt_456
```

---

## Troubleshooting

### Issue: "Invalid signature"

**Cause:** `STRIPE_WEBHOOK_SECRET` mismatch

**Solution:**
1. Get signing secret from Stripe Dashboard → Webhooks
2. Update `.env` with correct secret
3. Restart backend: `uvicorn main:app --reload`

---

### Issue: "Webhook not received"

**Cause:** Endpoint URL misconfigured

**Solution (Local):**
```bash
# Use Stripe CLI forwarding
stripe listen --forward-to localhost:8000/webhooks/stripe
```

**Solution (Production):**
1. Verify endpoint URL in Stripe Dashboard
2. Check firewall allows incoming webhooks
3. Test with `curl` from external server

---

### Issue: "Database error"

**Cause:** Migration not applied

**Solution:**
```bash
# Apply migration
npx supabase db push

# Verify table exists
psql -c "SELECT * FROM stripe_webhook_events LIMIT 1;"
```

---

### Issue: "Cache not invalidated"

**Cause:** Redis connection failed

**Solution:**
1. Check `REDIS_URL` in `.env`
2. Verify Redis running: `redis-cli ping`
3. Fallback: Uses in-memory cache automatically

---

## Production Deployment Checklist

- [ ] **Database Migration Applied**
  - `008_stripe_webhook_events.sql` executed on production DB
  - Verified: `SELECT * FROM stripe_webhook_events;` works

- [ ] **Environment Variables Configured**
  - `STRIPE_SECRET_KEY` (live mode, not test)
  - `STRIPE_WEBHOOK_SECRET` (from live webhook endpoint)
  - `STRIPE_PRICE_*_ANUAL` (all 3 Price IDs from live mode)

- [ ] **Webhook Endpoint Configured**
  - Stripe Dashboard → Webhooks → Add endpoint
  - URL: `https://your-domain.com/webhooks/stripe`
  - Events: `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`
  - Signing secret copied to `.env`

- [ ] **Redis Running**
  - `REDIS_URL` configured
  - Redis accessible from backend
  - Test: `redis-cli -u $REDIS_URL ping` returns `PONG`

- [ ] **Testing Completed**
  - Unit tests pass (95%+ coverage)
  - Integration test with Stripe CLI
  - Manual webhook trigger verified

- [ ] **Monitoring Configured**
  - Webhook error rate alert (<5%)
  - Signature verification failures alert (<10/hour)
  - Log aggregation (Datadog, Sentry, etc.)

- [ ] **Documentation Updated**
  - Team trained on webhook debugging
  - Runbook created for common issues

---

## Next Steps (Post-Track 3)

After this track is complete, the following features will be built:

1. **Track 1: Database Schema** (AC4)
   - Migration `006_add_billing_period.sql`
   - Migration `007_create_plan_features.sql`

2. **Track 2: Backend API Endpoints** (AC5, AC6)
   - `POST /api/subscriptions/update-billing-period`
   - `GET /api/features/me` (with Redis cache)

3. **Track 4: Frontend Components** (AC1, AC2, AC3)
   - `PlanToggle` component
   - `AnnualBenefits` component
   - `TrustSignals` component

4. **Track 5: Testing & Documentation** (AC7-AC10)
   - E2E tests
   - Architecture documentation

---

## Related Documents

- **Story:** [STORY-171](../stories/STORY-171-annual-subscription-toggle.md)
- **Architect Review:** [STORY-171-architect-review.md](../stories/STORY-171-architect-review.md)
- **PO Review:** [STORY-171-po-review.md](../stories/STORY-171-po-review.md)
- **Price Creation Guide:** [create-annual-prices.md](./create-annual-prices.md)

---

**Last Updated:** 2026-02-07
**Author:** Backend Team (Track 3)
**Status:** ✅ Ready for Integration Testing
