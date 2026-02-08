# STORY-171 Backend Implementation - Quick Start Guide

**Status:** ✅ Ready for Testing
**Track:** TRACK 2 - Backend API + Database Migrations
**Date:** 2026-02-07

---

## Overview

Complete backend implementation for annual subscriptions including:
- 4 database migrations (billing_period, plan_features, webhook events, helper functions)
- Pro-rata billing calculations with edge case handling
- Feature flags API with Redis caching
- 30+ unit tests with ≥70% coverage target

---

## Quick Setup

### 1. Apply Database Migrations

```bash
# Ensure Supabase CLI is installed
npm install -g supabase

# Apply migrations in order
npx supabase db push

# Verify migrations
npx supabase db diff
```

**Expected Output:**
```
Applying migration 008_add_billing_period.sql...
Applying migration 009_create_plan_features.sql...
Applying migration 010_stripe_webhook_events.sql...
Applying migration 011_add_billing_helper_functions.sql...
✅ All migrations applied successfully
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New Dependencies:**
- `redis==5.2.1` - Feature flag caching (optional but recommended)

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run specific test suites
pytest tests/test_billing_period_update.py -v
pytest tests/test_prorata_edge_cases.py -v
pytest tests/test_feature_flags.py -v
pytest tests/test_feature_cache.py -v
```

**Expected Coverage:** ≥70%

---

## API Endpoints

### 1. Update Billing Period
**Endpoint:** `POST /api/subscriptions/update-billing-period`

**Request:**
```bash
curl -X POST https://api.smartlic.tech/api/subscriptions/update-billing-period \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_billing_period": "annual",
    "user_timezone": "America/Sao_Paulo"
  }'
```

**Response (Success - No Defer):**
```json
{
  "success": true,
  "new_billing_period": "annual",
  "next_billing_date": "2026-03-01T00:00:00+00:00",
  "prorated_credit": "148.50",
  "deferred": false,
  "message": "Período de cobrança atualizado para annual. Crédito de R$ 148.50 aplicado."
}
```

**Response (Deferred - < 7 days):**
```json
{
  "success": true,
  "new_billing_period": "annual",
  "next_billing_date": "2026-02-15T00:00:00+00:00",
  "prorated_credit": "0.00",
  "deferred": true,
  "message": "Menos de 7 dias até renovação (5 dias). A mudança será aplicada no próximo ciclo de cobrança."
}
```

---

### 2. Get User Features
**Endpoint:** `GET /api/features/me`

**Request:**
```bash
curl https://api.smartlic.tech/api/features/me \
  -H "Authorization: Bearer $TOKEN"
```

**Response (Annual Subscriber):**
```json
{
  "features": [
    {
      "key": "early_access",
      "enabled": true,
      "metadata": {"description": "Acesso antecipado a novos recursos"}
    },
    {
      "key": "proactive_search",
      "enabled": true,
      "metadata": {"description": "Alertas automáticos de novas licitações"}
    }
  ],
  "plan_id": "consultor_agil",
  "billing_period": "annual",
  "cached_at": "2026-02-07T12:00:00Z"
}
```

**Response (Monthly Subscriber):**
```json
{
  "features": [],
  "plan_id": "consultor_agil",
  "billing_period": "monthly",
  "cached_at": "2026-02-07T12:00:30Z"
}
```

---

## Testing Scenarios

### Scenario 1: Monthly → Annual Upgrade (15 days remaining)

**Setup:**
```sql
-- Create test user with monthly subscription
INSERT INTO user_subscriptions (user_id, plan_id, billing_period, expires_at, is_active)
VALUES (
  'test-user-123',
  'consultor_agil',
  'monthly',
  NOW() + INTERVAL '15 days',
  true
);
```

**Test:**
```bash
# Update to annual
curl -X POST http://localhost:8000/api/subscriptions/update-billing-period \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"new_billing_period": "annual"}'
```

**Expected:**
- `prorated_credit`: "148.50" (15 days * R$ 9.90/day)
- `deferred`: false
- DB updated: `billing_period = 'annual'`
- Stripe subscription updated
- Redis cache invalidated

---

### Scenario 2: Deferred Update (5 days remaining)

**Setup:**
```sql
-- Create test user with subscription expiring soon
INSERT INTO user_subscriptions (user_id, plan_id, billing_period, expires_at, is_active)
VALUES (
  'test-user-456',
  'consultor_agil',
  'monthly',
  NOW() + INTERVAL '5 days',
  true
);
```

**Test:**
```bash
curl -X POST http://localhost:8000/api/subscriptions/update-billing-period \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"new_billing_period": "annual"}'
```

**Expected:**
- `deferred`: true
- `prorated_credit`: "0.00"
- No Stripe update
- No DB update
- Message: "Menos de 7 dias até renovação..."

---

### Scenario 3: Feature Flags (Annual vs Monthly)

**Setup:**
```sql
-- Annual subscriber
INSERT INTO user_subscriptions (user_id, plan_id, billing_period, is_active)
VALUES ('annual-user', 'consultor_agil', 'annual', true);

-- Monthly subscriber
INSERT INTO user_subscriptions (user_id, plan_id, billing_period, is_active)
VALUES ('monthly-user', 'consultor_agil', 'monthly', true);
```

**Test:**
```bash
# Annual user (should get features)
curl http://localhost:8000/api/features/me -H "Authorization: Bearer $ANNUAL_TOKEN"

# Monthly user (should get empty features)
curl http://localhost:8000/api/features/me -H "Authorization: Bearer $MONTHLY_TOKEN"
```

**Expected:**
- Annual: 2 features (`early_access`, `proactive_search`)
- Monthly: 0 features

---

## Database Verification

### Check Migrations Applied
```sql
-- Check billing_period column
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_subscriptions'
  AND column_name = 'billing_period';

-- Check plan_features seeded
SELECT plan_id, billing_period, feature_key, enabled
FROM plan_features
ORDER BY plan_id, billing_period, feature_key;

-- Check helper functions
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name LIKE '%billing%' OR routine_name LIKE '%feature%';
```

**Expected Results:**
- `billing_period` column: VARCHAR(10), default 'monthly'
- 7 rows in `plan_features` (seeded annual features)
- 3 helper functions: `get_user_billing_period`, `user_has_feature`, `get_user_features`

---

## Redis Cache Testing

### Check Cache Keys
```bash
# Connect to Redis
redis-cli -u $REDIS_URL

# List all feature cache keys
KEYS features:*

# Get cached features for specific user
GET features:12345678-1234-1234-1234-123456789abc

# Check TTL
TTL features:12345678-1234-1234-1234-123456789abc
```

**Expected:**
- TTL: ~300 seconds (5 minutes)
- Cache format: JSON string (UserFeaturesResponse)

### Test Cache Invalidation
```bash
# 1. Get features (cache miss - slow)
time curl http://localhost:8000/api/features/me -H "Authorization: Bearer $TOKEN"

# 2. Get features again (cache hit - fast)
time curl http://localhost:8000/api/features/me -H "Authorization: Bearer $TOKEN"

# 3. Update billing period (invalidates cache)
curl -X POST http://localhost:8000/api/subscriptions/update-billing-period \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"new_billing_period": "annual"}'

# 4. Get features (cache miss again - slow, but with new features)
time curl http://localhost:8000/api/features/me -H "Authorization: Bearer $TOKEN"
```

**Expected Timing:**
- Cache miss: ~50-100ms
- Cache hit: ~2-5ms

---

## Common Issues & Troubleshooting

### Issue 1: Migration Fails
**Symptom:** `ERROR: column "billing_period" already exists`

**Solution:**
```bash
# Check migration state
npx supabase db diff

# Rollback if needed
psql $DATABASE_URL -f supabase/migrations/008_rollback.sql

# Reapply
npx supabase db push
```

---

### Issue 2: Redis Connection Failed
**Symptom:** `Failed to connect to Redis` (warning in logs)

**Solution:**
- Check `REDIS_URL` environment variable
- Verify Redis instance is running
- **Note:** System gracefully degrades (direct DB queries) if Redis unavailable

---

### Issue 3: Stripe API Error
**Symptom:** `Stripe API error: No such subscription`

**Solution:**
- Check `STRIPE_SECRET_KEY` is set
- Verify `stripe_subscription_id` exists in `user_subscriptions` table
- Test with Stripe test mode first

---

### Issue 4: Pro-rata Calculation Incorrect
**Symptom:** Wrong credit amount

**Debug:**
```python
from services.billing import calculate_prorata_credit
from decimal import Decimal
from datetime import datetime, timezone, timedelta

result = calculate_prorata_credit(
    current_billing_period="monthly",
    new_billing_period="annual",
    current_price_brl=Decimal("297.00"),
    new_price_brl=Decimal("2376.00"),
    next_billing_date=datetime.now(timezone.utc) + timedelta(days=15),
    user_timezone="America/Sao_Paulo",
)
print(f"Credit: {result.prorated_credit}, Days: {result.days_until_renewal}")
```

---

## Environment Variables

**Required:**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

**Optional:**
```bash
REDIS_URL=redis://localhost:6379  # For caching (recommended)
```

---

## Next Steps

1. **Run Tests:** `pytest --cov`
2. **Apply Migrations:** `npx supabase db push`
3. **Deploy to Railway:** `git push origin main`
4. **Test API Endpoints:** Use Postman/curl
5. **Verify Stripe Integration:** Check Stripe dashboard
6. **Frontend Integration:** Proceed to TRACK 3

---

## Support & Documentation

- **Full Implementation Guide:** `docs/implementation/STORY-171-backend-implementation.md`
- **API Documentation:** `http://localhost:8000/docs` (FastAPI Swagger UI)
- **Database Schema:** Supabase Dashboard → Table Editor
- **Test Coverage:** `backend/htmlcov/index.html` (after running tests with `--cov-report=html`)

---

**Questions?** Contact @architect or @qa for technical review.

**Status:** ✅ Ready for Deployment
