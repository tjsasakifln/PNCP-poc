"use client";

import { useState } from "react";

/**
 * DowngradeModal Component
 *
 * Warning modal for downgrade action from annual to monthly
 * STORY-171 AC12 & AC17: UX/UI Polish & Downgrade Flow
 *
 * Features:
 * - Shows retained benefits until expiry
 * - Requires confirmation checkbox
 * - Clear messaging about no refund policy
 * - Accessible
 */

export interface DowngradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  currentPlanName?: string;
  expiryDate?: string; // ISO date string
  retainedBenefits?: string[];
  isLoading?: boolean;
}

export function DowngradeModal({
  isOpen,
  onClose,
  onConfirm,
  currentPlanName = "Plano Anual",
  expiryDate,
  retainedBenefits = [
    "Early access a novas features",
    "Busca proativa de oportunidades",
    "Análise IA de editais",
  ],
  isLoading = false,
}: DowngradeModalProps) {
  const [confirmed, setConfirmed] = useState(false);

  // Format expiry date
  const formattedExpiryDate = expiryDate
    ? new Date(expiryDate).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      })
    : "31/12/2026";

  // Reset state when modal closes
  const handleClose = () => {
    setConfirmed(false);
    onClose();
  };

  const handleConfirm = () => {
    if (!confirmed || isLoading) return;
    onConfirm();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 animate-fade-in"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="downgrade-modal-title"
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div className="bg-surface-0 rounded-card shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto animate-fade-in-up">
          {/* Header */}
          <div className="p-6 border-b">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 flex items-center justify-center bg-warning-subtle rounded-full flex-shrink-0">
                <span className="text-xl" aria-hidden="true">⚠️</span>
              </div>
              <div className="flex-1">
                <h2 id="downgrade-modal-title" className="text-xl font-bold text-ink">
                  Downgrade para Plano Mensal
                </h2>
                <p className="text-sm text-ink-secondary mt-1">
                  Tem certeza que deseja fazer downgrade?
                </p>
              </div>
              <button
                onClick={handleClose}
                className="text-ink-muted hover:text-ink transition-colors"
                aria-label="Fechar modal"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Warning Alert */}
            <div className="p-4 bg-warning-subtle border border-warning rounded-card">
              <p className="text-sm font-semibold text-ink mb-2">
                ⚠️ Você está fora do período de garantia (7 dias)
              </p>
              <p className="text-sm text-ink-secondary">
                De acordo com nossa política de cancelamento, não será possível reembolso.
              </p>
            </div>

            {/* Downgrade Policy */}
            <div>
              <h3 className="font-semibold text-ink mb-2">
                O que acontece com o downgrade:
              </h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li className="flex items-start gap-2">
                  <span className="text-error flex-shrink-0">❌</span>
                  <span>Sem reembolso do valor pago</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-success flex-shrink-0">✅</span>
                  <span>Você mantém todos os benefícios anuais até <strong className="text-ink">{formattedExpiryDate}</strong></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-brand-blue flex-shrink-0">📅</span>
                  <span>Após {formattedExpiryDate}, sua assinatura será convertida para mensal</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-warning flex-shrink-0">💰</span>
                  <span>Próxima cobrança será o valor mensal em {formattedExpiryDate}</span>
                </li>
              </ul>
            </div>

            {/* Retained Benefits */}
            {retainedBenefits.length > 0 && (
              <div className="p-4 bg-brand-blue-subtle border border-brand-blue rounded-card">
                <h4 className="font-semibold text-ink mb-2">
                  Benefícios que você manterá até {formattedExpiryDate}:
                </h4>
                <ul className="space-y-1.5">
                  {retainedBenefits.map((benefit, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-ink-secondary">
                      <span className="text-success flex-shrink-0">✨</span>
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tip */}
            <div className="p-3 bg-surface-1 rounded-card border">
              <p className="text-sm text-ink-secondary">
                <span className="font-semibold text-brand-navy">💡 Dica:</span> Aproveite seus benefícios anuais até o fim do período! Você já pagou por eles.
              </p>
            </div>

            {/* Confirmation Checkbox */}
            <div className="pt-2">
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  className="mt-1 w-5 h-5 text-brand-blue border-strong rounded focus:ring-2 focus:ring-brand-blue cursor-pointer"
                  required
                />
                <span className="text-sm text-ink-secondary group-hover:text-ink transition-colors">
                  Entendo que não haverá reembolso e meus benefícios anuais serão mantidos até {formattedExpiryDate}.
                </span>
              </label>
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t bg-surface-1 flex gap-3">
            <button
              onClick={handleClose}
              disabled={isLoading}
              className="flex-1 px-6 py-3 bg-white border-2 border-strong text-ink rounded-button font-semibold hover:bg-surface-1 active:bg-surface-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancelar
            </button>
            <button
              onClick={handleConfirm}
              disabled={!confirmed || isLoading}
              className="flex-1 px-6 py-3 bg-warning text-white rounded-button font-semibold hover:bg-warning/90 active:bg-warning/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-warning focus:ring-offset-2"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processando...
                </span>
              ) : (
                "Confirmar Downgrade"
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
