# GTM-FIX-001: Fix Stripe Checkout-to-Activation Chain

## Dimension Impact
- Moves D02 (Payment Reliability) from 3/10 to 6-7/10

## Problem
Critical payment flow broken: `smartlic_pro` not recognized as subscription in `is_subscription()` (billing.py:63), `checkout.session.completed` webhook handler missing (webhooks/stripe.py:120-127), and `_activate_plan()` is dead code never called (billing.py:82). New users complete checkout but subscription never activates.

## Solution
1. `smartlic_pro` already in subscription list in `is_subscription()` (routes/billing.py:63) -- verified
2. `checkout.session.completed` handler already implemented in webhooks/stripe.py:150-227 -- verified
3. Added `subscription_status: "active"` to both user_subscriptions INSERT and profiles UPDATE in the checkout handler (was the missing piece preventing AC6)
4. Removed dead `_activate_plan()` from routes/billing.py -- webhook handler is the canonical activation path
5. Ensure Stripe webhook is registered in production environment (AC8 -- requires manual step)

## Acceptance Criteria
- [x] AC1: `is_subscription('smartlic_pro')` returns True
- [x] AC2: `checkout.session.completed` webhook handler exists and logs receipt
- [x] AC3: Handler activates plan with correct customer_id, plan, and billing_period
- [ ] AC4: Test with Stripe CLI: `stripe trigger checkout.session.completed` activates subscription
- [x] AC5: User's `profiles.plan_type` updates to `smartlic_pro` after checkout
- [x] AC6: User's `profiles.subscription_status` updates to `active` after checkout
- [x] AC7: Backend test coverage: test_checkout_session_completed() (8 tests in TestCheckoutSessionCompleted)
- [ ] AC8: Production webhook endpoint registered in Stripe dashboard

## Effort: S (4-8h)
## Priority: P0 (Blocking revenue)
## Dependencies: None

## Files Modified
- `backend/routes/billing.py` -- Removed dead `_activate_plan()` function (lines 82-112)
- `backend/webhooks/stripe.py` -- Added `subscription_status: "active"` to checkout handler (lines 215, 220-222)
- `backend/tests/test_stripe_webhook.py` -- Added `test_checkout_completed_sets_subscription_status_active` test

## Testing Strategy
1. Unit test: Mock checkout.session.completed payload → verify _activate_plan() called
2. Integration test: Create test checkout session → trigger webhook → verify DB state
3. Manual test: Complete real checkout in test mode → verify subscription active
4. Monitoring: Add Sentry breadcrumb for checkout completions
