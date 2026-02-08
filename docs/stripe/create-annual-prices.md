# Stripe Annual Price Creation Guide

**Purpose:** Create annual subscription prices in Stripe Dashboard for STORY-171

**Prerequisites:**
- Stripe account access (test mode for development, live mode for production)
- Admin access to Stripe Dashboard
- Monthly prices already created (baseline)

---

## Step-by-Step Instructions

### 1. Navigate to Products

1. Log in to [Stripe Dashboard](https://dashboard.stripe.com)
2. Switch to **Test mode** (toggle in top-right corner)
3. Go to **Products** in left sidebar
4. Click on the product you want to add an annual price to

---

### 2. Create Annual Price for "Consultor Ágil"

**Pricing Details:**
- **Monthly:** R$ 297/month
- **Annual:** R$ 2,851/year (R$ 237/month effective)
- **Discount:** 20% (save R$ 713/year)

**Steps:**

1. Click **"Add price"** button
2. Fill in the form:
   - **Type:** Recurring
   - **Price:** 285100 (in centavos, R$ 2,851.00)
   - **Billing interval:** Yearly
   - **Currency:** BRL (Brazilian Real)
   - **Price description (optional):** "Plano Anual - Consultor Ágil (20% desconto)"
3. Click **"Save"**
4. **Copy the Price ID** (format: `price_xxxxxxxxxxxxx`)
5. Paste Price ID into `.env` file:
   ```bash
   STRIPE_PRICE_CONSULTOR_AGIL_ANUAL=price_xxxxxxxxxxxxx
   ```

---

### 3. Create Annual Price for "Máquina"

**Pricing Details:**
- **Monthly:** R$ 597/month
- **Annual:** R$ 5,731/year (R$ 478/month effective)
- **Discount:** 20% (save R$ 1,433/year)

**Steps:**

1. Navigate to **Máquina** product
2. Click **"Add price"**
3. Fill in:
   - **Price:** 573100 (R$ 5,731.00)
   - **Billing interval:** Yearly
   - **Currency:** BRL
   - **Description:** "Plano Anual - Máquina (20% desconto)"
4. Save and **copy Price ID**
5. Update `.env`:
   ```bash
   STRIPE_PRICE_MAQUINA_ANUAL=price_xxxxxxxxxxxxx
   ```

---

### 4. Create Annual Price for "Sala de Guerra"

**Pricing Details:**
- **Monthly:** R$ 1,497/month
- **Annual:** R$ 14,362/year (R$ 1,197/month effective)
- **Discount:** 20% (save R$ 3,594/year)

**Steps:**

1. Navigate to **Sala de Guerra** product
2. Click **"Add price"**
3. Fill in:
   - **Price:** 1436200 (R$ 14,362.00)
   - **Billing interval:** Yearly
   - **Currency:** BRL
   - **Description:** "Plano Anual - Sala de Guerra (20% desconto)"
4. Save and **copy Price ID**
5. Update `.env`:
   ```bash
   STRIPE_PRICE_SALA_GUERRA_ANUAL=price_xxxxxxxxxxxxx
   ```

---

## 5. Verify Price IDs in .env

Your `.env` file should now have ALL price IDs filled in:

```bash
# Consultor Ágil
STRIPE_PRICE_CONSULTOR_AGIL_MENSAL=price_abc123  # R$ 297/month
STRIPE_PRICE_CONSULTOR_AGIL_ANUAL=price_def456   # R$ 2,851/year

# Máquina
STRIPE_PRICE_MAQUINA_MENSAL=price_ghi789         # R$ 597/month
STRIPE_PRICE_MAQUINA_ANUAL=price_jkl012          # R$ 5,731/year

# Sala de Guerra
STRIPE_PRICE_SALA_GUERRA_MENSAL=price_mno345     # R$ 1,497/month
STRIPE_PRICE_SALA_GUERRA_ANUAL=price_pqr678      # R$ 14,362/year
```

---

## 6. Configure Webhook Endpoint

**Purpose:** Receive subscription update events when users upgrade/downgrade

### 6.1. Local Development (Stripe CLI)

For local testing, use Stripe CLI webhook forwarding:

```bash
# Terminal 1: Start backend
uvicorn main:app --reload --port 8000

# Terminal 2: Forward webhooks to local endpoint
stripe listen --forward-to localhost:8000/webhooks/stripe
```

The Stripe CLI will output a webhook signing secret:
```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx
```

Copy this secret to `.env`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### 6.2. Production (Stripe Dashboard)

1. Go to **Developers → Webhooks** in Stripe Dashboard
2. Click **"Add endpoint"**
3. Fill in:
   - **Endpoint URL:** `https://your-production-domain.com/webhooks/stripe`
   - **Events to send:**
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
4. Click **"Add endpoint"**
5. **Copy the signing secret** (format: `whsec_xxxxxxxxxxxxx`)
6. Update production `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
   ```

---

## 7. Test Webhook Integration

Run the test script to verify webhooks work:

```bash
# Start backend (Terminal 1)
uvicorn main:app --reload --port 8000

# Run test script (Terminal 2)
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

## 8. Pricing Verification Checklist

Before deploying to production:

- [ ] All 6 Price IDs copied to `.env` (3 monthly + 3 annual)
- [ ] Webhook endpoint configured (test mode AND live mode)
- [ ] Webhook signing secret added to `.env`
- [ ] Webhook test script passes
- [ ] Pricing calculations verified:
  - [ ] Consultor Ágil: R$ 2,851 = R$ 297 × 9.6 ✓
  - [ ] Máquina: R$ 5,731 = R$ 597 × 9.6 ✓
  - [ ] Sala de Guerra: R$ 14,362 = R$ 1,497 × 9.6 ✓
- [ ] Discount display: "Economize 20%" badge shows correctly
- [ ] Test purchase in Stripe test mode
- [ ] Verify `billing_period` updates in database after webhook

---

## 9. Common Issues & Troubleshooting

### Issue: "Price already exists"
**Solution:** Stripe prevents duplicate prices. Check existing prices under Product → Prices.

### Issue: "Webhook signature verification failed"
**Solution:**
1. Verify `STRIPE_WEBHOOK_SECRET` is correct in `.env`
2. Restart backend after updating `.env`
3. Check webhook secret matches in Stripe Dashboard

### Issue: "Currency mismatch"
**Solution:** All prices MUST use BRL (Brazilian Real). Check currency in Stripe Dashboard.

### Issue: "Webhook not received"
**Solution:**
1. Verify endpoint URL is correct
2. Check firewall allows incoming webhooks
3. Use Stripe CLI for local testing: `stripe listen --forward-to localhost:8000/webhooks/stripe`

---

## 10. Production Deployment Checklist

Before switching to live mode:

- [ ] Create products in **Live mode** (not test mode)
- [ ] Copy Live mode Price IDs to production `.env`
- [ ] Configure webhook endpoint with production URL
- [ ] Update `STRIPE_WEBHOOK_SECRET` with live mode secret
- [ ] Test annual subscription purchase (use real card)
- [ ] Verify webhook received and processed
- [ ] Check `stripe_webhook_events` table has event recorded
- [ ] Verify `billing_period = 'annual'` in `user_subscriptions`

---

## Additional Resources

- [Stripe Pricing Documentation](https://stripe.com/docs/billing/prices-guide)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe CLI Reference](https://stripe.com/docs/stripe-cli)
- [STORY-171: Annual Subscription Implementation](../stories/STORY-171-annual-subscription-toggle.md)

---

**Last Updated:** 2026-02-07
**Author:** DevOps Team
**Related Story:** STORY-171 (Track 3)
