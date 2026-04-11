/**
 * Build-time validation: ensures all internal /blog/... hrefs in content files
 * point to slugs that actually exist in BLOG_ARTICLES.
 *
 * Catches accented slugs (e.g. /blog/análise-...) vs ASCII slugs used in lib/blog.ts.
 * Fails CI before deploy so broken links never reach production.
 */

import * as fs from 'fs';
import * as path from 'path';
import { BLOG_ARTICLES } from '@/lib/blog';

const CONTENT_DIR = path.join(process.cwd(), 'app', 'blog', 'content');
const BLOG_HREF_REGEX = /href="(\/blog\/[^"]+)"/g;

function extractBlogLinks(source: string): string[] {
  const links: string[] = [];
  let match: RegExpExecArray | null;
  BLOG_HREF_REGEX.lastIndex = 0;
  while ((match = BLOG_HREF_REGEX.exec(source)) !== null) {
    links.push(match[1]);
  }
  return links;
}

describe('Blog internal links', () => {
  const existingSlugs = new Set(BLOG_ARTICLES.map((a) => a.slug));

  const contentFiles = fs
    .readdirSync(CONTENT_DIR)
    .filter((f) => f.endsWith('.tsx') || f.endsWith('.ts'))
    .map((f) => path.join(CONTENT_DIR, f));

  // Slugs that are valid route prefixes (not article slugs) — skip these
  const ROUTE_PREFIXES = new Set([
    'contratos',
    'licitacoes',
    'programmatic',
    'weekly',
    'panorama',
    'author',
  ]);

  const broken: Array<{ file: string; href: string }> = [];

  for (const filePath of contentFiles) {
    const source = fs.readFileSync(filePath, 'utf-8');
    const links = extractBlogLinks(source);
    const fileName = path.basename(filePath);

    for (const href of links) {
      // Strip /blog/ prefix to get the slug
      const slug = href.replace(/^\/blog\//, '');

      // Skip if it's a route prefix (e.g. /blog/contratos/engenharia)
      const firstSegment = slug.split('/')[0];
      if (ROUTE_PREFIXES.has(firstSegment)) continue;

      // Skip external or anchor links
      if (slug.startsWith('http') || slug.startsWith('#')) continue;

      if (!existingSlugs.has(slug)) {
        broken.push({ file: fileName, href });
      }
    }
  }

  it('should have zero broken internal /blog/... links across all content files', () => {
    if (broken.length > 0) {
      const report = broken
        .map(({ file, href }) => `  ${file}: ${href}`)
        .join('\n');
      fail(
        `Found ${broken.length} broken internal blog link(s):\n${report}\n\n` +
          'Fix: replace accented hrefs with ASCII slugs matching lib/blog.ts BLOG_ARTICLES.',
      );
    }
    expect(broken).toHaveLength(0);
  });
});
