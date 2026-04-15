/**
 * Utilities for Billing E2E tests.
 *
 * Responsibilities:
 * - User provisioning (signup/login via UI).
 * - Polling the backend for webhook side-effects to land.
 * - Supabase admin cleanup (best-effort).
 *
 * All helpers are no-ops when required env vars are missing so they
 * degrade gracefully when billing tests are skipped.
 *
 * STORY-3.5 — EPIC-TD-2026Q2 (P1)
 */

import { Page } from '@playwright/test';
import { BillingPageObject } from './billing-page-objects';

export interface TestUser {
  email: string;
  password: string;
  fullName?: string;
}

/**
 * Default password for every E2E billing test user.  Not a secret — these
 * accounts are scoped to the test.smartlic.tech domain and are deleted
 * after every run.
 */
export const DEFAULT_E2E_PASSWORD = 'E2eBilling!Test#2026';

/**
 * Create a test user via the signup UI.  Kept simple: UI is the source of
 * truth, so we exercise the exact same path a real user takes.
 */
export async function createTestUser(page: Page, user: TestUser): Promise<void> {
  const billing = new BillingPageObject(page);
  await billing.signup(user.email, user.password, user.fullName);
}

/**
 * Log a previously-created test user in via the UI.
 */
export async function loginTestUser(page: Page, user: TestUser): Promise<void> {
  const billing = new BillingPageObject(page);
  await billing.login(user.email, user.password);
}

interface TrialStatus {
  is_trial_active?: boolean;
  trial_days_remaining?: number | null;
  plan_type?: string;
  subscription_status?: string | null;
  cancel_at_period_end?: boolean;
  [k: string]: unknown;
}

/**
 * Poll an arbitrary JSON endpoint until `predicate` returns true or the
 * timeout elapses.  Returns the last observed payload.
 *
 * Uses the Playwright page's APIRequestContext so that auth cookies from
 * the browser session are reused (no need to forward tokens manually).
 */
export async function pollEndpoint<T = unknown>(
  page: Page,
  endpoint: string,
  predicate: (body: T) => boolean,
  timeoutMs = 30_000,
  intervalMs = 1_000,
): Promise<T | null> {
  const start = Date.now();
  let lastBody: T | null = null;
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await page.request.get(endpoint);
      if (res.ok()) {
        const body = (await res.json()) as T;
        lastBody = body;
        if (predicate(body)) return body;
      }
    } catch {
      // Ignore transient failures and retry.
    }
    await page.waitForTimeout(intervalMs);
  }
  return lastBody;
}

/**
 * Wait until the backend has processed the Stripe webhook and the user's
 * subscription has transitioned to `active` with `plan_type=smartlic_pro`.
 *
 * Polls `/v1/trial-status`, which exposes plan_type/subscription_status after
 * webhook processing (see backend/routes/user.py).
 */
export async function waitForWebhookProcessed(
  page: Page,
  opts: { expectPlanType?: string; expectCancelAtPeriodEnd?: boolean } = {},
  timeoutMs = 30_000,
): Promise<TrialStatus | null> {
  const { expectPlanType = 'smartlic_pro', expectCancelAtPeriodEnd } = opts;
  return pollEndpoint<TrialStatus>(
    page,
    '/api/trial-status',
    (body) => {
      if (body.plan_type !== expectPlanType) return false;
      if (expectCancelAtPeriodEnd !== undefined && body.cancel_at_period_end !== expectCancelAtPeriodEnd) {
        return false;
      }
      return true;
    },
    timeoutMs,
  );
}

/**
 * Delete a test user via Supabase admin API.  Requires SUPABASE_URL and
 * SUPABASE_SERVICE_ROLE_KEY env vars.  No-op when either is missing.
 *
 * This helper is best-effort: failures are logged but never thrown so that
 * afterAll hooks don't mask the primary test result.
 */
export async function deleteTestUser(email: string): Promise<void> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? process.env.SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !serviceKey) {
    return;
  }
  try {
    const lookup = await fetch(
      `${url}/auth/v1/admin/users?filter=${encodeURIComponent(`email.eq.${email}`)}`,
      {
        method: 'GET',
        headers: {
          apikey: serviceKey,
          Authorization: `Bearer ${serviceKey}`,
        },
      },
    );
    if (!lookup.ok) return;
    const body = (await lookup.json()) as { users?: Array<{ id: string }> };
    for (const u of body.users ?? []) {
      await fetch(`${url}/auth/v1/admin/users/${u.id}`, {
        method: 'DELETE',
        headers: {
          apikey: serviceKey,
          Authorization: `Bearer ${serviceKey}`,
        },
      }).catch(() => { /* best-effort */ });
    }
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('[deleteTestUser] best-effort cleanup failed:', err);
  }
}
