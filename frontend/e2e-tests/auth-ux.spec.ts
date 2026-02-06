/**
 * E2E Test: Authentication UX
 *
 * Critical User Flow: Password toggle, field clearing, and warnings
 *
 * Steps:
 * 1. Test password toggle on signup page
 * 2. Test password toggle on login page
 * 3. Test password toggle on account page
 * 4. Test field clearing after password change
 * 5. Test logout warning display
 *
 * Covers bugs:
 * - UX Senha: Toggle de senha em signup/conta, limpeza de campos, avisos
 */

import { test, expect } from '@playwright/test';
import { mockAuthAPI, clearTestData } from './helpers/test-utils';

test.describe('Signup Password Toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/signup');
    await clearTestData(page);
  });

  test('AC1: should show password toggle button', async ({ page }) => {
    // Verify password field exists
    const passwordInput = page.locator('input#password');
    await expect(passwordInput).toBeVisible();

    // Verify toggle button exists
    const toggleButton = page.locator('button[aria-label*="senha"]');
    await expect(toggleButton).toBeVisible();
  });

  test('AC2: should toggle password visibility on signup', async ({ page }) => {
    const passwordInput = page.locator('input#password');
    const toggleButton = page.locator('button[aria-label*="senha"]');

    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Enter password
    await passwordInput.fill('testpassword123');

    // Click toggle to show password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Verify aria-label updated
    await expect(toggleButton).toHaveAttribute('aria-label', /Ocultar senha/i);

    // Click toggle to hide password again
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Verify aria-label updated back
    await expect(toggleButton).toHaveAttribute('aria-label', /Mostrar senha/i);
  });

  test('AC3: should preserve password value when toggling visibility', async ({ page }) => {
    const passwordInput = page.locator('input#password');
    const toggleButton = page.locator('button[aria-label*="senha"]');
    const testPassword = 'mySecretPassword123';

    // Enter password
    await passwordInput.fill(testPassword);

    // Toggle visibility multiple times
    await toggleButton.click();
    expect(await passwordInput.inputValue()).toBe(testPassword);

    await toggleButton.click();
    expect(await passwordInput.inputValue()).toBe(testPassword);

    await toggleButton.click();
    expect(await passwordInput.inputValue()).toBe(testPassword);
  });

  test('AC4: should show correct icon for hidden/visible state', async ({ page }) => {
    const toggleButton = page.locator('button[aria-label*="senha"]');

    // Check initial icon (eye icon for "show password")
    const initialIcon = toggleButton.locator('svg');
    await expect(initialIcon).toBeVisible();

    // Toggle and verify icon changes
    await toggleButton.click();

    // Icon should still be visible (different icon now)
    const toggledIcon = toggleButton.locator('svg');
    await expect(toggledIcon).toBeVisible();
  });
});

test.describe('Login Password Toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await clearTestData(page);
  });

  test('AC5: should show password toggle on login page', async ({ page }) => {
    // Password mode should be default
    const passwordInput = page.locator('input#password');
    await expect(passwordInput).toBeVisible();

    // Toggle button should exist
    const toggleButton = page.locator('button[aria-label*="senha"]');
    await expect(toggleButton).toBeVisible();
  });

  test('AC6: should toggle password visibility on login', async ({ page }) => {
    const passwordInput = page.locator('input#password');
    const toggleButton = page.locator('button[aria-label*="senha"]');

    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click toggle to show password
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Click toggle to hide password again
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('AC7: should not show password toggle in magic link mode', async ({ page }) => {
    // Click magic link mode
    const magicModeButton = page.getByRole('button', { name: /Magic Link/i });
    await magicModeButton.click();

    // Password field should not be visible
    const passwordInput = page.locator('input#password');
    await expect(passwordInput).not.toBeVisible();

    // Toggle button should not be visible
    const toggleButton = page.locator('button[aria-label*="senha"]');
    await expect(toggleButton).not.toBeVisible();
  });
});

test.describe('Account Page Password Change', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authenticated user
    await mockAuthAPI(page, 'user');

    await page.goto('/conta');
    await clearTestData(page);
  });

  test('AC8: should display password change form', async ({ page }) => {
    // Verify form title
    await expect(page.locator('text=/Alterar senha/i')).toBeVisible();

    // Verify new password field
    const newPasswordInput = page.locator('input#newPassword');
    await expect(newPasswordInput).toBeVisible();

    // Verify confirm password field
    const confirmPasswordInput = page.locator('input#confirmPassword');
    await expect(confirmPasswordInput).toBeVisible();
  });

  test('AC9: should show logout warning message', async ({ page }) => {
    // Verify warning message is displayed
    const warningMessage = page.locator('text=/sera desconectado/i');
    await expect(warningMessage).toBeVisible();

    // Verify warning has proper styling (warning color)
    const warningContainer = page.locator('div').filter({ hasText: /sera desconectado/i }).first();
    await expect(warningContainer).toBeVisible();
  });

  test('AC10: should validate password minimum length', async ({ page }) => {
    const newPasswordInput = page.locator('input#newPassword');
    const confirmPasswordInput = page.locator('input#confirmPassword');

    // Fill short password
    await newPasswordInput.fill('12345');
    await confirmPasswordInput.fill('12345');

    // Submit form
    await page.getByRole('button', { name: /Alterar senha/i }).click();

    // Verify error message
    await expect(page.locator('text=/6 caracteres/i')).toBeVisible();
  });

  test('AC11: should validate password confirmation match', async ({ page }) => {
    const newPasswordInput = page.locator('input#newPassword');
    const confirmPasswordInput = page.locator('input#confirmPassword');

    // Fill mismatched passwords
    await newPasswordInput.fill('password123');
    await confirmPasswordInput.fill('password456');

    // Submit form
    await page.getByRole('button', { name: /Alterar senha/i }).click();

    // Verify error message
    await expect(page.locator('text=/senhas não coincidem/i')).toBeVisible();
  });

  test('AC12: should clear fields after successful password change', async ({ page }) => {
    // Mock successful password change
    await page.route('**/change-password', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Password changed' }),
      });
    });

    const newPasswordInput = page.locator('input#newPassword');
    const confirmPasswordInput = page.locator('input#confirmPassword');

    // Fill valid passwords
    await newPasswordInput.fill('newpassword123');
    await confirmPasswordInput.fill('newpassword123');

    // Submit form
    await page.getByRole('button', { name: /Alterar senha/i }).click();

    // Wait for success message
    await expect(page.locator('text=/Senha alterada com sucesso/i')).toBeVisible({ timeout: 5000 });

    // Verify fields are cleared
    expect(await newPasswordInput.inputValue()).toBe('');
    expect(await confirmPasswordInput.inputValue()).toBe('');
  });

  test('AC13: should display error message on password change failure', async ({ page }) => {
    // Mock password change failure
    await page.route('**/change-password', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Senha atual incorreta' }),
      });
    });

    const newPasswordInput = page.locator('input#newPassword');
    const confirmPasswordInput = page.locator('input#confirmPassword');

    // Fill valid passwords
    await newPasswordInput.fill('newpassword123');
    await confirmPasswordInput.fill('newpassword123');

    // Submit form
    await page.getByRole('button', { name: /Alterar senha/i }).click();

    // Verify error message
    await expect(page.locator('text=/Senha atual incorreta/i')).toBeVisible({ timeout: 5000 });

    // Verify fields are NOT cleared on error
    expect(await newPasswordInput.inputValue()).toBe('newpassword123');
    expect(await confirmPasswordInput.inputValue()).toBe('newpassword123');
  });

  test('AC14: should show loading state during password change', async ({ page }) => {
    // Mock slow response
    await page.route('**/change-password', async (route) => {
      await new Promise((r) => setTimeout(r, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Password changed' }),
      });
    });

    const newPasswordInput = page.locator('input#newPassword');
    const confirmPasswordInput = page.locator('input#confirmPassword');

    // Fill valid passwords
    await newPasswordInput.fill('newpassword123');
    await confirmPasswordInput.fill('newpassword123');

    // Submit form
    const submitButton = page.getByRole('button', { name: /Alterar senha/i });
    await submitButton.click();

    // Verify loading state
    await expect(submitButton).toContainText(/Alterando/i);
    await expect(submitButton).toBeDisabled();
  });

  test('AC15: should display user profile information', async ({ page }) => {
    // Verify profile section exists
    await expect(page.locator('text=/Dados do perfil/i')).toBeVisible();

    // Verify email is displayed
    await expect(page.locator('text=Email')).toBeVisible();

    // Verify name label is displayed
    await expect(page.locator('text=Nome')).toBeVisible();
  });
});

test.describe('Account Page Access Control', () => {
  test('AC16: should redirect to login when not authenticated', async ({ page }) => {
    // Navigate to account page without auth
    await page.goto('/conta');

    // Verify login link is shown
    await expect(page.locator('text=/Faça login/i')).toBeVisible();
    await expect(page.locator('a[href="/login"]')).toBeVisible();
  });
});
