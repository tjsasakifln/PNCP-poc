# STORY-215: Stripe/Billing Test Suite — Replace Placeholder Tests

**Status:** Done
**Priority:** P0 — Blocks GTM Launch (Revenue Safety)
**Sprint:** Sprint 2 (Weeks 2-3)
**Estimated Effort:** 3 days
**Source:** AUDIT-FRENTE-3-TESTS (GAP-1), AUDIT-CONSOLIDATED (QA-02)
**Squad:** team-bidiq-backend (dev, qa)

---

## Context

`test_stripe_webhook.py` contains 20 "test" methods across 8 test classes. Of these, **18 contain NO assertions** — they set up mocks, write `# Expected: X` comments, and do nothing else. The remaining 2 have trivial assertions (`assert mock_construct.called or True`).

This means the entire revenue path — webhook processing, subscription activation, billing period updates, cache invalidation, subscription deletion — is **completely untested**. A regression here means silent revenue loss: users pay but don't get upgraded, or subscriptions expire but users retain access.

Additionally, `sys.modules['stripe'] = MagicMock()` is used as a global module replacement, which is fragile and affects other tests in the same session.

## Problem

The billing/Stripe area has the lowest test coverage (Grade D) despite being the most revenue-critical path. 18 of 20 tests are fake.

## Acceptance Criteria

### Webhook Signature Tests

- [x] AC1: Test: Missing `stripe-signature` header → HTTP 400
- [x] AC2: Test: Invalid/tampered payload → HTTP 400
- [x] AC3: Test: Valid signature → HTTP 200, event processed

### Idempotency Tests

- [x] AC4: Test: Duplicate `event.id` → HTTP 200 with `"already_processed"` message
- [x] AC5: Test: New `event.id` → inserted into `stripe_webhook_events` table
- [x] AC6: Test: Database stores `event_id`, `event_type`, `processed_at`

### Subscription Event Tests

- [x] AC7: Test: `customer.subscription.updated` with `interval=month` → sets `billing_period="monthly"` in DB
- [x] AC8: Test: `customer.subscription.updated` with `interval=year` → sets `billing_period="annual"` in DB
- [x] AC9: Test: `customer.subscription.updated` syncs `profiles.plan_type` (critical fallback)
- [x] AC10: Test: `customer.subscription.deleted` → sets `is_active=False` in `user_subscriptions`
- [x] AC11: Test: `customer.subscription.deleted` syncs `profiles.plan_type`
- [x] AC12: Test: Unknown subscription_id → logged warning, no crash (HTTP 200)

### Invoice/Payment Tests

- [x] AC13: Test: `invoice.payment_succeeded` → syncs `profiles.plan_type`
- [x] AC14: Test: `invoice.payment_succeeded` → invalidates features cache key `"features:{user_id}"`

### Cache Invalidation Tests

- [x] AC15: Test: After billing update, cache key `"features:{user_id}"` is deleted from Redis
- [x] AC16: Test: Redis unavailable → webhook still processes (graceful degradation)

### Error Handling Tests

- [x] AC17: Test: Database error during webhook processing → HTTP 500, error logged
- [x] AC18: Test: Unhandled event type → HTTP 200 with `"unhandled"` message
- [x] AC19: Test: Malformed event payload → HTTP 400, not HTTP 500

### Test Infrastructure

- [x] AC20: Remove `sys.modules['stripe'] = MagicMock()` hack — use proper `@patch('stripe.Webhook.construct_event')` instead
- [x] AC21: All tests use actual assertions (no `# Expected:` comments without corresponding asserts)
- [x] AC22: All billing-related pre-existing failures fixed or explicitly skipped with reason

### Coverage Gate

- [x] AC23: `pytest tests/test_stripe_webhook.py --cov=webhooks.stripe --cov-report=term-missing` shows >85% coverage
- [x] AC24: All tests pass with zero warnings about stale mocks

## Validation Metric

- Zero placeholder tests (no test method without at least one `assert`)
- Coverage of `webhooks/stripe.py` > 85%
- `grep -c "assert" tests/test_stripe_webhook.py` > 30

## Risk Mitigated

- P0: Silent revenue loss from webhook processing regression
- P0: User pays but subscription not activated
- P0: Duplicate webhook charges user twice
- P1: Cache not invalidated after plan change

## File References

| File | Change |
|------|--------|
| `backend/tests/test_stripe_webhook.py` | Complete rewrite with real assertions |
| `backend/webhooks/stripe.py` | Target coverage area |
| `backend/tests/conftest.py` | Add Stripe webhook test fixtures |
