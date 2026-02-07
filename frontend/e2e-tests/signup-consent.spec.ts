/**
 * E2E Tests: Signup with WhatsApp and Consent Flow
 *
 * Tests the complete signup flow including:
 * - Phone field with Brazilian format masking
 * - Consent terms scroll requirement
 * - Checkbox enabled only after scrolling
 * - Form validation
 */

import { test, expect } from "@playwright/test";

test.describe("Signup with WhatsApp Consent", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/signup");
  });

  test("should display signup form with all required fields", async ({ page }) => {
    // Check heading
    await expect(page.getByRole("heading", { name: /Criar conta/i })).toBeVisible();

    // Check all form fields are present
    await expect(page.getByLabel(/Nome completo/i)).toBeVisible();
    await expect(page.getByLabel(/Empresa/i)).toBeVisible();
    await expect(page.getByLabel(/Setor de atuação/i)).toBeVisible();
    await expect(page.getByLabel(/Email/i)).toBeVisible();
    await expect(page.getByPlaceholder(/\(11\) 99999-9999/i)).toBeVisible();
    await expect(page.getByPlaceholder(/Minimo 6 caracteres/i)).toBeVisible();

    // Check consent section
    await expect(page.getByText(/Termos de consentimento/i)).toBeVisible();
    await expect(page.getByText(/TERMOS DE CONSENTIMENTO PARA COMUNICACOES PROMOCIONAIS/i)).toBeVisible();
  });

  test("should format phone number as Brazilian format", async ({ page }) => {
    const phoneInput = page.getByLabel(/WhatsApp/i);

    // Type 11 digit phone
    await phoneInput.fill("11999998888");

    // Should be formatted
    await expect(phoneInput).toHaveValue("(11) 99999-8888");
  });

  test("should format 10 digit phone correctly", async ({ page }) => {
    const phoneInput = page.getByLabel(/WhatsApp/i);

    // Type 10 digit phone (landline format)
    await phoneInput.fill("1133334444");

    // Should be formatted
    await expect(phoneInput).toHaveValue("(11) 3333-4444");
  });

  test("should have consent checkbox disabled initially", async ({ page }) => {
    const checkbox = page.getByRole("checkbox");
    await expect(checkbox).toBeDisabled();
  });

  test("should show scroll indicator initially", async ({ page }) => {
    await expect(page.getByText(/Role para baixo/i)).toBeVisible();
  });

  test("should enable checkbox after scrolling to bottom", async ({ page }) => {
    const checkbox = page.getByRole("checkbox");
    const scrollBox = page.locator(".overflow-y-auto").first();

    // Initially disabled
    await expect(checkbox).toBeDisabled();

    // Scroll to bottom
    await scrollBox.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });

    // Wait for state update
    await page.waitForTimeout(100);

    // Now enabled
    await expect(checkbox).not.toBeDisabled();
  });

  test("should hide scroll indicator after scrolling to bottom", async ({ page }) => {
    const scrollBox = page.locator(".overflow-y-auto").first();

    // Initially visible
    await expect(page.getByText(/Role para baixo/i)).toBeVisible();

    // Scroll to bottom
    await scrollBox.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });

    // Wait for state update
    await page.waitForTimeout(100);

    // Now hidden
    await expect(page.getByText(/Role para baixo/i)).not.toBeVisible();
  });

  test("should have submit button disabled when form is incomplete", async ({ page }) => {
    const submitButton = page.getByRole("button", { name: /Criar conta$/i });
    await expect(submitButton).toBeDisabled();
  });

  test("should enable submit button when all fields are valid and consent given", async ({ page }) => {
    // Fill all fields
    await page.getByLabel(/Nome completo/i).fill("Test User");
    await page.getByLabel(/Empresa/i).fill("Test Company");
    await page.getByLabel(/Setor de atuação/i).selectOption("informatica");
    await page.getByLabel(/Email/i).fill("test@example.com");
    await page.getByPlaceholder(/\(11\) 99999-9999/i).fill("11999998888");
    await page.getByPlaceholder(/Minimo 6 caracteres/i).fill("password123");

    // Scroll consent to bottom
    const scrollBox = page.locator(".overflow-y-auto").first();
    await scrollBox.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    await page.waitForTimeout(100);

    // Check consent
    await page.getByRole("checkbox").check();

    // Submit should be enabled
    const submitButton = page.getByRole("button", { name: /Criar conta$/i });
    await expect(submitButton).not.toBeDisabled();
  });

  test("should keep submit disabled with invalid phone", async ({ page }) => {
    // Fill all fields but with short phone
    await page.getByLabel(/Nome completo/i).fill("Test User");
    await page.getByLabel(/Empresa/i).fill("Test Company");
    await page.getByLabel(/Setor de atuação/i).selectOption("informatica");
    await page.getByLabel(/Email/i).fill("test@example.com");
    await page.getByPlaceholder(/\(11\) 99999-9999/i).fill("123"); // Too short
    await page.getByPlaceholder(/Minimo 6 caracteres/i).fill("password123");

    // Scroll and consent
    const scrollBox = page.locator(".overflow-y-auto").first();
    await scrollBox.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    await page.waitForTimeout(100);
    await page.getByRole("checkbox").check();

    // Submit should still be disabled
    const submitButton = page.getByRole("button", { name: /Criar conta$/i });
    await expect(submitButton).toBeDisabled();
  });

  test("should show other sector input when 'outro' is selected", async ({ page }) => {
    const sectorSelect = page.getByLabel(/Setor de atuação/i);

    // Initially, other sector field should not be visible
    await expect(page.getByLabel(/Qual setor\?/i)).not.toBeVisible();

    // Select "outro"
    await sectorSelect.selectOption("outro");

    // Now the other sector field should appear
    await expect(page.getByLabel(/Qual setor\?/i)).toBeVisible();
  });

  test("should navigate to login page via link", async ({ page }) => {
    const loginLink = page.getByRole("link", { name: /Fazer login/i });
    await loginLink.click();

    await expect(page).toHaveURL(/\/login/);
  });

  test("should have Google signup button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /Cadastrar com Google/i })).toBeVisible();
  });

  test("should toggle password visibility", async ({ page }) => {
    const passwordInput = page.getByPlaceholder(/Minimo 6 caracteres/i);
    const toggleButton = page.getByRole("button", { name: /Mostrar senha/i });

    // Initially hidden
    await expect(passwordInput).toHaveAttribute("type", "password");

    // Click to show
    await toggleButton.click();
    await expect(passwordInput).toHaveAttribute("type", "text");

    // Click to hide again
    const hideButton = page.getByRole("button", { name: /Ocultar senha/i });
    await hideButton.click();
    await expect(passwordInput).toHaveAttribute("type", "password");
  });

  test("complete signup flow - happy path", async ({ page }) => {
    // Fill all fields
    await page.getByLabel(/Nome completo/i).fill("Test User");
    await page.getByLabel(/Empresa/i).fill("Test Company");
    await page.getByLabel(/Setor de atuação/i).selectOption("informatica");
    await page.getByLabel(/Email/i).fill("test@example.com");
    await page.getByPlaceholder(/\(11\) 99999-9999/i).fill("11999998888");
    await page.getByPlaceholder(/Minimo 6 caracteres/i).fill("password123");

    // Scroll consent to bottom
    const scrollBox = page.locator(".overflow-y-auto").first();
    await scrollBox.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    await page.waitForTimeout(100);

    // Check consent
    await page.getByRole("checkbox").check();

    // Verify checkbox is checked
    await expect(page.getByRole("checkbox")).toBeChecked();

    // Submit button should be enabled
    const submitButton = page.getByRole("button", { name: /Criar conta$/i });
    await expect(submitButton).not.toBeDisabled();

    // Note: We don't actually submit to avoid creating real accounts
    // In a real E2E test with mock backend, we would click submit and verify success state
  });
});
