"use client";

import { useEffect, useState } from "react";
import { useAnalytics } from "../../hooks/useAnalytics";
import { PlanToggle, BillingPeriod } from "../../components/subscriptions/PlanToggle";
import { Dialog } from "./Dialog";

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  source?: string;
}

/**
 * Upgrade modal — GTM-002 Single Plan Model
 * Shows SmartLic Pro with 3 billing period options.
 * Copy rules: No "plano", "assinatura", "tier", "busca" words.
 *
 * Now uses the reusable Dialog component for WCAG-compliant
 * focus trap, ARIA attributes, and Escape handling.
 */
export function UpgradeModal({ isOpen, onClose, source }: UpgradeModalProps) {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly");
  const { trackEvent } = useAnalytics();

  useEffect(() => {
    if (isOpen && typeof window !== "undefined") {
      trackEvent("upgrade_modal_opened", { source });
    }
  }, [isOpen, source]);

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
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="SmartLic Pro"
      className="max-w-lg max-h-[90vh] overflow-y-auto p-0"
      id="upgrade-modal"
    >
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
    </Dialog>
  );
}
