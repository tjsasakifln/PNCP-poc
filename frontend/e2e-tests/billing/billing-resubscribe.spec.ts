/**
 * AC4 — Re-subscribe flow.
 *
 * Starting from a canceled-but-within-grace-period subscription:
 *   - Visit /planos and click "Reativar" (or generic upgrade CTA).
 *   - Complete checkout if Stripe prompts for one.
 *   - Assert cancel_at_period_end flips back to false and subscription stays active.
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

test.describe('@billing @stripe Re-subscribe after cancel', () => {
  test.skip(skip, reason || 'Billing test disabled');

  let email: string;

  test.beforeAll(async () => {
    email = makeTestEmail('resubscribe');
  });

  test.afterAll(async () => {
    await cleanupTestCustomer(email);
    await deleteTestUser(email);
  });

  test('AC4.1 setup: subscribe then cancel', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await createTestUser(page, { email, password: DEFAULT_E2E_PASSWORD });
    await billing.goToPlanos();
    await billing.clickUpgrade();
    await billing.fillStripeCheckout(STRIPE_TEST_CARDS.success);
    await billing.waitForSubscriptionActive();
    await waitForWebhookProcessed(page, { expectPlanType: 'smartlic_pro' });

    await billing.goToConta();
    await billing.clickCancelSubscription();
    await billing.confirmCancel('missing_features');
    const canceled = await waitForWebhookProcessed(
      page,
      { expectPlanType: 'smartlic_pro', expectCancelAtPeriodEnd: true },
      30_000,
    );
    expect(canceled?.cancel_at_period_end).toBe(true);
  });

  test('AC4.2 reactivate → cancel_at_period_end=false, subscription active', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await billing.goToPlanos();
    await billing.clickResubscribe();

    // If Stripe Checkout opens, complete it.  Otherwise the reactivation is
    // a one-click server-side flip (Stripe removes the pending cancellation).
    if (/checkout\.stripe\.com/.test(page.url())) {
      await billing.fillStripeCheckout(STRIPE_TEST_CARDS.success);
    }
    await billing.waitForSubscriptionActive();

    const restored = await waitForWebhookProcessed(
      page,
      { expectPlanType: 'smartlic_pro', expectCancelAtPeriodEnd: false },
      30_000,
    );
    expect(restored?.cancel_at_period_end).toBe(false);
    expect(restored?.plan_type).toBe('smartlic_pro');
  });
});
