# Stripe Price ID Seeding — Onboarding Guide

## Overview

Stripe price IDs are used to link SmartLic plans to Stripe checkout sessions. Production IDs are baked into SQL migrations; staging/dev environments need their own IDs from Stripe's test mode.

## Production Price IDs (reference only)

| Plan | Period | Price ID | Amount |
|------|--------|----------|--------|
| SmartLic Pro | Monthly | `price_1T54vN9FhmvPslGYgfTGIAzV` | R$ 397/mo |
| SmartLic Pro | Semiannual | `price_1T54w99FhmvPslGY0coDMQGn` | R$ 357/mo |
| SmartLic Pro | Annual | `price_1T54wt9FhmvPslGYqX6bTNo0` | R$ 297/mo |

Source: migration `20260226120000_story277_repricing_stripe_ids.sql`

> **WARNING:** Never use production price IDs in staging/dev. They charge real money.

## Setting Up Staging/Dev

### Prerequisites

1. A Stripe account with **test mode** enabled
2. Products and prices created in Stripe test mode matching SmartLic plans
3. Supabase project URL and service role key

### Step 1: Create Prices in Stripe Test Mode

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/products) (test mode)
2. Create a product "SmartLic Pro" with 3 recurring prices:
   - Monthly: R$ 397/month
   - Semiannual: R$ 357/month (billed every 6 months = R$ 2,142)
   - Annual: R$ 297/month (billed yearly = R$ 3,564)
3. (Optional) Create "Consultoria" with similar structure
4. Copy the `price_xxx` IDs for each

### Step 2: Set Environment Variables

Add to your `.env` file:

```bash
# Required
STRIPE_PRICE_PRO_MONTHLY=price_1Txxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_PRO_SEMIANNUAL=price_1Txxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_PRO_ANNUAL=price_1Txxxxxxxxxxxxxxxxxxxxx

# Optional (Consultoria plan)
STRIPE_PRICE_CONSULTORIA_MONTHLY=price_1Txxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_CONSULTORIA_SEMIANNUAL=price_1Txxxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_CONSULTORIA_ANNUAL=price_1Txxxxxxxxxxxxxxxxxxxxx

# Required for seed script
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
```

### Step 3: Run the Seed Script

**Option A: Python script (recommended)**

```bash
cd backend
python ../scripts/seed_stripe_prices.py

# Dry run first:
python ../scripts/seed_stripe_prices.py --dry-run
```

**Option B: SQL seed**

```bash
# Set PostgreSQL variables, then run:
psql $DATABASE_URL \
  -v smartlic_pro_monthly="'price_xxx'" \
  -v smartlic_pro_semiannual="'price_xxx'" \
  -v smartlic_pro_annual="'price_xxx'" \
  -f supabase/seed/seed_stripe_prices.sql
```

**Option C: Shell helper**

```bash
bash scripts/seed-stripe-prices.sh
```

### Step 4: Verify

```sql
SELECT id, stripe_price_id_monthly, stripe_price_id_semiannual, stripe_price_id_annual
FROM plans WHERE id IN ('smartlic_pro', 'consultoria');

SELECT plan_id, billing_period, stripe_price_id
FROM plan_billing_periods ORDER BY plan_id, billing_period;
```

## Tables Involved

| Table | Column(s) | Purpose |
|-------|-----------|---------|
| `plans` | `stripe_price_id`, `stripe_price_id_monthly`, `stripe_price_id_semiannual`, `stripe_price_id_annual` | Denormalized price references |
| `plan_billing_periods` | `stripe_price_id` | Source of truth per (plan, period) |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Checkout fails with "No such price" | Wrong mode (test vs live) | Verify price IDs match your Stripe mode |
| Seed script says "0 rows updated" | Plan doesn't exist in DB | Run migrations first (`supabase db push`) |
| Missing env vars error | `.env` not loaded | Ensure `python-dotenv` installed or export vars manually |

## Files

| File | Purpose |
|------|---------|
| `scripts/seed_stripe_prices.py` | Python seed script (uses Supabase client) |
| `supabase/seed/seed_stripe_prices.sql` | SQL seed (uses `current_setting()`) |
| `scripts/seed-stripe-prices.sh` | Shell wrapper |
| `.env.example` | Template with all required vars |
