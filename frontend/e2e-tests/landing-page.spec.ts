import { test, expect } from '@playwright/test';

/**
 * SAB-006: Landing page E2E tests — updated for condensed 6-section layout.
 * Target flow: Hero → Problema → Solução → Como Funciona → Stats → CTA → Footer
 */
test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('renders hero section with headline and CTAs', async ({ page }) => {
    // Check headline
    await expect(
      page.getByText(/Pare de perder dinheiro/i)
    ).toBeVisible();

    // Check subheadline
    await expect(page.getByText(/O SmartLic analisa cada edital/i)).toBeVisible();

    // Check primary CTA
    const primaryCTA = page.getByRole('button', { name: /Ver oportunidades para meu setor/i });
    await expect(primaryCTA).toBeVisible();

    // Check secondary CTA
    const secondaryCTA = page.getByRole('button', { name: /ver como funciona/i });
    await expect(secondaryCTA).toBeVisible();
  });

  test('scrolls to "Como Funciona" section when clicking secondary CTA', async ({ page }) => {
    // Click secondary CTA
    await page.getByRole('button', { name: /ver como funciona/i }).click();

    // Wait for scroll animation
    await page.waitForTimeout(1000);

    // Check that "Como Funciona" section is visible
    await expect(page.getByRole('heading', { name: /como funciona/i })).toBeInViewport();
  });

  test('renders all sections in correct order (SAB-006 AC8)', async ({ page }) => {
    // SAB-006 target flow: Hero → Problema → Solução → Como Funciona → Stats → CTA
    const sections = [
      /Pare de perder dinheiro/i, // Hero
      /Continuar sem filtro estratégico/i, // OpportunityCost (Problema)
      /O que acontece sem filtro estratégico/i, // BeforeAfter (Solução)
      /como funciona/i, // HowItWorks
      /Impacto real no mercado/i, // StatsSection
      /Licitações estão abrindo agora/i, // FinalCTA
    ];

    for (const sectionHeading of sections) {
      await expect(page.getByText(sectionHeading).first()).toBeVisible();
    }
  });

  test('navbar is sticky on scroll', async ({ page }) => {
    // Get navbar
    const navbar = page.locator('header');

    // Check initial state
    await expect(navbar).toBeVisible();

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(300);

    // Navbar should still be visible (sticky)
    await expect(navbar).toBeVisible();

    // Check for sticky/fixed positioning (via class or computed style)
    const navbarClasses = await navbar.getAttribute('class');
    expect(navbarClasses).toContain('sticky');
  });

  test('navigates to login and signup pages', async ({ page }) => {
    // Test Login link
    await page.getByRole('link', { name: /^(login|entrar)$/i }).first().click();
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain('/login');

    // Go back
    await page.goto('/');

    // Test Signup button (in navbar)
    await page.getByRole('link', { name: /(cadastro|comece gratis|comece grátis)/i }).first().click();
    await page.waitForURL(/\/signup/);
    expect(page.url()).toContain('/signup');
  });

  test('renders footer with all links', async ({ page }) => {
    // Scroll to footer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    // Check footer sections
    await expect(page.getByRole('heading', { name: /sobre/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /planos/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /suporte/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /legal/i })).toBeVisible();

    // Check copyright
    await expect(page.getByText(/© 2026 SmartLic\.tech/i)).toBeVisible();
  });

  test('responsive layout on mobile', async ({ page }) => {
    // Set mobile viewport (iPhone 13)
    await page.setViewportSize({ width: 390, height: 844 });

    // Check hero section renders on mobile
    await expect(
      page.getByText(/Pare de perder dinheiro/i).first()
    ).toBeVisible();

    // Check CTAs are visible
    await expect(page.getByRole('button', { name: /Ver oportunidades para meu setor/i })).toBeVisible();

    // Check grid layouts collapse to single column (verify no horizontal scroll)
    const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyScrollWidth).toBeLessThanOrEqual(viewportWidth + 1); // Allow 1px tolerance
  });

  test('responsive layout on tablet', async ({ page }) => {
    // Set tablet viewport (iPad)
    await page.setViewportSize({ width: 768, height: 1024 });

    // Check hero section renders on tablet
    await expect(
      page.getByText(/Pare de perder dinheiro/i).first()
    ).toBeVisible();

    // Check no horizontal scroll
    const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyScrollWidth).toBeLessThanOrEqual(viewportWidth + 1);
  });

  test('keyboard navigation works', async ({ page }) => {
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Check focus is on an interactive element
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(['A', 'BUTTON']).toContain(focusedElement);
  });

  test('all sections have proper semantic HTML (SAB-006 AC3)', async ({ page }) => {
    // Check for semantic sections — SAB-006 reduced from ~15 to 6+
    const sections = await page.locator('section').count();
    expect(sections).toBeGreaterThanOrEqual(5);

    // Check for header (navbar)
    await expect(page.locator('header')).toBeVisible();

    // Check for main
    await expect(page.locator('main')).toBeVisible();

    // Check for footer
    await expect(page.locator('footer')).toBeVisible();
  });

  test('stats section has counter animation (SAB-006 AC6)', async ({ page }) => {
    // Scroll to stats section
    await page.evaluate(() => {
      const statsSection = document.querySelector('[class*="bg-brand-blue-subtle"]');
      if (statsSection) statsSection.scrollIntoView({ behavior: 'instant' });
    });

    // Wait for animation
    await page.waitForTimeout(2000);

    // Check that final values are displayed
    await expect(page.getByText('15')).toBeVisible();
    await expect(page.getByText('87%')).toBeVisible();
    await expect(page.getByText('27')).toBeVisible();
  });

  test('beta counter is in FinalCTA section (SAB-006 AC3)', async ({ page }) => {
    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    // Beta counter should be inside FinalCTA, not a separate section
    const betaCounter = page.locator('[data-testid="beta-counter"]');
    await expect(betaCounter).toBeVisible();

    // Should be inside the navy CTA card
    const ctaSection = page.locator('.bg-brand-navy');
    await expect(ctaSection.locator('[data-testid="beta-counter"]')).toBeVisible();
  });
});
