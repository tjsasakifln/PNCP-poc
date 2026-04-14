/**
 * SEO-476: Sitemap index manual para Next.js 16.
 *
 * Em Next.js 16, o `app/sitemap.ts` com `generateSitemaps()` gera os
 * sub-sitemaps em /sitemap/[id].xml corretamente, mas NÃO gera o index
 * em /sitemap.xml (bug conhecido). Este route handler serve o index manualmente.
 *
 * Sub-sitemaps gerados por app/sitemap.ts:
 *   /sitemap/0.xml — Core static (~35 URLs)
 *   /sitemap/1.xml — Sector landing pages (~60 URLs)
 *   /sitemap/2.xml — Sector×UF combos (~1620 URLs)
 *   /sitemap/3.xml — Content/blog pages (~300+ URLs)
 *   /sitemap/4.xml — Entity pages (CNPJs, órgãos, fornecedores)
 */
export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';

  const sitemapIds = [0, 1, 2, 3, 4];

  const sitemapEntries = sitemapIds
    .map((id) => `  <sitemap><loc>${baseUrl}/sitemap/${id}.xml</loc></sitemap>`)
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemapEntries}
</sitemapindex>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600, s-maxage=86400',
    },
  });
}
