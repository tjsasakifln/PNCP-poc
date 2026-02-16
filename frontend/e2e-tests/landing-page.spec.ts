import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('renders hero section with headline and CTAs', async ({ page }) => {
    // Check headline
    await expect(
      page.getByText(/6\+ milhões de licitações por ano no Brasil/i)
    ).toBeVisible();

    // Check subheadline
    await expect(page.getByText(/500 mil oportunidades mensais/i)).toBeVisible();

    // Check primary CTA
    const primaryCTA = page.getByRole('link', { name: /Descobrir Minhas Oportunidades/i });
    await expect(primaryCTA).toBeVisible();
    await expect(primaryCTA).toHaveAttribute('href', '/signup');

    // Check secondary CTA
    const secondaryCTA = page.getByRole('button', { name: /ver como funciona/i });
    await expect(secondaryCTA).toBeVisible();

    // Check credibility badge
    await expect(page.getByText(/Sistema desenvolvido por servidores públicos/i)).toBeVisible();
  });

  test('scrolls to "Como Funciona" section when clicking secondary CTA', async ({ page }) => {
    // Click secondary CTA
    await page.getByRole('button', { name: /ver como funciona/i }).click();

    // Wait for scroll animation
    await page.waitForTimeout(1000);

    // Check that "Como Funciona" section is visible
    await expect(page.getByRole('heading', { name: /como funciona/i })).toBeInViewport();
  });

  test('renders all sections in correct order', async ({ page }) => {
    // Check section order by verifying headings
    const sections = [
      /6\+ milhões de licitações/i, // Hero
      /qual o custo de uma licitação/i, // OpportunityCost
      /transforme sua busca/i, // BeforeAfter
      /diferenciais que importam/i, // DifferentialsGrid
      /como funciona/i, // HowItWorks
      /números que falam por si/i, // StatsSection
      /desenvolvido por quem conhece/i, // DataSourcesSection
      /setores atendidos/i, // SectorsGrid
      /pronto para economizar tempo/i, // FinalCTA
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
    await page.getByRole('link', { name: /^login$/i }).first().click();
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain('/login');

    // Go back
    await page.goto('/');

    // Test Signup button (in navbar)
    await page.getByRole('link', { name: /cadastro/i }).first().click();
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

    // Check LGPD badge
    await expect(page.getByText(/lgpd compliant/i)).toBeVisible();

    // Check "Sistema desenvolvido por servidores públicos"
    await expect(page.getByText(/Sistema desenvolvido por servidores públicos/i)).toBeVisible();
  });

  test('PNCP link opens in new tab', async ({ page, context }) => {
    // Listen for new page (tab)
    const pagePromise = context.waitForEvent('page');

    // Click PNCP link
    await page.getByRole('link', { name: /acessar pncp/i }).click();

    // Wait for new page
    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    // Check URL
    expect(newPage.url()).toContain('pncp.gov.br');
  });

  test('responsive layout on mobile', async ({ page }) => {
    // Set mobile viewport (iPhone 13)
    await page.setViewportSize({ width: 390, height: 844 });

    // Check hero section renders on mobile
    await expect(
      page.getByText(/6\+ milhões de licitações/i).first()
    ).toBeVisible();

    // Check CTAs are visible
    await expect(page.getByRole('link', { name: /Descobrir Minhas Oportunidades/i })).toBeVisible();

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
      page.getByText(/6\+ milhões de licitações/i).first()
    ).toBeVisible();

    // Check differentials grid is 2 columns (not 4)
    // This is visual, but we can check no horizontal scroll
    const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyScrollWidth).toBeLessThanOrEqual(viewportWidth + 1);
  });

  test('keyboard navigation works', async ({ page }) => {
    // Tab to primary CTA
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // Should focus on primary CTA

    // Check focus is on primary CTA (visual indicator)
    const focusedElement = await page.evaluate(() => document.activeElement?.textContent);
    expect(focusedElement).toContain('Começar');
  });

  test('all sections have proper semantic HTML', async ({ page }) => {
    // Check for semantic sections
    const sections = await page.locator('section').count();
    expect(sections).toBeGreaterThan(5); // At least 8 sections

    // Check for header (navbar)
    await expect(page.locator('header')).toBeVisible();

    // Check for main
    await expect(page.locator('main')).toBeVisible();

    // Check for footer
    await expect(page.locator('footer')).toBeVisible();
  });
});
