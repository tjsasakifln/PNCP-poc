import { BLOG_ARTICLES } from '@/lib/blog';

/**
 * STORY-261 AC9: RSS 2.0 feed for blog articles.
 * Route Handler: GET /blog/rss.xml
 */
export async function GET() {
  const baseUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || 'https://smartlic.tech';

  const items = BLOG_ARTICLES.map((article) => {
    const pubDate = new Date(article.publishDate + 'T12:00:00-03:00');
    return `    <item>
      <title><![CDATA[${article.title}]]></title>
      <link>${baseUrl}/blog/${article.slug}</link>
      <description><![CDATA[${article.description}]]></description>
      <pubDate>${pubDate.toUTCString()}</pubDate>
      <guid isPermaLink="true">${baseUrl}/blog/${article.slug}</guid>
      <category><![CDATA[${article.category}]]></category>
    </item>`;
  }).join('\n');

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>SmartLic Blog</title>
    <link>${baseUrl}/blog</link>
    <description>Artigos, guias e análises sobre licitações públicas para empresas B2G e consultorias.</description>
    <language>pt-BR</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${baseUrl}/blog/rss.xml" rel="self" type="application/rss+xml" />
${items}
  </channel>
</rss>`;

  return new Response(rss, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}
