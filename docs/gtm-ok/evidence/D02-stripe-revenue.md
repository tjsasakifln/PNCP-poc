# D02: Revenue Infrastructure Assessment

## Verdict: FAIL
## Score: 3/10

Revenue cannot flow from checkout to plan activation. The most critical webhook
(`checkout.session.completed`) is not handled, meaning paying customers remain on
`free_trial` after completing Stripe Checkout. This is a P0 blocker for any
revenue-generating launch.

---

## 1. Checkout-to-Activation Analysis

### 1.1 Checkout Flow (POST /v1/checkout)

**File:** `backend/routes/billing.py` lines 33-79

The checkout endpoint creates a Stripe Checkout Session correctly:
- Validates `billing_period` (monthly/semiannual/annual) -- line 43
- Looks up the plan and its Stripe price ID -- lines 52-61
- Sets `client_reference_id` and `metadata` with `user_id` and `plan_id` -- lines 72-73
- Uses `api_key=` parameter (not global assignment) for thread safety -- line 78

**CRITICAL BUG (P0): `smartlic_pro` is treated as one-time payment, not subscription.**

Line 63:
```python
is_subscription = plan_id in ("consultor_agil", "maquina", "sala_guerra")
```

The current plan `smartlic_pro` (GTM-002) is **NOT** in this list. This means:
- `mode` is set to `"payment"` (line 69) instead of `"subscription"`
- Stripe creates a **one-time charge**, not a recurring subscription
- No `subscription` ID is generated, so no `customer.subscription.*` webhooks fire
- Renewal, cancellation, and billing period changes are all impossible

This is a legacy check from before GTM-002 introduced `smartlic_pro`. The
`smartlic_pro` plan was added but the checkout logic was never updated.

### 1.2 Plan Activation (_activate_plan)

**File:** `backend/routes/billing.py` lines 82-112

The `_activate_plan()` function exists and would correctly:
- Deactivate existing subscriptions (line 98)
- Insert a new `user_subscriptions` record (lines 100-108)
- Sync `profiles.plan_type` (line 110)

**CRITICAL: `_activate_plan()` is NEVER called by any code path.**

A codebase-wide search for `_activate_plan` returns only:
1. Its definition at `routes/billing.py:82`
2. A docstring reference in `quota.py:512`

No webhook handler, no endpoint, no background task ever invokes this function.
It is dead code.

### 1.3 checkout.session.completed Webhook

**NOT HANDLED.**

The webhook handler in `backend/webhooks/stripe.py` (lines 120-127) processes
exactly three event types:

| Event Type | Handler | Line |
|---|---|---|
| `customer.subscription.updated` | `_handle_subscription_updated` | 120 |
| `customer.subscription.deleted` | `_handle_subscription_deleted` | 122 |
| `invoice.payment_succeeded` | `_handle_invoice_payment_succeeded` | 124 |
| **All other events** | **Logged and ignored** | **126-127** |

`checkout.session.completed` falls into the "else" branch at line 126-127:
```python
else:
    logger.info(f"Unhandled event type: {event.type}")
```

The GTM-002 story (`docs/stories/GTM-002-modelo-assinatura-unico.md`) explicitly
required this handler at lines 73, 223, and 329, but it was never implemented.

### 1.4 What Happens After Payment Today

Complete user journey when someone pays:

1. User clicks "Assinar" on the pricing page
2. Frontend calls `POST /v1/checkout?plan_id=smartlic_pro&billing_period=monthly`
3. Backend creates Stripe Checkout Session with `mode="payment"` (BUG: should be subscription)
4. User is redirected to Stripe, enters card, pays
5. Stripe fires `checkout.session.completed` webhook
6. Backend receives webhook, logs "Unhandled event type: checkout.session.completed"
7. **User's plan remains `free_trial`**
8. User is redirected to `/planos/obrigado?plan=smartlic_pro` (success page)
9. User sees "thank you" but still has trial limitations
10. **User has been charged but received nothing**

### 1.5 Delayed Webhook Impact

Even if the webhook were implemented, there is no polling fallback. If webhook
delivery is delayed 5 minutes, the user would be on `free_trial` for that entire
duration. There is no client-side verification of checkout session status.

---

## 2. Lifecycle Completeness Table

| Operation | Code Exists | Tested | Verdict |
|---|---|---|---|
| Create subscription (checkout) | YES (but mode=payment for smartlic_pro) | NO test for smartlic_pro | BROKEN |
| Activate plan (post-checkout) | `_activate_plan` exists but is dead code | NO | BROKEN |
| `checkout.session.completed` handler | NO | NO | MISSING |
| `customer.subscription.created` handler | NO | NO | MISSING |
| `customer.subscription.updated` handler | YES (L120, L145-220) | YES (24 tests) | WORKS |
| `customer.subscription.deleted` handler | YES (L122, L223-273) | YES (tests AC10-12) | WORKS |
| `invoice.payment_succeeded` handler | YES (L124, L276-336) | YES (tests AC13-14) | WORKS |
| `invoice.payment_failed` handler | NO | NO | MISSING |
| Change billing period | YES (`routes/subscriptions.py`) | YES (4 tests) | WORKS |
| Cancel subscription (standalone) | NO endpoint exists | NO | MISSING |
| Cancel at period end | NO `cancel_at_period_end` usage | NO | MISSING |
| Reactivate after cancellation | NO endpoint exists | NO | MISSING |
| Handle refund | NO handler | NO | MISSING |
| Account deletion (with Stripe cancel) | YES (`routes/user.py` L260-345) | Not verified | PARTIAL |
| Dunning (payment failure notification) | NO | NO | MISSING |

**Summary:** 4 of 15 lifecycle operations work. 11 are missing or broken.

---

## 3. Payment Failure Handling

### 3.1 invoice.payment_failed

**NOT HANDLED.** A codebase-wide search for `invoice.payment_failed` returns zero
results in all Python files.

When a card is declined on renewal:
1. Stripe fires `invoice.payment_failed`
2. Backend logs "Unhandled event type: invoice.payment_failed" and returns 200
3. The subscription remains `is_active=True` in the database
4. User continues to have full access despite non-payment
5. Eventually Stripe cancels the subscription (fires `customer.subscription.deleted`)
6. Backend marks subscription inactive and sets `plan_type=free_trial`

**Impact:** There is a window (Stripe default: up to 4 failed attempts over ~3 weeks)
where the user has full access without paying. No email notification is sent to
the user about the failed payment. No in-app banner warns them.

### 3.2 Dunning Process

No dunning process exists:
- No `invoice.payment_failed` handler
- No email template for failed payments
- No in-app notification for billing issues
- No grace period differentiation between "payment processing" and "declined"
- Full reliance on Stripe's Smart Retries (which is good, but the app should still
  inform the user)

---

## 4. Quota Enforcement

### 4.1 Atomic Operations

**File:** `backend/quota.py` lines 437-497, Migration: `supabase/migrations/003_atomic_quota_increment.sql`

The `check_and_increment_quota_atomic()` function correctly:
- Calls PostgreSQL RPC `check_and_increment_quota` (line 465)
- Uses `FOR UPDATE` row locking in the SQL function (migration L32)
- Has `ON CONFLICT DO UPDATE` with conditional increment (migration L90-97)
- Returns `(allowed, new_count, quota_remaining)` tuple

**Verdict: PASS.** The atomic quota implementation is solid. The PostgreSQL function
uses row-level locking and atomic upsert to prevent race conditions.

### 4.2 Fallback Behavior

If the RPC function is unavailable (`quota.py` lines 489-497):
- Falls back to non-atomic check (read current, compare, then increment)
- This has a TOCTOU window but is better than blocking the user
- The fallback correctly calls `increment_monthly_quota` which itself uses upsert

**Minor concern:** The fallback at line 409-424 (`increment_monthly_quota`) reads
current count, adds 1 in Python, then upserts. This is NOT truly atomic -- two
concurrent requests could both read count=5, both write count=6, losing one
increment. However, this is the fallback path and the RPC path is the primary.

### 4.3 Grace Period

**File:** `backend/quota.py` lines 504-505, 611-639, 678-701

- `SUBSCRIPTION_GRACE_DAYS = 3` (line 505)
- Layer 2 checks for recently-expired subscriptions within grace period (lines 612-639)
- Expired paid plans get a 3-day grace window before blocking (lines 679-701)
- Free trial expires immediately with no grace (lines 665-677)

**Verdict: PASS.** Grace period logic is correct and well-documented.

### 4.4 Multi-Layer Plan Resolution

The `check_quota()` function (lines 565-733) uses a 4-layer lookup:
1. Active subscription (primary)
2. Recently-expired within grace period
3. `profiles.plan_type` (fallback -- prevents "fail to free")
4. `free_trial` (absolute last resort)

**Verdict: PASS.** This is well-engineered and prevents the "paid user sees free
trial" anti-pattern during transient DB errors.

---

## 5. Security Assessment

### 5.1 Webhook Signature Validation

**File:** `backend/webhooks/stripe.py` lines 82-99

- Uses `stripe.Webhook.construct_event()` with signature verification (line 91-93)
- Rejects missing `stripe-signature` header with HTTP 400 (lines 85-87)
- Handles `ValueError` (invalid payload) with HTTP 400 (lines 94-96)
- Handles `SignatureVerificationError` with HTTP 400 (lines 97-99)
- `STRIPE_WEBHOOK_SECRET` loaded from environment variable (line 46)

**Verdict: PASS.** Signature validation is correctly implemented.

### 5.2 Idempotency Protection

**File:** `backend/webhooks/stripe.py` lines 106-117

- Checks `stripe_webhook_events` table for duplicate event IDs (lines 107-113)
- Returns `{"status": "already_processed"}` for duplicates (lines 115-117)
- Records processed events with timestamp (lines 130-135)
- Database has RLS policies restricting inserts to `service_role` only
  (verified in `test_webhook_rls_security.py`)

**Verdict: PASS.** Idempotency is correctly implemented.

### 5.3 API Keys in Frontend

No `STRIPE_SECRET_KEY` or `STRIPE_WEBHOOK_SECRET` found in frontend code.
Frontend only interacts with Stripe via the checkout URL returned by the backend.

**Verdict: PASS.**

### 5.4 Rate Limiting on Checkout Endpoint

**NOT IMPLEMENTED.** The `POST /v1/checkout` endpoint has no rate limiting.
An attacker could:
- Create thousands of Stripe Checkout Sessions (each costing Stripe API calls)
- Enumerate valid plan IDs
- Potentially trigger Stripe rate limits that affect legitimate users

The endpoint requires authentication (`Depends(require_auth)`), which provides
some protection, but a compromised or malicious authenticated user could still
abuse it.

**Verdict: MINOR RISK.** Authentication provides baseline protection, but a
dedicated rate limiter (e.g., 5 checkout sessions per user per hour) would be
appropriate.

### 5.5 Webhook RLS Security

Verified via `test_webhook_rls_security.py`:
- INSERT restricted to `service_role` (migration 028)
- SELECT restricted to admins via `is_admin` check (migration 028)
- CHECK constraint enforces `evt_` prefix on event IDs (migration 010)

**Verdict: PASS.**

---

## 6. Critical Gaps (Ordered by Severity)

### P0 -- Revenue-Blocking (Must fix before launch)

**GAP-01: `checkout.session.completed` webhook not handled**
- **Impact:** Paying customers never get their plan activated
- **Evidence:** `webhooks/stripe.py` lines 120-127 -- only 3 event types handled
- **Story reference:** GTM-002 lines 73, 223, 329 explicitly required this
- **Fix:** Add handler that calls `_activate_plan()` with session data

**GAP-02: `smartlic_pro` checkout creates one-time payment instead of subscription**
- **Impact:** No recurring billing, no subscription lifecycle events
- **Evidence:** `routes/billing.py` line 63 -- `smartlic_pro` not in subscription list
- **Fix:** Add `"smartlic_pro"` to the `is_subscription` check, or better, derive
  subscription mode from the plan's configuration

**GAP-03: `_activate_plan()` is dead code -- never called**
- **Impact:** Even if checkout.session.completed were handled, no code path invokes activation
- **Evidence:** Only 2 references in codebase: definition (billing.py:82) and docstring (quota.py:512)
- **Fix:** Wire `_activate_plan()` into the `checkout.session.completed` handler

### P1 -- Revenue Leakage

**GAP-04: `invoice.payment_failed` not handled**
- **Impact:** Users retain access for weeks during payment failure retry cycle
- **Evidence:** Zero code references to this event type
- **Fix:** Add handler that marks subscription as "past_due", notifies user

**GAP-05: No standalone cancel subscription endpoint**
- **Impact:** Users cannot cancel without deleting their entire account
- **Evidence:** Cancel only exists in `user.py:delete_account` (line 292)
- **Fix:** Add `POST /v1/subscriptions/cancel` with `cancel_at_period_end=True`

### P2 -- Operational Gaps

**GAP-06: No `customer.subscription.created` handler**
- **Impact:** New subscriptions only sync via `subscription.updated` (which may not fire
  on initial creation depending on Stripe configuration)
- **Fix:** Add handler or rely on `checkout.session.completed` for initial activation

**GAP-07: No subscription reactivation endpoint**
- **Impact:** Cancelled users must go through full checkout again instead of reactivating
- **Fix:** Add `POST /v1/subscriptions/reactivate` for subscriptions cancelled with
  `cancel_at_period_end=True` (before period end)

**GAP-08: No refund handling**
- **Impact:** Refunded users keep their plan until manual intervention
- **Fix:** Handle `charge.refunded` or `invoice.payment_refunded` webhooks

**GAP-09: No dunning notifications**
- **Impact:** Users with failing payments have no visibility into billing issues
- **Fix:** Email template + in-app banner when `invoice.payment_failed` fires

**GAP-10: No rate limiting on checkout endpoint**
- **Impact:** Potential abuse by authenticated users
- **Fix:** Add per-user rate limit (e.g., 5 sessions/hour)

---

## 7. What Works Well

Despite the critical gaps, several components are well-implemented:

1. **Webhook signature validation** -- proper use of `stripe.Webhook.construct_event()`
2. **Idempotency** -- database-backed duplicate event detection
3. **Quota enforcement** -- atomic PostgreSQL RPC with row-level locking
4. **Multi-layer plan resolution** -- 4-layer fallback prevents false downgrades
5. **Grace period** -- 3-day buffer for billing gaps
6. **`profiles.plan_type` sync** -- all existing webhook handlers sync the fallback column
7. **Thread-safe Stripe calls** -- `api_key=` parameter, not global `stripe.api_key`
8. **RLS security** -- webhook events table properly locked down
9. **Test coverage for existing handlers** -- 24+ tests covering AC1-AC24
10. **Email notifications** -- payment confirmation and cancellation emails fire-and-forget

---

## 8. Test Coverage Summary

| Test File | Tests | Coverage Area |
|---|---|---|
| `test_stripe_webhook.py` | 24 | Signature, idempotency, sub updated/deleted, invoice paid |
| `test_billing_period_update.py` | 4 | Monthly to annual/semiannual, error cases |
| `test_webhook_rls_security.py` | 17 | RLS policies, CHECK constraints, migration SQL |
| `test_quota.py` | (exists) | Quota check/increment |
| `test_quota_race_condition.py` | (exists) | Concurrent quota operations |

**Missing test coverage:**
- `checkout.session.completed` handling (handler does not exist)
- `_activate_plan()` (dead code, no test)
- `smartlic_pro` checkout mode (should be subscription, tested as payment)
- `invoice.payment_failed` handling (handler does not exist)
- Cancel subscription flow (endpoint does not exist)
- Reactivation flow (endpoint does not exist)

---

## 9. Conclusion

The Stripe revenue infrastructure has strong foundations (security, idempotency,
quota enforcement) but is **fundamentally broken at the checkout-to-activation
junction**. A user who pays R$1,999/month will have their card charged but will
remain on `free_trial` with 3 searches/month.

The three P0 gaps (GAP-01, GAP-02, GAP-03) must all be fixed together -- they
form a chain: checkout mode must be `subscription` -> `checkout.session.completed`
must be handled -> `_activate_plan()` must be called.

Estimated fix effort for P0: 2-4 hours (the activation code already exists, it
just needs to be wired up and the checkout mode fixed).

Estimated fix effort for P1+P2: 1-2 sprints for full lifecycle completeness.
