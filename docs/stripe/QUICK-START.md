# Stripe Integration - Quick Start Guide

**Story:** STORY-171 (Track 3)
**Time Required:** 45-60 minutes
**Prerequisites:** Stripe account, Stripe CLI

---

## 🚀 Step-by-Step Setup (5 Steps)

### Step 1: Install Dependencies (5 min)

```bash
cd backend
pip install -r requirements.txt
```

**New packages:**
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL adapter
- `stripe` (already installed)
- `redis` (already installed)

---

### Step 2: Apply Database Migration (5 min)

```bash
# Using Supabase CLI
npx supabase db push

# Verify migration applied
npx supabase db diff
```

**Expected:** `stripe_webhook_events` table created

**Manual Verification (SQL):**
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name = 'stripe_webhook_events';
```

---

### Step 3: Create Stripe Prices (20-30 min)

**Follow:** `create-annual-prices.md` (detailed guide)

**Summary:**

1. **Log in to Stripe Dashboard**
   - URL: https://dashboard.stripe.com
   - Switch to **Test mode** (toggle in top-right)

2. **Create 3 Annual Prices**

   Navigate to **Products** → Select product → **Add price**

   | Plan | Amount | Interval | Currency |
   |------|--------|----------|----------|
   | Consultor Ágil | 285100 | Yearly | BRL |
   | Máquina | 573100 | Yearly | BRL |
   | Sala de Guerra | 1436200 | Yearly | BRL |

   **Note:** Amount is in centavos (R$ 2,851.00 = 285100 centavos)

3. **Copy Price IDs**

   After creating each price, copy the Price ID (format: `price_xxxxxxxxxxxxx`)

4. **Update `.env`**

   ```bash
   # backend/.env
   STRIPE_PRICE_CONSULTOR_AGIL_ANUAL=price_xxxxxxxxxxxxx
   STRIPE_PRICE_MAQUINA_ANUAL=price_xxxxxxxxxxxxx
   STRIPE_PRICE_SALA_GUERRA_ANUAL=price_xxxxxxxxxxxxx
   ```

---

### Step 4: Configure Webhook (10 min)

#### Option A: Local Development (Recommended for Testing)

```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Forward webhooks
stripe listen --forward-to localhost:8000/webhooks/stripe
```

**Output:**
```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx
```

**Copy secret to `.env`:**
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

#### Option B: Production

1. **Stripe Dashboard → Webhooks → Add endpoint**
2. **Endpoint URL:** `https://your-domain.com/webhooks/stripe`
3. **Select events:**
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
4. **Copy signing secret** to production `.env`

---

### Step 5: Test Integration (10 min)

```bash
# Terminal 1: Backend running (from Step 4)
uvicorn main:app --reload --port 8000

# Terminal 2: Stripe CLI listening (from Step 4)
stripe listen --forward-to localhost:8000/webhooks/stripe

# Terminal 3: Run test script
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

**Verify in Database:**
```sql
-- Should show processed webhook events
SELECT * FROM stripe_webhook_events ORDER BY processed_at DESC LIMIT 5;

-- Should show billing_period updated (if test user exists)
SELECT user_id, billing_period, updated_at
FROM user_subscriptions
WHERE stripe_subscription_id IS NOT NULL
ORDER BY updated_at DESC LIMIT 5;
```

---

## ✅ Setup Complete!

You can now:
- ✅ Receive Stripe webhook events
- ✅ Process subscription updates
- ✅ Update billing_period in database
- ✅ Invalidate feature flags cache

---

## 🔍 Testing Checklist

- [ ] Dependencies installed (`pip list | grep sqlalchemy`)
- [ ] Migration applied (table exists in DB)
- [ ] 3 annual prices created in Stripe
- [ ] Price IDs added to `.env`
- [ ] Webhook endpoint configured (local or production)
- [ ] Webhook signing secret added to `.env`
- [ ] Backend running on port 8000
- [ ] Stripe CLI forwarding webhooks
- [ ] Test script passes (all ✅)
- [ ] Webhook events logged in database

---

## 🐛 Troubleshooting

### Issue: "Invalid signature"

**Cause:** Wrong `STRIPE_WEBHOOK_SECRET`

**Fix:**
```bash
# Get secret from Stripe CLI
stripe listen --print-secret

# Update .env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Restart backend
```

---

### Issue: "Table stripe_webhook_events does not exist"

**Cause:** Migration not applied

**Fix:**
```bash
npx supabase db push
```

---

### Issue: "Webhook not received"

**Cause:** Stripe CLI not forwarding

**Fix:**
```bash
# Verify Stripe CLI is running
stripe listen --forward-to localhost:8000/webhooks/stripe

# Verify backend is reachable
curl http://localhost:8000/health
```

---

### Issue: "Redis connection failed"

**Cause:** Redis not running (optional)

**Fix:** Webhook handler automatically falls back to in-memory cache. No action needed.

**Optional:** Install Redis locally
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis

# Test
redis-cli ping  # Should return PONG
```

---

## 📚 Next Steps

After setup is complete:

1. **Test Real Subscription Flow**
   - Create test subscription in Stripe Dashboard
   - Verify webhook received
   - Check `billing_period` updated in DB

2. **Review Integration Points**
   - See `STRIPE_INTEGRATION.md` for architecture
   - See `create-annual-prices.md` for detailed Stripe setup

3. **Deploy to Production**
   - Switch Stripe to live mode
   - Create live mode prices
   - Update production `.env`
   - Configure production webhook endpoint

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **QUICK-START.md** (this file) | 5-step setup guide |
| **create-annual-prices.md** | Detailed Stripe Dashboard walkthrough |
| **STRIPE_INTEGRATION.md** | Complete architecture & troubleshooting |
| **TRACK-3-COMPLETION-SUMMARY.md** | Technical overview & file inventory |

---

## 🆘 Need Help?

**Common Issues:**
- Signature validation failures → Check webhook secret
- Database errors → Apply migration
- Webhook not received → Verify Stripe CLI forwarding

**Full Troubleshooting Guide:** `STRIPE_INTEGRATION.md` (Section: Troubleshooting)

---

**Last Updated:** 2026-02-07
**Related Story:** STORY-171 (Track 3)
**Time to Complete:** 45-60 minutes
