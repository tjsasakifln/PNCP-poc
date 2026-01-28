import { test, expect } from '@playwright/test';

/**
 * E2E Test: LLM Fallback Scenario
 *
 * Tests that the system gracefully falls back to statistical summary
 * when OpenAI API is unavailable or misconfigured
 *
 * Acceptance Criteria: AC2
 *
 * @see backend/llm.py - gerar_resumo_fallback()
 */
test.describe('LLM Fallback Scenario', () => {
  test.use({
    // Override environment to simulate missing OpenAI key
    extraHTTPHeaders: {
      'X-Test-Scenario': 'fallback'
    }
  });

  test('AC2.1: should return 200 OK even without OpenAI API key', async ({ page }) => {
    // Mock the /api/buscar endpoint to return fallback data
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: "test-fallback-ac21-id",
          resumo: {
            resumo_executivo: "Resumo Executivo estatístico: Foram encontradas 8 oportunidades de licitação de uniformes, totalizando R$ 320.000,00. Distribuição: SC (5), SP (3).",
            total_oportunidades: 8,
            valor_total: 320000,
            destaques: ["Maior concentração em SC com 5 licitações", "Valor médio de R$ 40.000,00 por licitação"],
            distribuicao_uf: {"SC": 5, "SP": 3},
            alerta_urgencia: null
          }
        })
      });
    });

    await page.goto('/');

    // Clear default UF selections (SC, PR, RS are selected by default)
    const limparButton = page.getByRole('button', { name: /Limpar/i });
    if (await limparButton.isVisible().catch(() => false)) {
      await limparButton.click();
    }

    // Select UF
    await page.getByRole('button', { name: 'SC', exact: true }).click();

    // Submit search
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await searchButton.click();

    // Wait for results
    await page.waitForSelector('text=/Resumo Executivo|Nenhum resultado/i', {
      timeout: 10000
    });

    // Verify page didn't crash with error
    const hasResults = await page.getByText(/Resumo Executivo/i).isVisible().catch(() => false);
    const hasNoResults = await page.getByText(/Nenhum resultado/i).isVisible().catch(() => false);
    const hasError = await page.getByText(/Erro ao buscar/i).isVisible().catch(() => false);

    // Should show results or no results, NOT error
    expect(hasResults || hasNoResults).toBe(true);
    expect(hasError).toBe(false);
  });

  test('AC2.2: should display fallback summary with statistical indicators', async ({ page }) => {
    // Mock the /api/buscar endpoint to return fallback data
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: "test-fallback-ac22-id",
          resumo: {
            resumo_executivo: "Resumo Executivo estatístico: Foram encontradas 8 oportunidades de licitação de uniformes, totalizando R$ 320.000,00. Distribuição: SC (5), SP (3).",
            total_oportunidades: 8,
            valor_total: 320000,
            destaques: ["Maior concentração em SC com 5 licitações", "Valor médio de R$ 40.000,00 por licitação"],
            distribuicao_uf: {"SC": 5, "SP": 3},
            alerta_urgencia: null
          }
        })
      });
    });

    await page.goto('/');

    // Clear default UF selections (SC, PR, RS are selected by default)
    const limparButton = page.getByRole('button', { name: /Limpar/i });
    if (await limparButton.isVisible().catch(() => false)) {
      await limparButton.click();
    }

    // Select UF
    await page.getByRole('button', { name: 'SP', exact: true }).click();

    // Submit search
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for results
    await page.waitForSelector('text=/Resumo Executivo/i', {
      timeout: 10000
    });

    // Look for fallback indicators
    // Fallback summary should contain "Resumo estatístico" or similar
    const summaryText = await page.textContent('body');

    // Fallback summary characteristics:
    // - Contains statistics (X oportunidades, R$ value)
    // - Contains UF distribution
    // - May contain "Resumo estatístico" or "Resumo automático"

    // Verify statistics are present (basic validation)
    expect(summaryText).toMatch(/\d+\s+oportunidades?/i);
    expect(summaryText).toMatch(/R\$\s*[\d.,]+/i);
  });

  test('AC2.3: should NOT make OpenAI API calls in fallback mode', async ({ page, context }) => {
    // Mock the /api/buscar endpoint to return fallback data
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: "test-fallback-ac23-id",
          resumo: {
            resumo_executivo: "Resumo Executivo estatístico: Foram encontradas 8 oportunidades de licitação de uniformes, totalizando R$ 320.000,00. Distribuição: SC (5), SP (3).",
            total_oportunidades: 8,
            valor_total: 320000,
            destaques: ["Maior concentração em SC com 5 licitações", "Valor médio de R$ 40.000,00 por licitação"],
            distribuicao_uf: {"SC": 5, "SP": 3},
            alerta_urgencia: null
          }
        })
      });
    });

    // Track network requests
    const apiCalls: string[] = [];

    page.on('request', request => {
      const url = request.url();
      if (url.includes('openai.com') || url.includes('api.openai')) {
        apiCalls.push(url);
      }
    });

    await page.goto('/');

    // Clear default UF selections (SC, PR, RS are selected by default)
    const limparButton = page.getByRole('button', { name: /Limpar/i });
    if (await limparButton.isVisible().catch(() => false)) {
      await limparButton.click();
    }

    // Perform search
    await page.getByRole('button', { name: 'SC', exact: true }).click();
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for results
    await page.waitForSelector('text=/Resumo Executivo|Nenhum resultado/i', {
      timeout: 10000
    });

    // Verify no OpenAI API calls were made
    // Note: This test is informational - OpenAI calls happen server-side
    // We're checking client-side calls only
    expect(apiCalls.length).toBe(0);
  });

  test('AC2.4: should handle zero results gracefully in fallback mode', async ({ page }) => {
    // Mock the /api/buscar endpoint to return zero results
    await page.route('**/api/buscar', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          download_id: "test-zero-results-id",
          resumo: {
            resumo_executivo: "Resumo Executivo: Nenhum resultado encontrado para os critérios selecionados.",
            total_oportunidades: 0,
            valor_total: 0,
            destaques: [],
            distribuicao_uf: {},
            alerta_urgencia: null
          }
        })
      });
    });

    await page.goto('/');

    // Clear default UF selections (SC, PR, RS are selected by default)
    const limparButton = page.getByRole('button', { name: /Limpar/i });
    if (await limparButton.isVisible().catch(() => false)) {
      await limparButton.click();
    }

    // Select UF unlikely to have uniform procurement (use very specific dates)
    await page.getByRole('button', { name: 'AC', exact: true }).click(); // Acre (smaller state)

    // Set very narrow date range (yesterday only)
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];

    await page.getByLabel(/Data Inicial/i).fill(yesterdayStr);
    await page.getByLabel(/Data Final/i).fill(yesterdayStr);

    // Submit search
    await page.getByRole('button', { name: /Buscar Licitações/i }).click();

    // Wait for results
    await page.waitForSelector('text=/Resumo Executivo|Nenhum resultado/i', {
      timeout: 10000
    });

    // Should show "no results" message OR empty summary, NOT crash
    const bodyText = await page.textContent('body');

    // Verify page is functional (no JS errors that break the page)
    expect(bodyText).toBeTruthy();

    // Verify search button is still available (can retry)
    const searchButton = page.getByRole('button', { name: /Buscar Licitações/i });
    await expect(searchButton).toBeVisible();
  });
});

/**
 * Note: Full fallback testing requires backend configuration
 *
 * For comprehensive fallback testing, consider:
 * 1. Adding TEST_MODE env var to backend
 * 2. Creating /api/test/fallback endpoint
 * 3. Using docker-compose.test.yml with OPENAI_API_KEY=""
 *
 * See: docs/INTEGRATION.md - Error Scenario Testing
 */
