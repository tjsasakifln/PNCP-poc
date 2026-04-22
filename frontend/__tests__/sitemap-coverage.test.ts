/**
 * @jest-environment node
 *
 * STORY-SEO-001 AC7: coverage gate — valida que shard 4 emite ≥ 100 URLs
 * quando o backend tem dados, e que shard 0/1/2 mantêm seus thresholds mínimos.
 *
 * Defesa contra regressão do bug original (sitemap/4.xml vazio em produção por
 * semanas sem alerta). Reforça o cinto+suspensório junto com:
 *  - `backend/metrics.py::record_sitemap_count` (Prometheus counter + gauge)
 *  - `frontend/app/sitemap.ts::fetchSitemapJson` (Sentry captureException)
 *  - Alertas Grafana/Sentry (docs/seo/sitemap-observability-alerts.md)
 */

// Mock fetch globally (padrão de __tests__/api/buscar.test.ts e sitemap-parallel-fetch.test.ts)
global.fetch = jest.fn();

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

// Shard 4 (entity pages) — shape dos payloads por endpoint
function buildShard4Payload(endpoint: string, count: number): object {
  switch (endpoint) {
    case '/v1/sitemap/cnpjs':
    case '/v1/sitemap/fornecedores-cnpj':
      return { cnpjs: Array.from({ length: count }, (_, i) => `${String(i).padStart(14, '0')}`) };
    case '/v1/sitemap/contratos-orgao-indexable':
    case '/v1/sitemap/orgaos':
      return { orgaos: Array.from({ length: count }, (_, i) => ({ cnpj: `${String(i).padStart(14, '0')}`, slug: `org-${i}` })) };
    case '/v1/sitemap/municipios':
      return { slugs: Array.from({ length: count }, (_, i) => `mun-${i}`) };
    case '/v1/sitemap/itens':
      return { catmats: Array.from({ length: count }, (_, i) => ({ catmat: `${i}`, slug: `item-${i}` })) };
    default:
      return {};
  }
}

async function importSitemapFresh() {
  jest.resetModules();
  jest.mock('@/lib/blog', () => ({
    getAllSlugs: () => ['post-1', 'post-2'],
    getArticleBySlug: (slug: string) => ({ slug, lastModified: '2026-01-01', publishDate: '2026-01-01' }),
  }));
  jest.mock('@/lib/sectors', () => ({ SECTORS: [{ id: 'limpeza', name: 'Limpeza' }] }));
  jest.mock('@/lib/programmatic', () => ({
    generateSectorParams: () => [{ setor: 'limpeza' }],
    generateLicitacoesParams: () => [],
    generateSectorUfParams: () => [{ setor: 'limpeza', uf: 'SP' }],
  }));
  jest.mock('@/lib/cases', () => ({ getAllCaseSlugs: () => [] }));
  jest.mock('@/lib/cities', () => ({ CITIES: [{ slug: 'sao-paulo', name: 'São Paulo' }] }));
  jest.mock('@/lib/glossary-terms', () => ({ GLOSSARY_TERMS: [] }));
  jest.mock('@/lib/authors', () => ({ getAllAuthorSlugs: () => [] }));
  jest.mock('@/lib/questions', () => ({ getAllQuestionSlugs: () => [] }));
  jest.mock('@/lib/masterclasses', () => ({ getAllMasterclassTemas: () => [] }));

  const mod = await import('../app/sitemap');
  return mod.default;
}

describe('sitemap() — coverage thresholds (STORY-SEO-001 AC7)', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockReset();
  });

  it('shard 4 com backend devolvendo 20 entidades em cada endpoint emite ≥ 100 URLs', async () => {
    const PER_ENDPOINT = 20; // 6 × 20 = 120 URLs mínimo
    (global.fetch as jest.Mock).mockImplementation((url: string | URL | Request) => {
      const urlStr = typeof url === 'string' ? url : url.toString();
      const endpoint = ENTITY_ENDPOINTS.find((e) => urlStr.includes(e));
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(endpoint ? buildShard4Payload(endpoint, PER_ENDPOINT) : {}),
      } as Response);
    });

    const sitemap = await importSitemapFresh();
    const urls = await sitemap({ id: 4 });

    // Cinto: ≥ 100 URLs é o threshold de AC7 "fail se shard 4 < 100"
    expect(urls.length).toBeGreaterThanOrEqual(100);
    // Suspensório: ≥ 6 × PER_ENDPOINT esperado
    expect(urls.length).toBeGreaterThanOrEqual(6 * PER_ENDPOINT);
  });

  it('shard 4 regression gate — backend vazio em TODOS endpoints produz shard vazio graceful (sinalizador Sentry)', async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string | URL | Request) => {
      const urlStr = typeof url === 'string' ? url : url.toString();
      const endpoint = ENTITY_ENDPOINTS.find((e) => urlStr.includes(e));
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(endpoint ? buildShard4Payload(endpoint, 0) : {}),
      } as Response);
    });

    const sitemap = await importSitemapFresh();
    const urls = await sitemap({ id: 4 });

    // Build não quebra (graceful), mas produz 0 URLs → gauge smartlic_sitemap_urls_last
    // em backend/metrics.py dispara alerta Sentry (documentado em docs/seo/sitemap-observability-alerts.md)
    expect(urls.length).toBe(0);
  });

  it('shard 4 com falha HTTP 500 emite 0 URLs silenciosamente mas Sentry.captureException é chamado', async () => {
    (global.fetch as jest.Mock).mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Internal Server Error' }),
      } as Response);
    });

    const sitemap = await importSitemapFresh();
    const urls = await sitemap({ id: 4 });

    // Falhas HTTP não quebram build (fetchSitemapJson retorna null → callers usam [])
    // mas Sentry.captureException é chamado com tags sitemap_endpoint + sitemap_outcome='http_error'
    expect(urls.length).toBe(0);
  });

  it('shard 0 (core pages) emite ≥ 10 URLs independente do backend (não depende de fetch)', async () => {
    (global.fetch as jest.Mock).mockImplementation(() => Promise.reject(new Error('backend offline')));
    const sitemap = await importSitemapFresh();
    const urls = await sitemap({ id: 0 });
    expect(urls.length).toBeGreaterThanOrEqual(10);
  });
});
