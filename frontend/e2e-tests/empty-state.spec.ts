/**
 * E2E Test: Empty State
 *
 * Critical User Flow #4: Handling no results scenario
 *
 * Steps:
 * 1. Search with no results
 * 2. Verify empty state component
 * 3. Click "Adjust search"
 * 4. Verify form focus
 *
 * Reference: docs/reviews/qa-testing-analysis.md (lines 413-414)
 */

import { test, expect } from '@playwright/test';
import { SearchPage } from './helpers/page-objects';
import { mockSearchAPI, mockSetoresAPI, clearTestData } from './helpers/test-utils';

test.describe('Empty State E2E', () => {
  let searchPage: SearchPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);

    // Setup API mocks first (before navigation)
    await mockSetoresAPI(page);

    // Navigate to home
    await searchPage.goto();

    // Clear test data after navigation
    await clearTestData(page);
  });

  test('AC1: should display empty state when no results found', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Clear and select UF
    await searchPage.clearUFSelection();
    await searchPage.selectUF('AC'); // Remote state, likely no results

    // Execute search
    await searchPage.executeSearch();

    // Verify empty state is displayed
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Verify empty state message
    await expect(page.locator('text=/Nenhuma licitação encontrada/i')).toBeVisible();

    // Verify results section is NOT displayed
    await expect(searchPage.resultsSection).not.toBeVisible();

    // Verify download button is NOT displayed
    await expect(searchPage.downloadButton).not.toBeVisible();
  });

  test('AC2: should show filter statistics in empty state', async ({ page }) => {
    // Mock empty results with filter stats
    await mockSearchAPI(page, 'empty', {
      download_id: null,
      total_raw: 67,
      total_filtrado: 0,
      resumo: {
        resumo_executivo: 'Nenhuma licitação encontrada.',
        total_oportunidades: 0,
        valor_total: 0,
        destaques: [],
        distribuicao_uf: {},
        alerta_urgencia: null,
      },
      filter_stats: {
        rejected_by_value: 32,
        rejected_by_keywords: 25,
        rejected_by_exclusion: 10,
      },
    });

    // Select UF and search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('RR');
    await searchPage.executeSearch();

    // Verify filter stats displayed
    await expect(page.locator('text=/67.*licitações analisadas/i')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/0.*atenderam aos critérios/i')).toBeVisible();
  });

  test('AC3: should show "Adjust search" button in empty state', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('AP');
    await searchPage.executeSearch();

    // Verify empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Verify "Adjust search" button exists
    const adjustButton = page.getByRole('button', { name: /Ajustar busca|Refinar critérios/i });
    await expect(adjustButton).toBeVisible();
  });

  test('AC4: should scroll to top when clicking "Adjust search"', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('TO');
    await searchPage.executeSearch();

    // Wait for empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Scroll down to ensure we're not at top
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(300);

    // Click adjust search button
    const adjustButton = page.getByRole('button', { name: /Ajustar busca|Refinar critérios/i });
    await adjustButton.click();

    // Wait for scroll animation
    await page.waitForTimeout(800);

    // Verify scrolled to top (or near top)
    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBeLessThan(100);
  });

  test('AC5: should focus on form after clicking "Adjust search"', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SE');
    await searchPage.executeSearch();

    // Wait for empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Click adjust search
    const adjustButton = page.getByRole('button', { name: /Ajustar busca|Refinar critérios/i });
    await adjustButton.click();

    // Wait for scroll
    await page.waitForTimeout(800);

    // Verify we're at the top where the form is
    const formVisible = await searchPage.searchButton.isInViewport();
    expect(formVisible).toBe(true);
  });

  test('AC6: should show suggestions when no results', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('RO');
    await searchPage.executeSearch();

    // Verify empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Verify suggestions are shown
    const suggestions = page.locator('text=/Tente.*|Sugestões|Dicas/i');
    await expect(suggestions.first()).toBeVisible();
  });

  test('AC7: should display raw count vs filtered count', async ({ page }) => {
    // Mock empty with specific counts
    await mockSearchAPI(page, 'empty', {
      download_id: null,
      total_raw: 150,
      total_filtrado: 0,
      resumo: {
        resumo_executivo: 'Nenhuma licitação encontrada.',
        total_oportunidades: 0,
        valor_total: 0,
        destaques: [],
        distribuicao_uf: {},
        alerta_urgencia: null,
      },
    });

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('PI');
    await searchPage.executeSearch();

    // Verify counts displayed
    await expect(page.locator('text=/150/i')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/0.*atenderam/i')).toBeVisible();
  });

  test('AC8: should allow modifying search after empty result', async ({ page }) => {
    // Mock empty results first
    await mockSearchAPI(page, 'empty');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('MA');
    await searchPage.executeSearch();

    // Verify empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Click adjust search
    const adjustButton = page.getByRole('button', { name: /Ajustar busca|Refinar critérios/i });
    await adjustButton.click();
    await page.waitForTimeout(500);

    // Now mock successful results
    await mockSearchAPI(page, 'success');

    // Modify search by adding more UFs
    await searchPage.selectUF('CE');
    await searchPage.selectUF('BA');

    // Execute new search
    await searchPage.executeSearch();

    // Verify results now displayed (not empty state)
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });
    await expect(searchPage.emptyState).not.toBeVisible();
  });

  test('AC9: should show breakdown of rejection reasons', async ({ page }) => {
    // Mock empty with detailed filter stats
    await mockSearchAPI(page, 'empty', {
      download_id: null,
      total_raw: 100,
      total_filtrado: 0,
      resumo: {
        resumo_executivo: 'Nenhuma licitação encontrada.',
        total_oportunidades: 0,
        valor_total: 0,
        destaques: [],
        distribuicao_uf: {},
        alerta_urgencia: null,
      },
      filter_stats: {
        rejected_by_value: 45,
        rejected_by_keywords: 38,
        rejected_by_exclusion: 17,
      },
    });

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('AL');
    await searchPage.executeSearch();

    // Verify empty state with filter breakdown
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Check for rejection reason display (if implemented)
    // These may be in EmptyState component
    const filterInfo = page.locator('text=/valor|palavras-chave|exclu/i');
    await expect(filterInfo.first()).toBeVisible();
  });

  test('AC10: should maintain form state after empty result', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Set specific search parameters
    await searchPage.clearUFSelection();
    await searchPage.selectUF('ES');
    await searchPage.selectUF('MG');
    await searchPage.setDateRange('2024-01-01', '2024-01-31');

    // Execute search
    await searchPage.executeSearch();

    // Verify empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Verify form still has same values
    const esButton = page.getByRole('button', { name: 'ES', exact: true });
    const mgButton = page.getByRole('button', { name: 'MG', exact: true });

    await expect(esButton).toHaveClass(/bg-brand-navy/);
    await expect(mgButton).toHaveClass(/bg-brand-navy/);

    const dataInicial = await searchPage.dataInicial.inputValue();
    const dataFinal = await searchPage.dataFinal.inputValue();

    expect(dataInicial).toBe('2024-01-01');
    expect(dataFinal).toBe('2024-01-31');
  });

  test('AC11: should not show save search button on empty results', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('GO');
    await searchPage.executeSearch();

    // Verify empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Verify save search button is NOT displayed
    await expect(searchPage.saveSearchButton).not.toBeVisible();
  });

  test('AC12: should show helpful icon in empty state', async ({ page }) => {
    // Mock empty results
    await mockSearchAPI(page, 'empty');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('MT');
    await searchPage.executeSearch();

    // Verify empty state
    await expect(searchPage.emptyState).toBeVisible({ timeout: 10000 });

    // Verify icon/illustration present
    const icon = page.locator('svg').first();
    await expect(icon).toBeVisible();
  });
});
