"use client";

import { useEffect, useRef } from "react";

interface PlanFeature {
  text: string;
  available: boolean;
  highlight?: boolean;
}

interface PlanCard {
  id: string;
  name: string;
  price: string;
  priceMonthly: number;
  popular?: boolean;
  features: PlanFeature[];
  buttonText: string;
  buttonStyle: "outline" | "solid" | "premium";
}

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  preSelectedPlan?: "consultor_agil" | "maquina" | "sala_guerra";
  source?: string; // Analytics: 'excel_button', 'date_range', 'quota_counter'
}

const PLANS: PlanCard[] = [
  {
    id: "consultor_agil",
    name: "Consultor Ágil",
    price: "R$ 297/mês",
    priceMonthly: 297,
    features: [
      { text: "50 buscas por mês", available: true },
      { text: "30 dias de histórico", available: true },
      { text: "Resumo executivo IA (básico)", available: true },
      { text: "Filtros por setor e UF", available: true },
      { text: "Exportar Excel", available: false },
      { text: "Suporte prioritário", available: false },
    ],
    buttonText: "Assinar Consultor Ágil",
    buttonStyle: "outline",
  },
  {
    id: "maquina",
    name: "Máquina",
    price: "R$ 597/mês",
    priceMonthly: 597,
    popular: true,
    features: [
      { text: "300 buscas por mês", available: true, highlight: true },
      { text: "1 ano de histórico", available: true, highlight: true },
      { text: "Resumo executivo IA (completo)", available: true },
      { text: "Exportar Excel", available: true, highlight: true },
      { text: "Filtros avançados", available: true },
      { text: "Suporte prioritário", available: true },
      { text: "API básica", available: true },
    ],
    buttonText: "Assinar Máquina",
    buttonStyle: "solid",
  },
  {
    id: "sala_guerra",
    name: "Sala de Guerra",
    price: "R$ 1.497/mês",
    priceMonthly: 1497,
    features: [
      { text: "1000 buscas por mês", available: true, highlight: true },
      { text: "5 anos de histórico", available: true, highlight: true },
      { text: "Resumo executivo IA (premium)", available: true },
      { text: "Exportar Excel (formatação avançada)", available: true },
      { text: "Alertas automáticos", available: true },
      { text: "Suporte 24/7 dedicado", available: true, highlight: true },
      { text: "API completa + webhooks", available: true },
      { text: "Relatórios personalizados", available: true },
    ],
    buttonText: "Assinar Sala de Guerra",
    buttonStyle: "premium",
  },
];

/**
 * Upgrade modal with plan comparison
 * Based on UX design spec in docs/ux/STORY-165-plan-ui-design.md
 */
export function UpgradeModal({ isOpen, onClose, preSelectedPlan, source }: UpgradeModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      // Lock body scroll
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  // Track analytics when modal opens
  useEffect(() => {
    if (isOpen && typeof window !== "undefined") {
      // TODO: Implement analytics tracking
      console.log("Upgrade modal opened", { source, preSelectedPlan });
    }
  }, [isOpen, source, preSelectedPlan]);

  if (!isOpen) return null;

  const handlePlanClick = (planId: string) => {
    // TODO: Redirect to Stripe Checkout
    console.log("Plan clicked:", planId, { source });
    // For now, just redirect to /planos page
    window.location.href = `/planos?plan=${planId}`;
  };

  const getButtonClasses = (buttonStyle: string) => {
    const baseClasses = "w-full px-6 py-3 rounded-button font-semibold transition-all";

    switch (buttonStyle) {
      case "outline":
        return `${baseClasses} border-2 border-brand-navy text-brand-navy bg-transparent hover:bg-brand-blue-subtle`;
      case "solid":
        return `${baseClasses} bg-brand-navy text-white hover:bg-brand-blue-hover hover:-translate-y-0.5 hover:shadow-lg`;
      case "premium":
        return `${baseClasses} bg-gradient-to-br from-yellow-400 to-yellow-600 text-gray-900 font-bold hover:-translate-y-0.5 hover:shadow-xl`;
      default:
        return `${baseClasses} bg-brand-navy text-white`;
    }
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
        className="relative bg-surface-0 rounded-card shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-surface-0 border-b border-border px-6 py-4 flex items-center justify-between z-10">
          <h2 id="upgrade-modal-title" className="text-2xl font-bold text-ink">
            Escolha seu plano
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-1 rounded-full transition-colors"
            aria-label="Fechar modal"
          >
            <svg
              className="w-6 h-6 text-ink-secondary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Plan cards grid */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PLANS.map((plan) => {
              const isPreSelected = preSelectedPlan === plan.id;

              return (
                <div
                  key={plan.id}
                  className={`
                    relative p-6 rounded-card border-2 transition-all
                    ${plan.popular ? "scale-105 shadow-xl border-brand-blue" : "border-border"}
                    ${isPreSelected ? "ring-4 ring-brand-blue/30 animate-pulse-border" : ""}
                  `}
                >
                  {/* Popular badge */}
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-brand-blue text-white text-xs font-semibold rounded-full">
                      ⭐ Mais Popular
                    </div>
                  )}

                  {/* Plan name and price */}
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-ink mb-2">{plan.name}</h3>
                    <p className="text-3xl font-bold text-brand-navy">{plan.price}</p>
                  </div>

                  {/* Features list */}
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li
                        key={idx}
                        className={`flex items-start gap-2 text-sm ${
                          feature.highlight ? "font-semibold" : ""
                        }`}
                      >
                        <span
                          className={`flex-shrink-0 mt-0.5 ${
                            feature.available ? "text-green-500" : "text-gray-400"
                          }`}
                          aria-hidden="true"
                        >
                          {feature.available ? "✓" : "✗"}
                        </span>
                        <span className={feature.available ? "text-ink" : "text-ink-muted"}>
                          {feature.text}
                        </span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA button */}
                  <button
                    onClick={() => handlePlanClick(plan.id)}
                    className={getButtonClasses(plan.buttonStyle)}
                  >
                    {plan.buttonText}
                  </button>
                </div>
              );
            })}
          </div>

          {/* Footer tip */}
          <div className="mt-8 p-4 bg-brand-blue-subtle border border-brand-blue/20 rounded-card text-center">
            <p className="text-sm text-ink-secondary">
              💡 <strong>Dica:</strong> Upgrade a qualquer momento sem perder dados
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
