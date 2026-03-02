/**
 * MKT-002 AC4: Dynamic blog sitemap.
 *
 * Lists all editorial posts + programmatic pages with proper priorities:
 * - Editorial posts: 0.8
 * - Sector × UF programmatic: 0.7
 * - City pages: 0.6
 *
 * lastmod reflects last data update date.
 */

import { BLOG_ARTICLES } from '@/lib/blog';
import { SECTORS } from '@/lib/sectors';
import { ALL_UFS } from '@/lib/programmatic';

const BASE_URL = 'https://smartlic.tech';

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function urlEntry(
  loc: string,
  lastmod: string,
  changefreq: string,
  priority: string,
): string {
  return `<url><loc>${escapeXml(loc)}</loc><lastmod>${lastmod}</lastmod><changefreq>${changefreq}</changefreq><priority>${priority}</priority></url>`;
}

export async function GET() {
  const now = new Date().toISOString();

  const urls: string[] = [];

  // 1. Blog listing page
  urls.push(urlEntry(`${BASE_URL}/blog`, now, 'daily', '0.9'));

  // 2. Editorial blog posts (priority 0.8)
  for (const article of BLOG_ARTICLES) {
    const lastmod = article.publishDate
      ? new Date(article.publishDate).toISOString()
      : now;
    urls.push(
      urlEntry(`${BASE_URL}/blog/${article.slug}`, lastmod, 'weekly', '0.8'),
    );
  }

  // 3. Panorama pages — pillar pages (priority 0.8)
  for (const sector of SECTORS) {
    urls.push(
      urlEntry(
        `${BASE_URL}/blog/panorama/${sector.slug}`,
        now,
        'daily',
        '0.8',
      ),
    );
  }

  // 4. Sector programmatic pages (priority 0.7)
  for (const sector of SECTORS) {
    urls.push(
      urlEntry(
        `${BASE_URL}/blog/programmatic/${sector.slug}`,
        now,
        'daily',
        '0.7',
      ),
    );
  }

  // 5. Sector × UF programmatic pages (priority 0.7)
  for (const sector of SECTORS) {
    for (const uf of ALL_UFS) {
      urls.push(
        urlEntry(
          `${BASE_URL}/blog/programmatic/${sector.slug}/${uf.toLowerCase()}`,
          now,
          'daily',
          '0.7',
        ),
      );
    }
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}
