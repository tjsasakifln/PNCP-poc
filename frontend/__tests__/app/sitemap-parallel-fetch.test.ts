/**
 * @jest-environment node
 *
 * Regression test for sitemap fetch behavior.
 *
 * Historical context:
 *  - v1 (pre-SEO-460): awaits sequenciais → somou latência → HTTP 524.
 *  - v2 (SEO-460): Promise.all paraleliza + AbortSignal.timeout(15000).
 *  - v3 (#458, 2026-04-21): awaits sequenciais DE NOVO — 6 fetches paralelos
 *    saturavam o backend em produção (todos timeoutavam simultaneamente em ~30s+),
 *    resultando em sitemap/4.xml vazio. Serialização + ISR 1h (revalidate=3600)
 *    move o custo para 1 request/h por shard (amortizado entre crawlers).
 *
 * Por sub-sitemap:
 *  - id:2 → /v1/sitemap/licitacoes-indexable (1 endpoint)
 *  - id:4 → 6 endpoints de entidades em awaits sequenciais
 */

// Mock fetch globally (node env pattern — see __tests__/api/buscar.test.ts)
global.fetch = jest.fn();

// Env vars needed by sitemap()
process.env.BACKEND_URL = 'http://mock-backend';
process.env.NEXT_PUBLIC_CANONICAL_URL = 'https://smartlic.tech';

const ENTITY_ENDPOINTS = [
  '/v1/sitemap/cnpjs',
  '/v1/sitemap/contratos-orgao-indexable',
  '/v1/sitemap/orgaos',
  '/v1/sitemap/fornecedores-cnpj',
  '/v1/sitemap/municipios',
  '/v1/sitemap/itens',
] as const;

const PAYLOAD_BY_ENDPOINT: Record<string, object> = {
  '/v1/sitemap/licitacoes-indexable': { combos: [] },
  '/v1/sitemap/cnpjs': { cnpjs: [] },
  '/v1/sitemap/contratos-orgao-indexable': { orgaos: [] },
  '/v1/sitemap/orgaos': { orgaos: [] },
  '/v1/sitemap/fornecedores-cnpj': { cnpjs: [] },
  '/v1/sitemap/municipios': { slugs: [] },
  '/v1/sitemap/itens': { catmats: [] },
};

// Helper: importa sitemap fresco (sem cache de módulo) + mocks de filesystem
async function importSitemapFresh() {
  jest.resetModules();
  jest.mock('@/lib/blog', () => ({ getAllSlugs: () => [], getArticleBySlug: () => null }));
  jest.mock('@/lib/sectors', () => ({ SECTORS: [] }));
  jest.mock('@/lib/programmatic', () => ({
    generateSectorParams: () => [],
    generateLicitacoesParams: () => [],
    generateSectorUfParams: () => [],
  }));
  jest.mock('@/lib/cases', () => ({ getAllCaseSlugs: () => [] }));
  jest.mock('@/lib/cities', () => ({ CITIES: [] }));
  jest.mock('@/lib/glossary-terms', () => ({ GLOSSARY_TERMS: [] }));
  jest.mock('@/lib/authors', () => ({ getAllAuthorSlugs: () => [] }));
  jest.mock('@/lib/questions', () => ({ getAllQuestionSlugs: () => [] }));
  jest.mock('@/lib/masterclasses', () => ({ getAllMasterclassTemas: () => [] }));

  const mod = await import('../../app/sitemap');
  return mod.default;
}

function makeFastFetchMock() {
  (global.fetch as jest.Mock).mockImplementation(
    (url: string | URL | Request, _init?: RequestInit) => {
      const urlStr = typeof url === 'string' ? url : url.toString();
      const allEndpoints = [...ENTITY_ENDPOINTS, '/v1/sitemap/licitacoes-indexable'];
      const endpoint = allEndpoints.find((e) => urlStr.includes(e));
      const payload = endpoint ? PAYLOAD_BY_ENDPOINT[endpoint] : {};
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(payload),
      } as Response);
    },
  );
}

describe('sitemap() — fetch behavior (signal + serialization)', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockReset();
  });

  it('sub-sitemap id:2 chama licitacoes-indexable com signal (AbortSignal.timeout)', async () => {
    makeFastFetchMock();
    const sitemap = await importSitemapFresh();
    await sitemap({ id: 2 });

    const call = (global.fetch as jest.Mock).mock.calls.find(([url]: [string]) =>
      url.includes('/v1/sitemap/licitacoes-indexable'),
    );
    expect(call).toBeDefined();
    const [, init] = call as [string, RequestInit | undefined];
    expect(init?.signal).toBeDefined();
  });

  it('sub-sitemap id:4 chama todos os 6 endpoints de entidades com signal (AbortSignal.timeout)', async () => {
    makeFastFetchMock();
    const sitemap = await importSitemapFresh();
    await sitemap({ id: 4 });

    for (const endpoint of ENTITY_ENDPOINTS) {
      const call = (global.fetch as jest.Mock).mock.calls.find(([url]: [string]) =>
        url.includes(endpoint),
      );
      expect(call).toBeDefined(); // endpoint foi chamado
      const [, init] = call as [string, RequestInit | undefined];
      // Regression guard: ausência de signal era o bug original (faltava AbortSignal.timeout)
      expect(init?.signal).toBeDefined();
    }
  });

  it('sub-sitemap id:4 serializa os 6 fetches (um por vez) para proteger backend de saturação', async () => {
    // #458: código mudou de Promise.all → awaits sequenciais.
    // Garantia: no máximo 1 fetch em voo a qualquer momento; o próximo só inicia
    // após o anterior resolver. Isso previne o 6-way saturation que causava
    // sitemap/4.xml vazio em produção.
    const initiated: string[] = [];
    const resolvers: Array<() => void> = [];

    (global.fetch as jest.Mock).mockImplementation(
      (url: string | URL | Request) => {
        const urlStr = typeof url === 'string' ? url : url.toString();
        const endpoint = ENTITY_ENDPOINTS.find((e) => urlStr.includes(e));
        if (endpoint) {
          initiated.push(endpoint);
          return new Promise<Response>((resolve) => {
            resolvers.push(() =>
              resolve({
                ok: true,
                json: () => Promise.resolve(PAYLOAD_BY_ENDPOINT[endpoint]),
              } as Response),
            );
          });
        }
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response);
      },
    );

    const sitemap = await importSitemapFresh();
    const sitemapPromise = sitemap({ id: 4 });

    const flush = async () => {
      for (let i = 0; i < 20; i++) await Promise.resolve();
    };

    // Serial: após microtasks iniciais, APENAS 1 fetch em voo
    await flush();
    expect(initiated.length).toBe(1);

    // Resolve cada um → próximo inicia; contagem avança 1 a 1
    for (let step = 1; step < ENTITY_ENDPOINTS.length; step++) {
      resolvers[step - 1]();
      await flush();
      expect(initiated.length).toBe(step + 1);
    }

    // Resolve o último para completar a promise
    resolvers[ENTITY_ENDPOINTS.length - 1]();
    await sitemapPromise;
  });
});
