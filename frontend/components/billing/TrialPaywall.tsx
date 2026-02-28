"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import { useAnalytics } from "../../hooks/useAnalytics";

/**
 * STORY-320 AC6: Trial paywall overlay with blur effect.
 *
 * Semi-transparent overlay shown over blurred content in limited_access phase.
 * "Continue com preview" dismisses for 1 hour (sessionStorage).
 */

interface TrialPaywallProps {
  /** Number of additional results behind paywall */
  additionalCount: number;
  /** Tracking context */
  context?: string;
}

const DISMISS_KEY = "smartlic_paywall_dismiss";
const DISMISS_TTL = 3_600_000; // 1 hour

function isDismissed(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const ts = sessionStorage.getItem(DISMISS_KEY);
    if (!ts) return false;
    return Date.now() - parseInt(ts, 10) < DISMISS_TTL;
  } catch {
    return false;
  }
}

export function TrialPaywall({ additionalCount, context = "search" }: TrialPaywallProps) {
  const { trackEvent } = useAnalytics();
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (isDismissed()) {
      setDismissed(true);
    } else {
      trackEvent("trial_paywall_shown", { context, additional: additionalCount });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDismiss = useCallback(() => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem(DISMISS_KEY, String(Date.now()));
    }
    setDismissed(true);
    trackEvent("trial_paywall_dismissed", { context });
  }, [context, trackEvent]);

  const handleClick = useCallback(() => {
    trackEvent("trial_paywall_clicked", { context, additional: additionalCount });
  }, [context, additionalCount, trackEvent]);

  if (dismissed) return null;

  return (
    <div
      className="absolute inset-0 z-20 flex items-center justify-center bg-white/60 dark:bg-gray-900/70 backdrop-blur-sm rounded-card"
      data-testid="trial-paywall-overlay"
      role="dialog"
      aria-label="Paywall de trial"
    >
      <div className="text-center max-w-md px-6 py-8">
        {/* Lock icon */}
        <div className="mx-auto w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2">
          Desbloqueie {additionalCount} resultados adicionais
        </h3>
        <p className="text-sm text-[var(--text-secondary)] mb-6">
          Assine o SmartLic Pro para acessar todos os resultados, exportar Excel completo e pipeline ilimitado.
        </p>

        <div className="flex flex-col gap-3">
          <Link
            href="/planos"
            onClick={handleClick}
            className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-button hover:from-blue-700 hover:to-purple-700 transition-all text-center"
            data-testid="trial-paywall-cta"
          >
            Assinar SmartLic Pro
          </Link>
          <button
            onClick={handleDismiss}
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            data-testid="trial-paywall-dismiss"
          >
            Continuar com preview
          </button>
        </div>
      </div>
    </div>
  );
}
