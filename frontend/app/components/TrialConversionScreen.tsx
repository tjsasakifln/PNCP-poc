"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAnalytics } from "../../hooks/useAnalytics";
import { GlassCard } from "./ui/GlassCard";
import { PlanToggle, BillingPeriod } from "../../components/subscriptions/PlanToggle";

interface TrialValue {
  total_opportunities: number;
  total_value: number;
  searches_executed: number;
  avg_opportunity_value: number;
  top_opportunity: { title: string; value: number } | null;
}

interface TrialConversionScreenProps {
  trialValue: TrialValue | null;
  onClose: () => void;
  loading?: boolean;
}

const formatCurrency = (val: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);

const BILLING_PRICES: Record<BillingPeriod, { monthly: number; label: string; subtitle: string }> = {
  monthly: { monthly: 1999, label: "Mensal", subtitle: "Avaliação constante de oportunidades" },
  semiannual: { monthly: 1799, label: "Semestral", subtitle: "Consistência competitiva" },
  annual: { monthly: 1599, label: "Anual", subtitle: "Domínio do mercado" },
};

export function TrialConversionScreen({ trialValue, onClose, loading }: TrialConversionScreenProps) {
  const router = useRouter();
  const { trackEvent } = useAnalytics();
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly");

  useEffect(() => {
    trackEvent("trial_conversion_screen_viewed", {
      total_opportunities: trialValue?.total_opportunities ?? 0,
      total_value: trialValue?.total_value ?? 0,
    });
  }, []);

  const handleSelectPlan = (period: BillingPeriod) => {
    trackEvent("trial_conversion_cta_clicked", { billing_period: period });
    router.push(`/planos?billing=${period}`);
  };

  const handleClose = () => {
    trackEvent("trial_conversion_dismissed");
    router.push("/planos");
  };

  // Handle Escape key → redirect to /planos (AC8)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        handleClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const hasData = trialValue && trialValue.total_opportunities > 0;

  return (
    <div className="fixed inset-0 z-[60] bg-gradient-to-br from-[var(--surface-0)] to-[var(--surface-1)] flex items-center justify-center p-4 overflow-y-auto">
      {/* Close button */}
      <button
        onClick={handleClose}
        className="fixed top-4 right-4 z-[61] p-2 rounded-full bg-surface-1 hover:bg-surface-2 text-ink-muted hover:text-ink transition-colors"
        aria-label="Fechar"
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <GlassCard variant="pricing" hoverable={false} className="max-w-4xl w-full p-8 md:p-12 my-8">
        {/* Hero */}
        <h1 className="text-3xl md:text-4xl font-bold font-display text-center mb-2 text-ink">
          {hasData ? "Veja o que você descobriu em 7 dias" : "Descubra oportunidades para seu negócio"}
        </h1>
        <p className="text-center text-ink-secondary mb-8">
          {hasData
            ? "O SmartLic já trabalhou para você. Continue tendo vantagem."
            : "Configure seu perfil e encontre oportunidades adequadas ao seu negócio."}
        </p>

        {/* Stats Grid */}
        {loading ? (
          <div className="grid md:grid-cols-3 gap-6 my-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-surface-1 rounded-2xl p-6 animate-pulse">
                <div className="h-4 bg-surface-2 rounded w-2/3 mb-3" />
                <div className="h-8 bg-surface-2 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : hasData ? (
          <div className="grid md:grid-cols-3 gap-6 my-8">
            <div className="bg-surface-1 rounded-2xl p-6 text-center">
              <p className="text-sm text-ink-secondary mb-1">Oportunidades Analisadas</p>
              <p className="text-3xl font-bold text-ink">{trialValue!.total_opportunities}</p>
            </div>
            <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 rounded-2xl p-6 text-center border border-emerald-200 dark:border-emerald-800">
              <p className="text-sm text-emerald-700 dark:text-emerald-300 mb-1">Valor Total em Contratos</p>
              <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                {formatCurrency(trialValue!.total_value)}
              </p>
            </div>
            <div className="bg-surface-1 rounded-2xl p-6 text-center">
              <p className="text-sm text-ink-secondary mb-1">Análises Executadas</p>
              <p className="text-3xl font-bold text-ink">{trialValue!.searches_executed}/3</p>
            </div>
          </div>
        ) : null}

        {/* Anchor Message */}
        <div className="bg-gradient-to-r from-brand-navy/5 to-brand-blue/5 dark:from-brand-navy/20 dark:to-brand-blue/20 border border-brand-navy/10 dark:border-brand-blue/20 rounded-xl p-6 mb-8 text-center">
          <p className="text-lg md:text-xl font-semibold text-ink">
            Uma única licitação ganha pode pagar o sistema por um ano inteiro.
          </p>
        </div>

        {/* Billing Period Toggle */}
        <div className="mb-6">
          <PlanToggle value={billingPeriod} onChange={setBillingPeriod} />
        </div>

        {/* Billing Period Cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {(["monthly", "semiannual", "annual"] as BillingPeriod[]).map((period) => {
            const price = BILLING_PRICES[period];
            const isSelected = billingPeriod === period;
            const discount = period === "semiannual" ? "10%" : period === "annual" ? "20%" : null;

            return (
              <button
                key={period}
                onClick={() => setBillingPeriod(period)}
                className={`
                  relative rounded-2xl p-6 text-left transition-all border-2
                  ${isSelected
                    ? "border-brand-navy bg-brand-navy/5 dark:bg-brand-navy/20 shadow-lg"
                    : "border-transparent bg-surface-1 hover:border-brand-navy/30"
                  }
                `}
              >
                {discount && (
                  <span className="absolute -top-2.5 right-4 px-2 py-0.5 text-xs font-bold bg-success text-white rounded-full">
                    -{discount}
                  </span>
                )}
                <p className="text-sm font-medium text-ink-secondary mb-1">{price.label}</p>
                <p className="text-2xl font-bold text-ink">
                  {formatCurrency(price.monthly)}
                  <span className="text-sm font-normal text-ink-muted">/mês</span>
                </p>
                <p className="text-xs text-ink-secondary mt-1">{price.subtitle}</p>
              </button>
            );
          })}
        </div>

        {/* Primary CTA */}
        <button
          onClick={() => handleSelectPlan(billingPeriod)}
          className="w-full px-6 py-4 rounded-xl font-semibold text-lg bg-brand-navy text-white hover:bg-brand-blue-hover hover:-translate-y-0.5 hover:shadow-xl transition-all"
        >
          Continuar com SmartLic Pro — {formatCurrency(BILLING_PRICES[billingPeriod].monthly)}/mês
        </button>

        {/* Confidence Footer */}
        <div className="mt-6 text-center space-y-2">
          <p className="text-sm text-ink-secondary">
            Seu concorrente pode estar usando SmartLic agora. Continue tendo vantagem.
          </p>
          <p className="text-xs text-ink-muted">
            Cancele quando quiser. Sem contrato de fidelidade.
          </p>
        </div>
      </GlassCard>
    </div>
  );
}
