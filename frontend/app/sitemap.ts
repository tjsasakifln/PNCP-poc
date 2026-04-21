import { MetadataRoute } from 'next';
import * as Sentry from '@sentry/nextjs';
import { getAllSlugs, getArticleBySlug } from '@/lib/blog';
import { SECTORS } from '@/lib/sectors';
import { generateSectorParams, generateLicitacoesParams, generateSectorUfParams } from '@/lib/programmatic';
import { getAllCaseSlugs } from '@/lib/cases';
import { CITIES } from '@/lib/cities';
import { GLOSSARY_TERMS } from '@/lib/glossary-terms';
import { getAllAuthorSlugs } from '@/lib/authors';
import { getAllQuestionSlugs } from '@/lib/questions';
import { getAllMasterclassTemas } from '@/lib/masterclasses';

// STORY-SEO-001 AC3: Observable fetch wrapper. Replaces the silent `catch { return []; }`
// pattern that hid ECONNREFUSED / DNS / 5xx errors at build time — which is exactly how
// `sitemap/4.xml` went empty in production for weeks without Sentry or Prometheus alerting.
// The wrapper still returns null on failure (callers default to []), so build never breaks.
async function fetchSitemapJson<T>(
  endpoint: string,
  extract: (data: unknown) => T,
  label: string,
): Promise<T | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  const url = `${backendUrl}${endpoint}`;
  try {
    const resp = await fetch(url, {
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
    });
    if (!resp.ok) {
      const err = new Error(`Sitemap fetch ${label} returned HTTP ${resp.status}`);
      console.error(`[sitemap] ${err.message} url=${url}`);
      Sentry.captureException(err, {
        tags: { sitemap_endpoint: label, sitemap_outcome: 'http_error' },
        contexts: { sitemap: { endpoint, url, status: resp.status } },
      });
      return null;
    }
    const data = (await resp.json()) as unknown;
    return extract(data);
  } catch (err) {
    console.error(`[sitemap] fetch ${label} failed`, err);
    Sentry.captureException(err, {
      tags: { sitemap_endpoint: label, sitemap_outcome: 'fetch_error' },
      contexts: { sitemap: { endpoint, url } },
    });
    return null;
  }
}

/**
 * GTM-COPY-006 AC10: Dynamic sitemap with all public pages
 * STORY-261 AC10: Includes /blog and /blog/{slug} routes
 * STORY-324 AC12: Includes /licitacoes and /licitacoes/{setor} routes
 * SEO-PLAYBOOK P0: Includes programmatic, licitacoes setor×UF, and panorama routes
 * SEO-PLAYBOOK Onda 1: Includes /cnpj/{cnpj} pages from datalake (≥1 bid, ~4k-5k URLs)
 * SEO-PLAYBOOK Onda 2: Includes /orgaos/{cnpj} pages from datalake (≥1 bid, top 2000 by volume)
 * SEO-INDEX-001: Sitemap Index com sub-sitemaps segmentados por prioridade de crawl.
 *
 * Next.js generates sitemap.xml automatically as sitemap index from this file.
 * Sub-sitemaps: /sitemap/0.xml (core) → /sitemap/4.xml (entities)
 *
 * SEO-CAC-ZERO: lastmod uses actual content dates instead of build time.
 * Google ignores lastmod when all URLs share the same timestamp.
 */

// STORY-430 AC4: Cache for indexable licitacoes setor×UF combos
let _licitacoesIndexableCache: { setor: string; uf: string }[] | null = null;
let _licitacoesIndexableFetched = false;

async function fetchLicitacoesIndexable(): Promise<{ setor: string; uf: string }[]> {
  if (_licitacoesIndexableFetched && _licitacoesIndexableCache !== null) {
    return _licitacoesIndexableCache;
  }
  const result = await fetchSitemapJson<{ setor: string; uf: string }[]>(
    '/v1/sitemap/licitacoes-indexable',
    (d) => ((d as { combos?: { setor: string; uf: string }[] }).combos ?? []),
    'licitacoes-indexable',
  );
  // SEO-440: empty fallback — without confirmed backend data, we cannot indicate
  // which combos are indexable. Returning generateLicitacoesParams() (all 405 combos)
  // would place noindex pages in sitemap → GSC "Excluded by noindex" mass error.
  _licitacoesIndexableCache = result ?? [];
  _licitacoesIndexableFetched = true;
  return _licitacoesIndexableCache;
}

// SEO-460: Cache para órgãos com contratos reais em pncp_supplier_contracts
let _contratosOrgaoCache: string[] = [];
let _contratosOrgaoFetched = false;

async function fetchContratosOrgaoIndexable(): Promise<string[]> {
  if (_contratosOrgaoFetched) return _contratosOrgaoCache;
  const result = await fetchSitemapJson<string[]>(
    '/v1/sitemap/contratos-orgao-indexable',
    (d) => ((d as { orgaos?: string[] }).orgaos ?? []),
    'contratos-orgao-indexable',
  );
  _contratosOrgaoCache = result ?? [];
  _contratosOrgaoFetched = true;
  return _contratosOrgaoCache;
}

// Cache for CNPJ list fetched from backend (build-time)
let _cnpjCache: string[] = [];
let _cnpjFetched = false;

async function fetchSitemapCnpjs(): Promise<string[]> {
  if (_cnpjFetched) return _cnpjCache;
  const result = await fetchSitemapJson<string[]>(
    '/v1/sitemap/cnpjs',
    (d) => ((d as { cnpjs?: string[] }).cnpjs ?? []),
    'cnpjs',
  );
  _cnpjCache = result ?? [];
  _cnpjFetched = true;
  return _cnpjCache;
}

// SEO-PLAYBOOK Onda 2: Cache for órgãos compradores list
let _orgaoCache: string[] = [];
let _orgaoFetched = false;

// Parte 13 Sprint 3: Cache for fornecedores por CNPJ
let _fornecedoresCnpjCache: string[] = [];
let _fornecedoresCnpjFetched = false;

async function fetchSitemapFornecedoresCnpj(): Promise<string[]> {
  if (_fornecedoresCnpjFetched) return _fornecedoresCnpjCache;
  const result = await fetchSitemapJson<string[]>(
    '/v1/sitemap/fornecedores-cnpj',
    (d) => ((d as { cnpjs?: string[] }).cnpjs ?? []),
    'fornecedores-cnpj',
  );
  _fornecedoresCnpjCache = result ?? [];
  _fornecedoresCnpjFetched = true;
  return _fornecedoresCnpjCache;
}

// Parte 13 Sprint 4: Cache for municípios slugs
let _municipiosCache: string[] = [];
let _municipiosFetched = false;

async function fetchSitemapMunicipios(): Promise<string[]> {
  if (_municipiosFetched) return _municipiosCache;
  const result = await fetchSitemapJson<string[]>(
    '/v1/sitemap/municipios',
    (d) => ((d as { slugs?: string[] }).slugs ?? []),
    'municipios',
  );
  _municipiosCache = result ?? [];
  _municipiosFetched = true;
  return _municipiosCache;
}

// Parte 13 Sprint 6: Cache for CATMAT codes
let _itensCache: string[] = [];
let _itensFetched = false;

async function fetchSitemapItens(): Promise<string[]> {
  if (_itensFetched) return _itensCache;
  const result = await fetchSitemapJson<string[]>(
    '/v1/sitemap/itens',
    (d) => ((d as { catmats?: string[] }).catmats ?? []),
    'itens',
  );
  _itensCache = result ?? [];
  _itensFetched = true;
  return _itensCache;
}

async function fetchSitemapOrgaos(): Promise<string[]> {
  if (_orgaoFetched) return _orgaoCache;
  const result = await fetchSitemapJson<string[]>(
    '/v1/sitemap/orgaos',
    (d) => ((d as { orgaos?: string[] }).orgaos ?? []),
    'orgaos',
  );
  _orgaoCache = result ?? [];
  _orgaoFetched = true;
  return _orgaoCache;
}

/**
 * SEO-INDEX-001: Sitemap Index — 5 sub-sitemaps segmentados por prioridade de crawl.
 * Google processa na ordem: 0 (core) → 1 (setores) → 2 (combos) → 3 (blog) → 4 (entities).
 * Benefício: crawl budget focado nas páginas mais importantes primeiro.
 *
 * id:0 — Core static (~35 URLs, sem backend) — prioridade máxima
 * id:1 — Sector landing pages (~60 URLs, sem backend)
 * id:2 — Sector×UF combos (~1620 URLs, backend: licitacoes-indexable)
 * id:3 — Content/blog pages (~500 URLs, sem backend)
 * id:4 — Entity pages (~10k+ URLs, backend: cnpjs, orgaos, fornecedores)
 */
export async function generateSitemaps() {
  return [
    { id: 0 }, // Core static pages
    { id: 1 }, // Sector landing pages
    { id: 2 }, // Sector×UF programmatic combos
    { id: 3 }, // Content/blog pages
    { id: 4 }, // Entity pages (CNPJs, órgãos, fornecedores)
  ];
}

// SEO-476: Next.js 16 breaking change — id is now Promise<string>, not number.
// Must receive as props object and await the promise before using.
// See: https://nextjs.org/docs/app/api-reference/functions/generate-sitemaps (v16.0.0)
export default async function sitemap(props: { id: Promise<string> }): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';
  const STATIC_LAST_EDIT = new Date('2026-04-06');
  const today = new Date();
  // Await the Promise<string> and convert to number for switch comparison.
  const numericId = parseInt(await props.id, 10);

  switch (numericId) {
    // -----------------------------------------------------------------------
    // id:0 — Core Static Pages (no backend, ~35 URLs)
    // Highest priority — Google indexes these first via sitemap index ordering.
    // -----------------------------------------------------------------------
    case 0:
      return [
        {
          url: baseUrl,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly',
          priority: 1.0,
        },
        {
          url: `${baseUrl}/planos`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly',
          priority: 0.9,
        },
        {
          url: `${baseUrl}/features`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.8,
        },
        {
          url: `${baseUrl}/ajuda`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.7,
        },
        // /pricing removed: 301 redirect to /planos (ISSUE-SEO-005). Only /planos in sitemap.
        {
          url: `${baseUrl}/signup`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.6,
        },
        // /login removed: page is noindex, wastes crawl budget
        {
          url: `${baseUrl}/termos`,
          lastModified: new Date('2026-02-01'),
          changeFrequency: 'yearly',
          priority: 0.2,
        },
        {
          url: `${baseUrl}/privacidade`,
          lastModified: new Date('2026-02-01'),
          changeFrequency: 'yearly',
          priority: 0.2,
        },
        {
          url: `${baseUrl}/sobre`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.6,
        },
        // SEO-PLAYBOOK 6.3: Panorama Licitações Brasil 2026 T1 (gated digital PR asset)
        {
          url: `${baseUrl}/relatorio-2026-t1`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        },
        // SEO-PLAYBOOK P2: Calculadora B2G
        {
          url: `${baseUrl}/calculadora`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly',
          priority: 0.9,
        },
        // Hub pages (landing, no backend content)
        {
          url: `${baseUrl}/blog`,
          lastModified: today,
          changeFrequency: 'weekly',
          priority: 0.9,
        },
        {
          url: `${baseUrl}/licitacoes`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.9,
        },
        {
          url: `${baseUrl}/alertas-publicos`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.9,
        },
        {
          url: `${baseUrl}/contratos`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.8,
        },
        {
          url: `${baseUrl}/fornecedores`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.8,
        },
        {
          url: `${baseUrl}/dados`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.9,
        },
        {
          url: `${baseUrl}/estatisticas`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.8,
        },
        {
          url: `${baseUrl}/cnpj`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly',
          priority: 0.8,
        },
        {
          url: `${baseUrl}/orgaos`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly',
          priority: 0.8,
        },
        {
          url: `${baseUrl}/municipios`,
          lastModified: today,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        },
        {
          url: `${baseUrl}/compliance`,
          lastModified: today,
          changeFrequency: 'weekly' as const,
          priority: 0.7,
        },
        {
          url: `${baseUrl}/itens`,
          lastModified: today,
          changeFrequency: 'weekly' as const,
          priority: 0.7,
        },
        {
          url: `${baseUrl}/glossario`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly',
          priority: 0.8,
        },
        {
          url: `${baseUrl}/casos`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly' as const,
          priority: 0.8,
        },
        {
          url: `${baseUrl}/perguntas`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        },
        {
          url: `${baseUrl}/masterclass`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        },
        // STORY-431 AC6: Observatório de Licitações
        {
          url: `${baseUrl}/observatorio`,
          lastModified: today,
          changeFrequency: 'monthly' as const,
          priority: 0.8,
        },
        {
          url: `${baseUrl}/observatorio/raio-x-marco-2026`,
          lastModified: new Date('2026-04-01'),
          changeFrequency: 'monthly' as const,
          priority: 0.7,
        },
        // S3: Comparador de Editais
        {
          url: `${baseUrl}/comparador`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        },
        // S5: Demo Interativo
        {
          url: `${baseUrl}/demo`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        },
        // S8: Tech Stack page
        {
          url: `${baseUrl}/stack`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly' as const,
          priority: 0.7,
        },
        {
          url: `${baseUrl}/como-avaliar-licitacao`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.7,
        },
        {
          url: `${baseUrl}/como-evitar-prejuizo-licitacao`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.7,
        },
        {
          url: `${baseUrl}/como-filtrar-editais`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.7,
        },
        {
          url: `${baseUrl}/como-priorizar-oportunidades`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly',
          priority: 0.7,
        },
        // SEO-PLAYBOOK S4: Weekly digest hub
        {
          url: `${baseUrl}/blog/weekly`,
          lastModified: today,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        },
        // SEO Wave 3.2: Licitações do dia hub
        {
          url: `${baseUrl}/blog/licitacoes-do-dia`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.9,
        },
        // SEO-PLAYBOOK P7: RSS feed
        {
          url: `${baseUrl}/blog/rss.xml`,
          lastModified: today,
          changeFrequency: 'daily' as const,
          priority: 0.3,
        },
        // S9: Estatísticas embed
        {
          url: `${baseUrl}/estatisticas/embed`,
          lastModified: STATIC_LAST_EDIT,
          changeFrequency: 'monthly' as const,
          priority: 0.6,
        },
      ];

    // -----------------------------------------------------------------------
    // id:1 — Sector Landing Pages (no backend, ~60 URLs)
    // Uses SECTORS constant — no network calls needed.
    // -----------------------------------------------------------------------
    case 1: {
      const sectorRoutes: MetadataRoute.Sitemap = SECTORS.map((sector) => ({
        url: `${baseUrl}/licitacoes/${sector.slug}`,
        lastModified: today,
        changeFrequency: 'daily' as const,
        priority: 0.8,
      }));

      const programmaticSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
        url: `${baseUrl}/blog/programmatic/${setor}`,
        lastModified: today,
        changeFrequency: 'daily' as const,
        priority: 0.8,
      }));

      const panoramaSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
        url: `${baseUrl}/blog/panorama/${setor}`,
        lastModified: STATIC_LAST_EDIT,
        changeFrequency: 'weekly' as const,
        priority: 0.7,
      }));

      // SEO Wave 3.1: /blog/contratos/{setor} pillar pages (15)
      const blogContratosRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
        url: `${baseUrl}/blog/contratos/${setor}`,
        lastModified: today,
        changeFrequency: 'weekly' as const,
        priority: 0.8,
      }));

      return [
        ...sectorRoutes,
        ...programmaticSectorRoutes,
        ...panoramaSectorRoutes,
        ...blogContratosRoutes,
      ];
    }

    // -----------------------------------------------------------------------
    // id:2 — Sector×UF Programmatic Combos (~1620 URLs, needs backend)
    // SEO-440: licitações filtradas pelo endpoint; contratos/fornecedores usam todas as 405.
    // -----------------------------------------------------------------------
    case 2: {
      // Parallelizar: licitacoesIndexable é o único endpoint necessário neste sub-sitemap.
      // Contratos e fornecedores setor×UF usam todas as 405 combos (generateSectorUfParams).
      const indexableCombos = await fetchLicitacoesIndexable();

      // STORY-430 AC4 / SEO-440: filtrar por combos com >= MIN_ACTIVE_BIDS_FOR_INDEX editais
      const licitacoesUfRoutes: MetadataRoute.Sitemap = indexableCombos.map(({ setor, uf }) => ({
        url: `${baseUrl}/blog/licitacoes/${setor}/${uf}`,
        lastModified: today,
        changeFrequency: 'daily' as const,
        priority: 0.8,
      }));

      // S3: Alertas Publicos — reutiliza indexableCombos (já filtrados)
      const alertasRoutes: MetadataRoute.Sitemap = indexableCombos.map(({ setor, uf }) => ({
        url: `${baseUrl}/alertas-publicos/${setor}/${uf}`,
        lastModified: today,
        changeFrequency: 'hourly' as const,
        priority: 0.8,
      }));

      // SEO Wave 2 (12.2.1): Contratos setor×UF (405 combos — sem filtro de dados)
      // SEO-CAC-ZERO A1: modalidadeRoutes removidas do sitemap (ISSUE-SEO-002)
      const contratosUfRoutes: MetadataRoute.Sitemap = generateSectorUfParams().map(({ setor, uf }) => ({
        url: `${baseUrl}/contratos/${setor}/${uf}`,
        lastModified: today,
        changeFrequency: 'daily' as const,
        priority: 0.6,
      }));

      // SEO Wave 2 (12.2.2): Fornecedores setor×UF (405 combos)
      const fornecedoresUfRoutes: MetadataRoute.Sitemap = generateSectorUfParams().map(({ setor, uf }) => ({
        url: `${baseUrl}/fornecedores/${setor}/${uf}`,
        lastModified: today,
        changeFrequency: 'daily' as const,
        priority: 0.6,
      }));

      return [
        ...licitacoesUfRoutes,
        ...alertasRoutes,
        ...contratosUfRoutes,
        ...fornecedoresUfRoutes,
      ];
    }

    // -----------------------------------------------------------------------
    // id:3 — Content/Blog Pages (no backend, ~500 URLs)
    // Articles, glossary, questions, masterclasses, cases, city pages.
    // -----------------------------------------------------------------------
    case 3: {
      // STORY-261 AC10: Blog article routes — use actual publishDate/lastModified
      const blogArticleRoutes: MetadataRoute.Sitemap = getAllSlugs().map((slug) => {
        const article = getArticleBySlug(slug);
        const dateStr = article?.lastModified || article?.publishDate || '2026-04-06';
        return {
          url: `${baseUrl}/blog/${slug}`,
          lastModified: new Date(dateStr),
          changeFrequency: 'monthly' as const,
          priority: 0.7,
        };
      });

      // SEO-PLAYBOOK S1: Individual glossary term pages
      const glossaryRoutes: MetadataRoute.Sitemap = GLOSSARY_TERMS.map((t) => ({
        url: `${baseUrl}/glossario/${t.slug}`,
        lastModified: STATIC_LAST_EDIT,
        changeFrequency: 'weekly' as const,
        priority: 0.7,
      }));

      // S10: Individual question pages (53+)
      const questionRoutes: MetadataRoute.Sitemap = getAllQuestionSlugs().map((slug) => ({
        url: `${baseUrl}/perguntas/${slug}`,
        lastModified: STATIC_LAST_EDIT,
        changeFrequency: 'weekly' as const,
        priority: 0.7,
      }));

      // S13: Individual masterclass pages
      const masterclassRoutes: MetadataRoute.Sitemap = getAllMasterclassTemas().map((tema) => ({
        url: `${baseUrl}/masterclass/${tema}`,
        lastModified: STATIC_LAST_EDIT,
        changeFrequency: 'weekly' as const,
        priority: 0.8,
      }));

      // SEO-PLAYBOOK P5: Cases de sucesso
      const caseRoutes: MetadataRoute.Sitemap = getAllCaseSlugs().map((slug) => ({
        url: `${baseUrl}/casos/${slug}`,
        lastModified: STATIC_LAST_EDIT,
        changeFrequency: 'monthly' as const,
        priority: 0.8,
      }));

      // S7+S11: Author pages
      const authorRoutes: MetadataRoute.Sitemap = getAllAuthorSlugs().map((slug) => ({
        url: `${baseUrl}/blog/author/${slug}`,
        lastModified: STATIC_LAST_EDIT,
        changeFrequency: 'monthly' as const,
        priority: 0.6,
      }));

      // SEO-PLAYBOOK S4: Weekly digest pages (last 12 weeks)
      const weeklyRoutes: MetadataRoute.Sitemap = Array.from({ length: 12 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - i * 7);
        const jan4 = new Date(d.getFullYear(), 0, 4);
        const weekNum = Math.ceil(((d.getTime() - jan4.getTime()) / 86400000 + jan4.getDay() + 1) / 7);
        return {
          url: `${baseUrl}/blog/weekly/${d.getFullYear()}-w${weekNum}`,
          lastModified: today,
          changeFrequency: 'weekly' as const,
          priority: 0.8,
        };
      });

      // SEO Wave 3.2: Licitações do dia — last 30 days
      const licitacoesDoDialRoutes: MetadataRoute.Sitemap = Array.from({ length: 30 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const dateStr = d.toISOString().slice(0, 10);
        const freq: 'hourly' | 'daily' = i === 0 ? 'hourly' : 'daily';
        return {
          url: `${baseUrl}/blog/licitacoes-do-dia/${dateStr}`,
          lastModified: i === 0 ? today : d,
          changeFrequency: freq,
          priority: i === 0 ? 0.9 : 0.7,
        };
      });

      // SEO Frente 4: City pSEO pages (/blog/licitacoes/cidade/[cidade])
      // STORY-439 AC2: City × Sector pSEO pages (1.215 URLs) removidas do sitemap.
      const cidadeRoutes: MetadataRoute.Sitemap = CITIES.map((c) => ({
        url: `${baseUrl}/blog/licitacoes/cidade/${c.slug}`,
        lastModified: today,
        changeFrequency: 'daily' as const,
        priority: 0.7,
      }));

      return [
        ...blogArticleRoutes,
        ...glossaryRoutes,
        ...questionRoutes,
        ...masterclassRoutes,
        ...caseRoutes,
        ...authorRoutes,
        ...weeklyRoutes,
        ...licitacoesDoDialRoutes,
        ...cidadeRoutes,
      ];
    }

    // -----------------------------------------------------------------------
    // id:4 — Entity Pages (~10k+ URLs, needs backend)
    // CNPJs, órgãos, fornecedores, municípios, itens, contratos por órgão.
    // Lowest crawl priority — Google processes these last.
    // -----------------------------------------------------------------------
    case 4: {
      // 6 fetches paralelos saturavam o backend (todos timeoutavam em ~30s+) → sitemap vazio em produção.
      // Serializados: 5-7s cada, total ~30-45s, dentro do orçamento de runtime ISR.
      const cnpjList = await fetchSitemapCnpjs();
      const contratosOrgaoList = await fetchContratosOrgaoIndexable();
      const orgaoList = await fetchSitemapOrgaos();
      const fornecedoresCnpjList = await fetchSitemapFornecedoresCnpj();
      const municipiosList = await fetchSitemapMunicipios();
      const itensList = await fetchSitemapItens();

      // SEO-PLAYBOOK Onda 1: CNPJ pages from datalake (≥1 bid, ~4k-5k URLs)
      const cnpjRoutes: MetadataRoute.Sitemap = cnpjList.map((cnpj) => ({
        url: `${baseUrl}/cnpj/${cnpj}`,
        lastModified: today,
        changeFrequency: 'weekly' as const,
        priority: 0.5,
      }));

      // SEO-PLAYBOOK Onda 2: Órgãos compradores pages from datalake (≥1 bid, top 2000)
      const orgaoRoutes: MetadataRoute.Sitemap = orgaoList.map((cnpj) => ({
        url: `${baseUrl}/orgaos/${cnpj}`,
        lastModified: today,
        changeFrequency: 'weekly' as const,
        priority: 0.5,
      }));

      // Parte 13 Sprint 3: /fornecedores/{cnpj} — perfis de fornecedores (top 5k)
      const fornecedoresCnpjRoutes: MetadataRoute.Sitemap = fornecedoresCnpjList.map((cnpj) => ({
        url: `${baseUrl}/fornecedores/${cnpj}`,
        lastModified: today,
        changeFrequency: 'weekly' as const,
        priority: 0.5,
      }));

      // Parte 13 Sprint 4: /municipios/{slug} — licitações por município (200 pré-renderizados)
      const municipiosRoutes: MetadataRoute.Sitemap = municipiosList.map((slug) => ({
        url: `${baseUrl}/municipios/${slug}`,
        lastModified: today,
        changeFrequency: 'daily' as const,
        priority: 0.7,
      }));

      // Parte 13 Sprint 6: /itens/{catmat} — benchmark por código CATMAT
      const itensRoutes: MetadataRoute.Sitemap = itensList.map((catmat) => ({
        url: `${baseUrl}/itens/${catmat}`,
        lastModified: today,
        changeFrequency: 'weekly' as const,
        priority: 0.6,
      }));

      // SEO-460: /contratos/orgao/{cnpj} — usa lista filtrada por contratos reais.
      // Endpoint /v1/sitemap/contratos-orgao-indexable consulta pncp_supplier_contracts
      // (não pncp_raw_bids) para garantir que apenas CNPJs com contratos assinados
      // entram no sitemap, eliminando os 794 404s do GSC.
      const contratosOrgaoRoutes: MetadataRoute.Sitemap = contratosOrgaoList.map((cnpj) => ({
        url: `${baseUrl}/contratos/orgao/${cnpj}`,
        lastModified: today,
        changeFrequency: 'weekly' as const,
        priority: 0.5,
      }));

      return [
        ...municipiosRoutes, // Highest priority within entities (geographic, SSG)
        ...itensRoutes,
        ...cnpjRoutes,
        ...orgaoRoutes,
        ...fornecedoresCnpjRoutes,
        ...contratosOrgaoRoutes,
      ];
    }

    default:
      return [];
  }
}
