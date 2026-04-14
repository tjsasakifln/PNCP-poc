# STORY-3.5: E2E Billing/Subscription Flow (TD-QA-063)

**Priority:** P1 (cobertura crítica — checkout/cancel/upgrade não exercitados E2E)
**Effort:** S (8-16h)
**Squad:** @qa + @dev
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 2

---

## Story

**As a** SmartLic,
**I want** Playwright E2E tests cobrindo signup → trial → upgrade → cancel → re-upgrade,
**so that** billing regressions sejam pegos antes de produção.

---

## Acceptance Criteria

### AC1: Trial → Paid upgrade flow

- [ ] `tests/e2e/billing-trial-to-paid.spec.ts`
- [ ] Signup → confirma trial active → click upgrade → Stripe Checkout (test mode) → assert plan_type updated

### AC2: Plan downgrade flow

- [ ] `tests/e2e/billing-downgrade.spec.ts`
- [ ] Active sub → downgrade → confirm prorated change

### AC3: Cancel + grace period

- [ ] `tests/e2e/billing-cancel.spec.ts`
- [ ] Cancel → assert grace period banner → assert features still active until expiration

### AC4: Re-subscribe

- [ ] `tests/e2e/billing-resubscribe.spec.ts`
- [ ] Cancelled user → re-subscribe → assert plan reactivated

### AC5: Stripe test mode

- [ ] Use Stripe test mode keys in CI
- [ ] Test cards: `4242 4242 4242 4242` (success), `4000 0000 0000 0002` (decline)

---

## Tasks / Subtasks

- [ ] Task 1: Setup Stripe test mode + test fixtures
- [ ] Task 2: 4 specs (AC1-4)
- [ ] Task 3: CI integration (Playwright E2E workflow já existe)
- [ ] Task 4: Cleanup test customers via Stripe API after each run

## Dev Notes

- `backend/services/billing.py` — backend integration
- `backend/webhooks/stripe.py` — webhook handlers
- Stripe webhooks em test mode requerem ngrok ou similar local — usar staging URL em CI

## Testing

- E2E rodam em CI workflow `.github/workflows/e2e.yml`
- Manual run via `npm run test:e2e:headed`

## Definition of Done

- [ ] 4 specs criados + CI verde + cleanup script

## Risks

- **R1**: Stripe webhooks delay → flaky tests — mitigation: poll/wait for webhook event
- **R2**: Test customers acumulam em Stripe — mitigation: cleanup script after run

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
