"use client";

/**
 * STORY-298 AC5+AC6: Unified search state renderer.
 *
 * Single component that maps SearchPhase -> appropriate UI.
 * Consolidates ErrorDetail, DegradationBanner, CacheBanner, retry banners,
 * empty states, and loading indicators into one decision tree.
 *
 * AC2: Zero limbo states -- every phase has a visible action.
 * AC7: CSS transitions for smooth state transitions (DEBT-FE-004: replaced framer-motion).
 */

import type { SearchError } from "../hooks/useSearch";
import type { SearchPhase } from "../types/searchPhase";
import { ErrorDetail } from "./ErrorDetail";
import { Button } from "../../../components/ui/button";
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

  // UX-436: UF context for smart retry with reduction suggestion
  ufsSelecionadas?: Set<string>;
  onRetryWithUfs?: (ufs: string[]) => void;
}

/**
 * Wrapper that provides fade-in/fade-out CSS transitions,
 * replacing framer-motion AnimatePresence + motion.div.
 */
function FadePanel({
  show,
  children,
  className = "",
  ...rest
}: {
  show: boolean;
  children: React.ReactNode;
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>) {
  if (!show) return null;

  return (
    <div
      className={`animate-fadeIn ${className}`}
      style={{ animation: "fadeIn 200ms ease-in-out" }}
      {...rest}
    >
      {children}
    </div>
  );
}

/**
 * Renders the appropriate state UI based on the search phase.
 *
 * Renders ONLY for error/offline/quota/failed phases.
 * Returns null for idle/searching/partial_available/completed/empty_results/all_sources_failed/source_timeout
 * -- those are handled directly by SearchResults which already has well-tested rendering.
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
  ufsSelecionadas,
  onRetryWithUfs,
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

  const showOfflineCountdown =
    phase === "offline" && !!error && retryCountdown != null && retryCountdown > 0;
  const showOfflineExhausted =
    phase === "offline" && !!error && retryExhausted && (retryCountdown == null || retryCountdown <= 0);
  const showFailed = phase === "failed" && !!error;
  const showQuota = phase === "quota_exceeded" && !!quotaError;

  // UX-436: Detect timeout errors and suggest UF reduction
  const isTimeoutError = !!(error && (
    error.errorCode === "TIMEOUT" ||
    error.errorCode === "ASYNC_TIMEOUT" ||
    error.errorCode === "CLIENT_TIMEOUT" ||
    error.httpStatus === 504 ||
    error.rawMessage?.toLowerCase().includes("timeout") ||
    error.rawMessage?.includes("demorou demais")
  ));
  const ufArray = ufsSelecionadas ? Array.from(ufsSelecionadas) : [];
  const canSuggestReduction = isTimeoutError && ufArray.length > 2 && !!onRetryWithUfs;
  const suggestedUfs = ufArray.slice(0, 2);

  return (
    <>
      {/* Offline / Auto-retry active — DEBT-v3-S2 AC13-AC14: silent retry, no countdown visible */}
      <FadePanel
        show={showOfflineCountdown}
        className="mt-4 sm:mt-8 mx-0 p-3 sm:p-5 bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-xl max-w-full overflow-hidden"
        role="alert"
        aria-live="assertive"
        data-testid="retry-countdown"
      >
        <p
          className="text-sm sm:text-base font-medium text-blue-700 dark:text-blue-300 mb-3 break-words"
          data-testid="retry-message"
        >
          {retryMessage || "A busca esta demorando. Estamos tentando novamente automaticamente."}
        </p>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <Button
            onClick={onRetryNow}
            variant="primary"
            size="default"
            className="w-full sm:w-auto"
            type="button"
            data-testid="retry-now-button"
          >
            Tentar agora
          </Button>
          <Button
            onClick={onCancelRetry}
            variant="outline"
            size="default"
            className="w-full sm:w-auto"
            type="button"
          >
            Cancelar
          </Button>
        </div>
      </FadePanel>

      {/* Offline / Retry exhausted — DEBT-v3-S2 AC15: humanized final message */}
      <FadePanel
        show={showOfflineExhausted}
        className="mt-4 sm:mt-8 mx-0 p-3 sm:p-5 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-xl max-w-full overflow-hidden"
        role="alert"
        aria-live="assertive"
        data-testid="retry-exhausted"
      >
        <p className="text-sm sm:text-base font-medium text-amber-700 dark:text-amber-300 mb-3 break-words">
          Nao conseguimos completar a busca agora. Tente novamente em alguns minutos.
        </p>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <Button
            onClick={onRetryNow}
            disabled={loading}
            variant="primary"
            size="default"
            type="button"
            data-testid="retry-manual-button"
          >
            Tentar novamente
          </Button>
          {hasPartialResults && (
            <Button
              onClick={() => {
                const resultsEl = document.querySelector(
                  '[data-testid="results-header"]',
                );
                resultsEl?.scrollIntoView({ behavior: "smooth" });
              }}
              variant="outline"
              size="default"
              type="button"
              data-testid="view-partial-results-button"
            >
              Ver resultados parciais
            </Button>
          )}
        </div>
      </FadePanel>

      {/* Failed -- non-transient error, manual retry needed */}
      <FadePanel
        show={showFailed}
        className="mt-6 sm:mt-8 p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-xl"
        role="alert"
        aria-live="assertive"
        data-testid="search-state-failed"
      >
        {error && (
          <>
            <p className="text-sm sm:text-base font-medium text-error mb-3">
              {error.message}
            </p>
            <ErrorDetail error={error} />
          </>
        )}

        {/* UX-436: Smart retry with UF reduction suggestion for timeouts */}
        {canSuggestReduction && (
          <div className="mt-3 mb-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800" data-testid="uf-reduction-suggestion">
            <p className="text-sm text-amber-800 dark:text-amber-200 mb-2">
              Quer tentar novamente com menos estados? Pode ser mais rápido.
            </p>
            <Button
              onClick={() => onRetryWithUfs!(suggestedUfs)}
              disabled={loading}
              variant="outline"
              size="default"
              type="button"
              data-testid="retry-reduced-ufs-button"
            >
              Buscar apenas {suggestedUfs.join(" e ")}
            </Button>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-2 mt-3">
          <Button
            onClick={onRetry}
            disabled={loading}
            loading={loading}
            variant="destructive"
            size="default"
            type="button"
            data-testid="failed-retry-button"
          >
            {loading ? "Tentando..." : "Tentar novamente"}
          </Button>
        </div>
      </FadePanel>

      {/* Quota exceeded -- link to plans */}
      <FadePanel
        show={showQuota}
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
      </FadePanel>
    </>
  );
}
