# GTM-FIX-001: Fix Stripe Checkout-to-Activation Chain

## Dimension Impact
- Moves D02 (Payment Reliability) from 3/10 to 6-7/10

## Problem
Critical payment flow broken: `smartlic_pro` not recognized as subscription in `is_subscription()` (billing.py:63), `checkout.session.completed` webhook handler missing (webhooks/stripe.py:120-127), and `_activate_plan()` is dead code never called (billing.py:82). New users complete checkout but subscription never activates.

## Solution
1. Add `smartlic_pro` to subscription list in `is_subscription()`
2. Implement `checkout.session.completed` webhook handler in webhooks/stripe.py
3. Wire `_activate_plan()` to be called from checkout completion handler
4. Ensure Stripe webhook is registered in production environment

## Acceptance Criteria
- [ ] AC1: `is_subscription('smartlic_pro')` returns True
- [ ] AC2: `checkout.session.completed` webhook handler exists and logs receipt
- [ ] AC3: Handler calls `_activate_plan()` with correct customer_id and plan
- [ ] AC4: Test with Stripe CLI: `stripe trigger checkout.session.completed` activates subscription
- [ ] AC5: User's `profiles.plan_type` updates to `smartlic_pro` after checkout
- [ ] AC6: User's `profiles.subscription_status` updates to `active` after checkout
- [ ] AC7: Backend test coverage: test_checkout_session_completed()
- [ ] AC8: Production webhook endpoint registered in Stripe dashboard

## Effort: S (4-8h)
## Priority: P0 (Blocking revenue)
## Dependencies: None

## Files to Modify
- `backend/billing.py` (line 63, line 82)
- `backend/webhooks/stripe.py` (lines 120-127, add new handler)
- `backend/tests/test_billing.py` (add test_checkout_session_completed)

## Testing Strategy
1. Unit test: Mock checkout.session.completed payload → verify _activate_plan() called
2. Integration test: Create test checkout session → trigger webhook → verify DB state
3. Manual test: Complete real checkout in test mode → verify subscription active
4. Monitoring: Add Sentry breadcrumb for checkout completions
