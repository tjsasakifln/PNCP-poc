/**
 * AC1 — Trial → Paid upgrade flow.
 *
 * Signup creates a user in trial state, complete onboarding, click Upgrade
 * on /planos, fill Stripe Checkout with the success test card, then assert
 * that the backend reports plan_type=smartlic_pro.
 *
 * Runs serially because all three tests share one user lifecycle.
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

test.describe('@billing @stripe Trial → Paid upgrade', () => {
  test.skip(skip, reason || 'Billing test disabled');

  let email: string;

  test.beforeAll(async () => {
    email = makeTestEmail();
  });

  test.afterAll(async () => {
    await cleanupTestCustomer(email);
    await deleteTestUser(email);
  });

  test('AC1.1 signup creates user in trial active', async ({ page }) => {
    await createTestUser(page, { email, password: DEFAULT_E2E_PASSWORD });

    // Expect redirect to onboarding (new signups) or buscar.
    await expect(page).toHaveURL(/\/onboarding|\/buscar/);

    const status = await page.request.get('/api/trial-status');
    expect(status.ok()).toBeTruthy();
    const body = await status.json();
    expect(body.is_trial_active || body.plan_type === 'free_trial').toBeTruthy();
  });

  test('AC1.2 complete onboarding → lands on /buscar with trial active', async ({ page }) => {
    const billing = new BillingPageObject(page);
    // If we're still on onboarding, skip through it.
    if (!/\/buscar/.test(page.url())) {
      await billing.goToBuscar();
    }
    await expect(page).toHaveURL(/\/buscar/);

    const status = await page.request.get('/api/trial-status');
    expect(status.ok()).toBeTruthy();
    const body = await status.json();
    // Trial should still be active before the upgrade click.
    expect(body.plan_type === 'free_trial' || body.is_trial_active).toBeTruthy();
  });

  test('AC1.3 click upgrade → Stripe Checkout → webhook → plan=smartlic_pro', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await billing.goToPlanos();
    await billing.clickUpgrade();
    await billing.fillStripeCheckout(STRIPE_TEST_CARDS.success);
    await billing.waitForSubscriptionActive();

    const status = await waitForWebhookProcessed(page, { expectPlanType: 'smartlic_pro' });
    expect(status).not.toBeNull();
    expect(status?.plan_type).toBe('smartlic_pro');
  });
});
