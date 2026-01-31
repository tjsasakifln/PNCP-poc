/**
 * E2E Test: Search Flow
 *
 * Critical User Flow #1: Complete search and download journey
 *
 * Steps:
 * 1. Select UF (SC, PR)
 * 2. Choose date range
 * 3. Click search
 * 4. Verify results displayed
 * 5. Download Excel file
 * 6. Verify filename format
 *
 * Reference: docs/reviews/qa-testing-analysis.md (lines 411-442)
 */

import { test, expect } from '@playwright/test';
import { SearchPage } from './helpers/page-objects';
import {
  mockSearchAPI,
  mockDownloadAPI,
  mockSetoresAPI,
  clearTestData,
  getDateString,
} from './helpers/test-utils';

test.describe('Search Flow E2E', () => {
  let searchPage: SearchPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);

    // Setup API mocks first (before navigation)
    await mockSetoresAPI(page);
    await mockSearchAPI(page, 'success');
    await mockDownloadAPI(page);

    // Navigate to home
    await searchPage.goto();

    // Clear test data after navigation
    await clearTestData(page);
  });

  test('AC1: should complete full search and download flow', async ({ page }) => {
    // Step 1: Clear default selections
    await searchPage.clearUFSelection();

    // Step 2: Select UFs (SC, PR)
    await searchPage.selectUF('SC');
    await searchPage.selectUF('PR');

    // Verify selection counter
    await expect(searchPage.ufCounter).toHaveText(/2 estados selecionados/i);

    // Step 3: Verify default date range (7 days)
    const dataInicialValue = await searchPage.dataInicial.inputValue();
    const dataFinalValue = await searchPage.dataFinal.inputValue();

    expect(dataInicialValue).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(dataFinalValue).toMatch(/^\d{4}-\d{2}-\d{2}$/);

    // Calculate date difference
    const inicial = new Date(dataInicialValue);
    const final = new Date(dataFinalValue);
    const diffDays = Math.round(
      (final.getTime() - inicial.getTime()) / (1000 * 60 * 60 * 24)
    );
    expect(diffDays).toBeGreaterThanOrEqual(6);
    expect(diffDays).toBeLessThanOrEqual(8);

    // Step 4: Click search
    await expect(searchPage.searchButton).toBeEnabled();
    await searchPage.executeSearch();

    // Step 5: Verify results displayed
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });
    await expect(searchPage.resultsSection).toContainText(/15/); // total_oportunidades
    await expect(searchPage.resultsSection).toContainText(/750.000/); // valor_total

    // Step 6: Verify download button is enabled
    await expect(searchPage.downloadButton).toBeVisible();
    await expect(searchPage.downloadButton).toBeEnabled();

    // Step 7: Download Excel
    const download = await searchPage.downloadExcel();

    // Step 8: Verify filename format
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/DescompLicita_.*\.xlsx$/);
    expect(filename).toContain('Vestuário_e_Uniformes'); // Default setor

    // Verify file can be saved
    const path = await download.path();
    expect(path).toBeTruthy();
  });

  test('AC2: should handle custom date range', async () => {
    // Clear selections
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SP');

    // Set custom date range (30 days)
    const dataInicial = getDateString(-30);
    const dataFinal = getDateString(0);
    await searchPage.setDateRange(dataInicial, dataFinal);

    // Execute search
    await searchPage.executeSearch();

    // Verify results
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });
  });

  test('AC3: should handle multiple UF selection', async () => {
    // Clear and select 5 UFs
    await searchPage.clearUFSelection();
    await searchPage.selectUFs(['SC', 'PR', 'RS', 'SP', 'RJ']);

    // Verify counter
    await expect(searchPage.ufCounter).toHaveText(/5 estados selecionados/i);

    // Execute search
    await searchPage.executeSearch();

    // Verify results
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });
  });

  test('AC4: should display statistics correctly', async () => {
    // Clear and select UFs
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Execute search
    await searchPage.executeSearch();

    // Verify statistics are displayed
    await expect(searchPage.resultsSection).toBeVisible();

    // Check for total opportunities number (15)
    const totalOportunidades = searchPage.page.locator('text=/^15$/').first();
    await expect(totalOportunidades).toBeVisible();

    // Check for total value with currency
    const valorTotal = searchPage.page.locator('text=/R\\$\\s*750[\\.,]000/i').first();
    await expect(valorTotal).toBeVisible();

    // Verify "licitações" label
    await expect(searchPage.page.locator('text=licitações').first()).toBeVisible();

    // Verify "valor total" label
    await expect(searchPage.page.locator('text=valor total').first()).toBeVisible();
  });

  test('AC5: should display highlights section', async () => {
    // Clear and select UF
    await searchPage.clearUFSelection();
    await searchPage.selectUF('PR');

    // Execute search
    await searchPage.executeSearch();

    // Verify highlights section exists
    await expect(searchPage.page.locator('text=/Destaques:/i')).toBeVisible();

    // Verify at least one highlight is displayed
    const highlights = searchPage.page.locator('ul li').filter({ hasText: /Destaque|Oportunidade/i });
    await expect(highlights.first()).toBeVisible();
  });

  test('AC6: should display urgency alert when present', async () => {
    // Mock response with urgency alert
    await mockSearchAPI(searchPage.page, 'success', {
      download_id: 'test-urgency',
      resumo: {
        resumo_executivo: 'Test with urgency',
        total_oportunidades: 5,
        valor_total: 100000,
        destaques: ['Test highlight'],
        distribuicao_uf: { SC: 5 },
        alerta_urgencia: 'Atenção: 2 licitações com abertura nos próximos 3 dias úteis',
      },
    });

    // Clear and select UF
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Execute search
    await searchPage.executeSearch();

    // Verify urgency alert is displayed
    const alert = searchPage.page.locator('[role="alert"]').filter({ hasText: /Atenção/i });
    await expect(alert).toBeVisible();
    await expect(alert).toContainText(/2 licitações com abertura nos próximos 3 dias/i);
  });

  test('AC7: should complete journey within 60 seconds', async () => {
    const startTime = Date.now();

    // Clear and select UF
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Execute search
    await searchPage.executeSearch();

    // Wait for results
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 30000 });

    const elapsed = Date.now() - startTime;

    // Verify journey completed within timeout
    expect(elapsed).toBeLessThan(60000); // 60 seconds
  });

  test('AC8: should validate form before search', async () => {
    // Clear all UF selections
    await searchPage.clearUFSelection();

    // Try to search without UFs selected
    await expect(searchPage.searchButton).toBeDisabled();

    // Verify validation error message
    const validationError = searchPage.page.locator('[role="alert"]').filter({
      hasText: /Selecione pelo menos um estado/i,
    });
    await expect(validationError).toBeVisible();
  });

  test('AC9: should validate date range', async ({ page }) => {
    // Select UF
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Set invalid date range (final < inicial)
    await searchPage.setDateRange('2024-12-31', '2024-12-01');

    // Verify validation error
    const validationError = page.locator('[role="alert"]').filter({
      hasText: /Data final deve ser maior ou igual/i,
    });
    await expect(validationError).toBeVisible();

    // Search button should be disabled
    await expect(searchPage.searchButton).toBeDisabled();
  });
});
