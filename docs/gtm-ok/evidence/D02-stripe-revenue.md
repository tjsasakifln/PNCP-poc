# D02 - Stripe Revenue Infrastructure Evidence

**Assessor:** @architect (Phase 2, GTM-OK v2.0 Workflow)
**Date:** 2026-02-17
**Scope:** Complete revenue lifecycle audit -- checkout, activation, renewal, cancellation, payment failure, quota enforcement
**Method:** Static code analysis of all source files (no runtime verification)

---

## Executive Summary

The Stripe revenue infrastructure is **functionally complete** for the core lifecycle (checkout -> activation -> renewal -> cancel -> dunning) and demonstrates several production-quality patterns (idempotency, signature validation, multi-layer fallback). However, there are **7 identified gaps** that range from moderate to significant, including missing customer reuse, non-atomic idempotency, incomplete subscription_status sync, no refund handling, and a race window in the checkout-to-activation path.

**D02 Score: 6/10 (Conditional -- significant gaps but functional core)**

---

## 1. Checkout-to-Activation Flow

### 1.1 Checkout Creation (`routes/billing.py` L33-79)

**PRESENT:**
- `POST /v1/checkout` creates a Stripe Checkout Session
- Validates `billing_period` is one of `monthly | semiannual | annual`
- Fetches plan from DB, validates `is_active=True`
- Dynamically resolves `stripe_price_id_{period}` from plan record
- Sets `mode="subscription"` for known subscription plans (L63)
- Passes `client_reference_id=user["id"]` (critical for webhook linkage)
- Passes `metadata={plan_id, user_id, billing_period}` (redundant safety)
- Uses `api_key=` parameter (thread-safe, not global)
- Returns `checkout_url` for frontend redirect

**ISSUES:**

| # | Severity | Issue | Impact |
|---|----------|-------|--------|
| B1 | MEDIUM | **No Stripe Customer reuse.** Uses `customer_email` (L76) on every checkout, creating a new Stripe Customer each time. Repeat customers will have multiple Customer objects. | Stripe Customer fragmentation; duplicate payment methods; billing portal shows incomplete history. |
| B2 | LOW | **No `customer` parameter.** If the user already has a `stripe_customer_id` (stored in `user_subscriptions`), it should be passed to `Session.create(customer=...)` to reuse the existing Customer. | Existing payment methods not pre-populated at checkout. |
| B3 | LOW | **`is_subscription` is hardcoded list** (L63). If a new plan is added to the DB, it will NOT be treated as a subscription unless the code is also updated. | New plans would default to one-time `payment` mode instead of `subscription`. |

### 1.2 Checkout Completion (`webhooks/stripe.py` L150-232)

**PRESENT:**
- `checkout.session.completed` handler is implemented and registered
- Extracts `client_reference_id` (user_id), `metadata.plan_id`, `metadata.billing_period`
- Looks up plan for `duration_days` and `max_searches`
- **Deactivates previous active subscriptions** (L201-203) before inserting new one
- Creates new `user_subscriptions` row with all required fields
- Sets `subscription_status="active"` in both subscription and profile
- Syncs `profiles.plan_type` (critical fallback)
- Invalidates Redis cache
- Graceful handling: missing metadata/user_id causes `return` (no crash)

**ISSUES:**

| # | Severity | Issue | Impact |
|---|----------|-------|--------|
| A1 | HIGH | **Activation depends entirely on webhook delivery.** If Stripe's webhook is delayed (minutes to hours), the user sees the "Obrigado" page but has no active plan. The frontend `/planos/obrigado` page (L34-115) shows "Assinatura confirmada!" purely based on the `?plan=` URL parameter, regardless of whether the webhook has fired. | User pays, sees confirmation, but searches are blocked until webhook arrives. No polling or fallback mechanism exists. |
| A2 | MEDIUM | **No webhook replay handling.** If the webhook endpoint returns 500 (e.g., DB down), Stripe will retry, but the idempotency check depends on a SELECT then INSERT that is NOT atomic (see Section 5). A retry could fail on the SELECT and re-process the event. | Potential double activation is mitigated by the deactivation step (L201) but could leave orphan subscription rows. |
| A3 | LOW | **`duration_days` defaults to 30 if plan not found** (L192-196). For subscription-based billing this field is somewhat misleading since Stripe manages the actual billing cycle. The `expires_at` field is set from `duration_days` but is never updated by Stripe's `current_period_end`. | `expires_at` drifts from Stripe's actual period end over time. |

### 1.3 Frontend Post-Checkout (`frontend/app/planos/obrigado/page.tsx`)

**PRESENT:**
- Shows plan name, capabilities, and links to `/buscar` and `/conta`
- Fires `checkout_completed` analytics event
- Shows receipt email notice

**ISSUES:**
- **No backend verification.** Page does NOT call any API to verify the subscription is actually active. It trusts the `?plan=` query parameter entirely.

---

## 2. Payment Failure Handling

### 2.1 `invoice.payment_failed` Handler (`webhooks/stripe.py` L429-516)

**PRESENT:**
- Updates `subscription_status` to `past_due` in both `user_subscriptions` and `profiles` tables
- Extracts `attempt_count` and `amount_due` from invoice data
- Logs to Sentry with full context (user_id, plan_id, customer_id, attempt_count, amount)
- Structured logging for analytics tracking
- Sends payment failed email via `_send_payment_failed_email()` (fire-and-forget, never raises)
- Email includes: user name, plan name, amount, failure reason, days until cancellation
- Graceful: no-subscription-found returns early; no-subscription_id returns early

**ISSUES:**

| # | Severity | Issue | Impact |
|---|----------|-------|--------|
| P1 | MEDIUM | **No credit/quota reset on payment failure.** When payment fails and status becomes `past_due`, the user's quota continues to work normally (quota.py does not check `subscription_status`). Only `is_active` and `expires_at` are checked. | Users on `past_due` status continue to have full access indefinitely until Stripe cancels the subscription. |
| P2 | LOW | **`_send_payment_failed_email` uses generic failure reason** when charge is a string ID (L646-647). The actual charge details are not fetched from Stripe API. | Email says "Nao foi possivel processar o pagamento" instead of the specific bank decline reason. |

### 2.2 Dunning Process

**PRESENT (partial):**
- Stripe's built-in Smart Retries handle automatic payment retry (up to 4 attempts over ~2 weeks)
- Email template calculates `days_until_cancellation = max(0, 14 - attempt_count * 3)` (L656)
- After final failure, Stripe sends `customer.subscription.deleted` which is handled

**MISSING:**
- No in-app banner or notification for `past_due` users (only email)
- No manual retry option via the billing portal (though the billing portal link is in the email)

---

## 3. Subscription Lifecycle

### 3.1 Create Subscription
- **Handled by:** `checkout.session.completed` webhook
- **Status:** IMPLEMENTED and TESTED (7 tests in `TestCheckoutSessionCompleted`)

### 3.2 Activate Plan Post-Checkout
- **Handled by:** `_handle_checkout_session_completed()` in `webhooks/stripe.py`
- **Status:** IMPLEMENTED -- creates subscription row, syncs profiles, invalidates cache
- **Gap:** See A1 (webhook delay)

### 3.3 Change Billing Period
- **Handled by:** `POST /api/subscriptions/update-billing-period` in `routes/subscriptions.py`
- **Status:** IMPLEMENTED and TESTED (4 tests in `test_billing_period_update.py`)
- Uses `stripe.Subscription.modify()` with `proration_behavior="create_prorations"`
- Updates local DB and invalidates cache
- **Correctly detects** DATA INCONSISTENCY if Stripe succeeds but DB fails (L146-148)

### 3.4 Cancel Subscription
- **Handled by:** `POST /api/subscriptions/cancel` in `routes/subscriptions.py`
- **Status:** IMPLEMENTED and TESTED (3 tests in `test_cancel_subscription.py`)
- Uses `cancel_at_period_end=True` (correct -- user retains access until period end)
- Updates `profiles.subscription_status` to `"canceling"`
- Logs action via `log_user_action`
- Returns `ends_at` date to user

### 3.5 Handle Cancellation at Period End
- **Handled by:** `customer.subscription.deleted` webhook
- **Status:** IMPLEMENTED -- deactivates subscription, sets `profiles.plan_type` to `free_trial`
- Sends cancellation confirmation email with reactivation link
- **Gap:** Does NOT set `profiles.subscription_status` to `"canceled"` (only sets `plan_type` to `free_trial`). The `subscription_status` field is stale after deletion.

### 3.6 Reactivate After Cancellation
- **Status:** NOT IMPLEMENTED
- No endpoint exists for resubscription. User would need to go through full checkout flow again.
- Cancellation email template includes a "reactivation link" (tested in `test_email_templates.py` L276-277), but this likely links to `/planos` (new checkout), not a true reactivation.

### 3.7 Handle Payment Failure
- **Handled by:** `invoice.payment_failed` webhook
- **Status:** IMPLEMENTED and TESTED (5 tests in `test_payment_failed_webhook.py`)

### 3.8 Handle Refund
- **Status:** NOT IMPLEMENTED
- No `charge.refunded` or `charge.dispute.*` webhook handlers exist
- No refund API endpoint exists
- If a refund occurs in Stripe dashboard, the local system has no awareness

### Lifecycle Coverage Matrix

| Operation | Code | Tests | Stripe Webhook | Profile Sync | Cache Invalidation |
|-----------|------|-------|----------------|-------------|-------------------|
| Create (checkout) | YES | 7 | `checkout.session.completed` | YES (`plan_type` + `subscription_status`) | YES |
| Update (billing period) | YES | 4 | `customer.subscription.updated` | YES (`plan_type`) | YES |
| Cancel (at period end) | YES | 3 | `customer.subscription.deleted` | PARTIAL (plan_type but not subscription_status) | YES |
| Renew (invoice paid) | YES | 4 | `invoice.payment_succeeded` | YES (`plan_type`) | YES |
| Payment failure | YES | 5 | `invoice.payment_failed` | YES (`subscription_status`) | NO (not invalidated) |
| Refund | NO | NO | NOT HANDLED | N/A | N/A |
| Reactivate | NO | NO | N/A (new checkout) | N/A | N/A |

---

## 4. Quota Enforcement (`quota.py`)

### 4.1 `check_quota()` (L565-733)

**PRESENT:**
- 4-layer resilience pattern:
  1. Active subscription (primary)
  2. Recently-expired subscription within 3-day grace period
  3. `profiles.plan_type` (reliable fallback)
  4. `free_trial` (absolute last resort)
- Monthly quota tracking via `monthly_quota` table
- Atomic increment via PostgreSQL RPC function `check_and_increment_quota`
- Plan capabilities loaded from DB with 5-min in-memory cache
- Proper expiry handling: free_trial blocks immediately; paid plans get grace period

**QUALITY:**
- The "fail to last known plan" pattern is excellent -- prevents paid users from being downgraded on transient errors
- Grace period (3 days) bridges Stripe billing gaps
- Atomic quota increment eliminates TOCTOU race conditions (when RPC function is available)

**ISSUES:**

| # | Severity | Issue | Impact |
|---|----------|-------|--------|
| Q1 | MEDIUM | **`subscription_status` not checked in quota.** `check_quota()` only checks `is_active` and `expires_at`, not `subscription_status`. A user with `subscription_status=past_due` continues with full access. | Revenue leakage during dunning period. |
| Q2 | LOW | **Fallback quota gives `quota_remaining=999999`** (L837). When subscription check fails, the fallback grants effectively unlimited searches. | In DB-down scenarios, a user could run unlimited searches on the fallback plan. |
| Q3 | LOW | **`credits_remaining` on checkout** (L210) but quota uses `monthly_quota` table. Two parallel quota tracking systems exist. | Confusion; `credits_remaining` in `user_subscriptions` is never decremented by the main quota path. |

---

## 5. Security Analysis

### 5.1 Webhook Signature Validation

**PRESENT and CORRECT:**
- `stripe.Webhook.construct_event()` validates signature (L92-94)
- Missing `stripe-signature` header -> 400 (L86-88)
- Invalid signature -> 400 (L98-100)
- Invalid payload -> 400 (L96-97)
- `STRIPE_WEBHOOK_SECRET` loaded from env at module level (L47)
- Warning logged if not configured (L49-50)

**QUALITY:** Excellent. No bypasses possible.

### 5.2 Idempotency

**PRESENT but has gap:**
- Checks `stripe_webhook_events` table for existing event ID (L107-114)
- Records processed events with id, type, processed_at, payload (L135-140)

**ISSUE:**

| # | Severity | Issue | Impact |
|---|----------|-------|--------|
| S1 | MEDIUM | **Non-atomic idempotency.** The SELECT check (L108-114) and INSERT record (L135-140) are separate operations with the event handler running between them. If two identical webhook deliveries arrive simultaneously, both could pass the SELECT (both see empty), both process the event, and one INSERT would fail (if `id` has a UNIQUE constraint) or both succeed (if no constraint). | Potential double-processing of webhook events under concurrent delivery. Mitigated by Stripe's sequential delivery model, but not guaranteed. |

### 5.3 No API Keys in Frontend

**VERIFIED:** Grep found zero matches for `STRIPE_SECRET_KEY` or `STRIPE_WEBHOOK_SECRET` in the `frontend/` directory.

### 5.4 Thread Safety

**PRESENT:**
- `stripe.api_key` NOT set globally (noted in comments at L45-46 of stripe.py, L49 of billing.py)
- All Stripe API calls use `api_key=` parameter

### 5.5 PII in Logs

- Log sanitizer used (`get_sanitized_logger`, `mask_user_id`)
- User IDs masked in all log messages
- Stripe customer/subscription IDs truncated in logs (e.g., `[:8]***`)

---

## 6. Test Coverage Assessment

### 6.1 Files and Test Count

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_stripe_webhook.py` | ~40 | Signature validation, idempotency, all 5 event types, edge cases, meta-quality checks |
| `test_cancel_subscription.py` | 3 | Success, no-active, no-stripe-id |
| `test_billing_period_update.py` | 4 | Monthly->annual, monthly->semiannual, no-active, already-on-target |
| `test_payment_failed_webhook.py` | 7 | Status update, email sending, no-subscription, attempt count, no-sub-id, email template (2) |
| **Total** | ~54 | |

### 6.2 What IS Tested

- All 5 webhook event types (checkout.completed, subscription.updated, subscription.deleted, invoice.paid, invoice.failed)
- Signature validation (missing, invalid, valid)
- Idempotency (duplicate events)
- Profile sync on all event types
- Cache invalidation on all event types
- Unknown subscription handling (graceful)
- Billing period inference (monthly, semiannual, annual)
- Plan change via metadata
- Missing metadata edge cases
- Email template rendering
- Test quality meta-checks (no sys.modules hack, no assertion-free tests, >30 assertions)

### 6.3 What is NOT Tested

| Gap | Severity |
|-----|----------|
| **No integration test** with real Stripe API (even in test mode) | MEDIUM |
| **No test for concurrent webhook processing** (race condition in idempotency) | MEDIUM |
| **No test for webhook signature with actual HMAC** (all mocked) | LOW |
| **Checkout creation endpoint** (`POST /checkout`) has no dedicated test file | MEDIUM |
| **`check_quota` interaction with billing events** not tested end-to-end | MEDIUM |
| **No test for `customer.subscription.updated` with `cancel_at_period_end` status** | LOW |
| **No test for webhook failure + Stripe retry behavior** | LOW |

---

## 7. Strengths

1. **Complete lifecycle coverage** -- All critical paths from checkout to cancellation are implemented
2. **Multi-layer quota fallback** -- Excellent resilience pattern prevents "fail to free" anti-pattern
3. **Profile sync on every event** -- `profiles.plan_type` is updated on checkout, update, delete, and payment success
4. **Graceful degradation** -- Redis failure does not block webhook processing; email failures do not crash handlers
5. **Thread-safe Stripe usage** -- `api_key=` parameter instead of global `stripe.api_key`
6. **Dunning flow** -- `invoice.payment_failed` -> status update -> email -> Sentry alert -> structured logging
7. **54 total tests** with good edge case coverage
8. **Cancellation at period end** -- Uses `cancel_at_period_end=True` (correct Stripe pattern)
9. **Billing portal** -- Self-service payment method management via Stripe Billing Portal

---

## 8. Critical Gaps Summary

| # | Issue | Severity | Effort to Fix |
|---|-------|----------|---------------|
| A1 | Webhook-dependent activation with no polling fallback | HIGH | 4-8h |
| S1 | Non-atomic idempotency (SELECT-process-INSERT race) | MEDIUM | 2-4h |
| B1 | No Stripe Customer reuse (new customer per checkout) | MEDIUM | 2-4h |
| Q1 | `subscription_status` not checked in quota enforcement | MEDIUM | 1-2h |
| A3 | `expires_at` drifts from Stripe's `current_period_end` | MEDIUM | 2-4h |
| -- | No refund handling (no `charge.refunded` webhook) | MEDIUM | 4-8h |
| -- | Incomplete `subscription_status` sync on deletion | LOW | 30min |
| Q3 | Dual quota systems (`credits_remaining` vs `monthly_quota`) | LOW | 1-2h cleanup |
| -- | Checkout endpoint not tested | MEDIUM | 2-4h |

---

## 9. D02 Score: 6/10

**Rationale:**

The revenue infrastructure has a **complete functional core** covering the full subscription lifecycle. The code quality is good with proper security (signature validation, no global API keys, log sanitization), resilience (multi-layer fallback, graceful degradation), and reasonable test coverage (54 tests).

However, the system falls short of production-ready (7+) due to:

1. **The activation gap (A1)** is the most serious issue. If a webhook is delayed, a paying customer is stuck with no access. There is no polling mechanism, no client-side verification, and the success page gives false confirmation. This is a revenue AND trust risk.

2. **Non-atomic idempotency (S1)** could cause double-processing under concurrent webhook delivery, though this is partially mitigated by Stripe's delivery model.

3. **No Customer reuse (B1)** means repeat customers get duplicate Stripe Customers, making the billing portal show incomplete history.

4. **Missing refund handling** means admin-initiated refunds in Stripe dashboard leave the local system in an inconsistent state.

5. **`subscription_status` is not checked in quota**, so users in dunning (`past_due`) retain full access.

**To reach 7/10 (Production-Ready):**
- Implement checkout completion polling/verification (A1) -- 4-8h
- Add atomic idempotency via `INSERT ... ON CONFLICT DO NOTHING` (S1) -- 2h
- Implement Stripe Customer reuse (B1) -- 3h
- Check `subscription_status` in `check_quota()` (Q1) -- 1h

**To reach 8/10 (Production-Excellent):**
- All above PLUS:
- Add `charge.refunded` webhook handler -- 4h
- Sync `subscription_status` on deletion handler -- 30min
- Add integration tests with Stripe test mode -- 8h
- Clean up dual quota tracking -- 2h

---

## Appendix: File Inventory

| File | Purpose | Lines |
|------|---------|-------|
| `backend/routes/billing.py` | Checkout creation, billing portal | 142 |
| `backend/webhooks/stripe.py` | All webhook handlers (5 event types) | 674 |
| `backend/routes/subscriptions.py` | Billing period update, cancellation | 269 |
| `backend/services/billing.py` | Stripe subscription modification | 111 |
| `backend/quota.py` | Quota enforcement, plan capabilities | 928 |
| `backend/tests/test_stripe_webhook.py` | Webhook handler tests | 1456 |
| `backend/tests/test_cancel_subscription.py` | Cancellation tests | 116 |
| `backend/tests/test_billing_period_update.py` | Billing period tests | 166 |
| `backend/tests/test_payment_failed_webhook.py` | Payment failure tests | 317 |
| `frontend/app/planos/obrigado/page.tsx` | Post-checkout success page | 116 |
