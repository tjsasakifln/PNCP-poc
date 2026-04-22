/**
 * Trial terms notice — disclosure above PaymentElement (STORY-CONV-003b AC1).
 *
 * Exact copy locked in the story ("Cartão não será cobrado hoje...").
 * Separated from CardCollect so UX designer can tweak typography without
 * touching Stripe wiring.
 */
"use client";

export function TrialTermsNotice() {
  return (
    <div
      data-testid="trial-terms-notice"
      className="mb-3 p-3 bg-surface-1 rounded-input text-xs text-ink-secondary space-y-1"
    >
      <p className="font-medium text-ink">
        Cartão não será cobrado hoje.
      </p>
      <p>
        Cobrança automática em 14 dias (R$ 397/mês). Cancele a qualquer
        momento em 1 clique — link no email de aviso 24h antes.
      </p>
    </div>
  );
}
