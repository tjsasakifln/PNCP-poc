import { test, expect } from '@playwright/test';

/**
 * E2E Test: Error Handling Scenarios
 *
 * Tests system behavior under various failure conditions:
 * - PNCP API timeout
 * - Backend unavailable
 * - Excel download failures
 *
 * Acceptance Criteria: AC4
 *
 * @see frontend/app/error.tsx - Error boundary
 * @see frontend/app/api/ - API route error handling
 */
test.describe('Error Handling Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');

    // Clear default UF selections (SC, PR, RS are selected by default)
    const limparButton = page.getByRole('button', { name: /Limpar/i });
    if (await limparButton.isVisible().catch(() => false)) {
      await limparButton.click();
    }
  });

  test('AC4.1: should show user-friendly error on PNCP API timeout', async ({ page }) => {
    // Note: This test simulates timeout by using very large date range
    // or by intercepting network requests

    // Select UF
    await page.getByRole('button', { name: 'SP', exact: true }).click();

    // Intercept API call and delay response to cause timeout
    await page.route('**/api/buscar', async route => {
      // Delay for 35 seconds (backend timeout is 30s)
      await new Promise(resolve => setTimeout(resolve, 35000));
      await route.abort('timedout');
    });

    // Submit search
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await searchButton.click();

    // Wait for error message (should appear within 40s)
    const errorMessage = page.getByText(/erro|timeout|tempo esgotado/i);
    await expect(errorMessage).toBeVisible({ timeout: 45000 });

    // Verify page is still functional (not crashed)
    await expect(searchButton).toBeVisible();
    await expect(searchButton).toBeEnabled();
  });

  test('AC4.2: should display error boundary on backend unavailable', async ({ page }) => {
    // Intercept backend API call and return 503
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Backend unavailable' })
      });
    });

    // Select UF and submit
    await page.getByRole('button', { name: 'RJ', exact: true }).click();
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await searchButton.click();

    // Wait for error message
    const errorMessage = page.getByText(/erro|falha|indisponível/i);
    await expect(errorMessage).toBeVisible({ timeout: 10000 });

    // Verify user can retry
    await expect(searchButton).toBeVisible();
  });

  test('AC4.3: should handle Excel download 404 gracefully', async ({ page }) => {
    // This test requires results to exist first
    // We'll mock a successful search, then fail the download

    // Select UF and submit
    await page.getByRole('button', { name: 'SC', exact: true }).click();

    // Mock successful search response
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-download-id',
          resumo: {
            resumo_executivo: 'Resumo Executivo: Encontradas 5 licitações de uniformes',
            total_oportunidades: 5,
            valor_total: 100000,
            destaques: ['Test'],
            distribuicao_uf: { SC: 5 },
            alerta_urgencia: null
          }
        })
      });
    });

    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await searchButton.click();

    // Wait for results to appear
    await expect(page.getByText(/Resumo Executivo/i)).toBeVisible({ timeout: 10000 });

    // Now mock 404 on download
    await page.route('**/api/download**', async route => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Excel file not found or expired' })
      });
    });

    // Try to download
    const downloadButton = page.getByRole('button', { name: /Baixar Excel/i });
    await downloadButton.click();

    // Should show error message
    const errorMessage = page.getByText(/erro.*download|arquivo.*encontrado|expirado/i);
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('AC4.4: should recover from error and allow new search', async ({ page }) => {
    // Cause an error first
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    // Submit search
    await page.getByRole('button', { name: 'SP', exact: true }).click();
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await searchButton.click();

    // Wait for error
    await expect(page.getByText(/erro/i)).toBeVisible({ timeout: 10000 });

    // Now remove the route to allow normal requests
    await page.unroute('**/api/buscar');

    // Change selection and try again
    await page.getByRole('button', { name: 'RJ', exact: true }).click();

    // Should be able to submit again
    await expect(searchButton).toBeEnabled();
  });

  test('AC4.5: should show loading state during long operations', async ({ page }) => {
    // Select UF
    await page.getByRole('button', { name: 'SP', exact: true }).click();

    // Delay API response to verify loading state, then return mock response
    await page.route('**/api/buscar', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2s delay
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-loading-id',
          resumo: {
            resumo_executivo: 'Resumo Executivo: Encontradas 10 licitações',
            total_oportunidades: 10,
            valor_total: 500000,
            destaques: ['Test'],
            distribuicao_uf: { SP: 10 },
            alerta_urgencia: null
          }
        })
      });
    });

    // Submit search
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await searchButton.click();

    // Verify loading indicator appears immediately
    const loadingText = page.getByText(/Buscando/i);
    await expect(loadingText).toBeVisible({ timeout: 1000 });

    // Verify search button shows loading state
    await expect(page.getByText(/Buscando\.\.\./i)).toBeVisible();
  });

  test('AC4.6: should handle network errors gracefully', async ({ page, context }) => {
    // Simulate offline mode
    await context.setOffline(true);

    // Select UF and submit
    await page.getByRole('button', { name: 'SC', exact: true }).click();
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await searchButton.click();

    // Should show network error
    const errorMessage = page.getByText(/erro.*conexão|offline|rede/i);
    await expect(errorMessage).toBeVisible({ timeout: 10000 });

    // Restore online mode
    await context.setOffline(false);

    // Should be able to retry
    await expect(searchButton).toBeEnabled();
  });

  test('AC4.7: should not leak sensitive errors to user', async ({ page }) => {
    // Cause server error with technical details
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Database connection failed at 127.0.0.1:5432',
          stack: 'Error: connection timeout\n  at DB.connect (db.js:42)',
          secret: 'sk-this-should-not-be-shown'
        })
      });
    });

    // Submit search
    await page.getByRole('button', { name: 'SP', exact: true }).click();
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for error message
    await page.waitForTimeout(2000);

    // Get all page text
    const pageText = await page.textContent('body');

    // Should NOT contain sensitive information
    expect(pageText).not.toContain('127.0.0.1');
    expect(pageText).not.toContain('5432');
    expect(pageText).not.toContain('sk-');
    expect(pageText).not.toContain('stack');

    // Should contain user-friendly generic error
    expect(pageText).toMatch(/erro|falha|problema/i);
  });
});
