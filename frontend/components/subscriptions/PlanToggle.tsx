"use client";

import { useState } from "react";

/**
 * PlanToggle Component — GTM-002
 *
 * Toggle for 3 períodos de acesso: Mensal, Semestral, Anual
 * NOT plan tiers — billing periods only.
 */

export type BillingPeriod = 'monthly' | 'semiannual' | 'annual';

export interface PlanToggleProps {
  value: BillingPeriod;
  onChange: (value: BillingPeriod) => void;
  className?: string;
  disabled?: boolean;
  /** STORY-360 AC6: Per-period discount overrides (e.g. { semiannual: 10, annual: 25 }) */
  discounts?: Partial<Record<BillingPeriod, number>>;
}

const DEFAULT_DISCOUNTS: Partial<Record<BillingPeriod, number>> = {
  semiannual: 10,
  annual: 25,
};

function buildBillingOptions(discounts: Partial<Record<BillingPeriod, number>>) {
  return [
    { value: 'monthly' as BillingPeriod, label: 'Mensal' },
    { value: 'semiannual' as BillingPeriod, label: 'Semestral', discount: discounts.semiannual ? `Economize ${discounts.semiannual}%` : undefined },
    { value: 'annual' as BillingPeriod, label: 'Anual', discount: discounts.annual ? `Economize ${discounts.annual}%` : undefined },
  ];
}

export function PlanToggle({
  value,
  onChange,
  className = "",
  disabled = false,
  discounts,
}: PlanToggleProps) {
  const effectiveDiscounts = discounts || DEFAULT_DISCOUNTS;
  const billingOptions = buildBillingOptions(effectiveDiscounts);
  const selectedOption = billingOptions.find(o => o.value === value);

  return (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      {/* Toggle Buttons */}
      <div
        role="radiogroup"
        aria-label="Escolha seu período de acesso"
        className="relative inline-flex items-center bg-surface-1 rounded-full p-1 border border-strong"
      >
        {billingOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={value === option.value}
            aria-label={`${option.label}${option.discount ? ` — ${option.discount}` : ''}`}
            disabled={disabled}
            onClick={() => !disabled && onChange(option.value)}
            className={`
              relative z-10 px-5 py-2 rounded-full text-sm font-semibold
              transition-all duration-300 ease-in-out
              focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
              disabled:cursor-not-allowed disabled:opacity-50
              ${value === option.value
                ? 'text-white bg-brand-navy shadow-md'
                : 'text-ink-secondary hover:text-ink'
              }
            `}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Savings Badge */}
      {selectedOption?.discount && (
        <div
          className="flex items-center gap-2 px-3 py-1.5 bg-success-subtle border border-success rounded-full animate-fade-in"
          role="status"
          aria-live="polite"
        >
          <span className="text-sm font-semibold text-success">
            {selectedOption.discount}
          </span>
        </div>
      )}
    </div>
  );
}
