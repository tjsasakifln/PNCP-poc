import { test, expect } from '@playwright/test';

/**
 * MKT-003 AC6: Google Search Console indexation scripts.
 *
 * Phase 1: Request indexation for 25 URLs via GSC URL Inspection.
 * Phase 1 verification: Re-inspect URLs and generate report.
 *
 * IMPORTANT: This script requires GSC authentication.
 * Run with: FRONTEND_URL=https://smartlic.tech npx playwright test mkt-003-gsc-indexation
 *
 * Credentials: Use GSC_EMAIL and GSC_PASSWORD env vars, or manual login.
 */

const SITE_URL = 'https://smartlic.tech';
const GSC_URL = 'https://search.google.com/search-console';

// Phase 1: 5 sectors × 5 UFs = 25 URLs
const PHASE1_SECTORS = ['informatica', 'saude', 'engenharia', 'facilities', 'software'];
const PHASE1_UFS = ['sp', 'rj', 'mg', 'pr', 'rs'];

function generatePhase1Urls(): string[] {
  const urls: string[] = [];
  for (const setor of PHASE1_SECTORS) {
    for (const uf of PHASE1_UFS) {
      urls.push(`${SITE_URL}/blog/licitacoes/${setor}/${uf}`);
    }
  }
  return urls;
}

// ---------------------------------------------------------------------------
// AC6: Request indexation for Phase 1 URLs
// ---------------------------------------------------------------------------

test.describe('MKT-003 AC6: GSC Indexation Request', () => {
  test.skip(
    !process.env.GSC_RUN,
    'Skipped: set GSC_RUN=1 to run GSC automation (requires manual Google login)',
  );

  test('Request indexation for 25 Phase 1 URLs', async ({ page }) => {
    test.setTimeout(300_000); // 5 minutes for all 25 URLs

    const urls = generatePhase1Urls();
    const results: { url: string; status: string }[] = [];

    // Navigate to GSC
    await page.goto(`${GSC_URL}?resource_id=${encodeURIComponent(SITE_URL)}`);

    // Wait for manual login if needed
    await page.waitForSelector('[data-resource-id]', { timeout: 120_000 });

    for (const url of urls) {
      try {
        // Open URL Inspection
        await page.goto(
          `${GSC_URL}/inspect?resource_id=${encodeURIComponent(SITE_URL)}&id=${encodeURIComponent(url)}`,
        );
        await page.waitForTimeout(3000);

        // Click "Request Indexing" if available
        const requestBtn = page.locator('text=Solicitar indexação');
        if (await requestBtn.isVisible({ timeout: 5000 })) {
          await requestBtn.click();
          await page.waitForTimeout(2000);
          results.push({ url, status: 'requested' });
        } else {
          results.push({ url, status: 'already_indexed_or_unavailable' });
        }
      } catch {
        results.push({ url, status: 'error' });
      }
    }

    // Log results
    console.log('\n=== MKT-003 Phase 1 Indexation Results ===');
    for (const r of results) {
      console.log(`  ${r.status.padEnd(35)} ${r.url}`);
    }
    console.log(`\nTotal: ${results.length}, Requested: ${results.filter((r) => r.status === 'requested').length}`);

    expect(results.length).toBe(25);
  });
});

// ---------------------------------------------------------------------------
// AC6: Verify indexation status (run 7 days after request)
// ---------------------------------------------------------------------------

test.describe('MKT-003 AC6: GSC Indexation Verification', () => {
  test.skip(
    !process.env.GSC_VERIFY,
    'Skipped: set GSC_VERIFY=1 to run verification (7 days after indexation request)',
  );

  test('Verify indexation for 25 Phase 1 URLs', async ({ page }) => {
    test.setTimeout(300_000);

    const urls = generatePhase1Urls();
    const results: { url: string; indexed: boolean; schema: boolean; errors: string }[] = [];

    await page.goto(`${GSC_URL}?resource_id=${encodeURIComponent(SITE_URL)}`);
    await page.waitForSelector('[data-resource-id]', { timeout: 120_000 });

    for (const url of urls) {
      try {
        await page.goto(
          `${GSC_URL}/inspect?resource_id=${encodeURIComponent(SITE_URL)}&id=${encodeURIComponent(url)}`,
        );
        await page.waitForTimeout(5000);

        const content = await page.textContent('body');
        const indexed = content?.includes('O URL está no Google') ?? false;
        const schema = content?.includes('FAQ') || content?.includes('Dataset') || false;
        const errors = content?.includes('Erro') ? 'Has errors' : 'None';

        results.push({ url, indexed, schema, errors });
      } catch {
        results.push({ url, indexed: false, schema: false, errors: 'Inspection failed' });
      }
    }

    // Generate report
    console.log('\n=== MKT-003 Phase 1 Indexation Verification ===');
    console.log(`Date: ${new Date().toISOString()}`);
    console.log('');
    for (const r of results) {
      const status = r.indexed ? 'INDEXED' : 'NOT_INDEXED';
      const schemaStr = r.schema ? 'SCHEMA_OK' : 'NO_SCHEMA';
      console.log(`  ${status.padEnd(15)} ${schemaStr.padEnd(12)} ${r.errors.padEnd(15)} ${r.url}`);
    }
    const indexedCount = results.filter((r) => r.indexed).length;
    console.log(`\nTotal: ${results.length}, Indexed: ${indexedCount}, Not indexed: ${results.length - indexedCount}`);

    // At least some should be indexed after 7 days
    expect(indexedCount).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// AC6: Rich Results Test by sampling (5 URLs)
// ---------------------------------------------------------------------------

test.describe('MKT-003 AC6: Rich Results Test', () => {
  const RICH_RESULTS_URL = 'https://search.google.com/test/rich-results';

  test.skip(
    !process.env.GSC_RICH,
    'Skipped: set GSC_RICH=1 to run Rich Results Test validation',
  );

  const sampleUrls = [
    `${SITE_URL}/blog/licitacoes/informatica/sp`,
    `${SITE_URL}/blog/licitacoes/saude/rj`,
    `${SITE_URL}/blog/licitacoes/engenharia/mg`,
    `${SITE_URL}/blog/licitacoes/facilities/pr`,
    `${SITE_URL}/blog/licitacoes/software/rs`,
  ];

  for (const url of sampleUrls) {
    test(`Rich Results Test: ${url.split('/').slice(-2).join('/')}`, async ({ page }) => {
      test.setTimeout(120_000);

      await page.goto(RICH_RESULTS_URL);
      await page.waitForTimeout(2000);

      // Enter URL
      const input = page.locator('input[type="url"], input[type="text"]').first();
      await input.fill(url);
      await page.keyboard.press('Enter');

      // Wait for results
      await page.waitForTimeout(15000);

      const content = await page.textContent('body');
      const hasFAQ = content?.includes('FAQ') ?? false;
      const hasDataset = content?.includes('Dataset') ?? false;
      const hasBreadcrumb = content?.includes('Breadcrumb') ?? false;

      console.log(`Rich Results: ${url}`);
      console.log(`  FAQ: ${hasFAQ}, Dataset: ${hasDataset}, Breadcrumb: ${hasBreadcrumb}`);

      // At minimum, page should be parseable
      expect(content).toBeTruthy();
    });
  }
});
