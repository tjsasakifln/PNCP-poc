/**
 * AC3 — Cancel + grace period.
 *
 * Starting from an active smartlic_pro subscription:
 *   - Open /conta/plano and trigger CancelSubscriptionModal.
 *   - Walk the modal steps (reason → (skip retention) → confirm → skip feedback).
 *   - Assert the backend reports cancel_at_period_end=true.
 *   - Assert the user can still perform a search (grace period).
 *
 * STORY-3.5 — EPIC-TD-2026Q2 (P1)
 */

import { test, expect } from '@playwright/test';
import {
  STRIPE_TEST_CARDS,
  cleanupTestCustomer,
  makeTestEmail,
  shouldSkipBillingTests,
} from './helpers/stripe-fixtures';
import { BillingPageObject } from './helpers/billing-page-objects';
import {
  DEFAULT_E2E_PASSWORD,
  createTestUser,
  deleteTestUser,
  waitForWebhookProcessed,
} from './helpers/billing-test-utils';

const { skip, reason } = shouldSkipBillingTests();

test.describe.configure({ mode: 'serial' });

test.describe('@billing @stripe Cancel + grace period', () => {
  test.skip(skip, reason || 'Billing test disabled');

  let email: string;

  test.beforeAll(async () => {
    email = makeTestEmail('cancel');
  });

  test.afterAll(async () => {
    await cleanupTestCustomer(email);
    await deleteTestUser(email);
  });

  test('AC3.1 setup: subscribe and reach active smartlic_pro', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await createTestUser(page, { email, password: DEFAULT_E2E_PASSWORD });
    await billing.goToPlanos();
    await billing.clickUpgrade();
    await billing.fillStripeCheckout(STRIPE_TEST_CARDS.success);
    await billing.waitForSubscriptionActive();
    const status = await waitForWebhookProcessed(page, { expectPlanType: 'smartlic_pro' });
    expect(status?.plan_type).toBe('smartlic_pro');
  });

  test('AC3.2 cancel subscription → cancel_at_period_end=true', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await billing.goToConta();
    await billing.clickCancelSubscription();
    // Use "missing_features" so we bypass the retention step entirely.
    await billing.confirmCancel('missing_features');

    const status = await waitForWebhookProcessed(
      page,
      { expectPlanType: 'smartlic_pro', expectCancelAtPeriodEnd: true },
      30_000,
    );
    expect(status?.cancel_at_period_end).toBe(true);
    expect(status?.plan_type).toBe('smartlic_pro');
  });

  test('AC3.3 features still active during grace period', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await billing.goToBuscar();
    // The search page should be reachable without redirect to /planos.
    await expect(page).toHaveURL(/\/buscar/);
    // A grace-period banner should be visible somewhere on the account page.
    await billing.goToConta();
    const body = page.locator('body');
    await expect(body).toContainText(/cancel|até|encerra|acesso até|período/i);
  });
});
