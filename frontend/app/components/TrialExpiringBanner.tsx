"use client";

import { useState } from "react";
import Link from "next/link";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useExperiments } from "../../hooks/useExperiments";

interface TrialExpiringBannerProps {
  daysRemaining: number;
  onConvert?: () => void;
}

/**
 * Proactive notification banner shown from day 8 of 14-day trial (6 days remaining).
 * GTM-010 AC9 + STORY-319 AC8: In-app banner for trial expiring notification.
 */
export function TrialExpiringBanner({ daysRemaining, onConvert }: TrialExpiringBannerProps) {
  const [dismissed, setDismissed] = useState(false);
  const { trackEvent } = useAnalytics();
  const { getExperimentProperties } = useExperiments();

  // STORY-319 AC8: Show from day 8 (6 days remaining) of 14-day trial
  if (dismissed || daysRemaining > 6) return null;

  // COPY-369 AC1: Dynamic copy based on daysRemaining
  const expiryMessage =
    daysRemaining === 0
      ? "Seu acesso completo ao SmartLic termina hoje."
      : daysRemaining === 1
        ? "Seu acesso completo ao SmartLic termina amanhã."
        : `Seu acesso completo ao SmartLic termina em ${daysRemaining} dias.`;

  const handleDismiss = () => {
    setDismissed(true);
    trackEvent("trial_expiring_banner_dismissed", { days_remaining: daysRemaining, ...getExperimentProperties() });
  };

  const handleCTA = () => {
    trackEvent("trial_expiring_banner_cta_clicked", { days_remaining: daysRemaining, ...getExperimentProperties() });
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
              {expiryMessage}
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
              Continue com acesso a todas as funcionalidades. Planos a partir de R$ 297/mês.
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
