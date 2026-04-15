# STORY-3.5: E2E Billing/Subscription Flow (TD-QA-063)

**Priority:** P1 (cobertura crítica — checkout/cancel/upgrade não exercitados E2E)
**Effort:** S (8-16h)
**Squad:** @qa + @dev
**Status:** InReview
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

- [x] `tests/e2e/billing-trial-to-paid.spec.ts` (implemented at `frontend/e2e-tests/billing/billing-trial-to-paid.spec.ts`)
- [x] Signup → confirma trial active → click upgrade → Stripe Checkout (test mode) → assert plan_type updated

### AC2: Plan downgrade flow

- [x] `tests/e2e/billing-downgrade.spec.ts` (implemented at `frontend/e2e-tests/billing/billing-downgrade.spec.ts`)
- [x] Active sub → downgrade (annual → monthly) → confirm prorated change (Stripe handles proration server-side)

### AC3: Cancel + grace period

- [x] `tests/e2e/billing-cancel.spec.ts` (implemented at `frontend/e2e-tests/billing/billing-cancel.spec.ts`)
- [x] Cancel → assert grace period banner → assert features still active until expiration

### AC4: Re-subscribe

- [x] `tests/e2e/billing-resubscribe.spec.ts` (implemented at `frontend/e2e-tests/billing/billing-resubscribe.spec.ts`)
- [x] Cancelled user → re-subscribe → assert plan reactivated (`cancel_at_period_end=false`)

### AC5: Stripe test mode

- [x] Use Stripe test mode keys in CI (secondary job `e2e-billing` gated on `STRIPE_TEST_SECRET_KEY` secret)
- [x] Test cards: `4242 4242 4242 4242` (success), `4000 0000 0000 0002` (decline), `4000 0027 6000 3184` (3DS) in `helpers/stripe-fixtures.ts`

---

## Tasks / Subtasks

- [x] Task 1: Setup Stripe test mode + test fixtures (`helpers/stripe-fixtures.ts` with `STRIPE_TEST_CARDS`, `shouldSkipBillingTests`, `cleanupTestCustomer`)
- [x] Task 2: 4 specs (AC1-4) with `@billing @stripe` tags and `test.describe.configure({ mode: 'serial' })`
- [x] Task 3: CI integration — new `e2e-billing` job in `.github/workflows/e2e.yml` (existing `e2e-tests` job unchanged); job gracefully skips when `STRIPE_TEST_SECRET_KEY` is absent
- [x] Task 4: Cleanup — `frontend/scripts/cleanup-stripe-test-customers.js` + per-spec `afterAll` hooks + CI always-on cleanup step
- [x] Task 5: Page objects (`helpers/billing-page-objects.ts`) wrapping /planos, /conta/plano, Stripe Checkout
- [x] Task 6: Test utilities (`helpers/billing-test-utils.ts`) — `createTestUser`, `loginTestUser`, `waitForWebhookProcessed`, `deleteTestUser`, `pollEndpoint`
- [x] Task 7: Update `frontend/e2e-tests/README.md` with billing section
- [x] Task 8: `.gitignore` entries for billing fixtures secrets

## Dev Notes

- `backend/services/billing.py` — backend integration
- `backend/webhooks/stripe.py` — webhook handlers
- Stripe webhooks em test mode requerem ngrok ou similar local — usar staging URL em CI
- Billing specs são OPT-IN: sem `STRIPE_TEST_SECRET_KEY` + `E2E_BILLING_ENABLED`, todas skipam com reason visível. Isso preserva o job principal `e2e-tests`.
- `cleanupTestCustomer` recusa chaves que não comecem com `sk_test_` (guard-rail contra execução em live mode).
- O Deep-link polling usa `/api/trial-status` (user.py) e `/api/subscription/status` (billing proxy) — mesmos endpoints que o frontend consome.
- Single-plan model (GTM-002): não há downgrade de tier — "downgrade" nesta story significa mudança de billing period (annual → monthly) com proração automática do Stripe.

## Testing

- E2E principal rodam em CI workflow `.github/workflows/e2e.yml` job `e2e-tests` (inalterado).
- Billing E2E rodam em novo job `e2e-billing` (condicional em `STRIPE_TEST_SECRET_KEY`).
- Manual run local: `STRIPE_TEST_SECRET_KEY=sk_test_... E2E_BILLING_ENABLED=true npx playwright test --grep @billing`.
- Manual cleanup: `STRIPE_TEST_SECRET_KEY=sk_test_... node scripts/cleanup-stripe-test-customers.js --dry-run`.

## Definition of Done

- [x] 4 specs criados
- [x] CI workflow atualizado (secondary job, não bloqueante)
- [x] Cleanup script operacional com `--dry-run` e guard contra live keys
- [x] `npx playwright test --list --grep @billing` lista 20 tests (4 specs × 5 tests × 2 projetos / ajustado) em 4 arquivos sem erro
- [x] `npx tsc --noEmit` sem erros relacionados aos novos arquivos

## Risks

- **R1**: Stripe webhooks delay → flaky tests — mitigation: poll `/api/trial-status` com `waitForWebhookProcessed` (30s timeout, 1s interval).
- **R2**: Test customers acumulam em Stripe — mitigation: `afterAll` hooks + CI sweeper via `cleanup-stripe-test-customers.js`.
- **R3**: Billing specs flaky em dev sem Stripe configurado — mitigation: `shouldSkipBillingTests` gate skipa tudo cleanly.
- **R4**: Execução acidental contra live Stripe — mitigation: helpers recusam chaves não-`sk_test_`.

## File List

**Novos arquivos:**

- `frontend/e2e-tests/billing/helpers/stripe-fixtures.ts`
- `frontend/e2e-tests/billing/helpers/billing-page-objects.ts`
- `frontend/e2e-tests/billing/helpers/billing-test-utils.ts`
- `frontend/e2e-tests/billing/billing-trial-to-paid.spec.ts`
- `frontend/e2e-tests/billing/billing-downgrade.spec.ts`
- `frontend/e2e-tests/billing/billing-cancel.spec.ts`
- `frontend/e2e-tests/billing/billing-resubscribe.spec.ts`
- `frontend/scripts/cleanup-stripe-test-customers.js`

**Arquivos modificados:**

- `.github/workflows/e2e.yml` — adicionado job `e2e-billing` (job `e2e-tests` inalterado)
- `frontend/e2e-tests/README.md` — seção "Billing E2E Suite (STORY-3.5)"
- `.gitignore` — padrões para `frontend/e2e-tests/billing/fixtures/*.secret.{json,yaml}`

## Change Log

| Date       | Version | Description                                       | Author |
|------------|---------|---------------------------------------------------|--------|
| 2026-04-14 | 1.0     | Initial draft                                     | @sm    |
| 2026-04-14 | 2.0     | E2E billing specs + helpers + CI gate             | @dev   |
