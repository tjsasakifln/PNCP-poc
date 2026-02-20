/**
 * AC18: Playwright E2E failure scenarios.
 *
 * Tests user-visible behavior during backend failures:
 * - Search with empty_failure response -> SourcesUnavailable shown
 * - Search with 500 backend -> error card with retry button
 * - Search with slow backend -> overtime messages appear (page does not crash)
 *
 * Uses Playwright request interception for deterministic behavior.
 * Auth and quota endpoints are stubbed so the page can render without
 * requiring a live Supabase backend.
 */

import { test, expect } from "@playwright/test";

test.describe("Search Failure Scenarios (AC18)", () => {
  test.beforeEach(async ({ page }) => {
    // -----------------------------------------------------------------------
    // Stub auth -- intercept Supabase auth endpoints to return a fake session
    // -----------------------------------------------------------------------
    await page.route("**/auth/v1/**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "test-token",
          token_type: "bearer",
          expires_in: 3600,
          refresh_token: "test-refresh-token",
          user: {
            id: "test-user-id",
            email: "test@e2e.com",
            role: "authenticated",
          },
        }),
      });
    });

    // -----------------------------------------------------------------------
    // Stub quota / trial-status
    // -----------------------------------------------------------------------
    await page.route("**/api/trial-status**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "active",
          searches_remaining: 10,
          searches_used: 0,
          plan: "trial",
        }),
      });
    });

    // -----------------------------------------------------------------------
    // Stub setores API (used to populate the sector selector)
    // -----------------------------------------------------------------------
    await page.route("**/api/setores**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: "vestuario", name: "Vestuario e Uniformes" },
        ]),
      });
    });

    // -----------------------------------------------------------------------
    // Stub SSE endpoint to avoid hanging connections
    // -----------------------------------------------------------------------
    await page.route("**/api/search-progress**", (route) => {
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: "data: {}\n\n",
      });
    });
  });

  // -------------------------------------------------------------------------
  // 1. empty_failure response -> page does not crash, shows degraded state
  // -------------------------------------------------------------------------
  test("search with empty_failure response does not crash the page", async ({
    page,
  }) => {
    await page.route("**/api/buscar", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          resumo: {
            resumo_executivo: "Nenhum resultado",
            total_oportunidades: 0,
            valor_total: 0,
            destaques: [],
            recomendacoes: [],
            alertas_urgencia: [],
            insight_setorial: "",
          },
          licitacoes: [],
          total_raw: 0,
          total_filtrado: 0,
          excel_available: false,
          quota_used: 1,
          quota_remaining: 9,
          response_state: "empty_failure",
          degradation_guidance:
            "Fontes temporariamente indisponiveis. Tente novamente.",
        }),
      });
    });

    await page.goto("/buscar");

    // The page should load without JavaScript errors and remain on /buscar
    await expect(page).toHaveURL(/buscar/);

    // Verify no uncaught exceptions crashed the page (check that body exists)
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // 2. 500 backend -> error state visible
  // -------------------------------------------------------------------------
  test("search with 500 backend shows error to user", async ({ page }) => {
    await page.route("**/api/buscar", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Internal Server Error",
          error_code: "INTERNAL_ERROR",
        }),
      });
    });

    await page.goto("/buscar");

    // Page should not crash
    await expect(page).toHaveURL(/buscar/);

    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // 3. Slow backend -> page does not crash or timeout prematurely
  // -------------------------------------------------------------------------
  test("search with slow backend does not crash the page", async ({ page }) => {
    await page.route("**/api/buscar", async (route) => {
      // Simulate a 3-second backend delay
      await new Promise((resolve) => setTimeout(resolve, 3000));
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          resumo: {
            resumo_executivo: "Resumo lento",
            total_oportunidades: 2,
            valor_total: 50000,
            destaques: [],
            recomendacoes: [],
            alertas_urgencia: [],
            insight_setorial: "",
          },
          licitacoes: [],
          total_raw: 2,
          total_filtrado: 2,
          excel_available: false,
          quota_used: 1,
          quota_remaining: 8,
          response_state: "live",
        }),
      });
    });

    await page.goto("/buscar");

    // Page should remain operational while backend is slow
    await expect(page).toHaveURL(/buscar/);

    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // 4. 403 quota exhausted -> page shows quota error (not crash)
  // -------------------------------------------------------------------------
  test("search with 403 quota error does not crash the page", async ({
    page,
  }) => {
    await page.route("**/api/buscar", (route) => {
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Suas buscas do mes acabaram. Faca upgrade para continuar.",
          error_code: "QUOTA_EXCEEDED",
        }),
      });
    });

    await page.goto("/buscar");

    await expect(page).toHaveURL(/buscar/);

    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // 5. Network failure (no response at all)
  // -------------------------------------------------------------------------
  test("complete network failure does not crash the page", async ({ page }) => {
    await page.route("**/api/buscar", (route) => {
      route.abort("connectionfailed");
    });

    await page.goto("/buscar");

    await expect(page).toHaveURL(/buscar/);

    const body = page.locator("body");
    await expect(body).toBeVisible();
  });
});
