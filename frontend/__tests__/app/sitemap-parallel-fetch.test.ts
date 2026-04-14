/**
 * @jest-environment node
 *
 * Regression test for HTTP 524 sitemap timeout fix.
 *
 * Bug: sitemap() chamava 7 endpoints do backend sequencialmente (cada await bloqueava
 * o próximo), somando até ~100s de latência → Railway/Cloudflare retornava HTTP 524.
 *
 * Fix: Promise.all() paraleliza as 7 chamadas; AbortSignal.timeout(15000) limita cada
 * fetch a 15s individualmente. Worst-case: 15s total em vez de 7×15s = 105s.
 */

// Mock fetch globally (node env pattern — see __tests__/api/buscar.test.ts)
global.fetch = jest.fn();

// Env vars needed by sitemap()
process.env.BACKEND_URL = 'http://mock-backend';
process.env.NEXT_PUBLIC_CANONICAL_URL = 'https://smartlic.tech';

const BACKEND_ENDPOINTS = [
  '/v1/sitemap/licitacoes-indexable',
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
      const endpoint = BACKEND_ENDPOINTS.find((e) => urlStr.includes(e));
      const payload = endpoint ? PAYLOAD_BY_ENDPOINT[endpoint] : {};
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(payload),
      } as Response);
    },
  );
}

describe('sitemap() — parallel fetch regression (HTTP 524 fix)', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockReset();
  });

  it('chama todos os 7 endpoints com opção signal (AbortSignal.timeout)', async () => {
    makeFastFetchMock();
    const sitemap = await importSitemapFresh();
    await sitemap();

    for (const endpoint of BACKEND_ENDPOINTS) {
      const call = (global.fetch as jest.Mock).mock.calls.find(([url]: [string]) =>
        url.includes(endpoint),
      );
      expect(call).toBeDefined(); // endpoint foi chamado
      const [, init] = call as [string, RequestInit | undefined];
      // Regression guard: ausência de signal era o bug original (faltava AbortSignal.timeout)
      expect(init?.signal).toBeDefined();
    }
  });

  it('inicia todos os 7 fetches antes de qualquer resposta resolver (Promise.all)', async () => {
    const initiated: string[] = [];
    let releaseAll!: () => void;
    const gate = new Promise<void>((res) => {
      releaseAll = res;
    });

    (global.fetch as jest.Mock).mockImplementation(
      (url: string | URL | Request) => {
        const urlStr = typeof url === 'string' ? url : url.toString();
        const endpoint = BACKEND_ENDPOINTS.find((e) => urlStr.includes(e));
        if (endpoint) {
          initiated.push(endpoint);
          return gate.then(() => ({
            ok: true,
            json: () => Promise.resolve(PAYLOAD_BY_ENDPOINT[endpoint]),
          })) as Promise<Response>;
        }
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response);
      },
    );

    const sitemap = await importSitemapFresh();
    const sitemapPromise = sitemap();

    // Flush microtasks para que Promise.all dispare todos os fetches
    for (let i = 0; i < 20; i++) await Promise.resolve();

    // Com Promise.all: todos os 7 devem estar em voo antes de qualquer resposta resolver
    // Com sequential awaits (bug original): apenas 1 teria sido iniciado
    expect(initiated.length).toBe(7);

    releaseAll();
    await sitemapPromise;
  });
});
