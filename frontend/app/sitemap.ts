import { MetadataRoute } from 'next';
import { getAllSlugs, getArticleBySlug } from '@/lib/blog';
import { SECTORS } from '@/lib/sectors';
import { generateSectorParams, generateLicitacoesParams, generateSectorUfParams } from '@/lib/programmatic';
import { getAllCaseSlugs } from '@/lib/cases';
import { CITIES } from '@/lib/cities';
import { GLOSSARY_TERMS } from '@/lib/glossary-terms';
import { getAllAuthorSlugs } from '@/lib/authors';
import { getAllQuestionSlugs } from '@/lib/questions';
import { getAllMasterclassTemas } from '@/lib/masterclasses';

/**
 * GTM-COPY-006 AC10: Dynamic sitemap with all public pages
 * STORY-261 AC10: Includes /blog and /blog/{slug} routes
 * STORY-324 AC12: Includes /licitacoes and /licitacoes/{setor} routes
 * SEO-PLAYBOOK P0: Includes programmatic, licitacoes setor×UF, and panorama routes
 * SEO-PLAYBOOK Onda 1: Includes /cnpj/{cnpj} pages from datalake (≥3 bids)
 * SEO-PLAYBOOK Onda 2: Includes /orgaos/{cnpj} pages from datalake (≥5 bids)
 *
 * Next.js generates sitemap.xml automatically from this file.
 *
 * SEO-CAC-ZERO: lastmod uses actual content dates instead of build time.
 * Google ignores lastmod when all URLs share the same timestamp.
 */

// Cache for CNPJ list fetched from backend (build-time)
let _cnpjCache: string[] = [];
let _cnpjFetched = false;

async function fetchSitemapCnpjs(): Promise<string[]> {
  if (_cnpjFetched) return _cnpjCache;
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const resp = await fetch(`${backendUrl}/v1/sitemap/cnpjs`, {
      next: { revalidate: 86400 }, // 24h ISR
    });
    if (!resp.ok) return [];
    const data = await resp.json();
    _cnpjCache = data.cnpjs || [];
    _cnpjFetched = true;
    return _cnpjCache;
  } catch {
    return [];
  }
}

// SEO-PLAYBOOK Onda 2: Cache for órgãos compradores list
let _orgaoCache: string[] = [];
let _orgaoFetched = false;

async function fetchSitemapOrgaos(): Promise<string[]> {
  if (_orgaoFetched) return _orgaoCache;
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const resp = await fetch(`${backendUrl}/v1/sitemap/orgaos`, {
      next: { revalidate: 86400 }, // 24h ISR
    });
    if (!resp.ok) return [];
    const data = await resp.json();
    _orgaoCache = data.orgaos || [];
    _orgaoFetched = true;
    return _orgaoCache;
  } catch {
    return [];
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';

  // Stable dates for static pages (use actual last-edit date, not build time)
  const STATIC_LAST_EDIT = new Date('2026-04-06');
  // Programmatic/data pages update daily via ISR — use today
  const today = new Date();

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

  // STORY-324 AC12: Sector landing page routes — data updates daily via ISR
  const sectorRoutes: MetadataRoute.Sitemap = SECTORS.map((sector) => ({
    url: `${baseUrl}/licitacoes/${sector.slug}`,
    lastModified: today,
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));

  // SEO-PLAYBOOK P0: Programmatic sector pages (/blog/programmatic/[setor])
  const programmaticSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
    url: `${baseUrl}/blog/programmatic/${setor}`,
    lastModified: today,
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));

  // SEO-PLAYBOOK P0: Sector×UF pages (/blog/licitacoes/[setor]/[uf])
  const licitacoesUfRoutes: MetadataRoute.Sitemap = generateLicitacoesParams().map(({ setor, uf }) => ({
    url: `${baseUrl}/blog/licitacoes/${setor}/${uf}`,
    lastModified: today,
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));

  // SEO-PLAYBOOK P0: Panorama sector pages (/blog/panorama/[setor])
  const panoramaSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
    url: `${baseUrl}/blog/panorama/${setor}`,
    lastModified: STATIC_LAST_EDIT,
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }));

  // SEO-CAC-ZERO A1: Modalidade variants são parâmetros de UI — removidos do sitemap.
  // Canonical de ?modalidade=X aponta para URL base → Google consolidaria ranking mesmo com estas no sitemap.
  // Remoção elimina 1.620 URLs parasitas e concentra link equity nas 405 URLs canônicas.
  // As páginas ainda são acessíveis via UI — só não ficam no sitemap.

  // SEO Frente 4: City pSEO pages (/blog/licitacoes/cidade/[cidade])
  const cidadeRoutes: MetadataRoute.Sitemap = CITIES.map((c) => ({
    url: `${baseUrl}/blog/licitacoes/cidade/${c.slug}`,
    lastModified: today,
    changeFrequency: 'daily' as const,
    priority: 0.7,
  }));

  // Onda 3: City × Sector pSEO pages (81 cities × 15 sectors = 1,215 URLs)
  const cidadeSectorRoutes: MetadataRoute.Sitemap = CITIES.flatMap((c) =>
    SECTORS.map((s) => ({
      url: `${baseUrl}/blog/licitacoes/cidade/${c.slug}/${s.slug}`,
      lastModified: today,
      changeFrequency: 'daily' as const,
      priority: 0.6,
    })),
  );

  // SEO-PLAYBOOK Onda 1: CNPJ pages from datalake
  const cnpjList = await fetchSitemapCnpjs();
  const cnpjRoutes: MetadataRoute.Sitemap = cnpjList.map((cnpj) => ({
    url: `${baseUrl}/cnpj/${cnpj}`,
    lastModified: today,
    changeFrequency: 'weekly' as const,
    priority: 0.5,
  }));

  // SEO-PLAYBOOK Onda 2: Órgãos compradores pages from datalake
  const orgaoList = await fetchSitemapOrgaos();
  const orgaoRoutes: MetadataRoute.Sitemap = orgaoList.map((cnpj) => ({
    url: `${baseUrl}/orgaos/${cnpj}`,
    lastModified: today,
    changeFrequency: 'weekly' as const,
    priority: 0.5,
  }));

  // S3: Alertas Publicos pages (15 sectors × 27 UFs = 405 pages)
  const alertasRoutes: MetadataRoute.Sitemap = generateSectorUfParams().map(({ setor, uf }) => ({
    url: `${baseUrl}/alertas-publicos/${setor}/${uf}`,
    lastModified: today,
    changeFrequency: 'hourly' as const,
    priority: 0.8,
  }));

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
    {
      url: `${baseUrl}/pricing`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'monthly',
      priority: 0.7,
    },
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
    // STORY-261 AC10: Blog listing page
    {
      url: `${baseUrl}/blog`,
      lastModified: today,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    // STORY-261 AC10: Individual blog articles
    ...blogArticleRoutes,
    // STORY-324 AC12: Sector landing pages index
    {
      url: `${baseUrl}/licitacoes`,
      lastModified: today,
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    // STORY-324 AC12: Individual sector landing pages
    ...sectorRoutes,
    {
      url: `${baseUrl}/glossario`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly',
      priority: 0.8,
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
    // SEO-PLAYBOOK P3: CNPJ B2G lookup
    {
      url: `${baseUrl}/cnpj`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    // SEO-PLAYBOOK Onda 2: Órgãos Compradores landing
    {
      url: `${baseUrl}/orgaos`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    // SEO-PLAYBOOK P0: About page
    {
      url: `${baseUrl}/sobre`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'monthly',
      priority: 0.6,
    },
    // SEO-PLAYBOOK P0: Programmatic sector pages
    ...programmaticSectorRoutes,
    // SEO-PLAYBOOK P0: Sector × UF pages (405 combinations)
    ...licitacoesUfRoutes,
    // SEO-CAC-ZERO A1: modalidadeRoutes removidas do sitemap (ISSUE-SEO-002)
    // ?modalidade=X pages canonical → base URL; não precisam de entrada separada no sitemap.
    // SEO-PLAYBOOK P0: Panorama sector pages
    ...panoramaSectorRoutes,
    // SEO Frente 4: City pSEO pages
    ...cidadeRoutes,
    // Onda 3: City × Sector pSEO pages
    ...cidadeSectorRoutes,
    // SEO-PLAYBOOK S1: Individual glossary term pages
    ...GLOSSARY_TERMS.map((t) => ({
      url: `${baseUrl}/glossario/${t.slug}`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    })),
    // SEO-PLAYBOOK S4: Weekly digest index
    {
      url: `${baseUrl}/blog/weekly`,
      lastModified: today,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    },
    // SEO-PLAYBOOK S4: Weekly digest pages (last 12 weeks)
    ...Array.from({ length: 12 }, (_, i) => {
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
    }),
    // SEO-PLAYBOOK S6: Citable statistics
    {
      url: `${baseUrl}/estatisticas`,
      lastModified: today,
      changeFrequency: 'daily' as const,
      priority: 0.8,
    },
    // SEO-PLAYBOOK S2: Public data hub
    {
      url: `${baseUrl}/dados`,
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
    // SEO-PLAYBOOK P5: Cases de sucesso
    {
      url: `${baseUrl}/casos`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'monthly' as const,
      priority: 0.8,
    },
    ...getAllCaseSlugs().map((slug) => ({
      url: `${baseUrl}/casos/${slug}`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'monthly' as const,
      priority: 0.8,
    })),
    // S3: Alertas Publicos hub
    {
      url: `${baseUrl}/alertas-publicos`,
      lastModified: today,
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    // S3: Alertas Publicos pages (405)
    ...alertasRoutes,
    // S5: Demo Interativo
    {
      url: `${baseUrl}/demo`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    },
    // S3: Comparador de Editais
    {
      url: `${baseUrl}/comparador`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    },
    // S7+S11: Author pages
    ...getAllAuthorSlugs().map((slug) => ({
      url: `${baseUrl}/blog/author/${slug}`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'monthly' as const,
      priority: 0.6,
    })),
    // S8: Tech Stack page
    {
      url: `${baseUrl}/stack`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'monthly' as const,
      priority: 0.7,
    },
    // S10: Perguntas hub
    {
      url: `${baseUrl}/perguntas`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    },
    // S10: Individual question pages (53+)
    ...getAllQuestionSlugs().map((slug) => ({
      url: `${baseUrl}/perguntas/${slug}`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    })),
    // S9: Estatísticas embed page
    {
      url: `${baseUrl}/estatisticas/embed`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'monthly' as const,
      priority: 0.6,
    },
    // S13: Masterclass listing
    {
      url: `${baseUrl}/masterclass`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    },
    // S13: Individual masterclass pages
    ...getAllMasterclassTemas().map((tema) => ({
      url: `${baseUrl}/masterclass/${tema}`,
      lastModified: STATIC_LAST_EDIT,
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    })),
    // SEO-PLAYBOOK Onda 1: CNPJ pages from datalake (≥3 bids)
    ...cnpjRoutes,
    // SEO-PLAYBOOK Onda 2: Órgãos compradores pages from datalake (≥5 bids)
    ...orgaoRoutes,
  ];
}
