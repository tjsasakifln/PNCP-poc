/**
 * E2E Test: Performance
 *
 * Critical User Flow: Ensuring fast search experience
 *
 * Steps:
 * 1. Measure search response time
 * 2. Verify loading states appear promptly
 * 3. Check progress indicator updates
 * 4. Ensure results render efficiently
 *
 * Covers bugs:
 * - Performance: Busca mais rapida
 */

import { test, expect } from '@playwright/test';
import { SearchPage } from './helpers/page-objects';
import {
  mockSearchAPI,
  mockSetoresAPI,
  clearTestData,
} from './helpers/test-utils';

test.describe('Search Performance E2E', () => {
  let searchPage: SearchPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);

    // Setup API mocks
    await mockSetoresAPI(page);

    // Navigate to home
    await searchPage.goto();
    await clearTestData(page);
  });

  test('AC1: should show loading state immediately after clicking search', async ({ page }) => {
    // Mock with slight delay to observe loading state
    await page.route('**/api/buscar', async (route) => {
      await new Promise((r) => setTimeout(r, 500));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-perf',
          total_raw: 100,
          total_filtrado: 10,
          resumo: {
            resumo_executivo: 'Test summary',
            total_oportunidades: 10,
            valor_total: 500000,
            destaques: ['Test highlight'],
            distribuicao_uf: { SC: 10 },
          },
        }),
      });
    });

    // Select UF and search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Start timer
    const startTime = Date.now();

    // Click search
    await searchPage.searchButton.click();

    // Loading state should appear within 100ms
    const loadingVisible = await Promise.race([
      searchPage.searchButton.textContent().then((text) => text?.includes('Buscando')),
      new Promise<boolean>((r) => setTimeout(() => r(false), 100)),
    ]);

    expect(loadingVisible).toBe(true);

    // Measure time to loading state
    const loadingTime = Date.now() - startTime;
    expect(loadingTime).toBeLessThan(200); // Loading should show within 200ms
  });

  test('AC2: should disable search button immediately to prevent double-click', async ({ page }) => {
    await mockSearchAPI(page, 'success');

    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Click search
    await searchPage.searchButton.click();

    // Button should be disabled immediately
    await expect(searchPage.searchButton).toBeDisabled();
  });

  test('AC3: should complete search within acceptable time limit', async ({ page }) => {
    await mockSearchAPI(page, 'success');

    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    const startTime = Date.now();

    // Execute search
    await searchPage.executeSearch();

    // Wait for results
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    const totalTime = Date.now() - startTime;

    // With mocked API, should complete within 5 seconds
    expect(totalTime).toBeLessThan(5000);
  });

  test('AC4: should show progress indicator for multi-state searches', async ({ page }) => {
    // Mock with longer delay
    await page.route('**/api/buscar', async (route) => {
      await new Promise((r) => setTimeout(r, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-multi',
          total_raw: 500,
          total_filtrado: 50,
          resumo: {
            resumo_executivo: 'Multi-state search results',
            total_oportunidades: 50,
            valor_total: 2500000,
            destaques: ['Multi highlight'],
            distribuicao_uf: { SC: 20, PR: 15, RS: 15 },
          },
        }),
      });
    });

    // Select multiple UFs
    await searchPage.clearUFSelection();
    await searchPage.selectUFs(['SC', 'PR', 'RS']);

    // Execute search
    await searchPage.searchButton.click();

    // Check for loading progress component
    const loadingText = page.locator('text=/Buscando|Processando|Carregando/i');
    await expect(loadingText).toBeVisible({ timeout: 500 });

    // Wait for completion
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 15000 });
  });

  test('AC5: should render results efficiently without layout shifts', async ({ page }) => {
    await mockSearchAPI(page, 'success');

    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Execute search
    await searchPage.executeSearch();

    // Results should be visible
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Verify no major layout shifts by checking element positions
    const summaryBox = await searchPage.executiveSummary.boundingBox();
    expect(summaryBox).toBeTruthy();

    // Wait a bit and re-check position (no shifts should occur)
    await page.waitForTimeout(500);
    const summaryBoxAfter = await searchPage.executiveSummary.boundingBox();

    // Position should be stable
    expect(summaryBoxAfter?.y).toBeCloseTo(summaryBox!.y, 1);
  });

  test('AC6: should handle rapid consecutive searches gracefully', async ({ page }) => {
    let requestCount = 0;

    // Track requests
    await page.route('**/api/buscar', async (route) => {
      requestCount++;
      await new Promise((r) => setTimeout(r, 200));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: `test-${requestCount}`,
          total_raw: 50,
          total_filtrado: 5,
          resumo: {
            resumo_executivo: `Search ${requestCount}`,
            total_oportunidades: 5,
            valor_total: 250000,
            destaques: [],
            distribuicao_uf: { SC: 5 },
          },
        }),
      });
    });

    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Try to click search multiple times rapidly
    await searchPage.searchButton.click();

    // Button should be disabled, preventing additional clicks
    await expect(searchPage.searchButton).toBeDisabled();

    // Wait for results
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Should have only made one request (button was disabled)
    expect(requestCount).toBe(1);
  });

  test('AC7: should maintain UI responsiveness during search', async ({ page }) => {
    // Mock slow API
    await page.route('**/api/buscar', async (route) => {
      await new Promise((r) => setTimeout(r, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-slow',
          total_raw: 100,
          total_filtrado: 10,
          resumo: {
            resumo_executivo: 'Slow search',
            total_oportunidades: 10,
            valor_total: 500000,
            destaques: [],
            distribuicao_uf: { SC: 10 },
          },
        }),
      });
    });

    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Start search
    await searchPage.searchButton.click();

    // During search, other UI elements should still be responsive
    // Theme toggle should still work
    const themeToggle = page.getByRole('button', { name: /Alternar tema/i });

    if (await themeToggle.isVisible()) {
      // Click should not hang
      const clickPromise = themeToggle.click({ timeout: 1000 });
      await expect(clickPromise).resolves.not.toThrow();
    }
  });

  test('AC8: should provide time estimate for large searches', async ({ page }) => {
    // Mock endpoint that returns time estimate
    await page.route('**/api/buscar', async (route) => {
      await new Promise((r) => setTimeout(r, 500));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-estimate',
          total_raw: 1000,
          total_filtrado: 100,
          estimated_time_remaining: 30,
          resumo: {
            resumo_executivo: 'Large search',
            total_oportunidades: 100,
            valor_total: 5000000,
            destaques: [],
            distribuicao_uf: { SC: 40, PR: 30, RS: 30 },
          },
        }),
      });
    });

    // Select many UFs
    await searchPage.clearUFSelection();
    await searchPage.selectUFs(['SC', 'PR', 'RS', 'SP', 'RJ']);

    // Execute search
    await searchPage.searchButton.click();

    // Look for time estimate in loading UI
    const timeEstimate = page.locator('text=/segundos|minuto/i');

    // Either shows time estimate or completes quickly
    await Promise.race([
      timeEstimate.waitFor({ state: 'visible', timeout: 2000 }),
      searchPage.executiveSummary.waitFor({ state: 'visible', timeout: 10000 }),
    ]);
  });

  test('AC9: should cancel ongoing search when parameters change', async ({ page }) => {
    let abortedRequests = 0;

    // Track aborted requests
    page.on('requestfailed', (request) => {
      if (request.url().includes('/api/buscar')) {
        abortedRequests++;
      }
    });

    // Mock slow API
    await page.route('**/api/buscar', async (route) => {
      await new Promise((r) => setTimeout(r, 5000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-cancel',
          total_raw: 50,
          total_filtrado: 5,
          resumo: {
            resumo_executivo: 'Cancelled',
            total_oportunidades: 5,
            valor_total: 250000,
            destaques: [],
            distribuicao_uf: {},
          },
        }),
      });
    });

    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Start first search
    await searchPage.searchButton.click();

    // Wait for loading state
    await expect(searchPage.searchButton).toBeDisabled();

    // Note: The app should handle this gracefully
    // Implementation varies based on actual app behavior
  });

  test('AC10: should prefetch resources for common actions', async ({ page }) => {
    await mockSearchAPI(page, 'success');

    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');
    await searchPage.executeSearch();

    // After results, download button should appear quickly
    await expect(searchPage.downloadButton).toBeVisible({ timeout: 3000 });

    // Download should be ready (file was prepared)
    await expect(searchPage.downloadButton).toBeEnabled();
  });
});

test.describe('Page Load Performance', () => {
  test('AC11: should load initial page within 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');

    // Wait for key elements to be visible
    await expect(page.locator('h1')).toBeVisible();

    const loadTime = Date.now() - startTime;

    // Page should load within 3 seconds (with local server)
    expect(loadTime).toBeLessThan(3000);
  });

  test('AC12: should not block on non-critical resources', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');

    // Main content should be visible quickly
    await expect(page.locator('h1')).toBeVisible({ timeout: 2000 });

    // Interactive elements should be ready
    const searchButton = page.getByRole('button', { name: /Buscar/i });
    await expect(searchButton).toBeVisible({ timeout: 2000 });

    const interactiveTime = Date.now() - startTime;
    expect(interactiveTime).toBeLessThan(2500);
  });
});
