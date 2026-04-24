import { formatCurrency } from '@/lib/copy/roi';
import { Button } from "../../../components/ui/button";
import type { BillingPeriod } from "../../../components/subscriptions/PlanToggle";

interface PricingInfo {
  monthly: number;
  total: number;
  period: string;
  discount?: number;
}

interface Feature {
  text: string;
  detail: string;
}

interface PlanConsultoriaCardProps {
  pricing: Record<BillingPeriod, PricingInfo>;
  billingPeriod: BillingPeriod;
  features: Feature[];
  isConsultoriaLead: boolean;
  checkoutLoading: boolean;
  onCheckout: () => void;
  couponDiscountPercent?: number;
}

export function PlanConsultoriaCard({
  pricing,
  billingPeriod,
  features,
  isConsultoriaLead,
  checkoutLoading,
  onCheckout,
  couponDiscountPercent,
}: PlanConsultoriaCardProps) {
  const currentPricing = pricing[billingPeriod];
  const discountedMonthly = couponDiscountPercent
    ? currentPricing.monthly * (1 - couponDiscountPercent / 100)
    : null;

  return (
    <div className="mt-16 max-w-lg mx-auto">
      <div className="text-center mb-6">
        {isConsultoriaLead && (
          <span className="inline-block mb-4 px-3 py-1 bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400 text-sm font-semibold rounded-full">
            Recomendado para consultorias
          </span>
        )}
        <h2 className="text-2xl font-bold text-[var(--ink)]">Para Consultorias e Assessorias</h2>
        <p className="text-sm text-[var(--ink-secondary)] mt-1">
          Gerencie sua equipe e consolide resultados em uma conta
        </p>
      </div>
      <div className="backdrop-blur-xl bg-white/50 dark:bg-gray-900/40 border-2 border-amber-500 rounded-card p-8 shadow-gem-amethyst">
        {/* Plan Name */}
        <div className="text-center mb-6">
          <div className="flex items-center justify-center gap-2 mb-1">
            <h3 className="text-2xl font-bold text-[var(--ink)]">SmartLic Consultoria</h3>
          </div>
        </div>
        {/* Dynamic Price */}
        <div className="text-center mb-6">
          {discountedMonthly !== null ? (
            <>
              <div className="flex items-center justify-center gap-2 mb-1">
                <span className="text-2xl line-through text-[var(--ink-muted)]" data-testid="consultoria-price-original">
                  {formatCurrency(currentPricing.monthly)}
                </span>
                <span
                  className="inline-block px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400 text-xs font-bold rounded-full"
                  data-testid="consultoria-coupon-pill"
                >
                  -{couponDiscountPercent}%
                </span>
              </div>
              <div className="flex items-baseline justify-center gap-1">
                <span className="text-5xl font-bold text-emerald-600 dark:text-emerald-400" data-testid="consultoria-price-discounted">
                  {formatCurrency(discountedMonthly)}
                </span>
                <span className="text-lg text-[var(--ink-muted)]">/mês</span>
              </div>
            </>
          ) : (
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-5xl font-bold text-amber-700 dark:text-amber-400">
                {formatCurrency(currentPricing.monthly)}
              </span>
              <span className="text-lg text-[var(--ink-muted)]">/mês</span>
            </div>
          )}
          {currentPricing.discount && (
            <div className="mt-2">
              <span className="inline-block px-3 py-1 bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400 text-sm font-semibold rounded-full">
                Economize {currentPricing.discount}%
              </span>
            </div>
          )}
        </div>
        {/* Feature List */}
        <ul className="space-y-3 mb-8">
          {features.map((feature) => (
            <li key={feature.text} className="flex items-start gap-3">
              <span className="flex-shrink-0 mt-0.5 w-5 h-5 rounded-full bg-amber-500 text-white flex items-center justify-center text-xs font-bold">&#10003;</span>
              <div>
                <span className="text-sm font-medium text-[var(--ink)]">{feature.text}</span>
                <span className="block text-xs text-[var(--ink-muted)]">{feature.detail}</span>
              </div>
            </li>
          ))}
        </ul>
        {/* CTA */}
        <Button
          variant="primary"
          size="lg"
          className="w-full text-lg font-bold bg-amber-600 hover:bg-amber-700 hover:shadow-lg"
          onClick={onCheckout}
          disabled={checkoutLoading}
          loading={checkoutLoading}
        >
          {checkoutLoading ? "Processando..." : "Começar com Consultoria"}
        </Button>
        <p className="mt-3 text-center text-xs text-[var(--ink-muted)]">
          Ideal para consultorias com 3-5 colaboradores
        </p>
      </div>
    </div>
  );
}
