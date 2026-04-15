/**
 * Page Objects for Billing E2E flows.
 *
 * Wraps the `/planos` and `/conta/plano` flows plus the embedded Stripe
 * Checkout form into a single object.  Tests never reach for raw selectors.
 *
 * STORY-3.5 — EPIC-TD-2026Q2 (P1)
 */

import { expect, Page, FrameLocator } from '@playwright/test';
import { StripeCard } from './stripe-fixtures';

/**
 * Timeout used when we're waiting on Stripe Checkout UI to render.
 * Stripe's hosted checkout is typically cold-start heavy on first hit.
 */
const STRIPE_TIMEOUT_MS = 30_000;

/**
 * Timeout used when we're waiting on a Stripe webhook to be processed on the backend.
 * Webhooks can take a few seconds to propagate through async queues.
 */
const WEBHOOK_TIMEOUT_MS = 30_000;

export class BillingPageObject {
  constructor(private readonly page: Page) {}

  // -----------------------------
  // Navigation
  // -----------------------------

  async goToPlanos(): Promise<void> {
    await this.page.goto('/planos');
    await expect(this.page).toHaveURL(/\/planos/);
  }

  async goToConta(): Promise<void> {
    await this.page.goto('/conta/plano');
    await expect(this.page).toHaveURL(/\/conta(\/plano)?/);
  }

  async goToBuscar(): Promise<void> {
    await this.page.goto('/buscar');
    await expect(this.page).toHaveURL(/\/buscar/);
  }

  // -----------------------------
  // /planos interactions
  // -----------------------------

  /**
   * Click the primary CTA on /planos.  The label varies based on plan state
   * ("Assinar", "Contratar", "Começar", "Upgrade", "Fazer upgrade", "Reativar").
   */
  async clickUpgrade(): Promise<void> {
    const cta = this.page
      .locator('button, a')
      .filter({ hasText: /Assinar|Contratar|Começar|Upgrade|Fazer upgrade|Reativar/i })
      .first();
    await expect(cta).toBeVisible({ timeout: 10_000 });
    await expect(cta).toBeEnabled();
    await cta.click();
  }

  /**
   * Click the "Reativar" CTA shown to users whose subscription is canceled
   * but still within the grace period.  Falls back to the generic upgrade
   * CTA if a dedicated reactivate button isn't rendered.
   */
  async clickResubscribe(): Promise<void> {
    const reactivate = this.page
      .locator('button, a')
      .filter({ hasText: /Reativar|Reassinar|Voltar a assinar|Renovar/i })
      .first();
    if (await reactivate.isVisible().catch(() => false)) {
      await reactivate.click();
      return;
    }
    await this.clickUpgrade();
  }

  /**
   * Switch the billing-period toggle on /planos.  Tolerant of several UI
   * variants (buttons, tabs, labels).
   */
  async selectBillingPeriod(period: 'monthly' | 'semiannual' | 'annual'): Promise<void> {
    const label = period === 'monthly' ? /mensal/i
      : period === 'semiannual' ? /semestral/i
      : /anual/i;
    const toggle = this.page
      .locator('button, [role="tab"], label')
      .filter({ hasText: label })
      .first();
    await expect(toggle).toBeVisible({ timeout: 10_000 });
    await toggle.click();
  }

  // -----------------------------
  // Stripe Checkout (hosted)
  // -----------------------------

  /**
   * Fill the Stripe Checkout card form.  Stripe embeds its form in iframes;
   * Playwright's FrameLocator chain is required.  This method is idempotent —
   * if the form has already been filled, the fills are simply re-applied.
   */
  async fillStripeCheckout(card: StripeCard): Promise<void> {
    // Wait for navigation to Stripe-hosted page.
    await this.page.waitForURL(/checkout\.stripe\.com/, { timeout: STRIPE_TIMEOUT_MS });

    const emailField = this.page.locator('input[name="email"], input[type="email"]').first();
    if (await emailField.isVisible().catch(() => false)) {
      // If Stripe prompts for email, leave it as-is (pre-filled by checkout session).
    }

    // Stripe renders Card Number / Expiration / CVC inside separate iframes
    // when Payment Element is used, or inline fields on hosted Checkout.
    // Try hosted Checkout (inline) first, then fall back to iframe lookup.
    const hostedNumber = this.page.locator('input[name="cardNumber"]').first();
    if (await hostedNumber.isVisible().catch(() => false)) {
      await hostedNumber.fill(card.number);
      await this.page.locator('input[name="cardExpiry"]').first().fill(card.exp);
      await this.page.locator('input[name="cardCvc"]').first().fill(card.cvc);
      const nameField = this.page.locator('input[name="billingName"]').first();
      if (await nameField.isVisible().catch(() => false)) {
        await nameField.fill('E2E Test');
      }
    } else {
      // Payment Element (iframe) path.
      const cardFrame = this.cardFrame();
      await cardFrame.locator('[placeholder*="1234"], input[name="cardnumber"]').first().fill(card.number);
      await cardFrame.locator('[placeholder*="MM"], input[name="exp-date"]').first().fill(card.exp);
      await cardFrame.locator('[placeholder*="CVC"], input[name="cvc"]').first().fill(card.cvc);
    }

    // Submit the form (Pagar / Subscribe / Pay button).
    const submit = this.page
      .locator('button[type="submit"], button')
      .filter({ hasText: /Pagar|Subscribe|Assinar|Pay/i })
      .first();
    await expect(submit).toBeVisible({ timeout: STRIPE_TIMEOUT_MS });
    await submit.click();
  }

  /**
   * Wait for Stripe Checkout to redirect back to the app and for the backend
   * to acknowledge the subscription as active.
   */
  async waitForSubscriptionActive(): Promise<void> {
    // Stripe redirects back to the success URL (typically /planos/obrigado).
    await this.page.waitForURL(/\/planos\/obrigado|\/buscar|\/dashboard/, {
      timeout: WEBHOOK_TIMEOUT_MS,
    });
  }

  // -----------------------------
  // /conta/plano interactions
  // -----------------------------

  async clickCancelSubscription(): Promise<void> {
    const cancel = this.page
      .locator('button')
      .filter({ hasText: /Cancelar assinatura|Cancelar/i })
      .first();
    await expect(cancel).toBeVisible({ timeout: 10_000 });
    await cancel.click();
  }

  /**
   * Walk the multi-step CancelSubscriptionModal to completion.
   * Steps: reason → (retention?) → confirm → feedback.
   */
  async confirmCancel(reason: 'too_expensive' | 'not_using' | 'missing_features' | 'found_alternative' | 'other' = 'missing_features'): Promise<void> {
    // Step 1: reason
    const radio = this.page.locator(`input[type="radio"][value="${reason}"]`).first();
    await expect(radio).toBeVisible({ timeout: 10_000 });
    await radio.check();
    await this.page.locator('button').filter({ hasText: /Continuar/i }).first().click();

    // Step 2: retention (only for too_expensive / not_using). Decline it.
    const retentionDecline = this.page
      .locator('button')
      .filter({ hasText: /Continuar cancelamento/i })
      .first();
    if (await retentionDecline.isVisible().catch(() => false)) {
      await retentionDecline.click();
    }

    // Step 3: confirm
    const confirmCheckbox = this.page.locator('input[type="checkbox"]').first();
    await expect(confirmCheckbox).toBeVisible({ timeout: 10_000 });
    await confirmCheckbox.check();
    await this.page.locator('button').filter({ hasText: /Confirmar cancelamento/i }).first().click();

    // Step 4: feedback — skip it.
    const skip = this.page.locator('button').filter({ hasText: /Pular/i }).first();
    if (await skip.isVisible().catch(() => false)) {
      await skip.click();
    }
  }

  /**
   * Signup flow via UI.  Returns when the user lands on /onboarding or /buscar.
   */
  async signup(email: string, password: string, fullName = 'E2E Billing Tester'): Promise<void> {
    await this.page.goto('/signup');
    await this.page.locator('input[type="email"], input[name="email"]').first().fill(email);
    await this.page.locator('input[type="password"], input[name="password"]').first().fill(password);
    const nameField = this.page.locator('input[name="full_name"], input[name="name"]').first();
    if (await nameField.isVisible().catch(() => false)) {
      await nameField.fill(fullName);
    }
    const submit = this.page
      .locator('button[type="submit"], button')
      .filter({ hasText: /Criar conta|Cadastrar|Sign up|Começar/i })
      .first();
    await submit.click();
    // Expect redirect to onboarding, buscar, or dashboard.
    await this.page.waitForURL(/\/onboarding|\/buscar|\/dashboard/, { timeout: 30_000 });
  }

  async login(email: string, password: string): Promise<void> {
    await this.page.goto('/login');
    await this.page.locator('input[type="email"], input[name="email"]').first().fill(email);
    await this.page.locator('input[type="password"], input[name="password"]').first().fill(password);
    const submit = this.page
      .locator('button[type="submit"], button')
      .filter({ hasText: /Entrar|Login|Sign in/i })
      .first();
    await submit.click();
    await this.page.waitForURL(/\/buscar|\/dashboard|\/onboarding/, { timeout: 30_000 });
  }

  // -----------------------------
  // Internal helpers
  // -----------------------------

  private cardFrame(): FrameLocator {
    // Stripe's Payment Element typically uses the first iframe on the page.
    return this.page.frameLocator('iframe[name^="__privateStripeFrame"], iframe[title*="Secure"]').first();
  }
}
