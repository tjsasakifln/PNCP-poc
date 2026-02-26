/**
 * Smoke Test Helpers for GTM-QUAL-001
 *
 * Specialized mocks and assertions for the GTM Root Cause smoke test suite.
 * Covers: async search (202+SSE), onboarding, pipeline, dashboard, payment,
 * and cross-cutting validations (zero English, max 1 banner, disabled tooltips).
 */

import { Page, Route, expect } from '@playwright/test';

// ---------------------------------------------------------------------------
// English text detection patterns (AC4)
// ---------------------------------------------------------------------------

/** Common English error/UI patterns that should NEVER appear in PT-BR app */
const ENGLISH_ERROR_PATTERNS = [
  /\bInvalid\b/,
  /\bError\b/,
  /\bFailed\b/,
  /\bunauthorized\b/i,
  /\bnot found\b/i,
  /\bforbidden\b/i,
  /\bsomething went wrong\b/i,
  /\binternal server error\b/i,
  /\bbad request\b/i,
  /\bsession expired\b/i,
  /\bplease try again\b/i,
  /\bloading\.\.\./i,
  /\bsubmit\b/i,
  /\bcancel\b/i,
  /\bdelete\b/i,
  /\bsave\b/i,
  /\bsuccess\b/i,
  /\bwarning\b/i,
  /\bconfirm\b/i,
];

/** Technical terms that are acceptable in English */
const ENGLISH_ALLOWLIST = [
  'Excel', 'PDF', 'WhatsApp', 'Google', 'Stripe', 'SSE', 'API',
  'Dashboard', 'Pipeline', 'Pro', 'SmartLic', 'DescompLicita',
  'email', 'login', 'logout', 'Wi-Fi', 'online', 'offline',
  'download', 'upload', 'drag', 'drop', 'OK', 'CNAE', 'UF',
  'checkbox', 'toggle', 'slider', 'tooltip', 'modal',
  'Premium', 'Basic', 'Free', 'Trial',
];

/**
 * AC4: Assert zero English text in any visible element during flows.
 * Scans all visible text nodes for English error/UI patterns,
 * excluding technical terms.
 */
export async function assertZeroEnglishText(page: Page): Promise<void> {
  const visibleText = await page.evaluate(() => {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const el = node.parentElement;
          if (!el) return NodeFilter.FILTER_REJECT;
          const style = getComputedStyle(el);
          if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return NodeFilter.FILTER_REJECT;
          }
          // Skip script/style/noscript tags
          const tag = el.tagName.toLowerCase();
          if (['script', 'style', 'noscript', 'svg', 'path'].includes(tag)) {
            return NodeFilter.FILTER_REJECT;
          }
          const text = node.textContent?.trim();
          if (!text || text.length < 3) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    const texts: string[] = [];
    let node: Node | null;
    while ((node = walker.nextNode())) {
      const t = node.textContent?.trim();
      if (t) texts.push(t);
    }
    return texts;
  });

  for (const text of visibleText) {
    for (const pattern of ENGLISH_ERROR_PATTERNS) {
      if (pattern.test(text)) {
        // Check if it's an allowlisted technical term
        const isAllowed = ENGLISH_ALLOWLIST.some((term) =>
          text.includes(term) && text.replace(new RegExp(term, 'gi'), '').trim().length < 5
        );
        if (!isAllowed) {
          throw new Error(
            `AC4 VIOLATION: English text found in visible element: "${text}" (matched pattern: ${pattern})`
          );
        }
      }
    }
  }
}

/**
 * AC5: Assert maximum 1 informational banner visible at any moment.
 * Counts visible banner-like elements (role=alert, role=status, data-banner).
 */
export async function assertMaxOneBanner(page: Page): Promise<void> {
  const bannerCount = await page.evaluate(() => {
    const selectors = [
      '[data-banner]',
      '[role="alert"]:not([aria-live="assertive"])',
      '[role="status"][data-type="banner"]',
      '.banner-informativo',
    ];
    let count = 0;
    for (const sel of selectors) {
      const els = document.querySelectorAll(sel);
      for (const el of els) {
        const style = getComputedStyle(el);
        if (
          style.display !== 'none' &&
          style.visibility !== 'hidden' &&
          style.opacity !== '0' &&
          (el as HTMLElement).offsetHeight > 0
        ) {
          count++;
        }
      }
    }
    return count;
  });

  expect(bannerCount, 'AC5: More than 1 informational banner visible simultaneously').toBeLessThanOrEqual(1);
}

/**
 * AC6: Assert no disabled button exists without a tooltip explaining why.
 */
export async function assertNoDisabledWithoutTooltip(page: Page): Promise<void> {
  const violations = await page.evaluate(() => {
    const buttons = document.querySelectorAll('button:disabled, button[aria-disabled="true"]');
    const issues: string[] = [];
    for (const btn of buttons) {
      const hasTitle = btn.getAttribute('title');
      const hasAriaLabel = btn.getAttribute('aria-label');
      const hasAriaDescribedBy = btn.getAttribute('aria-describedby');
      const hasTooltipParent = btn.closest('[data-tooltip]') || btn.closest('[title]');

      if (!hasTitle && !hasAriaLabel && !hasAriaDescribedBy && !hasTooltipParent) {
        issues.push(
          `Button "${btn.textContent?.trim() || btn.getAttribute('aria-label') || 'unnamed'}" is disabled without tooltip`
        );
      }
    }
    return issues;
  });

  expect(
    violations,
    `AC6: Disabled buttons without tooltip explanation: ${violations.join('; ')}`
  ).toHaveLength(0);
}

// ---------------------------------------------------------------------------
// Async Search Mocking (202 + SSE)
// ---------------------------------------------------------------------------

interface AsyncSearchOptions {
  searchId?: string;
  resultData?: Record<string, any>;
  shouldFail?: boolean;
  delayMs?: number;
}

/**
 * Mock the async search flow: POST /api/buscar returns 202,
 * then SSE stream delivers progress events, then results endpoint returns data.
 */
export async function mockAsyncSearchFlow(
  page: Page,
  options: AsyncSearchOptions = {}
): Promise<string> {
  const searchId = options.searchId || 'smoke-test-' + Date.now();

  // 1. Mock POST /api/buscar → 202 Accepted
  await page.route('**/api/buscar', async (route: Route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          search_id: searchId,
          status: 'queued',
        }),
      });
    } else {
      await route.continue();
    }
  });

  // 2. Mock SSE /api/buscar-progress → delivers events then complete
  await page.route('**/api/buscar-progress**', async (route: Route) => {
    const delay = options.delayMs || 500;

    if (options.shouldFail) {
      const sseBody = [
        `data: ${JSON.stringify({ stage: 'error', progress: 0, message: 'Erro ao processar busca. Tente novamente.', detail: { error: 'SEARCH_FAILED', error_code: 'SOURCE_UNAVAILABLE' } })}\n\n`,
      ].join('');

      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        body: sseBody,
      });
      return;
    }

    // Build SSE event stream
    const events = [
      { stage: 'connecting', progress: 3, message: 'Conectando aos portais...', detail: {} },
      { stage: 'fetching', progress: 25, message: 'Buscando em SC...', detail: { uf_index: 1, uf_total: 2 } },
      { stage: 'fetching', progress: 50, message: 'Buscando em PR...', detail: { uf_index: 2, uf_total: 2 } },
      { stage: 'filtering', progress: 65, message: 'Filtrando resultados...', detail: {} },
      { stage: 'llm', progress: 80, message: 'Gerando resumo executivo...', detail: {} },
      { stage: 'excel', progress: 95, message: 'Preparando Excel...', detail: {} },
      { stage: 'search_complete', progress: 100, message: 'Busca concluida', detail: { has_results: true, search_id: searchId, total_results: 15 } },
    ];

    const sseBody = events
      .map((evt) => `data: ${JSON.stringify(evt)}\n\n`)
      .join('');

    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
      body: sseBody,
    });
  });

  // 3. Mock GET /api/buscar-results/{searchId} → final results
  await page.route(`**/api/buscar-results/**`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(
        options.resultData || {
          search_id: searchId,
          download_id: searchId,
          total_raw: 125,
          total_filtrado: 15,
          resumo: {
            resumo_executivo:
              'Resumo Executivo: Encontradas 15 licitacoes de uniformes em SC e PR, totalizando R$ 750.000,00.',
            total_oportunidades: 15,
            valor_total: 750000,
            destaques: [
              'Destaque para licitacao de uniformes escolares em Curitiba no valor de R$ 120.000,00',
              'Oportunidade de fardamento militar em Florianopolis com prazo de entrega de 45 dias',
            ],
            distribuicao_uf: { SC: 8, PR: 7 },
            alerta_urgencia: null,
          },
          licitacoes: generateMockLicitacoes(15),
          excel_available: true,
          download_url: `/api/download/${searchId}`,
          response_state: 'live',
          coverage_metadata: {
            ufs_requested: ['SC', 'PR'],
            ufs_processed: ['SC', 'PR'],
            ufs_failed: [],
            coverage_pct: 100.0,
            freshness: 'live',
          },
        }
      ),
    });
  });

  // 4. Mock search status endpoint (polling fallback)
  await page.route('**/v1/search/*/status', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        search_id: searchId,
        status: 'completed',
        progress: 100,
      }),
    });
  });

  return searchId;
}

// ---------------------------------------------------------------------------
// Onboarding API mocks
// ---------------------------------------------------------------------------

export async function mockOnboardingAPIs(page: Page): Promise<void> {
  // Mock setores endpoint
  await page.route('**/api/setores', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        setores: [
          { id: 'vestuario', name: 'Vestuario e Uniformes', description: 'Confeccao, uniformes, EPIs' },
          { id: 'alimentos', name: 'Alimentos e Merenda', description: 'Generos alimenticios' },
          { id: 'informatica', name: 'Hardware e Equipamentos de TI', description: 'Computadores, perifericos' },
        ],
      }),
    });
  });

  // Mock /v1/setores
  await page.route('**/v1/setores', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        setores: [
          { id: 'vestuario', name: 'Vestuario e Uniformes', description: 'Confeccao, uniformes, EPIs' },
          { id: 'alimentos', name: 'Alimentos e Merenda', description: 'Generos alimenticios' },
          { id: 'informatica', name: 'Hardware e Equipamentos de TI', description: 'Computadores, perifericos' },
        ],
      }),
    });
  });

  // Mock first-analysis endpoint (onboarding → auto search)
  await page.route('**/api/first-analysis', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        search_id: 'onboarding-first-analysis-id',
        status: 'queued',
      }),
    });
  });
}

// ---------------------------------------------------------------------------
// Pipeline API mocks
// ---------------------------------------------------------------------------

export async function mockPipelineAPIs(page: Page): Promise<void> {
  const pipelineItems = [
    {
      id: 'pipe-1',
      title: 'Uniformes escolares - Prefeitura de Curitiba',
      stage: 'prospect',
      value: 120000,
      deadline: '2026-03-15',
      notes: '',
      created_at: new Date().toISOString(),
    },
    {
      id: 'pipe-2',
      title: 'Fardamento militar - Governo SC',
      stage: 'qualified',
      value: 85000,
      deadline: '2026-03-20',
      notes: 'Documentacao em andamento',
      created_at: new Date().toISOString(),
    },
  ];

  // GET pipeline items
  await page.route('**/api/pipeline', async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: pipelineItems }),
      });
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'pipe-new', message: 'Item adicionado ao pipeline' }),
      });
    } else {
      await route.continue();
    }
  });

  // PATCH pipeline item (drag-and-drop stage change)
  await page.route('**/api/pipeline/*', async (route: Route) => {
    if (route.request().method() === 'PATCH') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Pipeline atualizado' }),
      });
    } else if (route.request().method() === 'DELETE') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Item removido' }),
      });
    } else {
      await route.continue();
    }
  });
}

// ---------------------------------------------------------------------------
// Dashboard API mocks
// ---------------------------------------------------------------------------

export async function mockDashboardAPIs(page: Page): Promise<void> {
  await page.route('**/api/analytics**', async (route: Route) => {
    const url = route.request().url();

    if (url.includes('summary')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_searches: 42,
          total_opportunities: 186,
          total_value: 2750000,
          hours_saved: 84,
          success_rate: 92.5,
        }),
      });
    } else if (url.includes('searches-over-time')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            { date: '2026-02-17', searches: 5, opportunities: 22 },
            { date: '2026-02-18', searches: 7, opportunities: 31 },
            { date: '2026-02-19', searches: 6, opportunities: 28 },
          ],
        }),
      });
    } else if (url.includes('top-dimensions')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          top_ufs: [
            { uf: 'SC', count: 15 },
            { uf: 'PR', count: 12 },
            { uf: 'SP', count: 8 },
          ],
          top_sectors: [
            { sector: 'Vestuario', count: 20 },
            { sector: 'Informatica', count: 15 },
          ],
        }),
      });
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      });
    }
  });
}

// ---------------------------------------------------------------------------
// Payment / Billing mocks
// ---------------------------------------------------------------------------

export async function mockPaymentAPIs(page: Page): Promise<void> {
  // Plans endpoint
  await page.route('**/api/plans', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        plans: [
          { id: 'free', name: 'Gratuito', price: 0, searches_per_month: 3 },
          { id: 'smartlic_pro', name: 'SmartLic Pro', price: 397, searches_per_month: null },
        ],
      }),
    });
  });

  // Billing plans
  await page.route('**/api/billing/plans', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        plans: [
          { id: 'smartlic_pro', name: 'SmartLic Pro', price_monthly: 397, price_semiannual: 2142, price_annual: 3564 },
        ],
      }),
    });
  });

  // Checkout endpoint
  await page.route('**/api/v1/checkout**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        checkout_url: 'https://checkout.stripe.com/mock-session-id',
      }),
    });
  });

  // Subscription status
  await page.route('**/api/subscription/status', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        subscription_status: 'active',
        plan_id: 'smartlic_pro',
        plan_name: 'SmartLic Pro',
        current_period_end: '2026-03-23',
      }),
    });
  });
}

// ---------------------------------------------------------------------------
// Auth mocking for different user types
// ---------------------------------------------------------------------------

interface MockUserOptions {
  planId?: string;
  planName?: string;
  creditsRemaining?: number | null;
  subscriptionStatus?: string;
  isAdmin?: boolean;
  trialExpiresAt?: string | null;
}

export async function mockTrialUser(page: Page, opts: MockUserOptions = {}): Promise<void> {
  const user = {
    id: 'trial-user-smoke-test',
    email: 'trial@smoke-test.com',
    user_metadata: { full_name: 'Trial Smoke User' },
  };

  // Mock Supabase auth
  await page.route('**/auth/v1/token**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mock-trial-access-token',
        refresh_token: 'mock-trial-refresh-token',
        expires_in: 3600,
        token_type: 'bearer',
        user,
      }),
    });
  });

  // Mock /me for trial user
  await page.route('**/me', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: user.id,
        email: user.email,
        full_name: user.user_metadata.full_name,
        is_admin: opts.isAdmin || false,
        plan_id: opts.planId || 'free_trial',
        plan_name: opts.planName || 'Trial Gratuito',
        credits_remaining: opts.creditsRemaining ?? 3,
        subscription_status: opts.subscriptionStatus || 'trialing',
        trial_expires_at: opts.trialExpiresAt || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      }),
    });
  });

  // Set auth state
  await page.addInitScript(
    ({ user: u }) => {
      const authKey = 'sb-localhost-auth-token';
      localStorage.setItem(
        authKey,
        JSON.stringify({
          access_token: 'mock-trial-access-token',
          refresh_token: 'mock-trial-refresh-token',
          expires_at: Date.now() + 3600000,
          user: u,
        })
      );
      localStorage.setItem('auth-user', JSON.stringify(u));
      localStorage.setItem(
        'auth-session',
        JSON.stringify({
          access_token: 'mock-trial-access-token',
          refresh_token: 'mock-trial-refresh-token',
          expires_at: Date.now() + 3600000,
        })
      );
    },
    { user }
  );
}

export async function mockPaidUser(page: Page): Promise<void> {
  const user = {
    id: 'paid-user-smoke-test',
    email: 'paid@smoke-test.com',
    user_metadata: { full_name: 'Paid Smoke User' },
  };

  await page.route('**/auth/v1/token**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mock-paid-access-token',
        refresh_token: 'mock-paid-refresh-token',
        expires_in: 3600,
        token_type: 'bearer',
        user,
      }),
    });
  });

  await page.route('**/me', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: user.id,
        email: user.email,
        full_name: user.user_metadata.full_name,
        is_admin: false,
        plan_id: 'smartlic_pro',
        plan_name: 'SmartLic Pro',
        credits_remaining: null,
        subscription_status: 'active',
      }),
    });
  });

  await page.addInitScript(
    ({ user: u }) => {
      const authKey = 'sb-localhost-auth-token';
      localStorage.setItem(
        authKey,
        JSON.stringify({
          access_token: 'mock-paid-access-token',
          refresh_token: 'mock-paid-refresh-token',
          expires_at: Date.now() + 3600000,
          user: u,
        })
      );
      localStorage.setItem('auth-user', JSON.stringify(u));
      localStorage.setItem(
        'auth-session',
        JSON.stringify({
          access_token: 'mock-paid-access-token',
          refresh_token: 'mock-paid-refresh-token',
          expires_at: Date.now() + 3600000,
        })
      );
    },
    { user }
  );
}

// ---------------------------------------------------------------------------
// Download mocking
// ---------------------------------------------------------------------------

export async function mockDownloadEndpoint(page: Page, shouldFail = false): Promise<void> {
  await page.route('**/api/download**', async (route: Route) => {
    if (shouldFail) {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Arquivo nao encontrado' }),
      });
      return;
    }

    const headers = {
      'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'Content-Disposition': `attachment; filename=DescompLicita_Vestuario_e_Uniformes_${new Date().toISOString().slice(0, 10)}.xlsx`,
    };

    if (route.request().method() === 'HEAD') {
      await route.fulfill({ status: 200, headers });
    } else {
      const content = Buffer.from('PK\x05\x06' + '\x00'.repeat(18), 'binary');
      await route.fulfill({
        status: 200,
        headers: { ...headers, 'Content-Length': content.length.toString() },
        body: content,
      });
    }
  });
}

// ---------------------------------------------------------------------------
// Session/history mocking
// ---------------------------------------------------------------------------

export async function mockSessionsAPI(page: Page): Promise<void> {
  await page.route('**/api/sessions**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ sessions: [] }),
    });
  });

  await page.route('**/sessions', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ sessions: [] }),
    });
  });
}

// ---------------------------------------------------------------------------
// Misc catch-all mocks
// ---------------------------------------------------------------------------

export async function mockMiscAPIs(page: Page): Promise<void> {
  // Health endpoint
  await page.route('**/health', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'healthy' }),
    });
  });

  // Conversations/messages
  await page.route('**/api/conversations**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ conversations: [] }),
    });
  });

  await page.route('**/unread-count', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ count: 0 }),
    });
  });

  // Pipeline alerts
  await page.route('**/api/pipeline/alerts', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ alerts: [] }),
    });
  });

  // Google sheets
  await page.route('**/api/google-sheets**', async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ history: [] }),
    });
  });
}

// ---------------------------------------------------------------------------
// Mock Licitacao generator
// ---------------------------------------------------------------------------

function generateMockLicitacoes(count: number) {
  const items = [];
  for (let i = 0; i < count; i++) {
    items.push({
      id: `lic-${i + 1}`,
      titulo: `Licitacao ${i + 1} - Uniformes para orgao publico`,
      orgao: `Prefeitura Municipal ${i + 1}`,
      uf: i % 2 === 0 ? 'SC' : 'PR',
      valor_estimado: 50000 + i * 10000,
      data_abertura: '2026-03-15',
      modalidade: 'Pregao Eletronico',
      status: 'Recebendo Proposta',
      url: `https://pncp.gov.br/licitacao/${i + 1}`,
      relevance_score: 0.95 - i * 0.02,
    });
  }
  return items;
}
