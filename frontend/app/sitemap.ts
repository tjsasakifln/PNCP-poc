import { MetadataRoute } from 'next';
import { getAllSlugs } from '@/lib/blog';
import { SECTORS } from '@/lib/sectors';
import { generateSectorParams, generateLicitacoesParams } from '@/lib/programmatic';
import { getAllCaseSlugs } from '@/lib/cases';
import { CITIES } from '@/lib/cities';

/**
 * GTM-COPY-006 AC10: Dynamic sitemap with all public pages
 * STORY-261 AC10: Includes /blog and /blog/{slug} routes
 * STORY-324 AC12: Includes /licitacoes and /licitacoes/{setor} routes
 * SEO-PLAYBOOK P0: Includes programmatic, licitacoes setor×UF, and panorama routes
 *
 * Next.js generates sitemap.xml automatically from this file.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';

  // STORY-261 AC10: Blog article routes
  const blogArticleRoutes: MetadataRoute.Sitemap = getAllSlugs().map((slug) => ({
    url: `${baseUrl}/blog/${slug}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.7,
  }));

  // STORY-324 AC12: Sector landing page routes
  const sectorRoutes: MetadataRoute.Sitemap = SECTORS.map((sector) => ({
    url: `${baseUrl}/licitacoes/${sector.slug}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));

  // SEO-PLAYBOOK P0: Programmatic sector pages (/blog/programmatic/[setor])
  const programmaticSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
    url: `${baseUrl}/blog/programmatic/${setor}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));

  // SEO-PLAYBOOK P0: Sector×UF pages (/blog/licitacoes/[setor]/[uf])
  const licitacoesUfRoutes: MetadataRoute.Sitemap = generateLicitacoesParams().map(({ setor, uf }) => ({
    url: `${baseUrl}/blog/licitacoes/${setor}/${uf}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));

  // SEO-PLAYBOOK P0: Panorama sector pages (/blog/panorama/[setor])
  const panoramaSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
    url: `${baseUrl}/blog/panorama/${setor}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }));

  // SEO Frente 4: City pSEO pages (/blog/licitacoes/cidade/[cidade])
  const cidadeRoutes: MetadataRoute.Sitemap = CITIES.map((c) => ({
    url: `${baseUrl}/blog/licitacoes/cidade/${c.slug}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.7,
  }));

  return [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 1.0,
    },
    {
      url: `${baseUrl}/planos`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    {
      url: `${baseUrl}/features`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.8,
    },
    {
      url: `${baseUrl}/ajuda`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${baseUrl}/pricing`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${baseUrl}/signup`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.6,
    },
    {
      url: `${baseUrl}/login`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.4,
    },
    {
      url: `${baseUrl}/termos`,
      lastModified: new Date(),
      changeFrequency: 'yearly',
      priority: 0.2,
    },
    {
      url: `${baseUrl}/privacidade`,
      lastModified: new Date(),
      changeFrequency: 'yearly',
      priority: 0.2,
    },
    // STORY-261 AC10: Blog listing page
    {
      url: `${baseUrl}/blog`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    // STORY-261 AC10: Individual blog articles
    ...blogArticleRoutes,
    // STORY-324 AC12: Sector landing pages index
    {
      url: `${baseUrl}/licitacoes`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    // STORY-324 AC12: Individual sector landing pages
    ...sectorRoutes,
    {
      url: `${baseUrl}/glossario`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    {
      url: `${baseUrl}/como-avaliar-licitacao`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${baseUrl}/como-evitar-prejuizo-licitacao`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${baseUrl}/como-filtrar-editais`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${baseUrl}/como-priorizar-oportunidades`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    // SEO-PLAYBOOK 6.3: Panorama Licitações Brasil 2026 T1 (gated digital PR asset)
    {
      url: `${baseUrl}/relatorio-2026-t1`,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    },
    // SEO-PLAYBOOK P2: Calculadora B2G
    {
      url: `${baseUrl}/calculadora`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    // SEO-PLAYBOOK P3: CNPJ B2G lookup
    {
      url: `${baseUrl}/cnpj`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    // SEO-PLAYBOOK P0: About page
    {
      url: `${baseUrl}/sobre`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.6,
    },
    // SEO-PLAYBOOK P0: Programmatic sector pages
    ...programmaticSectorRoutes,
    // SEO-PLAYBOOK P0: Sector × UF pages (405 combinations)
    ...licitacoesUfRoutes,
    // SEO-PLAYBOOK P0: Panorama sector pages
    ...panoramaSectorRoutes,
    // SEO Frente 4: City pSEO pages
    ...cidadeRoutes,
    // SEO-PLAYBOOK P7: RSS feed
    {
      url: `${baseUrl}/blog/rss.xml`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.3,
    },
    // SEO-PLAYBOOK P5: Cases de sucesso
    {
      url: `${baseUrl}/casos`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.8,
    },
    ...getAllCaseSlugs().map((slug) => ({
      url: `${baseUrl}/casos/${slug}`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.8,
    })),
  ];
}
