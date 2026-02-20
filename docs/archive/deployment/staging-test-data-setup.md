# Staging Test Data Setup Guide - STORY-165

**Story:** PNCP-165 - Plan Restructuring - 3 Paid Tiers + FREE Trial
**Version:** 1.0
**Created:** February 4, 2026
**Environment:** Staging (Supabase)

---

## Overview

This guide provides step-by-step instructions to create test users in Supabase staging database for STORY-165 smoke tests.

**Required Test Users:** 8 users (4 plan types × 2 quota states)

---

## Supabase Access

### Prerequisites

- [ ] Access to Supabase staging project
- [ ] Database credentials or Supabase Studio access
- [ ] SQL query editor permissions

### Connection Details

**Supabase Studio URL:** `https://app.supabase.com/project/[PROJECT_ID]`
**Database:** Staging
**Schema:** `public`
**Table:** `users`, `monthly_quota`

---

## Test User Requirements

| User ID | Plan | Email | Password | Quota Used | Trial Status | Purpose |
|---------|------|-------|----------|------------|--------------|---------|
| `test-free-001` | `free_trial` | `free-trial@smartpncp.test` | `TestPass123!` | N/A | 3 days left | P0-2, P0-3 |
| `test-free-002` | `free_trial` | `free-expired@smartpncp.test` | `TestPass123!` | N/A | EXPIRED | P1-1 |
| `test-consultor-001` | `consultor_agil` | `consultor-low@smartpncp.test` | `TestPass123!` | 23/50 | N/A | P0-4, P0-5, P0-6 |
| `test-consultor-002` | `consultor_agil` | `consultor-exhausted@smartpncp.test` | `TestPass123!` | 50/50 | N/A | P0-10 |
| `test-maquina-001` | `maquina` | `maquina@smartpncp.test` | `TestPass123!` | 150/300 | N/A | P0-7, P0-8 |
| `test-guerra-001` | `sala_guerra` | `sala-guerra@smartpncp.test` | `TestPass123!` | 50/1000 | N/A | P0-9 |
| `test-consultor-003` | `consultor_agil` | `consultor-edge@smartpncp.test` | `TestPass123!` | 30/50 | N/A | P1-3 (edge cases) |
| `test-consultor-004` | `consultor_agil` | `consultor-rate@smartpncp.test` | `TestPass123!` | 5/50 | N/A | P1-5 (rate limiting) |

---

## Step 1: Create User Accounts

### SQL Script - Create Users Table Records

Run this SQL script in Supabase Studio:

```sql
-- Ensure users table exists with required columns
-- (Skip if already exists from STORY-165 migrations)

-- Create users if not exists
INSERT INTO users (id, email, plan_id, trial_expires_at, trial_started_at, created_at)
VALUES
  -- FREE Trial (Active - 3 days left)
  (
    'test-free-001',
    'free-trial@smartpncp.test',
    'free_trial',
    NOW() + INTERVAL '3 days',
    NOW() - INTERVAL '4 days',
    NOW() - INTERVAL '4 days'
  ),

  -- FREE Trial (Expired)
  (
    'test-free-002',
    'free-expired@smartpncp.test',
    'free_trial',
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '8 days',
    NOW() - INTERVAL '8 days'
  ),

  -- Consultor Ágil (Low usage - 23/50)
  (
    'test-consultor-001',
    'consultor-low@smartpncp.test',
    'consultor_agil',
    NULL,
    NULL,
    NOW() - INTERVAL '30 days'
  ),

  -- Consultor Ágil (Exhausted - 50/50)
  (
    'test-consultor-002',
    'consultor-exhausted@smartpncp.test',
    'consultor_agil',
    NULL,
    NULL,
    NOW() - INTERVAL '30 days'
  ),

  -- Máquina (50% usage - 150/300)
  (
    'test-maquina-001',
    'maquina@smartpncp.test',
    'maquina',
    NULL,
    NULL,
    NOW() - INTERVAL '60 days'
  ),

  -- Sala de Guerra (Low usage - 50/1000)
  (
    'test-guerra-001',
    'sala-guerra@smartpncp.test',
    'sala_guerra',
    NULL,
    NULL,
    NOW() - INTERVAL '90 days'
  ),

  -- Consultor Ágil (Edge case testing - 30/50)
  (
    'test-consultor-003',
    'consultor-edge@smartpncp.test',
    'consultor_agil',
    NULL,
    NULL,
    NOW() - INTERVAL '15 days'
  ),

  -- Consultor Ágil (Rate limiting test - 5/50)
  (
    'test-consultor-004',
    'consultor-rate@smartpncp.test',
    'consultor_agil',
    NULL,
    NULL,
    NOW() - INTERVAL '10 days'
  )
ON CONFLICT (id) DO UPDATE SET
  plan_id = EXCLUDED.plan_id,
  trial_expires_at = EXCLUDED.trial_expires_at,
  trial_started_at = EXCLUDED.trial_started_at;
```

### Verification Query

Run this to verify users were created:

```sql
SELECT
  id,
  email,
  plan_id,
  trial_expires_at,
  trial_started_at,
  created_at
FROM users
WHERE email LIKE '%@smartpncp.test'
ORDER BY plan_id, email;
```

**Expected Output:** 8 rows

---

## Step 2: Create Quota Records

### SQL Script - Create Monthly Quota Records

```sql
-- Ensure monthly_quota table exists
-- (Skip if already exists from STORY-165 migrations)

-- Get current month-year format (e.g., "2026-02")
-- Calculate quota for current month

INSERT INTO monthly_quota (user_id, month_year, searches_count)
VALUES
  -- FREE Trial users: no quota tracking (unlimited during trial)
  -- Skip free trial users

  -- Consultor Ágil (23/50)
  (
    'test-consultor-001',
    TO_CHAR(NOW(), 'YYYY-MM'),
    23
  ),

  -- Consultor Ágil (50/50 - EXHAUSTED)
  (
    'test-consultor-002',
    TO_CHAR(NOW(), 'YYYY-MM'),
    50
  ),

  -- Máquina (150/300 - 50% usage)
  (
    'test-maquina-001',
    TO_CHAR(NOW(), 'YYYY-MM'),
    150
  ),

  -- Sala de Guerra (50/1000 - low usage)
  (
    'test-guerra-001',
    TO_CHAR(NOW(), 'YYYY-MM'),
    50
  ),

  -- Consultor Ágil (30/50 - 60% for color test)
  (
    'test-consultor-003',
    TO_CHAR(NOW(), 'YYYY-MM'),
    30
  ),

  -- Consultor Ágil (5/50 - for rate limit test)
  (
    'test-consultor-004',
    TO_CHAR(NOW(), 'YYYY-MM'),
    5
  )
ON CONFLICT (user_id, month_year) DO UPDATE SET
  searches_count = EXCLUDED.searches_count;
```

### Verification Query

```sql
SELECT
  mq.user_id,
  u.email,
  u.plan_id,
  mq.month_year,
  mq.searches_count
FROM monthly_quota mq
JOIN users u ON mq.user_id = u.id
WHERE u.email LIKE '%@smartpncp.test'
ORDER BY u.plan_id, u.email;
```

**Expected Output:** 6 rows (no quota for FREE trial users)

---

## Step 3: Create Authentication Credentials

### Using Supabase Auth

If using Supabase Auth for authentication:

#### Option A: Supabase Studio UI

1. Navigate to **Authentication** > **Users** in Supabase Studio
2. Click **Add User** (repeat for each test user)
3. Fill in:
   - **Email:** Use email from table above
   - **Password:** `TestPass123!`
   - **User ID:** Use ID from table above (if supported)
   - **Auto Confirm User:** ✓ (checked)
4. Click **Create User**

#### Option B: SQL Script (Auth API)

```sql
-- This approach requires Supabase Auth API access
-- Contact DevOps if Auth API integration is needed

-- Example using Supabase REST API (run from backend):
-- POST https://[PROJECT_REF].supabase.co/auth/v1/admin/users
-- Authorization: Bearer [SERVICE_ROLE_KEY]
-- Body:
-- {
--   "email": "free-trial@smartpncp.test",
--   "password": "TestPass123!",
--   "email_confirm": true,
--   "user_metadata": {
--     "test_user": true
--   }
-- }
```

#### Option C: Manual Sign-Up (if auto-confirm disabled)

1. Navigate to staging frontend
2. Click **Sign Up**
3. Register with email/password from table
4. Check email for confirmation link
5. Confirm account
6. Update `users.plan_id` in database to match test plan

---

## Step 4: Verification Checklist

Run these checks to ensure test data is ready:

### Check 1: User Count

```sql
SELECT COUNT(*) FROM users WHERE email LIKE '%@smartpncp.test';
```

**Expected:** 8

### Check 2: Plan Distribution

```sql
SELECT plan_id, COUNT(*)
FROM users
WHERE email LIKE '%@smartpncp.test'
GROUP BY plan_id
ORDER BY plan_id;
```

**Expected:**
```
free_trial      | 2
consultor_agil  | 4
maquina         | 1
sala_guerra     | 1
```

### Check 3: Trial Expiration Dates

```sql
SELECT
  email,
  plan_id,
  trial_expires_at,
  CASE
    WHEN trial_expires_at IS NULL THEN 'N/A'
    WHEN trial_expires_at > NOW() THEN 'ACTIVE'
    ELSE 'EXPIRED'
  END AS trial_status
FROM users
WHERE email LIKE '%@smartpncp.test' AND plan_id = 'free_trial'
ORDER BY email;
```

**Expected:**
```
free-trial@smartpncp.test   | ACTIVE
free-expired@smartpncp.test | EXPIRED
```

### Check 4: Quota Data

```sql
SELECT
  u.email,
  u.plan_id,
  COALESCE(mq.searches_count, 0) AS quota_used
FROM users u
LEFT JOIN monthly_quota mq ON u.id = mq.user_id AND mq.month_year = TO_CHAR(NOW(), 'YYYY-MM')
WHERE u.email LIKE '%@smartpncp.test'
ORDER BY u.plan_id, u.email;
```

**Expected:**
```
consultor-exhausted@smartpncp.test | 50
consultor-low@smartpncp.test       | 23
consultor-edge@smartpncp.test      | 30
consultor-rate@smartpncp.test      | 5
maquina@smartpncp.test             | 150
sala-guerra@smartpncp.test         | 50
free-trial@smartpncp.test          | 0
free-expired@smartpncp.test        | 0
```

### Check 5: Authentication Test

Manually test login for each user:

- [ ] `free-trial@smartpncp.test` / `TestPass123!` → Login successful
- [ ] `free-expired@smartpncp.test` / `TestPass123!` → Login successful
- [ ] `consultor-low@smartpncp.test` / `TestPass123!` → Login successful
- [ ] `consultor-exhausted@smartpncp.test` / `TestPass123!` → Login successful
- [ ] `maquina@smartpncp.test` / `TestPass123!` → Login successful
- [ ] `sala-guerra@smartpncp.test` / `TestPass123!` → Login successful
- [ ] `consultor-edge@smartpncp.test` / `TestPass123!` → Login successful
- [ ] `consultor-rate@smartpncp.test` / `TestPass123!` → Login successful

---

## Step 5: Sample Search Parameters

For consistent testing, use these search parameters:

### Standard Search (All Users)

- **UF:** SP (São Paulo)
- **Date Range:** Last 7 days
- **Expected:** Results (may vary by PNCP data availability)

### Edge Case Searches

| User Plan | Test Case | UF | Date Range | Expected Result |
|-----------|-----------|-----|------------|----------------|
| FREE Trial | Success | SP | 7 days | HTTP 200, results displayed |
| FREE Trial | Blocked | SP | 30 days | Validation error, search disabled |
| Consultor Ágil | Success | SP | 30 days | HTTP 200, results displayed |
| Consultor Ágil | Blocked | SP | 31 days | Validation error |
| Máquina | Success | SP | 365 days | HTTP 200, results displayed |
| Máquina | Blocked | SP | 730 days | Validation error |
| Sala de Guerra | Success | SP | 1825 days | HTTP 200, results displayed |

---

## Step 6: Additional Test Data (Optional)

### Invalid Plan ID Test (P2-3)

```sql
-- Create user with invalid plan_id for fallback test
INSERT INTO users (id, email, plan_id, created_at)
VALUES
  (
    'test-invalid-001',
    'invalid-plan@smartpncp.test',
    'unknown_plan',
    NOW()
  )
ON CONFLICT (id) DO UPDATE SET plan_id = EXCLUDED.plan_id;
```

### Quota Color Transition Test (P2-1)

```sql
-- Create additional Consultor Ágil users for color testing
INSERT INTO monthly_quota (user_id, month_year, searches_count)
VALUES
  -- 60% usage (green)
  ('test-consultor-003', TO_CHAR(NOW(), 'YYYY-MM'), 30),

  -- 80% usage (yellow) - create new user
  ('test-consultor-yellow', TO_CHAR(NOW(), 'YYYY-MM'), 40),

  -- 96% usage (red) - create new user
  ('test-consultor-red', TO_CHAR(NOW(), 'YYYY-MM'), 48)
ON CONFLICT (user_id, month_year) DO UPDATE SET
  searches_count = EXCLUDED.searches_count;

-- Create corresponding users
INSERT INTO users (id, email, plan_id, created_at)
VALUES
  ('test-consultor-yellow', 'consultor-yellow@smartpncp.test', 'consultor_agil', NOW()),
  ('test-consultor-red', 'consultor-red@smartpncp.test', 'consultor_agil', NOW())
ON CONFLICT (id) DO UPDATE SET plan_id = EXCLUDED.plan_id;
```

---

## Step 7: Reset Test Data (After Testing)

After smoke tests complete, clean up test data:

```sql
-- Delete test users
DELETE FROM monthly_quota
WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE '%@smartpncp.test'
);

DELETE FROM users
WHERE email LIKE '%@smartpncp.test';

-- Verify cleanup
SELECT COUNT(*) FROM users WHERE email LIKE '%@smartpncp.test';
-- Expected: 0
```

---

## Troubleshooting

### Issue: Users not appearing in frontend

**Solution:**
- Verify users exist in `users` table
- Check Supabase Auth dashboard for confirmed accounts
- Ensure email confirmation completed
- Check frontend `/api/me` endpoint response

### Issue: Quota not updating after search

**Solution:**
- Verify `monthly_quota` table has correct `month_year` format
- Check backend logs for quota increment failures
- Ensure Supabase RLS policies allow updates
- Verify `check_quota()` function is being called

### Issue: Trial expiration not working

**Solution:**
- Check `trial_expires_at` timestamp is in correct timezone (UTC)
- Verify backend uses `datetime.utcnow()` for comparison
- Ensure `trial_expires_at` is properly set (not NULL for free trial users)

### Issue: Rate limiting not triggering

**Solution:**
- Verify rate limiting middleware is enabled
- Check Redis connection (or in-memory fallback)
- Ensure `max_requests_per_min` configured in `PLAN_CAPABILITIES`
- Test with shorter time window (e.g., 30 seconds instead of 60)

---

## Sign-Off

**Data Setup Completed By:** ___________________
**Date:** ___________________
**Environment:** Staging

**Verification Checklist:**

- [ ] 8 test users created
- [ ] Authentication working for all users
- [ ] Quota records created (6 users)
- [ ] Trial expiration dates correct
- [ ] Plan IDs match requirements
- [ ] Sample searches tested
- [ ] Evidence screenshots saved

**Approved By:** ___________________
**Date:** ___________________

---

**Next Steps:**

1. Share test user credentials with QA team securely
2. Proceed to smoke test execution (staging-smoke-test-checklist.md)
3. Record results in staging-smoke-test-results-template.md
4. Archive test data after testing complete
