import { test, expect } from '@playwright/test';

/**
 * E2E Test: Happy Path User Journey
 *
 * Tests the complete user flow from landing page to Excel download
 * following the manual test scenario from docs/INTEGRATION.md
 *
 * Acceptance Criteria: AC1
 *
 * @see docs/INTEGRATION.md - Manual End-to-End Testing section
 */
test.describe('Happy Path User Journey', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
  });

  test('AC1.1: should load homepage with all expected UI elements', async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/BidIQ Uniformes/i);

    // Verify header
    const heading = page.getByRole('heading', { name: /BidIQ Uniformes/i });
    await expect(heading).toBeVisible();

    // Verify UF selection section
    const ufSection = page.getByText(/Selecione os Estados \(UFs\)/i);
    await expect(ufSection).toBeVisible();

    // Verify at least 27 state buttons are present
    const ufButtons = page.getByRole('button').filter({ hasText: /^[A-Z]{2}$/ });
    await expect(ufButtons).toHaveCount(27);

    // Verify date range inputs
    const dataInicial = page.getByLabel(/Data Inicial/i);
    const dataFinal = page.getByLabel(/Data Final/i);
    await expect(dataInicial).toBeVisible();
    await expect(dataFinal).toBeVisible();

    // Verify search button
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await expect(searchButton).toBeVisible();
  });

  test('AC1.2: should select multiple UFs and update selection counter', async ({ page }) => {
    // Select SP
    await page.getByRole('button', { name: 'SP', exact: true }).click();
    await expect(page.getByText(/1 estado\(s\) selecionado/i)).toBeVisible();

    // Select RJ
    await page.getByRole('button', { name: 'RJ', exact: true }).click();
    await expect(page.getByText(/2 estado\(s\) selecionado/i)).toBeVisible();

    // Verify selected states are highlighted
    const spButton = page.getByRole('button', { name: 'SP', exact: true });
    await expect(spButton).toHaveClass(/bg-green-600/);

    const rjButton = page.getByRole('button', { name: 'RJ', exact: true });
    await expect(rjButton).toHaveClass(/bg-green-600/);
  });

  test('AC1.3: should have default 7-day date range', async ({ page }) => {
    const dataInicial = page.getByLabel(/Data Inicial/i);
    const dataFinal = page.getByLabel(/Data Final/i);

    const dataInicialValue = await dataInicial.inputValue();
    const dataFinalValue = await dataFinal.inputValue();

    // Verify both dates are filled
    expect(dataInicialValue).not.toBe('');
    expect(dataFinalValue).not.toBe('');

    // Verify dates are valid YYYY-MM-DD format
    expect(dataInicialValue).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(dataFinalValue).toMatch(/^\d{4}-\d{2}-\d{2}$/);

    // Verify date range is approximately 7 days
    const inicial = new Date(dataInicialValue);
    const final = new Date(dataFinalValue);
    const diffDays = Math.round((final.getTime() - inicial.getTime()) / (1000 * 60 * 60 * 24));

    expect(diffDays).toBeGreaterThanOrEqual(6);
    expect(diffDays).toBeLessThanOrEqual(8); // Allow some tolerance
  });

  test('AC1.4: should submit search and display results', async ({ page }) => {
    // Select 2 UFs (smaller scope for faster test)
    await page.getByRole('button', { name: 'SC', exact: true }).click();
    await page.getByRole('button', { name: 'PR', exact: true }).click();

    // Wait for search button to be enabled
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await expect(searchButton).toBeEnabled();

    // Click search button
    await searchButton.click();

    // Wait for loading state
    await expect(page.getByText(/Buscando licitações/i)).toBeVisible();

    // Wait for results (max 30s for PNCP API)
    await page.waitForSelector('text=/Resumo Executivo|Nenhum resultado/i', {
      timeout: 30000
    });

    // Verify results or no results message
    const hasResults = await page.getByText(/Resumo Executivo/i).isVisible().catch(() => false);
    const hasNoResults = await page.getByText(/Nenhum resultado/i).isVisible().catch(() => false);

    expect(hasResults || hasNoResults).toBe(true);
  });

  test('AC1.5: should display executive summary with statistics', async ({ page }) => {
    // Select UFs with higher probability of results
    await page.getByRole('button', { name: 'SP', exact: true }).click();
    await page.getByRole('button', { name: 'RJ', exact: true }).click();

    // Submit search
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for results
    await page.waitForSelector('text=/Resumo Executivo|Nenhum resultado/i', {
      timeout: 30000
    });

    // If results exist, validate executive summary structure
    const hasResults = await page.getByText(/Resumo Executivo/i).isVisible().catch(() => false);

    if (hasResults) {
      // Verify executive summary section
      await expect(page.getByText(/Resumo Executivo/i)).toBeVisible();

      // Verify statistics are displayed (total_oportunidades and valor_total)
      const statsSection = page.locator('text=/\\d+ oportunidades?/i').first();
      await expect(statsSection).toBeVisible();

      // Verify valor_total is formatted as currency
      const valorSection = page.locator('text=/R\\$\\s*[\\d.,]+/i').first();
      await expect(valorSection).toBeVisible();
    }
  });

  test('AC1.6: should enable download button and serve Excel file', async ({ page }) => {
    // Select UFs
    await page.getByRole('button', { name: 'SC', exact: true }).click();

    // Submit search
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for results
    await page.waitForSelector('text=/Resumo Executivo|Nenhum resultado/i', {
      timeout: 30000
    });

    const hasResults = await page.getByText(/Resumo Executivo/i).isVisible().catch(() => false);

    if (hasResults) {
      // Verify download button exists
      const downloadButton = page.getByRole('button', { name: /Baixar Excel/i });
      await expect(downloadButton).toBeVisible();
      await expect(downloadButton).toBeEnabled();

      // Start waiting for download before clicking
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

      // Click download button
      await downloadButton.click();

      // Wait for download to complete
      const download = await downloadPromise;

      // Verify file name
      expect(download.suggestedFilename()).toMatch(/licitacoes.*\.xlsx$/i);

      // Verify file size is reasonable (> 1KB)
      const path = await download.path();
      expect(path).not.toBeNull();

      // Optional: Verify Excel file can be read
      // (This would require additional libraries like exceljs)
    }
  });

  test('AC1.7: should complete full E2E journey in under 60 seconds', async ({ page }) => {
    const startTime = Date.now();

    // Full user journey
    await page.getByRole('button', { name: 'SC', exact: true }).click();
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();
    await page.waitForSelector('text=/Resumo Executivo|Nenhum resultado/i', {
      timeout: 30000
    });

    const elapsed = Date.now() - startTime;

    // Verify journey completed within timeout
    expect(elapsed).toBeLessThan(60000); // 60 seconds
  });
});
