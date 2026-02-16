"use client";

import { useState } from "react";
import Link from "next/link";
import { useAnalytics } from "../../hooks/useAnalytics";

interface TrialExpiringBannerProps {
  daysRemaining: number;
  onConvert?: () => void;
}

/**
 * Proactive notification banner shown on day 6 of trial (1 day remaining).
 * GTM-010 AC9: In-app banner for trial expiring notification.
 */
export function TrialExpiringBanner({ daysRemaining, onConvert }: TrialExpiringBannerProps) {
  const [dismissed, setDismissed] = useState(false);
  const { trackEvent } = useAnalytics();

  // Only show when 1 day remaining (day 6 of 7-day trial)
  if (dismissed || daysRemaining > 1) return null;

  const handleDismiss = () => {
    setDismissed(true);
    trackEvent("trial_expiring_banner_dismissed", { days_remaining: daysRemaining });
  };

  const handleCTA = () => {
    trackEvent("trial_expiring_banner_cta_clicked", { days_remaining: daysRemaining });
    if (onConvert) {
      onConvert();
    }
  };

  return (
    <div
      role="alert"
      className="mb-4 p-4 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-200 dark:border-amber-800 animate-fade-in"
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-800 flex items-center justify-center">
            <svg className="w-4 h-4 text-amber-600 dark:text-amber-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-amber-800 dark:text-amber-200 text-sm">
              Seu acesso ao SmartLic expira amanhã.
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
              Continue tendo vantagem competitiva a partir de R$ 1.599/mês.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {onConvert ? (
            <button
              onClick={handleCTA}
              className="px-4 py-2 text-sm font-semibold rounded-lg bg-brand-navy text-white hover:bg-brand-blue-hover transition-colors whitespace-nowrap"
            >
              Continuar tendo vantagem
            </button>
          ) : (
            <Link
              href="/planos"
              className="px-4 py-2 text-sm font-semibold rounded-lg bg-brand-navy text-white hover:bg-brand-blue-hover transition-colors whitespace-nowrap"
            >
              Continuar tendo vantagem
            </Link>
          )}
          <button
            onClick={handleDismiss}
            className="p-1 text-amber-600 dark:text-amber-400 hover:text-amber-800 dark:hover:text-amber-200 transition-colors"
            aria-label="Dispensar"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
