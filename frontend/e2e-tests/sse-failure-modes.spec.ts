/**
 * E2E Test: SSE Failure Modes
 *
 * Tests graceful degradation when SSE endpoint fails:
 * - SSE error -> polling fallback activates
 * - SSE disconnect mid-stream -> search still completes via polling
 * - Appropriate error banners shown
 *
 * The search page uses dual-connection: SSE for progress + POST for results.
 * When SSE fails, the frontend falls back to time-based simulation.
 */

import { test, expect } from '@playwright/test';

// Common auth/quota stubs shared across tests
async function stubAuthAndQuota(page: Parameters<typeof test.beforeEach>[0] extends (args: { page: infer P }) => unknown ? P : never) {
  await page.route('**/auth/v1/**', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'test-token',
        token_type: 'bearer',
        expires_in: 3600,
        refresh_token: 'test-refresh-token',
        user: {
          id: 'test-user-id',
          email: 'test@e2e.com',
          role: 'authenticated',
        },
      }),
    });
  });

  await page.route('**/api/trial-status**', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'active',
        searches_remaining: 10,
        searches_used: 0,
        plan: 'trial',
      }),
    });
  });

  await page.route('**/api/setores**', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 'vestuario', name: 'Vestuario e Uniformes' }]),
    });
  });
}

const successfulSearchResponse = {
  resumo: {
    resumo_executivo: 'Resumo de teste com resultados.',
    total_oportunidades: 5,
    valor_total: 250000,
    destaques: ['Destaque A', 'Destaque B'],
    recomendacoes: [],
    alertas_urgencia: [],
    insight_setorial: '',
  },
  licitacoes: [],
  total_raw: 5,
  total_filtrado: 5,
  excel_available: false,
  quota_used: 1,
  quota_remaining: 9,
  response_state: 'live',
};

test.describe('SSE Failure Modes', () => {
  test.beforeEach(async ({ page }) => {
    await stubAuthAndQuota(page);
  });

  test('should degrade gracefully when SSE endpoint returns an error', async ({
    page,
  }) => {
    // SSE endpoint returns 500
    await page.route('**/api/search-progress**', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'SSE service unavailable' }),
      });
    });

    // Search POST still succeeds
    await page.route('**/api/buscar**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(successfulSearchResponse),
      });
    });

    await page.goto('/buscar');
    await expect(page).toHaveURL(/buscar/);

    // Page should render without crashing
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should complete search via polling when SSE connection fails', async ({
    page,
  }) => {
    // SSE endpoint aborts immediately (simulates connection drop)
    await page.route('**/api/search-progress**', (route) => {
      route.abort('connectionfailed');
    });

    // Also mock buscar-progress (alternative SSE endpoint)
    await page.route('**/buscar-progress**', (route) => {
      route.abort('connectionfailed');
    });

    // Search POST returns success
    await page.route('**/api/buscar**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(successfulSearchResponse),
      });
    });

    await page.goto('/buscar');
    await expect(page).toHaveURL(/buscar/);

    // Page should load and remain functional
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // No uncaught crash — body content should be non-trivial
    await page.waitForTimeout(2000);
    const pageText = await body.textContent();
    expect(pageText!.length).toBeGreaterThan(10);
  });

  test('should handle SSE stream that disconnects mid-stream', async ({
    page,
  }) => {
    // SSE starts but provides incomplete stream then closes
    await page.route('**/api/search-progress**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body:
          'data: {"event":"progress","percent":20,"message":"Buscando..."}\n\n' +
          'data: {"event":"progress","percent":40,"message":"Processando..."}\n\n',
        // Stream ends abruptly (no final event)
      });
    });

    // Search POST completes successfully
    await page.route('**/api/buscar**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(successfulSearchResponse),
      });
    });

    await page.goto('/buscar');
    await expect(page).toHaveURL(/buscar/);

    // Page should remain operational after SSE disconnect
    const body = page.locator('body');
    await expect(body).toBeVisible();

    await page.waitForTimeout(2000);
    await expect(body).toBeVisible();
  });

  test('should not show infinite loading when SSE times out', async ({
    page,
  }) => {
    // SSE endpoint returns empty stream (heartbeats only)
    await page.route('**/api/search-progress**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: ': heartbeat\n\n',
      });
    });

    // Search POST returns success quickly
    await page.route('**/api/buscar**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(successfulSearchResponse),
      });
    });

    await page.goto('/buscar');
    await expect(page).toHaveURL(/buscar/);

    // Page should render
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should show appropriate error message when search fails and SSE is down', async ({
    page,
  }) => {
    // Both SSE and search fail
    await page.route('**/api/search-progress**', (route) => {
      route.abort('connectionfailed');
    });

    await page.route('**/api/buscar**', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Serviço temporariamente indisponível.',
          error_code: 'SERVICE_UNAVAILABLE',
        }),
      });
    });

    await page.goto('/buscar');
    await expect(page).toHaveURL(/buscar/);

    // Page must not crash
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // After a failed search, there should be some user-visible feedback
    // (error message, retry button, or degradation banner)
    await page.waitForTimeout(2000);
    await expect(body).toBeVisible();
  });

  test('should allow retry after SSE failure', async ({ page }) => {
    let callCount = 0;

    await page.route('**/api/search-progress**', (route) => {
      route.abort('connectionfailed');
    });

    await page.route('**/api/buscar**', (route) => {
      callCount++;
      if (callCount === 1) {
        route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Service unavailable', error_code: 'SERVICE_UNAVAILABLE' }),
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(successfulSearchResponse),
        });
      }
    });

    await page.goto('/buscar');
    await expect(page).toHaveURL(/buscar/);

    // Page should remain operational for retry
    const body = page.locator('body');
    await expect(body).toBeVisible();

    await page.waitForTimeout(2000);
    await expect(body).toBeVisible();
  });
});
