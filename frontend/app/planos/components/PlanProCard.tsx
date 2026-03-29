import { formatCurrency } from '@/lib/copy/roi';
import { Button } from "../../../components/ui/button";

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

type UserStatus = "subscriber" | "privileged" | "trial" | "trial_expired" | "anonymous";

interface PlanProCardProps {
  currentPricing: PricingInfo;
  billingPeriod: string;
  features: Feature[];
  userStatus: UserStatus;
  hasFullAccess: boolean;
  checkoutLoading: boolean;
  portalLoading: boolean;
  planLoading?: boolean;
  onCheckout: () => void;
  onManageSubscription: () => void;
}

export function PlanProCard({
  currentPricing,
  billingPeriod,
  features,
  userStatus,
  hasFullAccess,
  checkoutLoading,
  portalLoading,
  planLoading,
  onCheckout,
  onManageSubscription,
}: PlanProCardProps) {
  return (
    <div className="max-w-lg mx-auto">
      <div className="backdrop-blur-xl bg-white/50 dark:bg-gray-900/40 border-2 border-[var(--brand-blue)] rounded-card p-8 shadow-gem-amethyst">
        {/* Plan Name */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-[var(--ink)] mb-1">SmartLic Pro</h2>
          <p className="text-sm text-[var(--ink-secondary)]">
            Inteligência de decisão completa para licitações
          </p>
        </div>

        {/* Dynamic Price */}
        <div className="text-center mb-6">
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-5xl font-bold text-[var(--brand-navy)]">
              {formatCurrency(currentPricing.monthly)}
            </span>
            <span className="text-lg text-[var(--ink-muted)]">/mês</span>
          </div>

          {currentPricing.discount && (
            <div className="mt-2">
              <span className="inline-block px-3 py-1 bg-[var(--success-subtle)] text-[var(--success)] text-sm font-semibold rounded-full">
                Economize {currentPricing.discount}%
              </span>
              {billingPeriod === "semiannual" && (
                <p className="text-xs text-[var(--ink-muted)] mt-1">
                  Cobrado {formatCurrency(currentPricing.total)} a cada 6 meses
                </p>
              )}
              {billingPeriod === "annual" && (
                <p className="text-xs text-[var(--ink-muted)] mt-1">
                  Cobrado {formatCurrency(currentPricing.total)} por ano
                </p>
              )}
            </div>
          )}
        </div>

        {/* Feature List */}
        <ul className="space-y-3 mb-8">
          {features.map((feature) => (
            <li key={feature.text} className="flex items-start gap-3">
              <span className="flex-shrink-0 mt-0.5 w-5 h-5 rounded-full bg-[var(--success)] text-white flex items-center justify-center text-xs font-bold">
                &#10003;
              </span>
              <div>
                <span className="text-sm font-medium text-[var(--ink)]">{feature.text}</span>
                <span className="block text-xs text-[var(--ink-muted)]">{feature.detail}</span>
              </div>
            </li>
          ))}
        </ul>

        {/* CTA Button */}
        <Button
          variant="primary"
          size="lg"
          className="w-full text-lg font-bold hover:shadow-lg"
          onClick={hasFullAccess ? onManageSubscription : onCheckout}
          disabled={checkoutLoading || portalLoading}
          loading={checkoutLoading || portalLoading}
        >
          {checkoutLoading || portalLoading
            ? "Processando..."
            : planLoading
            ? "Carregando..."
            : userStatus === "subscriber"
            ? "Gerenciar assinatura"
            : userStatus === "privileged"
            ? "Ir para análises"
            : userStatus === "trial_expired"
            ? "Continuar com SmartLic"
            : userStatus === "trial"
            ? "Assinar agora"
            : "Começar a filtrar oportunidades"}
        </Button>

        <p className="mt-3 text-center text-xs text-[var(--ink-muted)]">
          Cancele quando quiser. Sem contrato de fidelidade. Pagamento seguro via Stripe.
        </p>

        {/* STORY-273 AC6: Stripe/Security Badge */}
        <div className="mt-4 flex items-center justify-center gap-3 pt-4 border-t border-white/10" data-testid="stripe-security-badge">
          <svg className="h-5 w-auto text-[var(--ink-muted)]" viewBox="0 0 60 25" fill="currentColor" aria-label="Stripe" role="img">
            <path d="M5 10.1c0-.7.6-1 1.5-1 1.3 0 3 .4 4.3 1.1V6.3c-1.5-.6-2.9-.8-4.3-.8C3.2 5.5.8 7.4.8 10.3c0 4.5 6.2 3.8 6.2 5.7 0 .8-.7 1.1-1.7 1.1-1.5 0-3.4-.6-4.9-1.4v3.9c1.7.7 3.3 1 4.9 1 3.4 0 5.7-1.7 5.7-4.6-.1-4.9-6.3-4-6.3-5.9zm11.5-4.3L12.3 7v7.7c0 2.8 2.1 4 4.1 4 1.3 0 2.3-.3 2.8-.6V15c-.5.2-2.9.9-2.9-1.3V9h2.9V5.9h-2.9l.2-.1zm6.8 4.8l-.3-1.6h-3.6v13h4.1v-8.8c1-1.3 2.6-1 3.1-.9V5.9c-.6-.2-2.5-.5-3.3 1.7zm4.3-1.7h4.1v13h-4.1zm0-1.6l4.1-.9V2.6l-4.1.9v3.8zm10 .1c-1.5 0-2.5.7-3 1.2l-.2-1h-3.6v17.4l4.1-.9v-4.2c.6.4 1.4 1 2.8 1 2.8 0 5.4-2.3 5.4-7.2-.1-4.6-2.7-7-5.5-7zm-1 10.7c-.9 0-1.5-.3-1.9-.8v-6c.4-.5 1-.8 1.9-.8 1.5 0 2.5 1.7 2.5 3.8 0 2.2-1 3.8-2.5 3.8zm13.8-10.6c-2.4 0-4 2-4 4.3 0 2.8 1.8 4.3 4.3 4.3 1.2 0 2.2-.3 2.9-.7v-3c-.7.4-1.5.6-2.5.6-1 0-1.9-.3-2-1.5h5c0-.1.1-.8.1-1.2-.1-2.5-1.3-4.8-3.8-4.8zm-1.5 3.5c0-1.1.7-1.6 1.3-1.6.7 0 1.3.5 1.3 1.6h-2.6z" />
          </svg>
          <div className="flex items-center gap-1.5 text-xs text-[var(--ink-muted)]">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span>Pagamento seguro</span>
          </div>
        </div>

        {/* STORY-280 AC4: Payment method icons */}
        <div className="mt-3 flex items-center justify-center gap-4 text-xs text-[var(--ink-muted)]" data-testid="payment-methods">
          <div className="flex items-center gap-1.5">
            <svg className="w-5 h-3.5" viewBox="0 0 24 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
              <rect x="1" y="1" width="22" height="14" rx="2" />
              <line x1="1" y1="6" x2="23" y2="6" />
              <rect x="3" y="9" width="5" height="2" rx="0.5" fill="currentColor" stroke="none" />
            </svg>
            <span>Cartao</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg className="w-5 h-3.5" viewBox="0 0 24 16" fill="currentColor" aria-hidden="true">
              <rect x="1" y="1" width="1.5" height="14" />
              <rect x="4" y="1" width="1" height="14" />
              <rect x="6.5" y="1" width="2" height="14" />
              <rect x="10" y="1" width="1" height="14" />
              <rect x="12.5" y="1" width="1.5" height="14" />
              <rect x="15.5" y="1" width="1" height="14" />
              <rect x="18" y="1" width="2" height="14" />
              <rect x="21.5" y="1" width="1.5" height="14" />
            </svg>
            <span>Boleto</span>
          </div>
        </div>
      </div>
    </div>
  );
}
