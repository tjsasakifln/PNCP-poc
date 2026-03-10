/**
 * DEBT-109 AC1-AC3: Automated Accessibility Audits via @axe-core/playwright
 *
 * Runs axe-core analysis on 5 core pages to detect critical a11y violations.
 * Critical violations must be 0; serious/moderate are documented as known issues.
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {
  mockAuthAPI,
  mockSearchAPI,
  mockSetoresAPI,
  mockDownloadAPI,
  mockMeAPI,
} from './helpers/test-utils';

// Helper: run axe audit and assert 0 critical violations
async function auditPage(page: any, context: string) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  const critical = results.violations.filter((v) => v.impact === 'critical');
  const serious = results.violations.filter((v) => v.impact === 'serious');
  const moderate = results.violations.filter((v) => v.impact === 'moderate');

  // Log non-critical for documentation (AC3)
  if (serious.length > 0 || moderate.length > 0) {
    console.log(`\n[${context}] Known a11y issues:`);
    for (const v of [...serious, ...moderate]) {
      console.log(`  - [${v.impact}] ${v.id}: ${v.description} (${v.nodes.length} nodes)`);
    }
  }

  // AC2: 0 critical violations
  expect(critical, `Critical a11y violations on ${context}`).toHaveLength(0);

  return { critical, serious, moderate, total: results.violations.length };
}

test.describe('Accessibility Audits — @axe-core/playwright', () => {
  // -----------------------------------------------------------------------
  // 1. Login page (public, no auth needed)
  // -----------------------------------------------------------------------
  test('AC1.1: Login page has 0 critical a11y violations', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    // Wait for form to render
    await page.waitForSelector('form', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(500); // Allow hydration

    const result = await auditPage(page, 'Login');
    console.log(`Login: ${result.total} total violations (${result.serious.length} serious, ${result.moderate.length} moderate)`);
  });

  // -----------------------------------------------------------------------
  // 2. Buscar page (core search page, needs setores mock)
  // -----------------------------------------------------------------------
  test('AC1.2: Buscar page has 0 critical a11y violations', async ({ page }) => {
    await mockSetoresAPI(page);
    await mockSearchAPI(page, 'success');
    await mockDownloadAPI(page);

    await page.goto('/buscar');
    await page.waitForLoadState('domcontentloaded');
    // Wait for search form to render (UF grid, sector selector)
    await page.waitForSelector('[data-testid="search-form"], form, .search-form, main', {
      timeout: 10000,
    }).catch(() => {});
    await page.waitForTimeout(500);

    const result = await auditPage(page, 'Buscar');
    console.log(`Buscar: ${result.total} total violations (${result.serious.length} serious, ${result.moderate.length} moderate)`);
  });

  // -----------------------------------------------------------------------
  // 3. Dashboard page (authenticated)
  // -----------------------------------------------------------------------
  test('AC1.3: Dashboard page has 0 critical a11y violations', async ({ page }) => {
    await mockAuthAPI(page, 'user');
    await mockMeAPI(page, {
      plan_id: 'smartlic_pro',
      plan_name: 'SmartLic Pro',
      credits_remaining: 50,
    });

    // Mock analytics endpoints
    await page.route('**/api/analytics**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_searches: 25,
          total_results: 150,
          searches_over_time: [],
          top_sectors: [],
          top_ufs: [],
        }),
      });
    });

    // Mock sessions endpoint
    await page.route('**/api/sessions**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ sessions: [], total: 0 }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000); // Allow data fetching + render

    const result = await auditPage(page, 'Dashboard');
    console.log(`Dashboard: ${result.total} total violations (${result.serious.length} serious, ${result.moderate.length} moderate)`);
  });

  // -----------------------------------------------------------------------
  // 4. Pipeline page (authenticated, needs pipeline mock)
  // -----------------------------------------------------------------------
  test('AC1.4: Pipeline page has 0 critical a11y violations', async ({ page }) => {
    await mockAuthAPI(page, 'user');
    await mockMeAPI(page, {
      plan_id: 'smartlic_pro',
      plan_name: 'SmartLic Pro',
      credits_remaining: 50,
    });

    // Mock pipeline endpoint
    await page.route('**/api/pipeline**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'pipe-1',
              titulo: 'Pregão Eletrônico - Uniformes',
              orgao: 'Prefeitura Municipal',
              valor: 150000,
              status: 'novo',
              uf: 'SP',
              data_abertura: '2026-03-15',
            },
          ],
          total: 1,
        }),
      });
    });

    await page.goto('/pipeline');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    const result = await auditPage(page, 'Pipeline');
    console.log(`Pipeline: ${result.total} total violations (${result.serious.length} serious, ${result.moderate.length} moderate)`);
  });

  // -----------------------------------------------------------------------
  // 5. Planos page (public pricing page)
  // -----------------------------------------------------------------------
  test('AC1.5: Planos page has 0 critical a11y violations', async ({ page }) => {
    // Mock plans endpoint
    await page.route('**/api/plans**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          plans: [
            {
              id: 'smartlic_pro',
              name: 'SmartLic Pro',
              price_monthly: 39700,
              price_semiannual: 35700,
              price_annual: 29700,
              features: ['1000 buscas/mês', 'Excel export', 'Pipeline'],
            },
          ],
        }),
      });
    });

    await page.goto('/planos');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(500);

    const result = await auditPage(page, 'Planos');
    console.log(`Planos: ${result.total} total violations (${result.serious.length} serious, ${result.moderate.length} moderate)`);
  });
});
