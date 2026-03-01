import { test, expect } from '@playwright/test';

/**
 * MKT-003 AC6: Schema validation for Phase 1 licitacoes pages.
 *
 * Validates JSON-LD for each of the 25 Phase 1 pages:
 *   - FAQPage schema: 5 questions with answers
 *   - Dataset schema: data points, temporal/spatial coverage
 *   - BreadcrumbList schema: 5 breadcrumb items
 *
 * Run against localhost:  npx playwright test mkt-003-schema-validation
 * Run against production: FRONTEND_URL=https://smartlic.tech npx playwright test mkt-003-schema-validation
 */

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

// Phase 1: 5 sectors × 5 UFs = 25 pages
const PHASE1_SECTORS = ['informatica', 'saude', 'engenharia', 'facilities', 'software'];
const PHASE1_UFS = ['sp', 'rj', 'mg', 'pr', 'rs'];

// Sample 5 URLs for Rich Results validation (AC6)
const SAMPLE_URLS = [
  { setor: 'informatica', uf: 'sp' },
  { setor: 'saude', uf: 'rj' },
  { setor: 'engenharia', uf: 'mg' },
  { setor: 'facilities', uf: 'pr' },
  { setor: 'software', uf: 'rs' },
];

function getUrl(setor: string, uf: string): string {
  return `${BASE_URL}/blog/licitacoes/${setor}/${uf}`;
}

// ---------------------------------------------------------------------------
// Phase 1 — All 25 pages: basic schema presence
// ---------------------------------------------------------------------------

for (const setor of PHASE1_SECTORS) {
  for (const uf of PHASE1_UFS) {
    test(`MKT-003 Schema: /blog/licitacoes/${setor}/${uf} has valid JSON-LD`, async ({ page }) => {
      await page.goto(getUrl(setor, uf), { waitUntil: 'domcontentloaded' });

      // Collect all JSON-LD scripts
      const schemas = await page.evaluate(() => {
        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
        return Array.from(scripts).map((s) => JSON.parse(s.textContent || '{}'));
      });

      expect(schemas.length).toBeGreaterThanOrEqual(3);

      // Find schema types
      const types = schemas.map((s: { '@type'?: string }) => s['@type']);

      // AC3: FAQPage + Dataset + BreadcrumbList
      expect(types).toContain('FAQPage');
      expect(types).toContain('Dataset');
      expect(types).toContain('BreadcrumbList');
    });
  }
}

// ---------------------------------------------------------------------------
// Sample 5 URLs — deep schema validation (AC6: Rich Results Test)
// ---------------------------------------------------------------------------

for (const { setor, uf } of SAMPLE_URLS) {
  test(`MKT-003 Rich Results: /blog/licitacoes/${setor}/${uf} — FAQPage deep validation`, async ({ page }) => {
    await page.goto(getUrl(setor, uf), { waitUntil: 'domcontentloaded' });

    const faqSchema = await page.evaluate(() => {
      const scripts = document.querySelectorAll('script[type="application/ld+json"]');
      for (const s of scripts) {
        const data = JSON.parse(s.textContent || '{}');
        if (data['@type'] === 'FAQPage') return data;
      }
      return null;
    });

    expect(faqSchema).not.toBeNull();
    expect(faqSchema.mainEntity).toHaveLength(5);

    for (const q of faqSchema.mainEntity) {
      expect(q['@type']).toBe('Question');
      expect(q.name).toBeTruthy();
      expect(q.acceptedAnswer['@type']).toBe('Answer');
      expect(q.acceptedAnswer.text).toBeTruthy();
      // 40-60 words per answer
      const wordCount = q.acceptedAnswer.text.split(/\s+/).length;
      expect(wordCount).toBeGreaterThanOrEqual(20);
      expect(wordCount).toBeLessThanOrEqual(80);
    }
  });

  test(`MKT-003 Rich Results: /blog/licitacoes/${setor}/${uf} — Dataset validation`, async ({ page }) => {
    await page.goto(getUrl(setor, uf), { waitUntil: 'domcontentloaded' });

    const datasetSchema = await page.evaluate(() => {
      const scripts = document.querySelectorAll('script[type="application/ld+json"]');
      for (const s of scripts) {
        const data = JSON.parse(s.textContent || '{}');
        if (data['@type'] === 'Dataset') return data;
      }
      return null;
    });

    expect(datasetSchema).not.toBeNull();
    expect(datasetSchema.name).toContain('Licitações');
    expect(datasetSchema.creator.name).toBe('SmartLic');
    expect(datasetSchema.temporalCoverage).toBeTruthy();
    expect(datasetSchema.spatialCoverage).toBeTruthy();
  });

  test(`MKT-003 Rich Results: /blog/licitacoes/${setor}/${uf} — BreadcrumbList validation`, async ({ page }) => {
    await page.goto(getUrl(setor, uf), { waitUntil: 'domcontentloaded' });

    const breadcrumbSchema = await page.evaluate(() => {
      const scripts = document.querySelectorAll('script[type="application/ld+json"]');
      for (const s of scripts) {
        const data = JSON.parse(s.textContent || '{}');
        if (data['@type'] === 'BreadcrumbList') return data;
      }
      return null;
    });

    expect(breadcrumbSchema).not.toBeNull();
    expect(breadcrumbSchema.itemListElement.length).toBeGreaterThanOrEqual(4);
    for (const item of breadcrumbSchema.itemListElement) {
      expect(item['@type']).toBe('ListItem');
      expect(item.position).toBeGreaterThan(0);
      expect(item.name).toBeTruthy();
      expect(item.item).toContain('https://smartlic.tech');
    }
  });
}

// ---------------------------------------------------------------------------
// Meta tags validation
// ---------------------------------------------------------------------------

for (const { setor, uf } of SAMPLE_URLS) {
  test(`MKT-003 Meta: /blog/licitacoes/${setor}/${uf} — title, description, canonical`, async ({ page }) => {
    await page.goto(getUrl(setor, uf), { waitUntil: 'domcontentloaded' });

    // AC3: Meta title format
    const title = await page.title();
    expect(title).toMatch(/Licitações de .+ em .+ — Editais Abertos \d{4} \| SmartLic/);

    // AC3: Meta description
    const description = await page.getAttribute('meta[name="description"]', 'content');
    expect(description).toBeTruthy();
    expect(description!.length).toBeGreaterThan(50);

    // AC3: Canonical URL
    const canonical = await page.getAttribute('link[rel="canonical"]', 'href');
    expect(canonical).toContain(`/blog/licitacoes/${setor}/${uf}`);

    // AC3: OG tags
    const ogTitle = await page.getAttribute('meta[property="og:title"]', 'content');
    expect(ogTitle).toBeTruthy();
  });
}

// ---------------------------------------------------------------------------
// 404 for invalid combinations
// ---------------------------------------------------------------------------

test('MKT-003 AC1: 404 for invalid sector', async ({ page }) => {
  const response = await page.goto(`${BASE_URL}/blog/licitacoes/invalid-sector/sp`, {
    waitUntil: 'domcontentloaded',
  });
  expect(response?.status()).toBe(404);
});

test('MKT-003 AC1: 404 for invalid UF', async ({ page }) => {
  const response = await page.goto(`${BASE_URL}/blog/licitacoes/informatica/xx`, {
    waitUntil: 'domcontentloaded',
  });
  expect(response?.status()).toBe(404);
});
