"use client";

import { useEffect, useRef, useState } from "react";

interface Plan {
  id: string;
  name: string;
  description: string;
  max_searches: number | null;
  price_brl: number;
  duration_days: number | null;
}

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  preSelectedPlan?: string;
  source?: string; // Analytics: 'excel_button', 'date_range', 'quota_counter'
}

/**
 * Upgrade modal with plan comparison
 * Now fetches plans dynamically from backend to ensure consistency with /planos page
 * Updated 2026-02-05: Removed hardcoded plans, synced with backend API
 */
export function UpgradeModal({ isOpen, onClose, preSelectedPlan, source }: UpgradeModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // Fetch plans from backend when modal opens
  useEffect(() => {
    if (!isOpen) return;

    const fetchPlans = async () => {
      setLoading(true);
      setError(null);
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
        const res = await fetch(`${backendUrl}/plans`);
        if (!res.ok) throw new Error("Erro ao carregar planos");
        const data = await res.json();
        // Hide free and master from public listing
        setPlans(data.plans.filter((p: Plan) => p.id !== "free" && p.id !== "master"));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar planos");
        setPlans([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, [isOpen]);

  // Track analytics when modal opens
  useEffect(() => {
    if (isOpen && typeof window !== "undefined") {
      console.log("Upgrade modal opened", { source, preSelectedPlan });
    }
  }, [isOpen, source, preSelectedPlan]);

  if (!isOpen) return null;

  const handlePlanClick = (planId: string) => {
    console.log("Plan clicked:", planId, { source });
    window.location.href = `/planos?plan=${planId}`;
  };

  const formatPrice = (val: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val);

  const getPlanLabel = (plan: Plan) => {
    if (plan.duration_days === 30) return "/mês";
    if (plan.duration_days === 365) return "/ano";
    return "";
  };

  const isPopular = (id: string) => id === "monthly" || id === "maquina";

  const getButtonClasses = (popular: boolean, isPreSelected: boolean) => {
    const baseClasses = "w-full px-6 py-3 rounded-button font-semibold transition-all";

    if (popular || isPreSelected) {
      return `${baseClasses} bg-brand-navy text-white hover:bg-brand-blue-hover hover:-translate-y-0.5 hover:shadow-lg`;
    }
    return `${baseClasses} border-2 border-brand-navy text-brand-navy bg-transparent hover:bg-brand-blue-subtle`;
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
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-72 bg-surface-1 rounded-card animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-error mb-4">{error}</p>
              <button
                onClick={() => window.location.href = "/planos"}
                className="text-brand-blue hover:underline"
              >
                Ver planos na página completa
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {plans.map((plan) => {
                const popular = isPopular(plan.id);
                const isPreSelected = preSelectedPlan === plan.id;

                return (
                  <div
                    key={plan.id}
                    className={`
                      relative p-6 rounded-card border-2 transition-all
                      ${popular ? "scale-105 shadow-xl border-brand-blue" : "border-border"}
                      ${isPreSelected ? "ring-4 ring-brand-blue/30" : ""}
                    `}
                  >
                    {/* Popular badge */}
                    {popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-brand-blue text-white text-xs font-semibold rounded-full whitespace-nowrap">
                        Mais Popular
                      </div>
                    )}

                    {/* Plan name and price */}
                    <div className="text-center mb-6">
                      <h3 className="text-xl font-bold text-ink mb-2">{plan.name}</h3>
                      <p className="text-3xl font-bold text-brand-navy">
                        {formatPrice(plan.price_brl)}
                        <span className="text-sm font-normal text-ink-muted">{getPlanLabel(plan)}</span>
                      </p>
                    </div>

                    {/* Features list */}
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 mt-0.5 text-green-500" aria-hidden="true">✓</span>
                        <span className="text-ink">
                          {plan.max_searches ? `${plan.max_searches} buscas/mês` : "Buscas ilimitadas"}
                        </span>
                      </li>
                      <li className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 mt-0.5 text-green-500" aria-hidden="true">✓</span>
                        <span className="text-ink">Todos os setores</span>
                      </li>
                      <li className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 mt-0.5 text-green-500" aria-hidden="true">✓</span>
                        <span className="text-ink">Exportar Excel</span>
                      </li>
                      <li className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 mt-0.5 text-green-500" aria-hidden="true">✓</span>
                        <span className="text-ink">Resumo executivo IA</span>
                      </li>
                      {!plan.max_searches && (
                        <li className="flex items-start gap-2 text-sm font-semibold">
                          <span className="flex-shrink-0 mt-0.5 text-green-500" aria-hidden="true">✓</span>
                          <span className="text-ink">Histórico completo</span>
                        </li>
                      )}
                    </ul>

                    {/* CTA button */}
                    <button
                      onClick={() => handlePlanClick(plan.id)}
                      className={getButtonClasses(popular, isPreSelected)}
                    >
                      Assinar {plan.name}
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* Footer tip */}
          <div className="mt-8 p-4 bg-brand-blue-subtle border border-brand-blue/20 rounded-card text-center">
            <p className="text-sm text-ink-secondary">
              Upgrade a qualquer momento sem perder dados
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
