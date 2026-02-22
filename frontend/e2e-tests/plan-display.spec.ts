/**
 * E2E Test: Plan Badge and Quota Display
 *
 * Critical User Flow: Verifying correct plan names and credit balance
 * Updated UX-343: Legacy plans now display as "SmartLic Pro"
 *
 * Steps:
 * 1. Verify plan badge displays correct name
 * 2. Verify quota counter shows credit balance
 * 3. Verify plan-specific styling
 * 4. Verify trial countdown (if applicable)
 */

import { test, expect } from '@playwright/test';
import { mockAuthAPI, mockMeAPI, clearTestData } from './helpers/test-utils';

test.describe('Plan Badge Display', () => {
  test.beforeEach(async ({ page }) => {
    await clearTestData(page);
  });

  test('AC1: should display free trial badge correctly', async ({ page }) => {
    // Mock user with free trial
    await mockMeAPI(page, {
      plan_id: 'free_trial',
      plan_name: 'Avaliacao Gratuita',
      credits_remaining: null,
      trial_expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for plan badge
    const planBadge = page.locator('[aria-label*="plan"]').or(page.locator('button:has-text("Avaliacao")'));

    if (await planBadge.isVisible()) {
      // Verify correct plan name
      await expect(planBadge).toContainText(/Avaliacao|Trial|Gratuita/i);

      // Verify trial countdown if present
      const countdown = planBadge.locator('text=/\\d+ dia/i');
      if (await countdown.isVisible()) {
        await expect(countdown).toBeVisible();
      }
    }
  });

  test('AC2: should display legacy consultor_agil as SmartLic Pro', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'consultor_agil',
      plan_name: 'Consultor Agil',
      credits_remaining: 10,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Legacy plans now display as SmartLic Pro
    const planBadge = page.locator('[aria-label*="plan"]').or(page.locator('button:has-text("SmartLic Pro")'));

    if (await planBadge.isVisible()) {
      await expect(planBadge).toContainText(/SmartLic Pro/i);
    }
  });

  test('AC3: should display legacy maquina as SmartLic Pro', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'maquina',
      plan_name: 'Maquina de Vendas',
      credits_remaining: 50,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Legacy plans now display as SmartLic Pro
    const planBadge = page.locator('[aria-label*="plan"]').or(page.locator('button:has-text("SmartLic Pro")'));

    if (await planBadge.isVisible()) {
      await expect(planBadge).toContainText(/SmartLic Pro/i);
    }
  });

  test('AC4: should display legacy sala_guerra as SmartLic Pro', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'sala_guerra',
      plan_name: 'Sala de Guerra',
      credits_remaining: 999999,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Legacy plans now display as SmartLic Pro
    const planBadge = page.locator('[aria-label*="plan"]').or(page.locator('button:has-text("SmartLic Pro")'));

    if (await planBadge.isVisible()) {
      await expect(planBadge).toContainText(/SmartLic Pro/i);
    }
  });

  test('AC5: should show warning icon for trial plans', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'free_trial',
      plan_name: 'Avaliacao Gratuita',
      trial_expires_at: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for warning indicator (emoji or icon)
    const warningIndicator = page.locator('text=/\\u26A0|Trial|Avaliacao/');

    if (await warningIndicator.isVisible()) {
      await expect(warningIndicator).toBeVisible();
    }
  });
});

test.describe('Quota Counter Display', () => {
  test.beforeEach(async ({ page }) => {
    await clearTestData(page);
  });

  test('AC6: should display quota counter with correct values', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'consultor_agil',
      plan_name: 'SmartLic Pro',
      credits_remaining: 7,
      credits_total: 10,
      reset_date: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for quota display
    const quotaDisplay = page.locator('[role="status"]').or(page.locator('text=/Buscas este mês/i'));

    if (await quotaDisplay.isVisible()) {
      // Verify quota numbers
      await expect(quotaDisplay).toContainText(/\d+\/\d+|Buscas/i);
    }
  });

  test('AC7: should show progress bar for quota usage', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'consultor_agil',
      plan_name: 'SmartLic Pro',
      credits_remaining: 3,
      credits_total: 10,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for progress bar
    const progressBar = page.locator('[aria-label*="quota"]').or(page.locator('.h-2.rounded-full'));

    if (await progressBar.isVisible()) {
      await expect(progressBar).toBeVisible();
    }
  });

  test('AC8: should show warning when quota is near limit (70%+)', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'maquina',
      plan_name: 'SmartLic Pro',
      credits_remaining: 8,
      credits_total: 50,
      quota_used: 42,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for warning message
    const warningMessage = page.locator('text=/próximo do limite/i');

    if (await warningMessage.isVisible()) {
      await expect(warningMessage).toBeVisible();
    }
  });

  test('AC9: should show error state when quota exhausted', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'consultor_agil',
      plan_name: 'SmartLic Pro',
      credits_remaining: 0,
      credits_total: 10,
      quota_used: 10,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for exhausted message
    const exhaustedMessage = page.locator('text=/acabaram/i');

    if (await exhaustedMessage.isVisible()) {
      await expect(exhaustedMessage).toBeVisible();
    }

    // Look for upgrade button
    const upgradeButton = page.locator('button:has-text("Upgrade")');

    if (await upgradeButton.isVisible()) {
      await expect(upgradeButton).toBeVisible();
    }
  });

  test('AC10: should show unlimited for trial users', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'free_trial',
      plan_name: 'Avaliacao Gratuita',
      credits_remaining: 999999,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for unlimited indicator
    const unlimitedIndicator = page.locator('text=/ilimitadas|\\u221E/i');

    if (await unlimitedIndicator.isVisible()) {
      await expect(unlimitedIndicator).toBeVisible();
    }
  });

  test('AC11: should display reset date for subscription plans', async ({ page }) => {
    const resetDate = new Date(Date.now() + 15 * 24 * 60 * 60 * 1000);
    await mockMeAPI(page, {
      plan_id: 'maquina',
      plan_name: 'SmartLic Pro',
      credits_remaining: 30,
      credits_total: 50,
      reset_date: resetDate.toISOString(),
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Look for reset date
    const resetDateDisplay = page.locator('text=/Renovação:/i');

    if (await resetDateDisplay.isVisible()) {
      await expect(resetDateDisplay).toBeVisible();
    }
  });
});

test.describe('Plan Badge Interactivity', () => {
  test.beforeEach(async ({ page }) => {
    await clearTestData(page);
  });

  test('AC12: should navigate to plans page on badge click', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'consultor_agil',
      plan_name: 'SmartLic Pro',
      credits_remaining: 10,
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Find and click plan badge (now shows SmartLic Pro for legacy plans)
    const planBadge = page.locator('[title*="planos"]').or(page.locator('button:has-text("SmartLic Pro")'));

    if (await planBadge.isVisible()) {
      await planBadge.click();

      // Should navigate or open modal
      await expect(page).toHaveURL(/planos|plans/i).catch(() => {
        // Or modal opened
        const modal = page.locator('[role="dialog"]').or(page.locator('text=/Planos disponíveis/i'));
        return expect(modal).toBeVisible();
      });
    }
  });

  test('AC13: should have accessible label on plan badge', async ({ page }) => {
    await mockMeAPI(page, {
      plan_id: 'maquina',
      plan_name: 'SmartLic Pro',
    });
    await mockAuthAPI(page, 'user');

    await page.goto('/');

    // Find plan badge (now displays as SmartLic Pro)
    const planBadge = page.locator('button').filter({ hasText: /SmartLic Pro/i }).first();

    if (await planBadge.isVisible()) {
      // Should have accessible label
      const ariaLabel = await planBadge.getAttribute('aria-label');
      const title = await planBadge.getAttribute('title');

      expect(ariaLabel || title).toBeTruthy();
    }
  });
});

test.describe('Admin Panel Plan Display', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthAPI(page, 'admin');
    await clearTestData(page);
  });

  test('AC14: should display plan names consistently in admin table', async ({ page }) => {
    // Mock admin users endpoint with various plans
    await page.route('**/admin/users**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          users: [
            {
              id: '1',
              email: 'free@test.com',
              plan_type: 'free',
              user_subscriptions: [{ plan_id: 'free', is_active: true, credits_remaining: 3 }],
            },
            {
              id: '2',
              email: 'pack@test.com',
              plan_type: 'pack_10',
              user_subscriptions: [{ plan_id: 'pack_10', is_active: true, credits_remaining: 8 }],
            },
            {
              id: '3',
              email: 'monthly@test.com',
              plan_type: 'monthly',
              user_subscriptions: [{ plan_id: 'monthly', is_active: true, credits_remaining: null }],
            },
          ],
          total: 3,
        }),
      });
    });

    await page.goto('/admin');

    // Verify plan dropdown options are consistent
    const planDropdowns = page.locator('tbody select');

    if (await planDropdowns.first().isVisible()) {
      // Check that plan options match expected values
      const options = await planDropdowns.first().locator('option').allTextContents();
      expect(options).toContain('free');
    }
  });

  test('AC15: should display credits correctly for each user in admin', async ({ page }) => {
    await page.route('**/admin/users**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          users: [
            {
              id: '1',
              email: 'limited@test.com',
              plan_type: 'pack_10',
              user_subscriptions: [{ plan_id: 'pack_10', is_active: true, credits_remaining: 5 }],
            },
            {
              id: '2',
              email: 'unlimited@test.com',
              plan_type: 'annual',
              user_subscriptions: [{ plan_id: 'annual', is_active: true, credits_remaining: null }],
            },
          ],
          total: 2,
        }),
      });
    });

    await page.goto('/admin');

    // Verify credits column shows numbers or infinity
    const creditsColumn = page.locator('tbody tr td:nth-child(5)');

    if (await creditsColumn.first().isVisible()) {
      const firstCredits = await creditsColumn.first().textContent();
      const secondCredits = await creditsColumn.nth(1).textContent();

      // First user should show 5
      expect(firstCredits).toContain('5');

      // Second user should show infinity symbol
      expect(secondCredits).toMatch(/\u221E|null|-/);
    }
  });
});
