"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { useAnalytics } from "../../hooks/useAnalytics";
import { safeSetItem } from "../../lib/storage";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type UpsellVariant =
  | "post-search"
  | "post-download"
  | "post-pipeline"
  | "dashboard"
  | "quota";

export interface UpsellContextData {
  /** Number of opportunities found (post-search) */
  opportunities?: number;
  /** Formatted total value analysed (dashboard) */
  valor?: string;
  /** Quota limit label, e.g. "47/50" (quota) */
  usageLabel?: string;
  /** Numeric quota percentage 0-100 (quota) */
  usagePct?: number;
  /** Monthly export limit (post-download) */
  exportLimit?: number;
  /** Pipeline item limit (post-pipeline) */
  pipelineLimit?: number;
}

interface TrialUpsellCTAProps {
  variant: UpsellVariant;
  contextData?: UpsellContextData;
  /** User plan_id — only renders when "free_trial" */
  planId: string | null | undefined;
  /** Subscription status — hides when trial expired (TrialConversionScreen handles that) */
  subscriptionStatus?: string;
}

// ---------------------------------------------------------------------------
// Copy per variant
// ---------------------------------------------------------------------------

function getVariantCopy(variant: UpsellVariant, ctx: UpsellContextData) {
  switch (variant) {
    case "post-search":
      return {
        message: `Voce encontrou ${ctx.opportunities ?? 0} oportunidades! Com o SmartLic Pro, analise ilimitada.`,
        cta: "Ver planos",
      };
    case "post-download":
      return {
        message: `Relatorio exportado! No plano Pro, exporte ate ${ctx.exportLimit ?? 1000} por mes.`,
        cta: "Assinar SmartLic Pro",
      };
    case "post-pipeline":
      return {
        message: `Pipeline ativo! Com o Pro, acompanhe ate ${ctx.pipelineLimit ?? 1000} oportunidades simultaneas.`,
        cta: "Conhecer plano Pro",
      };
    case "dashboard":
      return {
        message: `Voce ja analisou R$${ctx.valor ?? "0"} em oportunidades. Continue sem limites.`,
        cta: "Assinar agora",
      };
    case "quota":
      return {
        message: `Voce usou ${ctx.usageLabel ?? "?/?"}  buscas. Atualize para continuar sem interrupcao.`,
        cta: "Atualizar plano",
      };
  }
}

// ---------------------------------------------------------------------------
// Frequency helpers (AC7 + dismiss logic)
// ---------------------------------------------------------------------------

const SESSION_KEY = "smartlic_upsell_shown_count";
const DISMISS_PREFIX = "smartlic_upsell_dismiss_";
const DISMISS_TTL = 24 * 60 * 60 * 1000; // 24 hours

function getSessionCount(): number {
  if (typeof window === "undefined") return 0;
  return parseInt(sessionStorage.getItem(SESSION_KEY) || "0", 10);
}

function incrementSessionCount(): void {
  if (typeof window === "undefined") return;
  const current = getSessionCount();
  sessionStorage.setItem(SESSION_KEY, String(current + 1));
}

function isDismissed(variant: UpsellVariant): boolean {
  if (typeof window === "undefined") return false;
  try {
    const ts = localStorage.getItem(DISMISS_PREFIX + variant);
    if (!ts) return false;
    return Date.now() - parseInt(ts, 10) < DISMISS_TTL;
  } catch {
    return false;
  }
}

function setDismissed(variant: UpsellVariant): void {
  if (typeof window === "undefined") return;
  try {
    safeSetItem(DISMISS_PREFIX + variant, String(Date.now()));
  } catch {
    // ignore
  }
}

// ---------------------------------------------------------------------------
// Backend CTA tracking (AC11 — Prometheus counters for admin dashboard)
// ---------------------------------------------------------------------------

function reportCTAEvent(action: string, variant: string): void {
  if (typeof window === "undefined") return;
  try {
    fetch("/api/analytics?endpoint=track-cta", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, variant }),
    }).catch(() => {}); // fire-and-forget
  } catch {
    // ignore
  }
}

// ---------------------------------------------------------------------------
// Styles per variant
// ---------------------------------------------------------------------------

function getVariantStyles(variant: UpsellVariant) {
  switch (variant) {
    case "quota":
      return {
        container:
          "bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800",
        text: "text-amber-800 dark:text-amber-200",
        cta: "bg-amber-600 hover:bg-amber-700 text-white",
        icon: "text-amber-600 dark:text-amber-400",
      };
    case "post-search":
      return {
        container:
          "bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-200 dark:border-emerald-800",
        text: "text-emerald-800 dark:text-emerald-200",
        cta: "bg-[var(--brand-navy)] hover:bg-[var(--brand-blue)] text-white",
        icon: "text-emerald-600 dark:text-emerald-400",
      };
    default:
      return {
        container:
          "bg-[var(--brand-blue-subtle)] border border-[var(--border-accent)]",
        text: "text-[var(--ink)]",
        cta: "bg-[var(--brand-navy)] hover:bg-[var(--brand-blue)] text-white",
        icon: "text-[var(--brand-blue)]",
      };
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TrialUpsellCTA({
  variant,
  contextData = {},
  planId,
  subscriptionStatus,
}: TrialUpsellCTAProps) {
  const { trackEvent } = useAnalytics();
  const [visible, setVisible] = useState(false);

  // AC6: Only render for active trial users (not expired — TrialConversionScreen handles that)
  const isTrialActive =
    planId === "free_trial" && subscriptionStatus !== "expired";

  // AC7: Quota variant always shows (functional, not upsell). Others limited to 1/session.
  const isQuota = variant === "quota";

  const shouldShow = useMemo(() => {
    if (!isTrialActive) return false;
    if (isDismissed(variant)) return false;
    if (!isQuota && getSessionCount() >= 1) return false;
    return true;
  }, [isTrialActive, variant, isQuota]);

  // Mark as shown + track
  useEffect(() => {
    if (shouldShow && !visible) {
      setVisible(true);
      if (!isQuota) {
        incrementSessionCount();
      }
      trackEvent("trial_upsell_shown", { variant, ...contextData });
      reportCTAEvent("shown", variant);
    }
  }, [shouldShow]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDismiss = useCallback(() => {
    setDismissed(variant);
    setVisible(false);
    trackEvent("trial_upsell_dismissed", { variant });
    reportCTAEvent("dismissed", variant);
  }, [variant, trackEvent]);

  const handleClick = useCallback(() => {
    trackEvent("trial_upsell_clicked", { variant, ...contextData });
    reportCTAEvent("clicked", variant);
  }, [variant, contextData, trackEvent]);

  if (!visible) return null;

  const copy = getVariantCopy(variant, contextData);
  const styles = getVariantStyles(variant);

  return (
    <div
      className={`rounded-card p-4 flex items-center justify-between gap-3 ${styles.container}`}
      data-testid={`trial-upsell-${variant}`}
      role="complementary"
      aria-label="Oferta de upgrade"
    >
      <div className="flex items-center gap-3 min-w-0">
        {/* Icon */}
        <span className={`flex-shrink-0 ${styles.icon}`}>
          {variant === "quota" ? (
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          ) : (
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          )}
        </span>

        {/* Copy */}
        <p className={`text-sm ${styles.text}`}>{copy.message}</p>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {/* CTA */}
        <Link
          href="/planos"
          onClick={handleClick}
          className={`px-4 py-1.5 text-sm font-medium rounded-button transition-colors whitespace-nowrap ${styles.cta}`}
          data-testid={`trial-upsell-${variant}-cta`}
        >
          {copy.cta}
        </Link>

        {/* Dismiss */}
        <button
          onClick={handleDismiss}
          className="p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          aria-label="Fechar"
          data-testid={`trial-upsell-${variant}-dismiss`}
        >
          <svg
            className="w-4 h-4 text-[var(--ink-muted)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
