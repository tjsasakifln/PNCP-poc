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
          { id: 'informatica', name: 'Hardware e Equipamentos de TI', description: '' },
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

/**
 * Mock user data for different user types
 */
const mockUsers = {
  admin: {
    id: 'admin-user-id',
    email: 'admin@test.com',
    user_metadata: { full_name: 'Admin User', is_admin: true },
    app_metadata: { is_admin: true },
  },
  user: {
    id: 'regular-user-id',
    email: 'user@test.com',
    user_metadata: { full_name: 'Regular User' },
    app_metadata: {},
  },
};

/**
 * Mock session data
 */
const mockSession = {
  access_token: 'mock-access-token-12345',
  refresh_token: 'mock-refresh-token-12345',
  expires_at: Date.now() + 3600 * 1000,
};

/**
 * Setup authentication mocking
 * Simulates authenticated user for testing protected pages
 */
export async function mockAuthAPI(page: Page, userType: 'admin' | 'user' = 'user') {
  const user = mockUsers[userType];
  const isAdmin = userType === 'admin';

  // Mock Supabase auth endpoints
  await page.route('**/auth/v1/token**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: mockSession.access_token,
        refresh_token: mockSession.refresh_token,
        expires_in: 3600,
        token_type: 'bearer',
        user,
      }),
    });
  });

  // Mock /me endpoint
  await page.route('**/me', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: user.id,
        email: user.email,
        full_name: user.user_metadata.full_name,
        is_admin: isAdmin,
        plan_id: 'free',
        plan_name: 'Gratuito',
        credits_remaining: 3,
      }),
    });
  });

  // Set auth state in localStorage before page load
  await page.addInitScript(
    ({ user, session, isAdmin }) => {
      // Supabase stores auth in localStorage
      const authKey = 'sb-localhost-auth-token';
      const authData = {
        access_token: session.access_token,
        refresh_token: session.refresh_token,
        expires_at: session.expires_at,
        user: { ...user, is_admin: isAdmin },
      };
      localStorage.setItem(authKey, JSON.stringify(authData));

      // Also set a flag for our AuthProvider
      localStorage.setItem('auth-user', JSON.stringify({ ...user, is_admin: isAdmin }));
      localStorage.setItem('auth-session', JSON.stringify(session));
    },
    { user, session: mockSession, isAdmin }
  );
}

/**
 * Mock /me endpoint with custom user data
 * Used for testing different plan types and quota states
 */
export async function mockMeAPI(
  page: Page,
  userData: {
    plan_id?: string;
    plan_name?: string;
    credits_remaining?: number | null;
    credits_total?: number;
    quota_used?: number;
    reset_date?: string;
    trial_expires_at?: string;
    is_admin?: boolean;
  }
) {
  await page.route('**/me', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'mock-user-id',
        email: 'user@test.com',
        full_name: 'Test User',
        is_admin: userData.is_admin || false,
        plan_id: userData.plan_id || 'free',
        plan_name: userData.plan_name || 'Gratuito',
        credits_remaining: userData.credits_remaining ?? 3,
        credits_total: userData.credits_total,
        quota_used: userData.quota_used,
        reset_date: userData.reset_date,
        trial_expires_at: userData.trial_expires_at,
      }),
    });
  });
}

/**
 * Mock admin users API endpoint
 */
export async function mockAdminUsersAPI(page: Page) {
  // Mock GET /admin/users (list users)
  await page.route('**/admin/users**', async (route: Route) => {
    const method = route.request().method();

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          users: [
            {
              id: 'user-1',
              email: 'user1@test.com',
              full_name: 'User One',
              company: 'Company A',
              plan_type: 'free',
              created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
              user_subscriptions: [
                { id: 'sub-1', plan_id: 'free', credits_remaining: 2, is_active: true },
              ],
            },
            {
              id: 'user-2',
              email: 'user2@test.com',
              full_name: 'User Two',
              company: 'Company B',
              plan_type: 'monthly',
              created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
              user_subscriptions: [
                { id: 'sub-2', plan_id: 'monthly', credits_remaining: null, is_active: true },
              ],
            },
            {
              id: 'user-3',
              email: 'user3@test.com',
              full_name: null,
              company: null,
              plan_type: 'pack_10',
              created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
              user_subscriptions: [
                { id: 'sub-3', plan_id: 'pack_10', credits_remaining: 8, is_active: true },
              ],
            },
          ],
          total: 3,
        }),
      });
    } else if (method === 'POST') {
      // Create user
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'new-user-id',
          email: 'newuser@test.com',
          message: 'User created successfully',
        }),
      });
    }
  });

  // Mock DELETE /admin/users/:id
  await page.route('**/admin/users/*', async (route: Route) => {
    const method = route.request().method();

    if (method === 'DELETE') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'User deleted' }),
      });
    } else if (method === 'POST' && route.request().url().includes('assign-plan')) {
      // Assign plan
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Plan assigned' }),
      });
    } else {
      await route.continue();
    }
  });
}
