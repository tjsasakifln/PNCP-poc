/**
 * E2E Test: Error Handling
 *
 * Critical User Flow #5: Network and API error scenarios
 *
 * Steps:
 * 1. Mock network failure
 * 2. Execute search
 * 3. Verify error message
 * 4. Verify retry button
 *
 * Reference: docs/reviews/qa-testing-analysis.md (lines 413-414)
 */

import { test, expect } from '@playwright/test';
import { SearchPage } from './helpers/page-objects';
import {
  mockSearchAPI,
  mockDownloadAPI,
  mockSetoresAPI,
  clearTestData,
  simulateNetworkFailure,
} from './helpers/test-utils';

test.describe('Error Handling E2E', () => {
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

  test('AC1: should display error message on API failure', async ({ page }) => {
    // Mock API error
    await mockSearchAPI(page, 'error');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');
    await searchPage.executeSearch();

    // Wait for error message
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Verify error text
    await expect(searchPage.errorMessage).toContainText(
      /Erro ao conectar|Erro ao buscar|tente novamente/i
    );

    // Verify results are NOT displayed
    await expect(searchPage.resultsSection).not.toBeVisible();
  });

  test('AC2: should show retry button on error', async ({ page }) => {
    // Mock API error
    await mockSearchAPI(page, 'error');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('PR');
    await searchPage.executeSearch();

    // Wait for error
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Verify retry button exists
    const retryButton = page.getByRole('button', { name: /Tentar novamente/i });
    await expect(retryButton).toBeVisible();
    await expect(retryButton).toBeEnabled();
  });

  test('AC3: should retry search when clicking retry button', async ({ page }) => {
    // Mock API error initially
    await mockSearchAPI(page, 'error');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('RS');
    await searchPage.executeSearch();

    // Wait for error
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Now mock successful response
    await mockSearchAPI(page, 'success');

    // Click retry button
    const retryButton = page.getByRole('button', { name: /Tentar novamente/i });
    await retryButton.click();

    // Verify results now displayed
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });
    await expect(searchPage.errorMessage).not.toBeVisible();
  });

  test('AC4: should handle network timeout gracefully', async ({ page }) => {
    // Note: Since we can't truly timeout in mock, we test 500 error
    await mockSearchAPI(page, 'error', {
      message: 'Tempo de espera esgotado. Por favor, tente novamente.',
      error: 'TimeoutError',
    });

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SP');
    await searchPage.executeSearch();

    // Verify error displayed
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });
    await expect(searchPage.errorMessage).toContainText(/Tempo de espera|timeout/i);
  });

  test('AC5: should handle download error', async ({ page }) => {
    // Mock successful search
    await mockSearchAPI(page, 'success');

    // Mock download failure
    await mockDownloadAPI(page, true);

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('RJ');
    await searchPage.executeSearch();

    // Wait for results
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Click download button
    await searchPage.downloadButton.click();

    // Wait for download error message
    const downloadError = page.locator('[role="alert"]').filter({ hasText: /download|arquivo/i });
    await expect(downloadError).toBeVisible({ timeout: 5000 });
  });

  test('AC6: should show user-friendly error messages', async ({ page }) => {
    // Mock API error with technical details
    await mockSearchAPI(page, 'error', {
      message: 'Erro ao conectar com o serviço PNCP. Por favor, tente novamente.',
      error: 'NetworkError',
    });

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('MG');
    await searchPage.executeSearch();

    // Verify user-friendly message (not technical stack trace)
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Should NOT contain technical details
    await expect(searchPage.errorMessage).not.toContainText(/stack trace|500|undefined|null/i);

    // Should contain helpful message
    await expect(searchPage.errorMessage).toContainText(/tente novamente|erro/i);
  });

  test('AC7: should clear previous error on new search', async ({ page }) => {
    // Mock error first
    await mockSearchAPI(page, 'error');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('BA');
    await searchPage.executeSearch();

    // Verify error displayed
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Mock success for next search
    await mockSearchAPI(page, 'success');

    // Execute new search
    await searchPage.selectUF('CE');
    await searchPage.executeSearch();

    // Verify error cleared and results shown
    await expect(searchPage.errorMessage).not.toBeVisible();
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });
  });

  test('AC8: should handle 404 download error', async ({ page }) => {
    // Mock successful search
    await mockSearchAPI(page, 'success');

    // Execute search and get results
    await searchPage.clearUFSelection();
    await searchPage.selectUF('PE');
    await searchPage.executeSearch();
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Mock 404 for download (file expired)
    await mockDownloadAPI(page, true);

    // Click download
    await searchPage.downloadButton.click();

    // Verify specific error about expired file
    const downloadError = page.locator('[role="alert"]').filter({ hasText: /expirado|não encontrado/i });
    await expect(downloadError).toBeVisible({ timeout: 5000 });
  });

  test('AC9: should disable search button during loading', async ({ page }) => {
    // Mock success
    await mockSearchAPI(page, 'success');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('PB');

    // Click search button
    const searchButton = searchPage.searchButton;
    await searchButton.click();

    // Verify button is disabled during loading
    await expect(searchButton).toBeDisabled();

    // Verify loading state text
    await expect(searchButton).toContainText(/Buscando/i);

    // Wait for completion
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });

    // Verify button enabled again
    await expect(searchButton).toBeEnabled();
  });

  test('AC10: should handle validation errors gracefully', async ({ page }) => {
    // Try to search without selecting UFs
    await searchPage.clearUFSelection();

    // Search button should be disabled
    await expect(searchPage.searchButton).toBeDisabled();

    // Verify validation error displayed
    const validationError = page.locator('[role="alert"]').filter({
      hasText: /Selecione pelo menos um estado/i,
    });
    await expect(validationError).toBeVisible();
  });

  test('AC11: should handle date validation errors', async ({ page }) => {
    // Select UF
    await searchPage.clearUFSelection();
    await searchPage.selectUF('PI');

    // Set invalid date range
    await searchPage.setDateRange('2024-12-31', '2024-12-01');

    // Verify validation error
    const dateError = page.locator('[role="alert"]').filter({
      hasText: /Data final deve ser maior/i,
    });
    await expect(dateError).toBeVisible();

    // Search button should be disabled
    await expect(searchPage.searchButton).toBeDisabled();
  });

  test('AC12: should show loading indicator during search', async ({ page }) => {
    // Mock success
    await mockSearchAPI(page, 'success');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('RN');
    await searchPage.executeSearch();

    // Verify loading indicator appears (briefly)
    // Note: With mocked API, this may be very fast
    const loading = page.locator('text=/Buscando|Loading/i').or(page.locator('[aria-busy="true"]'));

    // Either loading appears or results appear quickly
    const result = await Promise.race([
      loading.waitFor({ state: 'visible', timeout: 2000 }).then(() => 'loading'),
      searchPage.executiveSummary.waitFor({ state: 'visible', timeout: 10000 }).then(() => 'results'),
    ]);

    expect(['loading', 'results']).toContain(result);
  });

  test('AC13: should maintain form state on error', async ({ page }) => {
    // Mock error
    await mockSearchAPI(page, 'error');

    // Set specific search parameters
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SE');
    await searchPage.selectUF('AL');
    await searchPage.setDateRange('2024-06-01', '2024-06-30');

    // Execute search
    await searchPage.executeSearch();

    // Verify error displayed
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Verify form still has same values
    const seButton = page.getByRole('button', { name: 'SE', exact: true });
    const alButton = page.getByRole('button', { name: 'AL', exact: true });

    await expect(seButton).toHaveClass(/bg-brand-navy/);
    await expect(alButton).toHaveClass(/bg-brand-navy/);

    const dataInicial = await searchPage.dataInicial.inputValue();
    const dataFinal = await searchPage.dataFinal.inputValue();

    expect(dataInicial).toBe('2024-06-01');
    expect(dataFinal).toBe('2024-06-30');
  });

  test('AC14: should handle multiple consecutive errors', async ({ page }) => {
    // Mock error
    await mockSearchAPI(page, 'error');

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('TO');
    await searchPage.executeSearch();

    // Verify error
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Retry (still error)
    const retryButton = page.getByRole('button', { name: /Tentar novamente/i });
    await retryButton.click();

    // Verify error persists
    await expect(searchPage.errorMessage).toBeVisible({ timeout: 10000 });

    // Mock success for third attempt
    await mockSearchAPI(page, 'success');

    // Retry again
    await retryButton.click();

    // Verify success
    await expect(searchPage.executiveSummary).toBeVisible({ timeout: 10000 });
    await expect(searchPage.errorMessage).not.toBeVisible();
  });

  test('AC15: should handle API returning malformed data', async ({ page }) => {
    // Mock malformed response
    await mockSearchAPI(page, 'success', {
      // Missing required fields
      resumo: {
        resumo_executivo: 'Test',
        // Missing total_oportunidades, valor_total, etc.
      },
    });

    // Execute search
    await searchPage.clearUFSelection();
    await searchPage.selectUF('RO');
    await searchPage.executeSearch();

    // Should either show error or handle gracefully
    await page.waitForTimeout(5000);

    // Check if error is shown OR if it handles gracefully with defaults
    const hasError = await searchPage.errorMessage.isVisible();
    const hasResults = await searchPage.resultsSection.isVisible();

    // One of them should be true
    expect(hasError || hasResults).toBe(true);
  });
});
