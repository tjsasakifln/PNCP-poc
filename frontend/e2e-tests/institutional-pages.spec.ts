import { test, expect } from '@playwright/test';

test.describe('Login Page - Institutional Sidebar', () => {
  test('displays institutional sidebar on login page', async ({ page }) => {
    await page.goto('/login');

    // Verify headline is visible
    await expect(page.getByRole('heading', { name: /Descubra oportunidades de licitação/i })).toBeVisible();
  });

  test('displays all login benefits', async ({ page }) => {
    await page.goto('/login');

    // Verify all 5 benefits are visible
    await expect(page.getByText('Monitoramento em tempo real de licitações')).toBeVisible();
    await expect(page.getByText('Filtros por estado, valor e setor')).toBeVisible();
    await expect(page.getByText('Resumo executivo gerado por IA')).toBeVisible();
    await expect(page.getByText('Exportação de relatórios em Excel')).toBeVisible();
    await expect(page.getByText('Histórico completo de buscas')).toBeVisible();
  });

  test('displays login statistics', async ({ page }) => {
    await page.goto('/login');

    // Verify statistics
    await expect(page.getByText('27')).toBeVisible();
    await expect(page.getByText('estados monitorados')).toBeVisible();
    await expect(page.getByText('9')).toBeVisible();
    await expect(page.getByText('setores pré-configurados')).toBeVisible();
  });

  test('official data badge is visible', async ({ page }) => {
    await page.goto('/login');

    // Find official data badge
    await expect(page.getByText('Dados oficiais em tempo real')).toBeVisible();
  });

  test('login form still works with sidebar', async ({ page }) => {
    await page.goto('/login');

    // Verify form elements are present and functional
    const emailInput = page.getByLabel('Email');
    await expect(emailInput).toBeVisible();

    const passwordInput = page.getByLabel('Senha');
    await expect(passwordInput).toBeVisible();

    const submitButton = page.getByRole('button', { name: /Entrar/i });
    await expect(submitButton).toBeVisible();

    // Verify Google OAuth button still works
    const googleButton = page.getByRole('button', { name: /Entrar com Google/i });
    await expect(googleButton).toBeVisible();
  });
});

test.describe('Signup Page - Institutional Sidebar', () => {
  test('displays institutional sidebar on signup page', async ({ page }) => {
    await page.goto('/signup');

    // Verify headline is visible
    await expect(page.getByRole('heading', { name: /Sua empresa a um passo/i })).toBeVisible();
  });

  test('displays all signup benefits', async ({ page }) => {
    await page.goto('/signup');

    // Verify all 5 benefits are visible
    await expect(page.getByText('Comece grátis com 3 buscas completas')).toBeVisible();
    await expect(page.getByText('Sem necessidade de cartão de crédito')).toBeVisible();
    await expect(page.getByText('Configuração em menos de 2 minutos')).toBeVisible();
    await expect(page.getByText('Suporte dedicado via plataforma')).toBeVisible();
    await expect(page.getByText('Dados protegidos e conformidade LGPD')).toBeVisible();
  });

  test('displays signup statistics', async ({ page }) => {
    await page.goto('/signup');

    // Verify statistics
    await expect(page.getByText('27')).toBeVisible();
    await expect(page.getByText('estados cobertos')).toBeVisible();
    await expect(page.getByText('1000+')).toBeVisible();
    await expect(page.getByText('licitações/dia')).toBeVisible();
    await expect(page.getByText('100%')).toBeVisible();
    await expect(page.getByText('fonte oficial')).toBeVisible();
  });

  test('signup form still works with sidebar', async ({ page }) => {
    await page.goto('/signup');

    // Verify form elements are present
    const fullNameInput = page.getByLabel('Nome completo');
    await expect(fullNameInput).toBeVisible();

    const companyInput = page.getByLabel('Empresa');
    await expect(companyInput).toBeVisible();

    const emailInput = page.getByLabel('Email');
    await expect(emailInput).toBeVisible();

    const submitButton = page.getByRole('button', { name: /Criar conta/i });
    await expect(submitButton).toBeVisible();
  });
});

test.describe('Responsive Behavior', () => {
  test('desktop layout - split screen on login', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/login');

    // Verify both sidebar and form are visible side-by-side
    await expect(page.getByText('Descubra oportunidades')).toBeVisible();
    await expect(page.getByRole('button', { name: /Entrar com Google/i })).toBeVisible();
  });

  test('desktop layout - split screen on signup', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/signup');

    // Verify both sidebar and form are visible
    await expect(page.getByText('Sua empresa a um passo')).toBeVisible();
    await expect(page.getByRole('button', { name: /Cadastrar com Google/i })).toBeVisible();
  });

  test('mobile layout - stacked on login', async ({ page }) => {
    // Set mobile viewport (iPhone 13)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/login');

    // Verify institutional content is above form (stacked)
    await expect(page.getByText('Descubra oportunidades')).toBeVisible();
    await expect(page.getByRole('button', { name: /Entrar com Google/i })).toBeVisible();

    // Scroll to see form (it should be below sidebar)
    await page.getByRole('button', { name: /Entrar/i }).scrollIntoViewIfNeeded();
    await expect(page.getByRole('button', { name: /Entrar/i })).toBeVisible();
  });

  test('mobile layout - stacked on signup', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/signup');

    // Verify institutional content is visible
    await expect(page.getByText('Sua empresa a um passo')).toBeVisible();

    // Scroll to form
    await page.getByRole('button', { name: /Criar conta/i }).scrollIntoViewIfNeeded();
    await expect(page.getByRole('button', { name: /Criar conta/i })).toBeVisible();
  });

  test('tablet layout - 768px breakpoint', async ({ page }) => {
    // Set tablet viewport (iPad)
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/login');

    // At 768px, should switch to desktop layout (side-by-side)
    await expect(page.getByText('Descubra oportunidades')).toBeVisible();
    await expect(page.getByRole('button', { name: /Entrar com Google/i })).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('keyboard navigation works on login page', async ({ page }) => {
    await page.goto('/login');

    // Tab to first interactive element (Google OAuth button)
    await page.keyboard.press('Tab');
    const googleButton = page.getByRole('button', { name: /Entrar com Google/i });
    await expect(googleButton).toBeFocused();
  });

  test('official data badge has proper content', async ({ page }) => {
    await page.goto('/login');

    const badge = page.getByText('Dados oficiais em tempo real');
    await expect(badge).toBeVisible();
    await expect(badge).toHaveText('Dados oficiais em tempo real');
  });

  test('heading hierarchy is correct on login', async ({ page }) => {
    await page.goto('/login');

    // Institutional sidebar should have h1
    const sidebarHeading = page.getByRole('heading', { level: 1, name: /Descubra oportunidades/i });
    await expect(sidebarHeading).toBeVisible();
  });

  test('heading hierarchy is correct on signup', async ({ page }) => {
    await page.goto('/signup');

    // Institutional sidebar should have h1
    const sidebarHeading = page.getByRole('heading', { level: 1, name: /Sua empresa a um passo/i });
    await expect(sidebarHeading).toBeVisible();
  });
});

test.describe('Regression Tests - Form Functionality', () => {
  test('login form validation still works', async ({ page }) => {
    await page.goto('/login');

    // Try to submit empty form
    const submitButton = page.getByRole('button', { name: 'Entrar' });
    await submitButton.click();

    // HTML5 validation should prevent submission (email required)
    const emailInput = page.getByLabel('Email');
    const validationMessage = await emailInput.evaluate((el: HTMLInputElement) => el.validationMessage);
    expect(validationMessage).toBeTruthy();
  });

  test('signup form validation still works', async ({ page }) => {
    await page.goto('/signup');

    // Try to submit empty form
    const submitButton = page.getByRole('button', { name: /Criar conta/i });
    await submitButton.click();

    // HTML5 validation should prevent submission
    const fullNameInput = page.getByLabel('Nome completo');
    const validationMessage = await fullNameInput.evaluate((el: HTMLInputElement) => el.validationMessage);
    expect(validationMessage).toBeTruthy();
  });

  test('navigation between login and signup works', async ({ page }) => {
    await page.goto('/login');

    // Click "Criar conta" link
    await page.getByRole('link', { name: /Criar conta/i }).click();
    await page.waitForURL('/signup');

    // Verify we're on signup page with institutional sidebar
    await expect(page.getByText('Sua empresa a um passo')).toBeVisible();

    // Go back to login
    await page.getByRole('link', { name: /Fazer login/i }).click();
    await page.waitForURL('/login');

    // Verify we're back on login
    await expect(page.getByText('Descubra oportunidades')).toBeVisible();
  });
});

test.describe('Visual Consistency', () => {
  test('gradient background is visible on login', async ({ page }) => {
    await page.goto('/login');

    // Find sidebar container
    const sidebar = page.locator('div').filter({ hasText: 'Descubra oportunidades' }).first();

    // Verify it has gradient classes (check computed style)
    const backgroundImage = await sidebar.evaluate((el) => {
      return window.getComputedStyle(el).backgroundImage;
    });

    expect(backgroundImage).toContain('gradient');
  });

  test('all icons render on login page', async ({ page }) => {
    await page.goto('/login');

    // Count SVG elements (should have 6: 5 benefits + 1 PNCP badge check icon)
    const svgCount = await page.locator('svg').count();
    expect(svgCount).toBeGreaterThanOrEqual(6);
  });

  test('all icons render on signup page', async ({ page }) => {
    await page.goto('/signup');

    // Count SVG elements
    const svgCount = await page.locator('svg').count();
    expect(svgCount).toBeGreaterThanOrEqual(6);
  });
});
