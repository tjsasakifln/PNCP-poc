"use client";

/**
 * TrustSignals Component
 *
 * Displays trust signals, guarantees, and urgency elements
 * STORY-171 AC15: Trust Signals & Urgency
 *
 * Features:
 * - Social proof badge (dynamic conversion rate)
 * - Launch offer (first 100 signups)
 * - Guarantees section (30-day refund, security, support)
 * - Early adopter discount code
 */

export interface TrustSignalsProps {
  annualConversionRate?: number; // 0-100
  currentAnnualSignups?: number; // For launch offer countdown
  launchOfferLimit?: number; // Default: 100
  showEarlyBirdCode?: boolean;
  className?: string;
}

export function TrustSignals({
  annualConversionRate = 65, // Default fallback
  currentAnnualSignups = 0,
  launchOfferLimit = 100,
  showEarlyBirdCode = true,
  className = "",
}: TrustSignalsProps) {
  const launchOfferActive = currentAnnualSignups < launchOfferLimit;
  const remainingSlots = launchOfferLimit - currentAnnualSignups;

  return (
    <div className={`space-y-6 ${className}`} data-testid="trust-signals">
      {/* Social Proof Badge */}
      {annualConversionRate > 0 && (
        <div className="flex justify-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-success-subtle border border-success rounded-full">
            <span className="text-lg" aria-hidden="true">⭐</span>
            <span className="text-sm font-semibold text-success">
              Escolha de {annualConversionRate}% dos nossos clientes
            </span>
          </div>
        </div>
      )}

      {/* Launch Offer */}
      {launchOfferActive && (
        <div
          className="p-4 bg-warning-subtle border-2 border-warning rounded-card animate-fade-in"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-start gap-3">
            <span className="text-2xl" aria-hidden="true">🎁</span>
            <div className="flex-1">
              <h4 className="font-semibold text-ink mb-1">
                Oferta de Lançamento - Tempo Limitado!
              </h4>
              <p className="text-sm text-ink-secondary mb-2">
                Primeiros {launchOfferLimit} assinantes ganham <strong>+1 mês grátis</strong>!
              </p>
              <p className="text-xs font-bold text-warning">
                Restam apenas {remainingSlots} vagas
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Early Adopter Discount Code */}
      {showEarlyBirdCode && (
        <div className="p-4 bg-brand-blue-subtle border border-brand-blue rounded-card">
          <div className="text-center">
            <p className="text-sm text-ink-secondary mb-2">
              Código de desconto adicional para early adopters:
            </p>
            <div className="inline-flex items-center gap-3 px-4 py-2 bg-white border-2 border-dashed border-brand-blue rounded-card">
              <code className="text-lg font-mono font-bold text-brand-navy">
                EARLYBIRD
              </code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText('EARLYBIRD');
                  // In production, show toast notification
                }}
                className="text-sm text-brand-blue hover:text-brand-blue-hover font-semibold"
                aria-label="Copiar código EARLYBIRD"
              >
                Copiar
              </button>
            </div>
            <p className="text-xs text-ink-muted mt-2">
              +10% de desconto extra (válido para os primeiros 50 usos)
            </p>
          </div>
        </div>
      )}

      {/* Guarantees Section */}
      <div className="bg-surface-0 rounded-card p-6 border">
        <h4 className="text-lg font-semibold text-ink mb-4 text-center">
          Nossas Garantias
        </h4>
        <div className="space-y-4">
          {/* 30-day refund */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 flex items-center justify-center bg-success-subtle rounded-full flex-shrink-0">
              <span className="text-xl" aria-hidden="true">💳</span>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-ink">Garantia de 30 dias</p>
              <p className="text-sm text-ink-secondary mt-0.5">
                Cancele e receba reembolso integral dentro de 30 dias
              </p>
            </div>
          </div>

          {/* Security */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 flex items-center justify-center bg-brand-blue-subtle rounded-full flex-shrink-0">
              <span className="text-xl" aria-hidden="true">🔒</span>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-ink">Segurança de nível bancário</p>
              <p className="text-sm text-ink-secondary mt-0.5">
                Seus dados protegidos com criptografia de ponta a ponta
              </p>
            </div>
          </div>

          {/* Priority Support */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 flex items-center justify-center bg-warning-subtle rounded-full flex-shrink-0">
              <span className="text-xl" aria-hidden="true">📞</span>
            </div>
            <div className="flex-1">
              <p className="font-semibold text-ink">Suporte prioritário 24/7</p>
              <p className="text-sm text-ink-secondary mt-0.5">
                Atendimento dedicado para assinantes anuais
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Trust Elements */}
      <div className="flex flex-wrap justify-center gap-4 text-xs text-ink-muted">
        <div className="flex items-center gap-1">
          <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>Cancelamento online simples</span>
        </div>
        <div className="flex items-center gap-1">
          <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>Sem taxas ocultas</span>
        </div>
        <div className="flex items-center gap-1">
          <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>LGPD compliant</span>
        </div>
      </div>
    </div>
  );
}
