/**
 * Test Utilities for E2E Tests
 *
 * Provides mock data, helper functions, and common test utilities
 */

import { Page, Route } from '@playwright/test';

/**
 * Mock API response for successful search
 */
export const mockSuccessfulSearch = {
  download_id: 'test-e2e-download-id',
  total_raw: 125,
  total_filtrado: 15,
  resumo: {
    resumo_executivo:
      'Resumo Executivo: Encontradas 15 licitações de uniformes em SC e PR, totalizando R$ 750.000,00. As oportunidades incluem uniformes escolares, fardamento militar e roupas profissionais para diversos órgãos públicos.',
    total_oportunidades: 15,
    valor_total: 750000,
    destaques: [
      'Destaque para licitação de uniformes escolares em Curitiba no valor de R$ 120.000,00',
      'Oportunidade de fardamento militar em Florianópolis com prazo de entrega de 45 dias',
      'Uniformes hospitalares em Porto Alegre com tecido antimicrobiano',
    ],
    distribuicao_uf: { SC: 8, PR: 7 },
    alerta_urgencia: 'Atenção: 2 licitações com abertura nos próximos 3 dias úteis',
  },
  filter_stats: {
    rejected_by_value: 45,
    rejected_by_keywords: 38,
    rejected_by_exclusion: 27,
  },
};

/**
 * Mock API response for empty results
 */
export const mockEmptySearch = {
  download_id: null,
  total_raw: 67,
  total_filtrado: 0,
  resumo: {
    resumo_executivo: 'Nenhuma licitação encontrada com os critérios especificados.',
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
};

/**
 * Mock API error response
 */
export const mockAPIError = {
  message: 'Erro ao conectar com o serviço PNCP. Por favor, tente novamente.',
  error: 'NetworkError',
};

/**
 * Setup API mocking for search endpoint
 */
export async function mockSearchAPI(
  page: Page,
  response: 'success' | 'empty' | 'error' | 'timeout',
  customData?: any
) {
  await page.route('**/api/buscar', async (route: Route) => {
    if (response === 'timeout') {
      // Simulate timeout by delaying indefinitely
      await new Promise(() => {}); // Never resolves
    } else if (response === 'error') {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify(customData || mockAPIError),
      });
    } else if (response === 'empty') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customData || mockEmptySearch),
      });
    } else {
      // success
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customData || mockSuccessfulSearch),
      });
    }
  });
}

/**
 * Setup download endpoint mocking
 */
export async function mockDownloadAPI(page: Page, shouldFail: boolean = false) {
  await page.route('**/api/download**', async (route: Route) => {
    if (shouldFail) {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Arquivo não encontrado' }),
      });
    } else {
      const headers = {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': 'attachment; filename=licitacoes_test-e2e-download-id.xlsx',
      };

      if (route.request().method() === 'HEAD') {
        await route.fulfill({ status: 200, headers });
      } else {
        // Create a minimal but valid ZIP/XLSX structure
        const content = Buffer.from('PK\x05\x06' + '\x00'.repeat(18), 'binary');
        await route.fulfill({
          status: 200,
          headers: { ...headers, 'Content-Length': content.length.toString() },
          body: content,
        });
      }
    }
  });
}

/**
 * Setup setores API mocking
 */
export async function mockSetoresAPI(page: Page) {
  await page.route('**/api/setores', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        setores: [
          { id: 'vestuario', name: 'Vestuário e Uniformes', description: '' },
          { id: 'alimentos', name: 'Alimentos e Merenda', description: '' },
          { id: 'informatica', name: 'Informática e Tecnologia', description: '' },
        ],
      }),
    });
  });
}

/**
 * Get current date in YYYY-MM-DD format
 */
export function getDateString(daysOffset: number = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + daysOffset);
  return date.toISOString().split('T')[0];
}

/**
 * Wait for network idle (no requests for specified time)
 */
export async function waitForNetworkIdle(page: Page, timeout: number = 500) {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Clear all test data (localStorage, cookies, etc.)
 */
export async function clearTestData(page: Page) {
  // Only clear localStorage/sessionStorage if we're on a navigated page
  try {
    await page.evaluate(() => {
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch (e) {
        // Ignore security errors on unnavigated pages
        console.log('Could not clear storage:', e);
      }
    });
  } catch (e) {
    // Page may not be loaded yet, skip storage clearing
  }

  // Clear cookies
  try {
    await page.context().clearCookies();
  } catch (e) {
    // Ignore if context doesn't support cookies
  }
}

/**
 * Take screenshot with timestamp
 */
export async function takeTimestampedScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ path: `screenshots/${name}-${timestamp}.png`, fullPage: true });
}

/**
 * Simulate network failure
 */
export async function simulateNetworkFailure(page: Page) {
  await page.route('**/*', (route) => {
    route.abort('failed');
  });
}

/**
 * Simulate slow network
 */
export async function simulateSlowNetwork(page: Page, delayMs: number = 2000) {
  await page.route('**/api/**', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, delayMs));
    await route.continue();
  });
}

/**
 * Check if CSS variable is applied
 */
export async function getCSSVariable(page: Page, variableName: string): Promise<string> {
  return await page.evaluate((varName) => {
    return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  }, variableName);
}

/**
 * Assert localStorage value
 */
export async function getLocalStorageItem(page: Page, key: string): Promise<string | null> {
  return await page.evaluate((k) => localStorage.getItem(k), key);
}

/**
 * Set localStorage value
 */
export async function setLocalStorageItem(page: Page, key: string, value: string) {
  await page.evaluate(
    ({ k, v }) => localStorage.setItem(k, v),
    { k: key, v: value }
  );
}

/**
 * Generate mock saved searches data
 */
export function generateMockSavedSearches(count: number = 3) {
  const searches = [];
  for (let i = 0; i < count; i++) {
    searches.push({
      id: `search-${i + 1}`,
      name: `Busca Teste ${i + 1}`,
      createdAt: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
      lastUsedAt: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
      searchParams: {
        ufs: ['SC', 'PR'],
        dataInicial: getDateString(-7),
        dataFinal: getDateString(0),
        searchMode: 'setor' as const,
        setorId: 'vestuario',
      },
    });
  }
  return searches;
}
