/**
 * E2E Test: Theme Switching
 *
 * Critical User Flow #2: Theme selection and persistence
 *
 * Steps:
 * 1. Click theme toggle
 * 2. Verify CSS variables applied
 * 3. Check localStorage persistence
 * 4. Reload page → theme persists
 *
 * Reference: docs/reviews/qa-testing-analysis.md (lines 413-414)
 */

import { test, expect } from '@playwright/test';
import { SearchPage, ThemeSelector } from './helpers/page-objects';
import { clearTestData, getCSSVariable, getLocalStorageItem } from './helpers/test-utils';

test.describe('Theme Switching E2E', () => {
  let searchPage: SearchPage;
  let themeSelector: ThemeSelector;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    themeSelector = new ThemeSelector(page);

    // Navigate to home
    await searchPage.goto();

    // Clear test data after navigation
    await clearTestData(page);
  });

  test('AC1: should open theme selector dropdown', async () => {
    // Click theme toggle
    await themeSelector.toggleButton.click();

    // Verify dropdown is visible
    await expect(themeSelector.dropdown).toBeVisible();

    // Verify theme options are present
    await expect(themeSelector.dropdown.locator('text=/Azul Descomplicita/i')).toBeVisible();
    await expect(themeSelector.dropdown.locator('text=/Oceano/i')).toBeVisible();
    await expect(themeSelector.dropdown.locator('text=/Floresta/i')).toBeVisible();
  });

  test('AC2: should switch theme and apply CSS variables', async ({ page }) => {
    // Get initial theme
    const initialTheme = await getLocalStorageItem(page, 'theme');
    expect(initialTheme).toBe('blue'); // Default theme

    // Get initial CSS variable
    const initialColor = await getCSSVariable(page, '--brand-blue');
    expect(initialColor).toBeTruthy();

    // Switch to Oceano theme
    await themeSelector.selectTheme('Oceano');

    // Wait for theme to be applied
    await page.waitForTimeout(300); // Allow CSS transition

    // Verify localStorage updated
    const newTheme = await getLocalStorageItem(page, 'theme');
    expect(newTheme).toBe('ocean');

    // Verify CSS variables changed
    const newColor = await getCSSVariable(page, '--brand-blue');
    expect(newColor).not.toBe(initialColor);
    expect(newColor).toBeTruthy();
  });

  test('AC3: should persist theme in localStorage', async ({ page }) => {
    // Switch to Floresta theme
    await themeSelector.selectTheme('Floresta');

    // Verify localStorage
    const storedTheme = await getLocalStorageItem(page, 'theme');
    expect(storedTheme).toBe('forest');

    // Verify CSS variable for forest theme
    const forestColor = await getCSSVariable(page, '--brand-blue');
    expect(forestColor).toBeTruthy();
  });

  test('AC4: should persist theme after page reload', async ({ page }) => {
    // Switch to Oceano theme
    await themeSelector.selectTheme('Oceano');

    // Get CSS variable value
    const oceanColor = await getCSSVariable(page, '--brand-blue');

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify theme persisted
    const storedTheme = await getLocalStorageItem(page, 'theme');
    expect(storedTheme).toBe('ocean');

    // Verify CSS variables still applied
    const reloadedColor = await getCSSVariable(page, '--brand-blue');
    expect(reloadedColor).toBe(oceanColor);
  });

  test('AC5: should persist theme across navigation', async ({ page }) => {
    // Switch to Floresta theme
    await themeSelector.selectTheme('Floresta');

    // Verify initial CSS
    const initialColor = await getCSSVariable(page, '--brand-blue');

    // Navigate away and back (simulate by reloading)
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Verify theme still applied
    const persistedTheme = await getLocalStorageItem(page, 'theme');
    expect(persistedTheme).toBe('forest');

    const persistedColor = await getCSSVariable(page, '--brand-blue');
    expect(persistedColor).toBe(initialColor);
  });

  test('AC6: should show active theme with checkmark', async ({ page }) => {
    // Open theme selector
    await themeSelector.open();

    // Find active theme (should have checkmark)
    const activeTheme = themeSelector.dropdown
      .locator('button')
      .filter({ has: page.locator('svg[class*="text-brand-blue"]') })
      .first();

    await expect(activeTheme).toBeVisible();

    // Verify default theme is active
    await expect(activeTheme).toContainText(/Azul Descomplicita/i);
  });

  test('AC7: should update active indicator when theme changes', async ({ page }) => {
    // Switch to Oceano
    await themeSelector.selectTheme('Oceano');

    // Open dropdown again
    await themeSelector.open();

    // Verify Oceano is now active
    const activeTheme = themeSelector.dropdown
      .locator('button')
      .filter({ has: page.locator('svg[class*="text-brand-blue"]') })
      .first();

    await expect(activeTheme).toContainText(/Oceano/i);
  });

  test('AC8: should close dropdown when clicking outside', async ({ page }) => {
    // Open dropdown
    await themeSelector.open();
    await expect(themeSelector.dropdown).toBeVisible();

    // Click outside (on the main heading)
    await page.locator('h1').click();

    // Verify dropdown closed
    await expect(themeSelector.dropdown).not.toBeVisible();
  });

  test('AC9: should apply theme preview colors in dropdown', async ({ page }) => {
    // Open dropdown
    await themeSelector.open();

    // Get all theme preview circles
    const previews = themeSelector.dropdown.locator('span.rounded-full');

    // Verify at least 3 previews (for 3 themes)
    await expect(previews).toHaveCount(3, { timeout: 5000 });

    // Verify each preview has a background color
    for (let i = 0; i < 3; i++) {
      const preview = previews.nth(i);
      const bgColor = await preview.evaluate((el) => {
        return window.getComputedStyle(el).backgroundColor;
      });
      expect(bgColor).toBeTruthy();
      expect(bgColor).not.toBe('rgba(0, 0, 0, 0)'); // Not transparent
    }
  });

  test('AC10: should handle rapid theme switching', async ({ page }) => {
    // Rapidly switch between themes
    await themeSelector.selectTheme('Oceano');
    await themeSelector.selectTheme('Floresta');
    await themeSelector.selectTheme('Azul Descomplicita');

    // Verify final theme is applied
    const finalTheme = await getLocalStorageItem(page, 'theme');
    expect(finalTheme).toBe('blue');

    // Verify CSS variables are correct
    const finalColor = await getCSSVariable(page, '--brand-blue');
    expect(finalColor).toBeTruthy();
  });

  test('AC11: should maintain theme through full user journey', async ({ page }) => {
    // Switch to Floresta theme
    await themeSelector.selectTheme('Floresta');

    // Get theme color
    const forestColor = await getCSSVariable(page, '--brand-blue');

    // Perform search (clear selections first)
    await searchPage.clearUFSelection();
    await searchPage.selectUF('SC');

    // Verify theme still applied
    const duringSearchColor = await getCSSVariable(page, '--brand-blue');
    expect(duringSearchColor).toBe(forestColor);

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify theme persisted
    const afterReloadColor = await getCSSVariable(page, '--brand-blue');
    expect(afterReloadColor).toBe(forestColor);
  });

  test('AC12: should have accessible theme selector', async ({ page }) => {
    // Verify toggle button has aria-label
    await expect(themeSelector.toggleButton).toHaveAttribute('aria-label', /Alternar tema/i);

    // Open dropdown
    await themeSelector.open();

    // Verify aria-expanded
    await expect(themeSelector.toggleButton).toHaveAttribute('aria-expanded', 'true');

    // Close dropdown
    await page.locator('h1').click();

    // Verify aria-expanded updated
    await expect(themeSelector.toggleButton).toHaveAttribute('aria-expanded', 'false');
  });
});
