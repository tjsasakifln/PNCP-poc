"use client";

import { useEffect, useRef, useState } from "react";
import { useAnalytics } from "../../hooks/useAnalytics";
import { PlanToggle, BillingPeriod } from "../../components/subscriptions/PlanToggle";

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  source?: string;
}

/**
 * Upgrade modal — GTM-002 Single Plan Model
 * Shows SmartLic Pro with 3 billing period options.
 * Copy rules: No "plano", "assinatura", "tier", "busca" words.
 */
export function UpgradeModal({ isOpen, onClose, source }: UpgradeModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly");
  const { trackEvent } = useAnalytics();

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape, true);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape, true);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen && typeof window !== "undefined") {
      trackEvent("upgrade_modal_opened", { source });
    }
  }, [isOpen, source]);

  if (!isOpen) return null;

  const prices: Record<BillingPeriod, { monthly: number; total: number; label: string }> = {
    monthly: { monthly: 1999, total: 1999, label: "/mês" },
    semiannual: { monthly: 1799, total: 10794, label: "/mês" },
    annual: { monthly: 1599, total: 19188, label: "/mês" },
  };

  const currentPrice = prices[billingPeriod];

  const formatPrice = (val: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val);

  const handleCTA = () => {
    trackEvent("upgrade_modal_cta_clicked", { billing_period: billingPeriod, source });
    window.location.href = `/planos?billing=${billingPeriod}`;
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
      aria-modal="true"
      role="dialog"
      aria-labelledby="upgrade-modal-title"
    >
      <div
        ref={modalRef}
        className="relative bg-surface-0 rounded-card shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-surface-0 border-b border-border px-6 py-4 flex items-center justify-between z-10">
          <h2 id="upgrade-modal-title" className="text-2xl font-bold text-ink">
            SmartLic Pro
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-1 rounded-full transition-colors"
            aria-label="Fechar modal"
          >
            <svg role="img" aria-label="Fechar" className="w-6 h-6 text-ink-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {/* Billing Period Toggle */}
          <div className="mb-6">
            <PlanToggle value={billingPeriod} onChange={setBillingPeriod} />
          </div>

          {/* Price Display */}
          <div className="text-center mb-6">
            <p className="text-4xl font-bold text-brand-navy">
              {formatPrice(currentPrice.monthly)}
              <span className="text-sm font-normal text-ink-muted">{currentPrice.label}</span>
            </p>
            {billingPeriod !== "monthly" && (
              <p className="text-sm text-ink-secondary mt-1">
                Total: {formatPrice(currentPrice.total)}
                {billingPeriod === "semiannual" ? " por semestre" : " por ano"}
              </p>
            )}
          </div>

          {/* Features */}
          <ul className="space-y-3 mb-6">
            {[
              "1.000 análises por mês",
              "Exportação Excel completa",
              "Pipeline de acompanhamento",
              "Inteligência de decisão completa",
              "5 anos de histórico",
              "Cobertura nacional — 27 estados",
            ].map((feature) => (
              <li key={feature} className="flex items-start gap-2 text-sm">
                <span className="flex-shrink-0 mt-0.5 text-green-500" aria-hidden="true">&#10003;</span>
                <span className="text-ink">{feature}</span>
              </li>
            ))}
          </ul>

          {/* CTA */}
          <button
            onClick={handleCTA}
            className="w-full px-6 py-3 rounded-button font-semibold bg-brand-navy text-white hover:bg-brand-blue-hover hover:-translate-y-0.5 hover:shadow-lg transition-all"
          >
            Começar Agora
          </button>

          {/* Footer */}
          <p className="mt-4 text-center text-xs text-ink-muted">
            Cancele quando quiser. Sem contrato de fidelidade.
          </p>
        </div>
      </div>
    </div>
  );
}
