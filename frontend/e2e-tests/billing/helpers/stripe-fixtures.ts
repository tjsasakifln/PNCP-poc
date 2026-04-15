/**
 * Stripe Test Mode Fixtures
 *
 * Provides canonical Stripe test cards and cleanup helpers for E2E billing specs.
 *
 * IMPORTANT:
 * - All helpers operate against Stripe TEST MODE only.
 * - Guarded by STRIPE_TEST_SECRET_KEY + E2E_BILLING_ENABLED env vars.
 * - Never attempts to call Stripe with a live key.
 *
 * STORY-3.5 — EPIC-TD-2026Q2 (P1)
 */

/**
 * Shape of a Stripe test card as expected by billing-page-objects fill helpers.
 */
export interface StripeCard {
  number: string;
  cvc: string;
  exp: string;
}

/**
 * Canonical Stripe TEST cards.
 * See: https://stripe.com/docs/testing#cards
 */
export const STRIPE_TEST_CARDS: Readonly<Record<'success' | 'decline' | 'require3DS', StripeCard>> = {
  success: { number: '4242 4242 4242 4242', cvc: '123', exp: '12/34' },
  decline: { number: '4000 0000 0000 0002', cvc: '123', exp: '12/34' },
  require3DS: { number: '4000 0027 6000 3184', cvc: '123', exp: '12/34' },
} as const;

/**
 * Prefix used by all E2E billing tests when provisioning test users.
 * Cleanup scripts pattern-match against this prefix + the test domain.
 */
export const E2E_BILLING_EMAIL_PREFIX = 'e2e-billing-';
export const E2E_BILLING_EMAIL_DOMAIN = 'test.smartlic.tech';

/**
 * Produce a deterministic-but-unique test email.
 * Keeps the prefix scannable by the cleanup script.
 */
export function makeTestEmail(suffix?: string): string {
  const unique = suffix ?? String(Date.now());
  return `${E2E_BILLING_EMAIL_PREFIX}${unique}@${E2E_BILLING_EMAIL_DOMAIN}`;
}

/**
 * Decides whether the billing specs should run or be skipped.
 * Billing specs require live Stripe test mode + an explicit opt-in flag so
 * they never accidentally run in environments that don't have Stripe wired up.
 */
export function shouldSkipBillingTests(): { skip: boolean; reason?: string } {
  if (!process.env.STRIPE_TEST_SECRET_KEY) {
    return { skip: true, reason: 'STRIPE_TEST_SECRET_KEY not set — skipping billing E2E' };
  }
  if (!process.env.E2E_BILLING_ENABLED) {
    return { skip: true, reason: 'E2E_BILLING_ENABLED not set — skipping billing E2E' };
  }
  return { skip: false };
}

/**
 * Minimal Stripe REST response types we actually use.
 */
interface StripeCustomer {
  id: string;
  email: string | null;
}

interface StripeList<T> {
  data: T[];
  has_more: boolean;
}

/**
 * Delete every Stripe test customer whose email matches `email` (exact match).
 * No-op when STRIPE_TEST_SECRET_KEY is missing — safe to call unconditionally in afterAll.
 *
 * Refuses to run against a live key (sk_live_*) as an extra guardrail.
 */
export async function cleanupTestCustomer(email: string): Promise<void> {
  const key = process.env.STRIPE_TEST_SECRET_KEY;
  if (!key) {
    // No cleanup possible without a key — silently skip.
    return;
  }
  if (!key.startsWith('sk_test_')) {
    // Refuse to run against a live key. This is defensive — the env var name
    // already implies test mode, but we double-check.
    // eslint-disable-next-line no-console
    console.warn('[cleanupTestCustomer] STRIPE_TEST_SECRET_KEY does not look like a test key; refusing to run.');
    return;
  }

  try {
    const searchUrl = `https://api.stripe.com/v1/customers?email=${encodeURIComponent(email)}&limit=100`;
    const res = await fetch(searchUrl, {
      method: 'GET',
      headers: { Authorization: `Bearer ${key}` },
    });
    if (!res.ok) {
      // eslint-disable-next-line no-console
      console.warn(`[cleanupTestCustomer] list failed ${res.status} for ${email}`);
      return;
    }
    const list = (await res.json()) as StripeList<StripeCustomer>;
    for (const customer of list.data) {
      if (!customer.id) continue;
      await fetch(`https://api.stripe.com/v1/customers/${customer.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${key}` },
      }).catch(() => { /* best-effort cleanup */ });
    }
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('[cleanupTestCustomer] unexpected error:', err);
  }
}
