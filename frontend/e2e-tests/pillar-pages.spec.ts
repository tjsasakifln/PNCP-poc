/**
 * STORY-SEO-008 AC7: Pillar Pages E2E validation
 *
 * Validates:
 *   - Each pillar route returns HTTP 200
 *   - Correct H1 is rendered
 *   - TOC has ≥5 anchors
 *   - ≥10 internal links to /blog/* (spokes)
 *   - JSON-LD Article + BreadcrumbList + ItemList + FAQPage is valid
 */
import { test, expect } from '@playwright/test';

const PILLARS = [
  {
    slug: 'licitacoes',
    h1: 'Guia Completo de Licitações Públicas no Brasil',
  },
  {
    slug: 'lei-14133',
    h1: 'Tudo Sobre a Lei 14.133/2021: A Nova Lei de Licitações',
  },
  {
    slug: 'pncp',
    h1: 'PNCP: Portal Nacional de Contratações Públicas — Guia Completo',
  },
];

for (const pillar of PILLARS) {
  test.describe(`Pillar /guia/${pillar.slug}`, () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(`/guia/${pillar.slug}`);
    });

    test('responds 200 and renders H1', async ({ page }) => {
      const response = await page.request.get(`/guia/${pillar.slug}`);
      expect(response.status()).toBe(200);

      const h1 = page.locator('h1').first();
      await expect(h1).toBeVisible();
      await expect(h1).toHaveText(pillar.h1);
    });

    test('has TOC with ≥5 anchors', async ({ page }) => {
      const toc = page.getByTestId('pillar-toc');
      await expect(toc).toBeVisible();
      const links = toc.locator('a[href^="#"]');
      const count = await links.count();
      expect(count).toBeGreaterThanOrEqual(5);
    });

    test('has ≥10 internal links to /blog spokes', async ({ page }) => {
      const spokes = page.getByTestId('pillar-spokes');
      await expect(spokes).toBeVisible();
      const links = spokes.locator('a[href^="/blog/"]');
      const count = await links.count();
      expect(count).toBeGreaterThanOrEqual(10);
    });

    test('emits Article + BreadcrumbList + ItemList + FAQPage JSON-LD', async ({
      page,
    }) => {
      const scripts = await page.locator('script[type="application/ld+json"]').all();
      expect(scripts.length).toBeGreaterThanOrEqual(4);

      const parsed = await Promise.all(
        scripts.map(async (s) => JSON.parse((await s.textContent()) || '{}')),
      );
      const types = parsed.map((p) => p['@type']);
      expect(types).toContain('Article');
      expect(types).toContain('BreadcrumbList');
      expect(types).toContain('ItemList');
      expect(types).toContain('FAQPage');
    });

    test('is indexable (no noindex meta)', async ({ page }) => {
      const robotsMeta = page.locator('meta[name="robots"]');
      const count = await robotsMeta.count();
      if (count > 0) {
        const content = await robotsMeta.first().getAttribute('content');
        expect(content || '').not.toMatch(/noindex/i);
      }
    });

    test('renders inline trial CTA', async ({ page }) => {
      const cta = page.getByTestId('pillar-inline-cta');
      await expect(cta).toBeVisible();
      await expect(cta).toHaveAttribute('href', /\/signup/);
    });
  });
}

test.describe('/guia hub', () => {
  test('lists 3 pillar cards', async ({ page }) => {
    await page.goto('/guia');
    const list = page.getByTestId('guias-list');
    await expect(list).toBeVisible();
    const items = list.locator('li');
    await expect(items).toHaveCount(3);
  });
});
