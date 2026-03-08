"use client";

/**
 * STORY-298 AC5+AC6: Unified search state renderer.
 *
 * Single component that maps SearchPhase → appropriate UI.
 * Consolidates ErrorDetail, DegradationBanner, CacheBanner, retry banners,
 * empty states, and loading indicators into one decision tree.
 *
 * AC2: Zero limbo states — every phase has a visible action.
 * AC7: Framer Motion AnimatePresence for smooth state transitions.
 */

import { AnimatePresence, motion } from "framer-motion";
import type { SearchError } from "../hooks/useSearch";
import type { SearchPhase } from "../types/searchPhase";
import { ErrorDetail } from "./ErrorDetail";
import { toast } from "sonner";
import { useEffect, useRef } from "react";

export interface SearchStateManagerProps {
  phase: SearchPhase;

  // Error state
  error: SearchError | null;
  quotaError: string | null;

  // Retry state
  retryCountdown: number | null;
  retryMessage: string | null;
  retryExhausted: boolean;

  // Handlers
  onRetry: () => void;
  onRetryNow: () => void;
  onCancelRetry: () => void;
  onCancel: () => void;

  // Loading indicator
  loading: boolean;

  // Result availability (for "view partial" button)
  hasPartialResults: boolean;
}

const fadeVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

const transition = { duration: 0.2, ease: "easeInOut" as const };

/**
 * Renders the appropriate state UI based on the search phase.
 *
 * Renders ONLY for error/offline/quota/failed phases.
 * Returns null for idle/searching/partial_available/completed/empty_results/all_sources_failed/source_timeout
 * — those are handled directly by SearchResults which already has well-tested rendering.
 *
 * This component focuses on the ERROR OVERLAY AREA (AC5+AC6).
 */
export function SearchStateManager({
  phase,
  error,
  quotaError,
  retryCountdown,
  retryMessage,
  retryExhausted,
  onRetry,
  onRetryNow,
  onCancelRetry,
  onCancel,
  loading,
  hasPartialResults,
}: SearchStateManagerProps) {
  const prevPhaseRef = useRef<SearchPhase>(phase);

  // AC3: Toast notifications for transient events
  useEffect(() => {
    const prevPhase = prevPhaseRef.current;
    prevPhaseRef.current = phase;

    // Transient toasts on phase transitions
    if (prevPhase === "offline" && phase === "searching") {
      toast.success("Conexão restabelecida", {
        description: "Retomando análise...",
        duration: 3000,
      });
    }
    if (prevPhase === "searching" && phase === "offline") {
      toast.warning("Conexão perdida", {
        description: "Tentando reconectar automaticamente...",
        duration: 4000,
      });
    }
    if (prevPhase === "partial_available" && phase === "completed") {
      toast.success("Análise concluída", {
        description: "Todos os resultados carregados",
        duration: 3000,
      });
    }
  }, [phase]);

  return (
    <AnimatePresence mode="wait">
      {/* Offline / Auto-retry active (with countdown) */}
      {phase === "offline" && error && retryCountdown != null && retryCountdown > 0 && (
        <motion.div
          key="offline-countdown"
          variants={fadeVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={transition}
          className="mt-4 sm:mt-8 mx-0 p-3 sm:p-5 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-xl max-w-full overflow-hidden"
          role="alert"
          aria-live="assertive"
          data-testid="retry-countdown"
        >
          <p
            className="text-sm sm:text-base font-medium text-blue-700 dark:text-blue-300 mb-1 break-words"
            data-testid="retry-message"
          >
            {retryMessage || "Temporariamente indisponível. Tentando novamente..."}
          </p>
          <p
            className="text-xs sm:text-sm text-blue-600/70 dark:text-blue-400/70 mb-3"
            data-testid="retry-countdown-text"
          >
            Tentando em {retryCountdown}s...
          </p>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <button
              onClick={onRetryNow}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors w-full sm:w-auto"
              type="button"
              data-testid="retry-now-button"
            >
              Tentar agora
            </button>
            <button
              onClick={onCancelRetry}
              className="px-4 py-2 bg-transparent text-blue-600 dark:text-blue-300 border border-blue-300 dark:border-blue-700 rounded-lg text-sm font-medium hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors w-full sm:w-auto"
              type="button"
            >
              Cancelar
            </button>
          </div>
        </motion.div>
      )}

      {/* Offline / Retry exhausted */}
      {phase === "offline" && error && retryExhausted && (retryCountdown == null || retryCountdown <= 0) && (
        <motion.div
          key="offline-exhausted"
          variants={fadeVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={transition}
          className="mt-4 sm:mt-8 mx-0 p-3 sm:p-5 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-xl max-w-full overflow-hidden"
          role="alert"
          aria-live="assertive"
          data-testid="retry-exhausted"
        >
          <p className="text-sm sm:text-base font-medium text-amber-700 dark:text-amber-300 mb-3 break-words">
            Análise indisponível no momento.
          </p>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <button
              onClick={onRetryNow}
              disabled={loading}
              className="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-medium hover:bg-amber-700 transition-colors disabled:opacity-50"
              type="button"
              data-testid="retry-manual-button"
            >
              Tentar novamente
            </button>
            {hasPartialResults && (
              <button
                onClick={() => {
                  const resultsEl = document.querySelector(
                    '[data-testid="results-header"]',
                  );
                  resultsEl?.scrollIntoView({ behavior: "smooth" });
                }}
                className="px-4 py-2 bg-transparent text-amber-600 dark:text-amber-300 border border-amber-300 dark:border-amber-700 rounded-lg text-sm font-medium hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
                type="button"
                data-testid="view-partial-results-button"
              >
                Ver resultados parciais
              </button>
            )}
          </div>
        </motion.div>
      )}

      {/* Failed — non-transient error, manual retry needed */}
      {phase === "failed" && error && (
        <motion.div
          key="failed"
          variants={fadeVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={transition}
          className="mt-6 sm:mt-8 p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-xl"
          role="alert"
          aria-live="assertive"
          data-testid="search-state-failed"
        >
          <p className="text-sm sm:text-base font-medium text-error mb-3">
            {error.message}
          </p>
          <ErrorDetail error={error} />
          <button
            onClick={onRetry}
            disabled={loading}
            className="mt-3 px-4 py-2 bg-error text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
            type="button"
            data-testid="failed-retry-button"
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin h-4 w-4"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Tentando...
              </>
            ) : (
              "Tentar novamente"
            )}
          </button>
        </motion.div>
      )}

      {/* Quota exceeded — link to plans */}
      {phase === "quota_exceeded" && quotaError && (
        <motion.div
          key="quota"
          variants={fadeVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={transition}
          className="mt-6 sm:mt-8 p-4 sm:p-5 bg-warning-subtle border border-warning/20 rounded-xl"
          role="alert"
          aria-live="assertive"
          data-testid="search-state-quota"
        >
          <div className="flex items-start gap-3">
            <svg
              className="w-6 h-6 text-warning flex-shrink-0 mt-0.5"
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
            <div>
              <p className="text-sm sm:text-base font-medium text-warning mb-2">
                {quotaError}
              </p>
              <p className="text-sm text-ink-secondary mb-4">
                Escolha um plano para continuar buscando oportunidades de
                licitação.
              </p>
              <a
                href="/planos"
                className="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white rounded-lg text-sm font-medium hover:bg-brand-blue-hover transition-colors"
                data-testid="quota-plans-link"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                  />
                </svg>
                Ver Planos
              </a>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
