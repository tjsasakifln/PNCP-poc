import { test, expect } from '@playwright/test';

/**
 * STORY-OBS-001 — Site-wide guard against "200 OK with zero data" regressions
 * on programmatic SEO pages.
 *
 * Incident (2026-04-24): /observatorio/raio-x-marco-2026 served 200 OK showing
 * "Total: 0 editais / R$ 0", because pncp_raw_bids was hard-purged after 12
 * days. Retention is now 400 days, but we keep this spec as a regression
 * tripwire for the SEO surface as a whole.
 *
 * Strategy:
 *   1. Fetch sitemap.xml, pull URLs under the observatório prefix.
 *   2. For each sampled URL: HTTP 200 + HTML must contain "TOTAL DE EDITAIS"
 *      AND the number immediately after must not be "0".
 */

const MONTH_NAMES = [
  'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
];

function previousMonthSlug(date: Date = new Date()): string {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() - 1, 1));
  const mes = MONTH_NAMES[d.getUTCMonth()];
  const ano = d.getUTCFullYear();
  return `raio-x-${mes}-${ano}`;
}

async function fetchSitemapUrls(request: import('@playwright/test').APIRequestContext, baseURL: string): Promise<string[]> {
  const resp = await request.get(`${baseURL}/sitemap.xml`, { timeout: 15000 });
  if (!resp.ok()) return [];
  const xml = await resp.text();
  // Simple regex extraction — sitemap.xml is structured enough for this.
  const urls = Array.from(xml.matchAll(/<loc>([^<]+)<\/loc>/g)).map((m) => m[1]);
  return urls;
}

function extractNumberNearLabel(html: string, label: string): number | null {
  const labelIdx = html.toLowerCase().indexOf(label.toLowerCase());
  if (labelIdx === -1) return null;
  const window = html.slice(labelIdx, labelIdx + 600);
  // Look for the first run of digits (pt-BR format uses . as thousands separator)
  const match = window.match(/([0-9][0-9.]{0,15})/);
  if (!match) return null;
  const digits = match[1].replace(/\./g, '');
  const n = Number(digits);
  return Number.isFinite(n) ? n : null;
}

test.describe('SEO programmatic pages — zero-data regression guard', () => {
  test('previous-month observatório slug must render non-zero total_editais', async ({ page }) => {
    const slug = previousMonthSlug();
    const response = await page.goto(`/observatorio/${slug}`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    expect(response, `No response for /observatorio/${slug}`).not.toBeNull();
    const status = response!.status();
    expect([200, 404, 500], `Unexpected HTTP status for ${slug}`).toContain(status);

    // A 404 is acceptable only if the backfill hasn't populated the month yet.
    // In production post-deploy the previous full month must always exist.
    if (process.env.CI && process.env.STRICT_SEO_COVERAGE === '1') {
      expect(status, 'CI strict mode: previous month must resolve 200').toBe(200);
    }

    if (status !== 200) {
      test.info().annotations.push({
        type: 'skip-reason',
        description: `Slug ${slug} returned HTTP ${status} — skipping numeric assertion.`,
      });
      return;
    }

    const html = await page.content();
    const total = extractNumberNearLabel(html, 'TOTAL DE EDITAIS');
    expect(
      total,
      `Expected numeric "total de editais" in ${slug}; got: ${total}`,
    ).not.toBeNull();
    expect(
      total!,
      `SEO regression — ${slug} rendered 0 editais (datalake empty or purge misconfigured).`,
    ).toBeGreaterThan(0);
  });

  test('sitemap sample — observatório URLs return 200 with non-zero content', async ({ request, page }) => {
    const baseURL = test.info().project.use.baseURL ?? 'http://localhost:3000';
    const allUrls = await fetchSitemapUrls(request, baseURL);

    const observatorioUrls = allUrls.filter((u) => /\/observatorio\/raio-x-/.test(u));

    test.skip(
      observatorioUrls.length === 0,
      'No /observatorio/raio-x-* URLs found in sitemap — nothing to sample.',
    );

    // Sample up to 5 URLs to keep the spec fast.
    const sample = observatorioUrls.slice(0, 5);
    const failures: string[] = [];

    for (const url of sample) {
      const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      const status = resp?.status() ?? 0;
      if (status !== 200) {
        failures.push(`${url} → HTTP ${status}`);
        continue;
      }
      const html = await page.content();
      const total = extractNumberNearLabel(html, 'TOTAL DE EDITAIS');
      if (total === null) {
        failures.push(`${url} — TOTAL DE EDITAIS label not found`);
      } else if (total === 0) {
        failures.push(`${url} — total_editais = 0`);
      }
    }

    expect(
      failures,
      `Zero-data / missing-label regressions in ${failures.length}/${sample.length} observatório slugs:\n${failures.join('\n')}`,
    ).toEqual([]);
  });
});
