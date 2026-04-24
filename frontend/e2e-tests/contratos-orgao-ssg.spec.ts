import { test, expect } from '@playwright/test';

const STATIC_TO_DYNAMIC_PATTERNS = [
  /Page changed from static to dynamic/i,
  /markCurrentScopeAsDynamic/i,
];

// AC5 SEN-FE-001: navegar para /contratos/orgao/[cnpj] nao pode emitir
// warning Next.js "Page changed from static to dynamic at runtime".
//
// Contexto: fetch interno usava `cache: 'no-store'` o que forcava pagina
// marcada como dynamic at runtime, quebrando SSG/ISR (revalidate 14400 da
// page). Fix: `next: { revalidate: 14400 }` alinhado com page.
test.describe('SEN-FE-001 — /contratos/orgao/[cnpj] preserves SSG/ISR', () => {
  const sampleCnpjs = ['10791831000182', '00394411000209'];

  for (const cnpj of sampleCnpjs) {
    test(`page /contratos/orgao/${cnpj} does not log static-to-dynamic warning`, async ({ page }) => {
      const consoleCaptured: string[] = [];

      page.on('console', (msg) => {
        consoleCaptured.push(`[${msg.type()}] ${msg.text()}`);
      });
      page.on('pageerror', (err) => {
        consoleCaptured.push(`[pageerror] ${err.message}`);
      });

      const response = await page.goto(`/contratos/orgao/${cnpj}`, {
        waitUntil: 'domcontentloaded',
        timeout: 20000,
      });

      const status = response?.status() ?? 0;
      expect([200, 404]).toContain(status);

      const dynamicWarnings = consoleCaptured.filter((m) =>
        STATIC_TO_DYNAMIC_PATTERNS.some((pattern) => pattern.test(m)),
      );

      expect(
        dynamicWarnings,
        `Page should not emit Next.js static-to-dynamic warning.\nCaptured:\n${consoleCaptured.join('\n')}`,
      ).toEqual([]);
    });
  }
});
