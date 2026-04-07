"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import FocusTrap from "focus-trap-react";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useExperiments } from "../../hooks/useExperiments";
import { useAuth } from "../components/AuthProvider";
import { usePlans } from "../../hooks/usePlans";
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
  monthly: { monthly: 397, label: "Mensal", subtitle: "Avaliação constante de oportunidades" },
  semiannual: { monthly: 357, label: "Semestral", subtitle: "Consistência competitiva" },
  annual: { monthly: 297, label: "Anual", subtitle: "Domínio do mercado" },
};

export function TrialConversionScreen({ trialValue, onClose, loading }: TrialConversionScreenProps) {
  const router = useRouter();
  const { trackEvent } = useAnalytics();
  const { getExperimentProperties } = useExperiments();
  const { session } = useAuth();
  const { plans } = usePlans();
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>("monthly");
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  // P0 zero-churn: Dynamic prices from backend, fallback to hardcoded
  const dynamicPrices = useMemo(() => {
    if (!plans) return BILLING_PRICES;
    const proPlan = Array.isArray(plans) ? plans.find((p: { id: string }) => p.id === "smartlic_pro") : null;
    if (!proPlan?.billing_periods) return BILLING_PRICES;
    const bp = proPlan.billing_periods as Record<string, { price_cents?: number }>;
    const result = { ...BILLING_PRICES };
    if (bp.monthly?.price_cents) result.monthly = { ...result.monthly, monthly: bp.monthly.price_cents / 100 };
    if (bp.semiannual?.price_cents) result.semiannual = { ...result.semiannual, monthly: bp.semiannual.price_cents / 100 };
    if (bp.annual?.price_cents) result.annual = { ...result.annual, monthly: bp.annual.price_cents / 100 };
    return result;
  }, [plans]);

  useEffect(() => {
    trackEvent("trial_conversion_screen_viewed", {
      total_opportunities: trialValue?.total_opportunities ?? 0,
      total_value: trialValue?.total_value ?? 0,
      ...getExperimentProperties(),
    });
  }, []);

  // P0 zero-churn: Direct checkout — skip /planos redirect (1-click conversion)
  const handleSelectPlan = async (period: BillingPeriod) => {
    trackEvent("trial_conversion_cta_clicked", { billing_period: period, ...getExperimentProperties() });

    if (!session?.access_token) {
      router.push(`/planos?billing=${period}`);
      return;
    }

    setCheckoutLoading(true);
    try {
      const res = await fetch(
        `/api/billing?endpoint=checkout&plan_id=smartlic_pro&billing_period=${period}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${session.access_token}` },
        }
      );
      if (!res.ok) throw new Error("checkout_failed");
      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
    } catch {
      // Graceful fallback: redirect to /planos if direct checkout fails
    }
    setCheckoutLoading(false);
    router.push(`/planos?billing=${period}`);
  };

  const handleClose = () => {
    trackEvent("trial_conversion_dismissed", getExperimentProperties());
    router.push(`/planos?billing=${billingPeriod}`);
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
    <FocusTrap
      focusTrapOptions={{
        escapeDeactivates: true,
        onDeactivate: handleClose,
        allowOutsideClick: true,
        returnFocusOnDeactivate: true,
        tabbableOptions: { displayCheck: "none" },
      }}
    >
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
          {hasData ? "Veja o que você descobriu no período de avaliação" : "Descubra oportunidades para seu negócio"}
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
              <p className="text-3xl font-bold text-ink">{trialValue!.searches_executed}</p>
            </div>
          </div>
        ) : null}

        {/* Zero-churn P2 §4.2: Trial vs Paid comparison table */}
        {hasData && (
          <div className="overflow-hidden rounded-xl border border-[var(--border)] mb-8">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-surface-1">
                  <th className="text-left px-4 py-3 font-medium text-ink-secondary">Recurso</th>
                  <th className="text-center px-4 py-3 font-medium text-ink-secondary">Trial (Agora)</th>
                  <th className="text-center px-4 py-3 font-medium text-brand-navy">Pro</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                <tr>
                  <td className="px-4 py-2.5 text-ink">Oportunidades analisadas</td>
                  <td className="px-4 py-2.5 text-center text-ink-secondary">{trialValue!.total_opportunities}</td>
                  <td className="px-4 py-2.5 text-center font-semibold text-brand-navy">Ilimitado</td>
                </tr>
                <tr>
                  <td className="px-4 py-2.5 text-ink">Pipeline</td>
                  <td className="px-4 py-2.5 text-center text-ink-secondary">15 itens</td>
                  <td className="px-4 py-2.5 text-center font-semibold text-brand-navy">Ilimitado</td>
                </tr>
                <tr>
                  <td className="px-4 py-2.5 text-ink">Alertas</td>
                  <td className="px-4 py-2.5 text-center text-ink-muted">—</td>
                  <td className="px-4 py-2.5 text-center font-semibold text-brand-navy">Automaticos</td>
                </tr>
                <tr>
                  <td className="px-4 py-2.5 text-ink">Relatorios</td>
                  <td className="px-4 py-2.5 text-center text-ink-secondary">Resumidos</td>
                  <td className="px-4 py-2.5 text-center font-semibold text-brand-navy">Completos + Excel</td>
                </tr>
                <tr>
                  <td className="px-4 py-2.5 text-ink">Historico</td>
                  <td className="px-4 py-2.5 text-center text-ink-secondary">30 dias</td>
                  <td className="px-4 py-2.5 text-center font-semibold text-brand-navy">Ilimitado</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* Zero-churn P2 §4.2: Personalized ROI anchor message */}
        <div className="bg-gradient-to-r from-brand-navy/5 to-brand-blue/5 dark:from-brand-navy/20 dark:to-brand-blue/20 border border-brand-navy/10 dark:border-brand-blue/20 rounded-xl p-6 mb-8 text-center">
          <p className="text-lg md:text-xl font-semibold text-ink">
            {hasData && trialValue!.total_value > 0
              ? `Você analisou ${formatCurrency(trialValue!.total_value)} em oportunidades. Uma vitória de 1% = ${formatCurrency(trialValue!.total_value * 0.01)} — ${Math.max(1, Math.round(trialValue!.total_value * 0.01 / 3564))}x o custo anual.`
              : "Uma única licitação ganha pode pagar o sistema por um ano inteiro."}
          </p>
        </div>

        {/* Billing Period Toggle */}
        <div className="mb-6">
          <PlanToggle value={billingPeriod} onChange={setBillingPeriod} />
        </div>

        {/* Billing Period Cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {(["monthly", "semiannual", "annual"] as BillingPeriod[]).map((period) => {
            const price = dynamicPrices[period];
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

        {/* Zero-churn P1 §9 + P2 §9: Social proof + satisfaction guarantee */}
        <div className="flex flex-wrap items-center justify-center gap-4 mt-4 mb-6 text-sm text-[var(--ink-secondary)]">
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Dados oficiais PNCP
          </span>
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Cancele quando quiser
          </span>
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Sem fidelidade
          </span>
          <span className="flex items-center gap-1.5">
            <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5C18.577 6.44 19 8.027 19 9.7c0 5.009-3.667 9.132-8.44 9.878a.75.75 0 01-.12.002.75.75 0 01-.12-.002C5.667 18.832 2 14.709 2 9.7c0-1.673.423-3.26 1.166-4.701zM10 5a1 1 0 011 1v3.586l2.207 2.207a1 1 0 01-1.414 1.414l-2.5-2.5A1 1 0 019 10V6a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Garantia 30 dias
          </span>
        </div>

        {/* Primary CTA */}
        <button
          onClick={() => handleSelectPlan(billingPeriod)}
          disabled={checkoutLoading}
          className="w-full px-6 py-4 rounded-xl font-semibold text-lg bg-brand-navy text-white hover:bg-brand-blue-hover hover:-translate-y-0.5 hover:shadow-xl transition-all disabled:opacity-60 disabled:cursor-wait"
        >
          {checkoutLoading
            ? "Redirecionando para pagamento..."
            : `Continuar com SmartLic Pro — ${formatCurrency(dynamicPrices[billingPeriod].monthly)}/mês`}
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
    </FocusTrap>
  );
}
