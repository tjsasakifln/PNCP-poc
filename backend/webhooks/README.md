# Webhooks Package

**Purpose:** Handle external API webhook events

---

## Stripe Webhook Handler

**File:** `stripe.py`
**Endpoint:** `POST /webhooks/stripe`

### Quick Start

```bash
# 1. Install Stripe CLI
curl -s https://packages.stripe.com/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.com/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
sudo apt update
sudo apt install stripe

# 2. Forward webhooks to local backend
stripe listen --forward-to localhost:8000/webhooks/stripe

# 3. Copy signing secret to .env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# 4. Trigger test event
stripe trigger customer.subscription.updated

# 5. Verify in logs
tail -f logs/app.log | grep "Webhook processed"
```

---

## Features

### 1. Signature Validation

**Purpose:** Prevent fake/forged webhooks

```python
# CRITICAL: Always verify signature
event = stripe.Webhook.construct_event(
    payload, sig_header, STRIPE_WEBHOOK_SECRET
)
```

**Rejects:**
- Missing `stripe-signature` header → HTTP 400
- Invalid signature → HTTP 400
- Malformed payload → HTTP 400

---

### 2. Idempotency

**Purpose:** Prevent duplicate processing (Stripe retries webhooks)

```python
# Check if event already processed
existing = db.query(StripeWebhookEvent).filter(
    StripeWebhookEvent.id == event.id
).first()

if existing:
    return {"status": "already_processed"}
```

**Benefits:**
- No duplicate billing updates
- Safe webhook retries
- Audit trail in `stripe_webhook_events` table

---

### 3. Atomic DB Updates

**Purpose:** Prevent race conditions with concurrent webhooks

```python
# Upsert (atomic operation)
stmt = insert(UserSubscription).values(...).on_conflict_do_update(
    index_elements=['stripe_subscription_id'],
    set_={'billing_period': billing_period}
)
```

---

### 4. Cache Invalidation

**Purpose:** Refresh feature flags after billing change

```python
# Invalidate user's features cache
redis_client.delete(f"features:{user_id}")
```

---

## Supported Events

| Event | Handler | Action |
|-------|---------|--------|
| `customer.subscription.updated` | `handle_subscription_updated()` | Update `billing_period` in DB |
| `customer.subscription.deleted` | `handle_subscription_deleted()` | Set `is_active = false` |
| `invoice.payment_succeeded` | `handle_invoice_payment_succeeded()` | Invalidate cache (renewal) |

---

## Testing

### Unit Tests

```bash
pytest backend/tests/test_stripe_webhook.py -v --cov=webhooks/stripe
```

**Coverage Target:** 95%+

---

### Integration Test

```bash
bash backend/scripts/test-stripe-webhooks.sh
```

**Expected Output:**
```
✅ Stripe CLI found
✅ Backend is running
✅ Webhook processed successfully
✅ Idempotency working
```

---

## Troubleshooting

### "Invalid signature"

**Cause:** `STRIPE_WEBHOOK_SECRET` mismatch

**Fix:**
```bash
# Get correct secret from Stripe CLI
stripe listen --print-secret

# Update .env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Restart backend
uvicorn main:app --reload
```

---

### "Webhook not received"

**Cause:** Endpoint not reachable

**Fix (Local):**
```bash
# Use Stripe CLI forwarding
stripe listen --forward-to localhost:8000/webhooks/stripe
```

**Fix (Production):**
1. Check Stripe Dashboard → Webhooks → Endpoint URL
2. Verify firewall allows incoming webhooks
3. Test: `curl -X POST https://your-domain.com/webhooks/stripe`

---

### "Database error"

**Cause:** Migration not applied

**Fix:**
```bash
npx supabase db push

# Verify
psql -c "SELECT * FROM stripe_webhook_events LIMIT 1;"
```

---

## Production Checklist

- [ ] `STRIPE_WEBHOOK_SECRET` configured (live mode)
- [ ] Webhook endpoint registered in Stripe Dashboard
- [ ] Database migration applied (`008_stripe_webhook_events.sql`)
- [ ] Redis configured (or fallback to in-memory)
- [ ] Monitoring alerts configured (<5% error rate)

---

## Monitoring

**Key Metrics:**
- Webhook success rate (target: >95%)
- Signature verification failures (alert: >10/hour)
- Idempotent rejections (normal: <20%)

**Logs:**
```python
logger.info("Webhook processed: event_id=%s", event.id)
logger.error("Signature verification failed: %s", error)
```

---

## Documentation

- **Complete Guide:** `docs/stripe/STRIPE_INTEGRATION.md`
- **Price Creation:** `docs/stripe/create-annual-prices.md`
- **Track Summary:** `docs/stripe/TRACK-3-COMPLETION-SUMMARY.md`

---

**Last Updated:** 2026-02-07
**Related Story:** STORY-171 (Track 3)
