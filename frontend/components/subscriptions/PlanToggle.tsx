"use client";

import { useState } from "react";

/**
 * PlanToggle Component
 *
 * Toggle component for switching between monthly and annual billing periods
 * STORY-171 AC1: Toggle UI - Seleção Mensal/Anual
 *
 * Features:
 * - Estados: "Mensal" (default) e "Anual"
 * - Badge "💰 Economize 20%" quando anual
 * - Animação suave (transition CSS 300ms)
 * - Acessível via teclado (Space/Enter)
 * - ARIA compliant
 * - Responsive (mobile + desktop)
 */

export type BillingPeriod = 'monthly' | 'annual';

export interface PlanToggleProps {
  value: BillingPeriod;
  onChange: (value: BillingPeriod) => void;
  className?: string;
  disabled?: boolean;
}

export function PlanToggle({
  value,
  onChange,
  className = "",
  disabled = false,
}: PlanToggleProps) {
  const [focused, setFocused] = useState(false);

  const handleToggle = () => {
    if (disabled) return;
    const newValue = value === 'monthly' ? 'annual' : 'monthly';
    onChange(newValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      {/* Toggle Switch */}
      <div
        role="radiogroup"
        aria-label="Alternar entre plano mensal e anual"
        className="relative inline-flex items-center bg-surface-1 rounded-full p-1 border border-strong"
      >
        {/* Monthly Option */}
        <button
          type="button"
          role="radio"
          aria-checked={value === 'monthly'}
          aria-label="Plano Mensal"
          disabled={disabled}
          onClick={() => !disabled && onChange('monthly')}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className={`
            relative z-10 px-6 py-2 rounded-full text-sm font-semibold
            transition-all duration-300 ease-in-out
            focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
            disabled:cursor-not-allowed disabled:opacity-50
            ${value === 'monthly'
              ? 'text-white bg-brand-navy shadow-md'
              : 'text-ink-secondary hover:text-ink'
            }
          `}
        >
          Mensal
        </button>

        {/* Annual Option */}
        <button
          type="button"
          role="radio"
          aria-checked={value === 'annual'}
          aria-label="Plano Anual"
          disabled={disabled}
          onClick={() => !disabled && onChange('annual')}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className={`
            relative z-10 px-6 py-2 rounded-full text-sm font-semibold
            transition-all duration-300 ease-in-out
            focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
            disabled:cursor-not-allowed disabled:opacity-50
            ${value === 'annual'
              ? 'text-white bg-brand-navy shadow-md'
              : 'text-ink-secondary hover:text-ink'
            }
          `}
        >
          Anual
        </button>
      </div>

      {/* Savings Badge (only shown when annual selected) */}
      {value === 'annual' && (
        <div
          className="flex items-center gap-2 px-3 py-1.5 bg-success-subtle border border-success rounded-full animate-fade-in"
          role="status"
          aria-live="polite"
        >
          <span className="text-lg" aria-hidden="true">💰</span>
          <span className="text-sm font-semibold text-success">
            Economize 20% pagando anual
          </span>
        </div>
      )}
    </div>
  );
}
