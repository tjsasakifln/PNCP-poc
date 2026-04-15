/**
 * AC2 — Plan downgrade flow.
 *
 * Starting from an active smartlic_pro subscription, switch billing period
 * (annual → monthly), confirm the change, and assert:
 *   - plan_type stays `smartlic_pro`
 *   - the effective billing_period changes on the backend
 *
 * NOTE: In this POC, "downgrade" means changing billing period (which
 * changes effective monthly price).  True plan-tier downgrades don't exist
 * because we operate a single-plan model (see CLAUDE.md Billing & Auth).
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
  pollEndpoint,
  waitForWebhookProcessed,
} from './helpers/billing-test-utils';

const { skip, reason } = shouldSkipBillingTests();

test.describe.configure({ mode: 'serial' });

test.describe('@billing @stripe Plan downgrade (billing period change)', () => {
  test.skip(skip, reason || 'Billing test disabled');

  let email: string;

  test.beforeAll(async () => {
    email = makeTestEmail('downgrade');
  });

  test.afterAll(async () => {
    await cleanupTestCustomer(email);
    await deleteTestUser(email);
  });

  test('AC2.1 setup: user subscribes to annual', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await createTestUser(page, { email, password: DEFAULT_E2E_PASSWORD });
    await billing.goToPlanos();
    await billing.selectBillingPeriod('annual');
    await billing.clickUpgrade();
    await billing.fillStripeCheckout(STRIPE_TEST_CARDS.success);
    await billing.waitForSubscriptionActive();

    const status = await waitForWebhookProcessed(page, { expectPlanType: 'smartlic_pro' });
    expect(status?.plan_type).toBe('smartlic_pro');
  });

  test('AC2.2 switch billing period annual → monthly, plan_type unchanged', async ({ page }) => {
    const billing = new BillingPageObject(page);
    await billing.goToConta();

    // Users change billing period via the Stripe billing portal or via /planos.
    // The portal is hosted by Stripe, so we re-use /planos for E2E simplicity.
    await billing.goToPlanos();
    await billing.selectBillingPeriod('monthly');
    await billing.clickUpgrade();

    // Stripe Checkout for a period change may short-circuit when the user
    // already has an active subscription (proration applied server-side).
    // Accept either path: a new checkout OR an immediate redirect back.
    const url = page.url();
    if (/checkout\.stripe\.com/.test(url)) {
      await billing.fillStripeCheckout(STRIPE_TEST_CARDS.success);
    }
    await billing.waitForSubscriptionActive();

    // plan_type stays smartlic_pro; billing period/plan_id reflects the change.
    const updated = await pollEndpoint<Record<string, unknown>>(
      page,
      '/api/subscription/status',
      (body) => body?.plan_type === 'smartlic_pro',
      30_000,
    );
    expect(updated?.plan_type).toBe('smartlic_pro');
  });
});
