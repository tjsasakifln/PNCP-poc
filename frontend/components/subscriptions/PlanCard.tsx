"use client";

import { BillingPeriod } from "./PlanToggle";

/**
 * PlanCard Component
 *
 * Displays subscription plan pricing with dynamic calculation
 * STORY-171 AC2: Cálculo de Preços Dinâmico (20% Discount)
 *
 * Features:
 * - Dynamic price calculation: annual = monthly × 12 × 0.8 (20% discount)
 * - Badge "💰 Economize 20%" when annual
 * - Tooltip showing annual savings
 * - Formatted prices in BRL
 */

export interface PlanCardProps {
  id: string;
  name: string;
  monthlyPrice: number;
  billingPeriod: BillingPeriod;
  features: string[];
  highlighted?: boolean;
  onSelect?: () => void;
  className?: string;
}

export function PlanCard({
  id,
  name,
  monthlyPrice,
  billingPeriod,
  features,
  highlighted = false,
  onSelect,
  className = "",
}: PlanCardProps) {
  // Calculate display price based on billing period (20% annual discount = 2 months free)
  const displayPrice = billingPeriod === 'annual'
    ? monthlyPrice * 12 * 0.8
    : monthlyPrice;

  // Calculate savings for annual plan (20% of yearly total)
  const annualSavings = monthlyPrice * 12 * 0.2;
  const monthlyEquivalent = billingPeriod === 'annual'
    ? displayPrice / 12
    : monthlyPrice;

  // Format price in BRL
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  return (
    <div
      className={`
        relative flex flex-col p-6 bg-surface-0 rounded-card border-2
        transition-all duration-300
        ${highlighted
          ? 'border-brand-blue shadow-lg scale-105'
          : 'border-strong hover:border-brand-blue-subtle hover:shadow-md'
        }
        ${className}
      `}
      data-testid={`plan-card-${id}`}
    >
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-xl font-bold font-display text-ink mb-2">
          {name}
        </h3>

        {/* Pricing */}
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-bold text-brand-navy">
            {formatPrice(displayPrice)}
          </span>
          <span className="text-sm text-ink-muted">
            /{billingPeriod === 'annual' ? 'ano' : 'mês'}
          </span>
        </div>

        {/* Annual Pricing Details */}
        {billingPeriod === 'annual' && (
          <div className="mt-2 space-y-1">
            <div
              className="group relative inline-block"
              role="tooltip"
              aria-label={`Economia anual de ${formatPrice(annualSavings)}`}
            >
              <p className="text-sm text-ink-secondary">
                Equivalente a <strong>{formatPrice(monthlyEquivalent)}/mês</strong>
              </p>

              {/* Tooltip */}
              <div className="invisible group-hover:visible absolute bottom-full left-0 mb-2 w-64 p-3 bg-ink text-white text-xs rounded-card shadow-lg z-50 animate-fade-in">
                <p className="font-semibold mb-1">Detalhes da economia:</p>
                <p>Plano Mensal: {formatPrice(monthlyPrice)}/mês × 12 = {formatPrice(monthlyPrice * 12)}/ano</p>
                <p className="mt-1">Plano Anual: {formatPrice(displayPrice)}/ano ({formatPrice(monthlyEquivalent)}/mês)</p>
                <p className="mt-2 font-bold text-success">
                  Você economiza: {formatPrice(annualSavings)} por ano!
                </p>
              </div>
            </div>

            {/* Savings Badge */}
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-success-subtle border border-success rounded-full">
              <span aria-hidden="true">💰</span>
              <span className="text-xs font-semibold text-success">
                Economize 20%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Features */}
      <ul className="flex-1 space-y-3 mb-6">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start gap-2 text-sm text-ink-secondary">
            <svg
              className="w-5 h-5 text-success mt-0.5 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      {/* CTA Button */}
      {onSelect && (
        <button
          onClick={onSelect}
          className={`
            w-full py-3 px-6 rounded-button font-semibold text-base
            transition-all duration-300
            focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
            ${highlighted
              ? 'bg-brand-navy text-white hover:bg-brand-blue-hover active:bg-brand-blue shadow-md'
              : 'bg-surface-1 text-brand-navy border-2 border-brand-navy hover:bg-brand-navy hover:text-white'
            }
          `}
        >
          Selecionar Plano
        </button>
      )}
    </div>
  );
}
