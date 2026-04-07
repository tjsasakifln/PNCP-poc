"use client";

/**
 * STAB-006 AC2: Humanized error banner for search failures.
 *
 * Uses blue/yellow colors ONLY (never red) per UX guidelines.
 * Provides contextual action buttons: "Tentar novamente" and "Reduzir escopo".
 */

import Link from "next/link";
import type { HumanizedError } from "../../../lib/error-messages";

interface SearchErrorBannerProps {
  /** Humanized error object from useSearch */
  humanizedError: HumanizedError;
  /** Retry countdown seconds (null when not counting) */
  retryCountdown: number | null;
  /** Contextual retry message */
  retryMessage: string | null;
  /** Whether all retry attempts are exhausted */
  retryExhausted: boolean;
  /** Callback for primary action (retry) */
  onRetry: () => void;
  /** Callback for secondary action (reduce scope) */
  onReduceScope?: () => void;
  /** Callback to cancel auto-retry */
  onCancelRetry?: () => void;
}

/**
 * Renders a humanized error banner with action buttons.
 * Blue tone for informational, yellow tone for warnings.
 * Never uses red.
 */
export function SearchErrorBanner({
  humanizedError,
  retryCountdown,
  retryMessage,
  retryExhausted,
  onRetry,
  onReduceScope,
  onCancelRetry,
}: SearchErrorBannerProps) {
  const isBlue = humanizedError.tone === "blue";
  const bgClass = isBlue
    ? "bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800"
    : "bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800";
  const textClass = isBlue
    ? "text-blue-800 dark:text-blue-200"
    : "text-amber-800 dark:text-amber-200";
  const iconColor = isBlue
    ? "text-blue-500 dark:text-blue-400"
    : "text-amber-500 dark:text-amber-400";
  const btnPrimary = isBlue
    ? "bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-700"
    : "bg-amber-100 dark:bg-amber-800 text-amber-700 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-700";

  return (
    <div className={`mb-4 p-4 rounded-lg border ${bgClass}`} role="alert" aria-live="assertive">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <svg
          className={`w-5 h-5 mt-0.5 flex-shrink-0 ${iconColor}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>

        <div className="flex-1 min-w-0">
          {/* Message */}
          <p className={`text-sm font-medium ${textClass}`}>
            {humanizedError.message}
          </p>

          {/* DEBT-v3-S2 AC13: Silent auto-retry — no countdown or attempt counter visible */}
          {retryCountdown != null && retryMessage && (
            <p className={`text-xs mt-1 ${textClass} opacity-80`}>
              {retryMessage}
            </p>
          )}

          {/* DEBT-v3-S2 AC15: Retries exhausted — humanized message */}
          {retryExhausted && (
            <p className={`text-xs mt-1 ${textClass} opacity-80`}>
              Nao conseguimos completar a busca agora. Tente novamente em alguns minutos.
            </p>
          )}

          {/* Action buttons */}
          <div className="flex items-center gap-2 mt-3">
            <button
              onClick={retryCountdown != null ? onRetry : onRetry}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${btnPrimary}`}
            >
              {retryCountdown != null ? `Tentar agora` : humanizedError.actionLabel}
            </button>

            {humanizedError.suggestReduceScope && onReduceScope && (
              <button
                onClick={onReduceScope}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${btnPrimary} opacity-80`}
              >
                {humanizedError.secondaryActionLabel || "Reduzir escopo"}
              </button>
            )}

            {retryCountdown != null && onCancelRetry && (
              <button
                onClick={onCancelRetry}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors text-[var(--ink-secondary)] hover:text-[var(--ink)]`}
              >
                Cancelar
              </button>
            )}
          </div>
          <div className="mt-3">
            <Link href="/ajuda#como-buscar" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
              Precisa de ajuda?
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * STAB-006 AC3: Banner shown when displaying partial results from localStorage.
 */
export function PartialResultsBanner({
  onDismiss,
}: {
  onDismiss: () => void;
}) {
  return (
    <div
      className="mb-4 p-4 rounded-lg border bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800 flex items-center justify-between gap-3"
      role="status"
    >
      <div className="flex items-center gap-3">
        <svg
          className="w-5 h-5 text-blue-500 dark:text-blue-400 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
          Mostrando resultados parciais salvos
        </p>
      </div>
      <button
        onClick={onDismiss}
        className="px-3 py-1 text-xs font-medium rounded bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-700 transition-colors whitespace-nowrap"
      >
        Entendi
      </button>
    </div>
  );
}
