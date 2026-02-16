"use client";

import { useState } from "react";

/**
 * PlanToggle Component — GTM-002
 *
 * Toggle for 3 "níveis de compromisso": Mensal, Semestral, Anual
 * NOT plan tiers — billing periods only.
 */

export type BillingPeriod = 'monthly' | 'semiannual' | 'annual';

export interface PlanToggleProps {
  value: BillingPeriod;
  onChange: (value: BillingPeriod) => void;
  className?: string;
  disabled?: boolean;
}

const BILLING_OPTIONS: { value: BillingPeriod; label: string; discount?: string }[] = [
  { value: 'monthly', label: 'Mensal' },
  { value: 'semiannual', label: 'Semestral', discount: 'Economize 10%' },
  { value: 'annual', label: 'Anual', discount: 'Economize 20%' },
];

export function PlanToggle({
  value,
  onChange,
  className = "",
  disabled = false,
}: PlanToggleProps) {
  const selectedOption = BILLING_OPTIONS.find(o => o.value === value);

  return (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      {/* Toggle Buttons */}
      <div
        role="radiogroup"
        aria-label="Escolha seu nível de compromisso"
        className="relative inline-flex items-center bg-surface-1 rounded-full p-1 border border-strong"
      >
        {BILLING_OPTIONS.map((option) => (
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
