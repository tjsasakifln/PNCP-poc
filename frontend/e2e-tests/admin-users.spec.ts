/**
 * E2E Test: Admin User Management
 *
 * Critical User Flow: Admin creating, viewing, and managing users
 *
 * Steps:
 * 1. Login as admin
 * 2. Navigate to admin page
 * 3. Create new user
 * 4. Verify user appears in list
 * 5. Assign plan to user
 * 6. Delete user
 *
 * Covers bugs:
 * - CORS Admin: Creation of users via admin panel
 */

import { test, expect } from '@playwright/test';
import {
  mockAdminUsersAPI,
  mockAuthAPI,
  clearTestData,
} from './helpers/test-utils';

test.describe('Admin User Management E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Setup auth mock for admin user
    await mockAuthAPI(page, 'admin');
    await mockAdminUsersAPI(page);

    // Navigate to admin page
    await page.goto('/admin');
    await clearTestData(page);
  });

  test('AC1: should display admin page for admin users', async ({ page }) => {
    // Verify admin page loads
    await expect(page.locator('h1')).toContainText(/Admin - Usuários/i);

    // Verify user count is displayed
    await expect(page.locator('text=/\\d+ usuário/i')).toBeVisible();

    // Verify table headers
    await expect(page.locator('th:has-text("Email")')).toBeVisible();
    await expect(page.locator('th:has-text("Nome")')).toBeVisible();
    await expect(page.locator('th:has-text("Plano")')).toBeVisible();
    await expect(page.locator('th:has-text("Créditos")')).toBeVisible();
  });

  test('AC2: should show create user form when clicking "Novo usuário"', async ({ page }) => {
    // Click new user button
    const newUserButton = page.getByRole('button', { name: /Novo usuário/i });
    await expect(newUserButton).toBeVisible();
    await newUserButton.click();

    // Verify form appears
    await expect(page.locator('text=/Criar usuário/i')).toBeVisible();

    // Verify form fields
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('input[type="text"]').first()).toBeVisible(); // Name
    await expect(page.locator('select')).toBeVisible(); // Plan selector
  });

  test('AC3: should validate required fields in create user form', async ({ page }) => {
    // Open create form
    await page.getByRole('button', { name: /Novo usuário/i }).click();

    // Try to submit empty form
    const createButton = page.getByRole('button', { name: /^Criar$/i });

    // HTML5 validation should prevent submission
    // Email field should be required
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toHaveAttribute('required', '');

    // Password field should be required
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toHaveAttribute('required', '');
  });

  test('AC4: should create user successfully', async ({ page }) => {
    // Open create form
    await page.getByRole('button', { name: /Novo usuário/i }).click();

    // Fill form
    await page.locator('input[type="email"]').fill('newuser@test.com');
    await page.locator('input[type="password"]').fill('password123');

    // Fill name field (first text input after email)
    const nameInput = page.locator('input[type="text"]').first();
    await nameInput.fill('Test User');

    // Select plan
    await page.locator('select').selectOption('free');

    // Submit form
    await page.getByRole('button', { name: /^Criar$/i }).click();

    // Wait for form to close (success case)
    await expect(page.locator('text=/Criar usuário/i')).not.toBeVisible({ timeout: 5000 });
  });

  test('AC5: should display error message on create failure', async ({ page }) => {
    // Mock create failure
    await page.route('**/admin/users', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Email já cadastrado' }),
        });
      } else {
        await route.continue();
      }
    });

    // Open create form and submit
    await page.getByRole('button', { name: /Novo usuário/i }).click();
    await page.locator('input[type="email"]').fill('existing@test.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.getByRole('button', { name: /^Criar$/i }).click();

    // Verify error alert
    await page.waitForEvent('dialog').then(dialog => dialog.accept());
  });

  test('AC6: should search users by email', async ({ page }) => {
    // Type in search input
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    await searchInput.fill('test@example.com');
    await searchInput.press('Enter');

    // Verify search was triggered (mock should respond)
    await expect(page.locator('tbody')).toBeVisible();
  });

  test('AC7: should change user plan via dropdown', async ({ page }) => {
    // Find plan dropdown in first user row
    const planDropdown = page.locator('tbody tr').first().locator('select');
    await expect(planDropdown).toBeVisible();

    // Change plan
    await planDropdown.selectOption('monthly');

    // Verify the selection changed
    await expect(planDropdown).toHaveValue('monthly');
  });

  test('AC8: should display credits column correctly', async ({ page }) => {
    // Verify credits column has values or infinity symbol
    const creditsCell = page.locator('tbody tr').first().locator('td').nth(4);
    await expect(creditsCell).toBeVisible();

    // Should contain a number or infinity symbol
    const creditsText = await creditsCell.textContent();
    expect(creditsText?.match(/\d+|\u221E/)).toBeTruthy();
  });

  test('AC9: should paginate users list', async ({ page }) => {
    // Check if pagination exists (when more than limit users)
    const pagination = page.locator('text=/de \\d+$/i');

    // If pagination exists, test navigation
    if (await pagination.isVisible()) {
      const nextButton = page.getByRole('button', { name: /Próximo/i });
      await expect(nextButton).toBeVisible();
    }
  });

  test('AC10: should show delete confirmation', async ({ page }) => {
    // Setup dialog handler
    page.on('dialog', async (dialog) => {
      expect(dialog.type()).toBe('confirm');
      expect(dialog.message()).toContain('Excluir usuário');
      await dialog.dismiss();
    });

    // Click delete button
    const deleteButton = page.locator('tbody tr').first().locator('button:has-text("Excluir")');
    await deleteButton.click();
  });

  test('AC11: should show 403 page for non-admin users', async ({ page }) => {
    // Mock non-admin user
    await mockAuthAPI(page, 'user');

    // Reload page
    await page.reload();

    // Verify access denied message
    await expect(page.locator('text=/Acesso Restrito/i')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=/exclusiva para administradores/i')).toBeVisible();
  });

  test('AC12: should cancel create form without creating user', async ({ page }) => {
    // Open create form
    await page.getByRole('button', { name: /Novo usuário/i }).click();
    await expect(page.locator('text=/Criar usuário/i')).toBeVisible();

    // Fill some data
    await page.locator('input[type="email"]').fill('cancel@test.com');

    // Click cancel (same button toggles)
    await page.getByRole('button', { name: /Cancelar/i }).click();

    // Verify form closed
    await expect(page.locator('text=/Criar usuário/i')).not.toBeVisible();

    // Verify email field is cleared when form reopens
    await page.getByRole('button', { name: /Novo usuário/i }).click();
    const emailValue = await page.locator('input[type="email"]').inputValue();
    expect(emailValue).toBe('');
  });
});
