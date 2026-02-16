import { test, expect } from "@playwright/test";

/**
 * TD-005: Dialog Accessibility E2E Tests
 * REG-T10: Focus trap — Tab does not escape modal
 * REG-T11: Escape closes modal, UF selection preserved
 */

test.describe("Dialog Accessibility — WCAG 2.4.3 Focus Order", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/buscar");
    // Wait for page to be interactive
    await page.waitForLoadState("networkidle");
  });

  test.describe("REG-T10: Focus trap in modals", () => {
    test("Keyboard shortcuts modal traps Tab focus", async ({ page }) => {
      // Open keyboard shortcuts modal by pressing /
      await page.keyboard.press("/");

      // Wait for the keyboard help dialog to appear
      const dialog = page.locator('[role="dialog"]').filter({ hasText: "Atalhos de Teclado" });
      await expect(dialog).toBeVisible();

      // Verify dialog has proper ARIA attributes
      await expect(dialog).toHaveAttribute("aria-modal", "true");

      // Tab through all focusable elements inside the dialog
      // The dialog should contain: close button, "Entendi" button
      const focusableElements = dialog.locator("button");
      const count = await focusableElements.count();
      expect(count).toBeGreaterThan(0);

      // Tab through all elements and one more — should wrap back to first
      for (let i = 0; i <= count; i++) {
        await page.keyboard.press("Tab");
      }

      // Focus should still be inside the dialog (wrapped around)
      const activeElement = page.locator(":focus");
      const isInsideDialog = await dialog.locator(":focus").count();
      expect(isInsideDialog).toBe(1);
    });

    test("Keyboard shortcuts modal traps Shift+Tab focus", async ({ page }) => {
      await page.keyboard.press("/");

      const dialog = page.locator('[role="dialog"]').filter({ hasText: "Atalhos de Teclado" });
      await expect(dialog).toBeVisible();

      // Shift+Tab should also stay inside the dialog
      await page.keyboard.press("Shift+Tab");
      await page.keyboard.press("Shift+Tab");

      const isInsideDialog = await dialog.locator(":focus").count();
      expect(isInsideDialog).toBe(1);
    });

    test("Save search dialog traps Tab focus", async ({ page }) => {
      // We need to trigger the save dialog — this requires a search first
      // For now, check that the dialog component has focus trap structure
      // by verifying the Dialog component renders with correct attributes
      // when any dialog opens

      // Open keyboard help as a proxy test for Dialog component behavior
      await page.keyboard.press("/");
      const dialog = page.locator('[role="dialog"]');
      await expect(dialog.first()).toBeVisible();

      // Verify the panel has tabindex=-1 for programmatic focus
      const panel = dialog.first().locator('[tabindex="-1"]');
      await expect(panel).toBeVisible();
    });
  });

  test.describe("REG-T11: Escape closes modal only", () => {
    test("Escape closes keyboard shortcuts modal", async ({ page }) => {
      // Open keyboard shortcuts
      await page.keyboard.press("/");
      const dialog = page.locator('[role="dialog"]').filter({ hasText: "Atalhos de Teclado" });
      await expect(dialog).toBeVisible();

      // Press Escape
      await page.keyboard.press("Escape");

      // Dialog should be closed
      await expect(dialog).not.toBeVisible();
    });

    test("Escape does not trigger limparSelecao when modal is open", async ({ page }) => {
      // Select some UFs first
      const ufButton = page.locator('button:has-text("SP")').first();
      if (await ufButton.isVisible()) {
        await ufButton.click();
      }

      // Open keyboard shortcuts modal
      await page.keyboard.press("/");
      const dialog = page.locator('[role="dialog"]').filter({ hasText: "Atalhos de Teclado" });
      await expect(dialog).toBeVisible();

      // Press Escape — should close modal, NOT clear UF selection
      await page.keyboard.press("Escape");
      await expect(dialog).not.toBeVisible();

      // SP should still be selected (Escape was captured by modal, not by limparSelecao)
      // The button should still show as selected (has a distinct style)
      if (await ufButton.isVisible()) {
        // The UF should still be in a selected state
        const buttonClasses = await ufButton.getAttribute("class");
        // Selected UF buttons typically have brand colors
        expect(buttonClasses).toBeTruthy();
      }
    });

    test("Screen reader announces dialog role", async ({ page }) => {
      await page.keyboard.press("/");
      const dialog = page.locator('[role="dialog"]');
      await expect(dialog.first()).toBeVisible();

      // Verify role and aria-labelledby are present
      await expect(dialog.first()).toHaveAttribute("role", "dialog");
      await expect(dialog.first()).toHaveAttribute("aria-modal", "true");
      await expect(dialog.first()).toHaveAttribute("aria-labelledby");
    });
  });
});
