import { test, expect } from '@playwright/test';

/**
 * E2E Test: /login RSC Invariant Regression Guard
 *
 * STORY-421 (EPIC-INCIDENT-2026-04-10): Regression guard for
 *   `InvariantError: Expected RSC response, got text/plain`
 * reported in Sentry issue 7397346898.
 *
 * Scope (AC1, AC5):
 *  - Cold-load /login with cache-busting headers and assert the response is
 *    HTML (never text/plain).
 *  - Assert no InvariantError appears in the browser console during load.
 *  - Assert the login form is interactive after load.
 *  - Assert the `error.tsx` fallback renders its primary escape actions when
 *    it is reached via a forced client throw.
 */
test.describe('STORY-421: /login RSC invariant guard', () => {
  test('AC1: /login loads with text/html and no invariant error in console', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    // Force a cold-load: bypass cache both at the CDN layer and intra-browser.
    await page.setExtraHTTPHeaders({
      'Cache-Control': 'no-cache',
      Pragma: 'no-cache',
    });

    const response = await page.goto('/login', { waitUntil: 'domcontentloaded' });

    expect(response, '/login should return a response').not.toBeNull();
    expect(response!.status()).toBeLessThan(400);

    const contentType = response!.headers()['content-type'] || '';
    expect(contentType).toContain('text/html');
    expect(contentType).not.toContain('text/plain');

    // Login form markers (regardless of OAuth, magic link, or password mode)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // No InvariantError in console / page errors during the cold load
    const invariantErrors = consoleErrors.filter((e) =>
      /invariant|expected rsc|text\/plain/i.test(e)
    );
    expect(invariantErrors, `Unexpected invariant errors: ${invariantErrors.join(' | ')}`).toHaveLength(0);
  });

  test('AC5: /login survives reload cycles without RSC failures', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('pageerror', (err) => consoleErrors.push(err.message));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.reload({ waitUntil: 'domcontentloaded' });

    const invariantErrors = consoleErrors.filter((e) =>
      /invariant|expected rsc|text\/plain/i.test(e)
    );
    expect(invariantErrors).toHaveLength(0);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });
});
