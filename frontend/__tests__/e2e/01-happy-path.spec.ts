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

    // Clear default UF selections (SC, PR, RS are selected by default)
    // This ensures tests start from a clean state
    const limparButton = page.getByRole('button', { name: /Limpar/i });
    if (await limparButton.isVisible().catch(() => false)) {
      await limparButton.click();
    }
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
    // Mock API response to avoid PNCP timeouts
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-happy-path-ac14-id',
          resumo: {
            resumo_executivo: 'Resumo Executivo: Encontradas 15 licitações de uniformes em SC e PR, totalizando R$ 750.000,00. As oportunidades incluem uniformes escolares, fardamento militar e roupas profissionais para diversos órgãos públicos.',
            total_oportunidades: 15,
            valor_total: 750000,
            destaques: [
              'Destaque para licitação de uniformes escolares em Curitiba no valor de R$ 120.000,00',
              'Oportunidade de fardamento militar em Florianópolis com prazo de entrega de 45 dias'
            ],
            distribuicao_uf: { SC: 8, PR: 7 },
            alerta_urgencia: null
          }
        })
      });
    });

    // Select 2 UFs (smaller scope for faster test)
    await page.getByRole('button', { name: 'SC', exact: true }).click();
    await page.getByRole('button', { name: 'PR', exact: true }).click();

    // Wait for search button to be enabled
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await expect(searchButton).toBeEnabled();

    // Click search button
    await searchButton.click();

    // Wait for results (mock responds instantly so loading state may not be visible)
    await page.waitForSelector('text=/Resumo Executivo/i', {
      timeout: 10000
    });

    // Verify results are displayed
    await expect(page.getByText(/Resumo Executivo/i)).toBeVisible();
  });

  test('AC1.5: should display executive summary with statistics', async ({ page }) => {
    // Mock API response with clear statistics
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-happy-path-ac15-id',
          resumo: {
            resumo_executivo: 'Resumo Executivo: Encontradas 23 licitações de uniformes em SP e RJ, totalizando R$ 1.250.000,00. Predominam uniformes escolares (65%) e fardamento para segurança pública (35%).',
            total_oportunidades: 23,
            valor_total: 1250000,
            destaques: [
              'Maior licitação: Uniformes escolares para rede municipal de São Paulo - R$ 450.000,00',
              'Prazo urgente: Fardamento para Polícia Civil do Rio de Janeiro - abertura em 7 dias',
              'Oportunidade diferenciada: Uniformes hospitalares com tecido antimicrobiano'
            ],
            distribuicao_uf: { SP: 15, RJ: 8 },
            alerta_urgencia: 'Atenção: 3 licitações com abertura nos próximos 5 dias úteis'
          }
        })
      });
    });

    // Select UFs with higher probability of results
    await page.getByRole('button', { name: 'SP', exact: true }).click();
    await page.getByRole('button', { name: 'RJ', exact: true }).click();

    // Submit search
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for results (should be fast with mock)
    await page.waitForSelector('text=/Resumo Executivo/i', {
      timeout: 10000
    });

    // Verify executive summary section
    await expect(page.getByText(/Resumo Executivo/i)).toBeVisible();

    // Verify statistics are displayed (total_oportunidades shown as number + "licitações" label)
    const statsNumber = page.locator('text=/^23$/').first();
    await expect(statsNumber).toBeVisible();
    await expect(page.getByText('licitações', { exact: true }).first()).toBeVisible();

    // Verify valor_total is formatted as currency
    const valorSection = page.locator('text=/R\\$\\s*1[\\.\\s]250[\\.\\s]000/i').first();
    await expect(valorSection).toBeVisible();
  });

  test('AC1.6: should enable download button and serve Excel file', async ({ page }) => {
    // Mock successful search response
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-happy-path-ac16-id',
          resumo: {
            resumo_executivo: 'Resumo Executivo: Encontradas 12 licitações de uniformes em SC, totalizando R$ 680.000,00.',
            total_oportunidades: 12,
            valor_total: 680000,
            destaques: [
              'Uniformes escolares para municípios de Santa Catarina',
              'Fardamento para segurança pública estadual'
            ],
            distribuicao_uf: { SC: 12 },
            alerta_urgencia: null
          }
        })
      });
    });

    // Mock download endpoint (HEAD + GET)
    await page.route('**/api/download**', async (route) => {
      const headers = {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename=licitacoes_test-happy-path-ac16-id.xlsx'
      };
      if (route.request().method() === 'HEAD') {
        await route.fulfill({ status: 200, headers });
      } else {
        // Create a minimal but valid ZIP/XLSX structure
        const content = Buffer.from('PK\x05\x06' + '\x00'.repeat(18), 'binary');
        await route.fulfill({
          status: 200,
          headers: { ...headers, 'Content-Length': content.length.toString() },
          body: content
        });
      }
    });

    // Select UFs
    await page.getByRole('button', { name: 'SC', exact: true }).click();

    // Submit search
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for results (should be fast with mock)
    await page.waitForSelector('text=/Resumo Executivo/i', {
      timeout: 10000
    });

    // Verify download button exists
    const downloadButton = page.getByRole('button', { name: /Baixar Excel/i });
    await expect(downloadButton).toBeVisible();
    await expect(downloadButton).toBeEnabled();

    // Track all download-related requests (HEAD check + GET download)
    const downloadRequests: { method: string; url: string }[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/download')) {
        downloadRequests.push({ method: request.method(), url: request.url() });
      }
    });

    // Click download button - triggers HEAD check then anchor click
    await downloadButton.click();

    // Wait for HEAD request and subsequent download trigger
    await page.waitForTimeout(2000);

    // Verify HEAD request was made (handleDownload checks file exists first)
    const headRequests = downloadRequests.filter(r => r.method === 'HEAD');
    expect(headRequests.length).toBeGreaterThanOrEqual(1);

    // Verify no download error is shown on the page
    const errorElement = page.locator('text=/Erro no download/i');
    await expect(errorElement).not.toBeVisible();
  });

  test('AC1.7: should complete full E2E journey in under 60 seconds', async ({ page }) => {
    // Mock API response for fast execution
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: 'test-happy-path-ac17-id',
          resumo: {
            resumo_executivo: 'Resumo Executivo: Encontradas 18 licitações de uniformes em SC, totalizando R$ 890.000,00. Performance test concluído com sucesso.',
            total_oportunidades: 18,
            valor_total: 890000,
            destaques: [
              'Sistema respondeu em tempo adequado',
              'Teste de performance bem-sucedido'
            ],
            distribuicao_uf: { SC: 18 },
            alerta_urgencia: null
          }
        })
      });
    });

    const startTime = Date.now();

    // Full user journey
    await page.getByRole('button', { name: 'SC', exact: true }).click();
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();
    await page.waitForSelector('text=/Resumo Executivo/i', {
      timeout: 10000
    });

    const elapsed = Date.now() - startTime;

    // Verify journey completed within timeout (should be much faster with mock)
    expect(elapsed).toBeLessThan(60000); // 60 seconds

    // Additional verification that results are displayed
    await expect(page.getByText(/Resumo Executivo/i)).toBeVisible();
  });
});
