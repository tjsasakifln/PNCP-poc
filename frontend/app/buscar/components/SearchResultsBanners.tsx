"use client";

/**
 * DEBT-FE-004: Consolidates the informational banners shown alongside search
 * results into a single BannerStack (max 2 visible, collapsible overflow).
 *
 * Covers 9 banners that previously appeared side-by-side in SearchResults,
 * reducing cognitive-load score from ~7/10 to ≤5/10.
 */

import type { BuscaResult } from "../../types";
import { BannerStack, type BannerItem } from "./BannerStack";
import { DataQualityBanner } from "./DataQualityBanner";
import { FilterRelaxedBanner } from "./FilterRelaxedBanner";
import RefreshBanner from "./RefreshBanner";
import type { RefreshAvailableInfo } from "../../../hooks/useSearchSSE";

// ============================================================================
// Props
// ============================================================================

export interface SearchResultsBannersProps {
  result: BuscaResult;
  loading: boolean;
  ufsSelecionadas: Set<string>;
  onSearch: () => void;
  onRetryForceFresh?: (() => void) | null;
  onRefreshResults?: () => void;
  refreshAvailable?: RefreshAvailableInfo | null;
  liveFetchInProgress?: boolean;
  liveFetchTimedOut?: boolean;
  pendingReviewCount?: number;
  pendingReviewUpdate?: {
    reclassifiedCount: number;
    acceptedCount: number;
    rejectedCount: number;
  } | null;
}

// ============================================================================
// Component
// ============================================================================

export function SearchResultsBanners({
  result,
  loading,
  ufsSelecionadas,
  onSearch,
  onRetryForceFresh,
  onRefreshResults,
  refreshAvailable,
  liveFetchInProgress,
  liveFetchTimedOut,
  pendingReviewCount = 0,
  pendingReviewUpdate,
}: SearchResultsBannersProps) {
  const banners: BannerItem[] = [];

  // ------------------------------------------------------------------
  // 1. DataQualityBanner — shows degraded/cached/partial source info
  //    warning severity because it indicates data quality issues
  // ------------------------------------------------------------------
  const showDataQuality =
    !loading &&
    result.response_state !== "degraded_expired" &&
    result.resumo.total_oportunidades > 0;

  if (showDataQuality) {
    banners.push({
      id: "data-quality",
      type: "warning",
      priority: 3,
      content: (
        <DataQualityBanner
          totalUfs={ufsSelecionadas.size}
          succeededUfs={
            ufsSelecionadas.size - (result.failed_ufs?.length ?? 0)
          }
          failedUfs={result.failed_ufs ?? []}
          isCached={!!result.cached && !liveFetchInProgress && !refreshAvailable}
          cachedAt={result.cached_at}
          cacheStatus={result.cache_status}
          isTruncated={!!result.is_truncated}
          cacheFallback={result.cache_fallback}
          cacheDateRange={result.cache_date_range}
          sourcesTotal={result.source_stats?.length ?? 1}
          sourcesAvailable={
            result.source_stats?.filter(
              (s: { status: string }) =>
                s.status === "success" || s.status === "partial",
            ).length ?? (result.source_stats?.length ?? 1)
          }
          sourceNames={result.source_stats?.map(
            (s: { source_code: string }) => s.source_code,
          )}
          responseState={result.response_state}
          coveragePct={result.coverage_pct}
          sourcesDegraded={result.sources_degraded}
          onRefresh={onRetryForceFresh || onSearch}
          onRetry={onSearch}
          loading={loading}
        />
      ),
    });
  }

  // ------------------------------------------------------------------
  // 2. FilterRelaxedBanner — filter thresholds were relaxed to return
  //    results; info severity
  // ------------------------------------------------------------------
  if (
    !loading &&
    result.filter_relaxed &&
    result.resumo.total_oportunidades > 0
  ) {
    banners.push({
      id: "filter-relaxed",
      type: "info",
      priority: 2,
      content: (
        <FilterRelaxedBanner
          relaxationLevel={
            result.hidden_by_min_match != null && result.hidden_by_min_match > 0
              ? "min_match_lowered"
              : undefined
          }
          originalCount={0}
          relaxedCount={result.resumo.total_oportunidades}
        />
      ),
    });
  }

  // ------------------------------------------------------------------
  // 3. RefreshBanner — newer data available, user can refresh
  // ------------------------------------------------------------------
  if (!loading && refreshAvailable && onRefreshResults) {
    banners.push({
      id: "refresh",
      type: "info",
      priority: 2,
      content: (
        <RefreshBanner refreshInfo={refreshAvailable} onRefresh={onRefreshResults} />
      ),
    });
  }

  // ------------------------------------------------------------------
  // 4. Live-fetch in-progress banner — background revalidation running
  // ------------------------------------------------------------------
  if (!loading && liveFetchInProgress && !liveFetchTimedOut && result) {
    banners.push({
      id: "live-fetch",
      type: "info",
      priority: 1,
      content: (
        <div
          className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-200"
          role="status"
        >
          <svg
            className="h-4 w-4 animate-spin flex-shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <span>Atualizando dados em tempo real...</span>
        </div>
      ),
    });
  }

  // ------------------------------------------------------------------
  // 5. Pending review banner — AI reclassification in progress/done
  // ------------------------------------------------------------------
  const hasReclassified =
    pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0;
  if (pendingReviewCount > 0 || hasReclassified) {
    banners.push({
      id: "pending-review",
      type: hasReclassified ? "success" : "info",
      priority: 2,
      content: (
        <div
          className={`flex items-start gap-3 p-3 rounded-lg border ${hasReclassified ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800" : "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"}`}
          data-testid="pending-review-banner"
        >
          <svg
            className={`w-5 h-5 mt-0.5 flex-shrink-0 ${hasReclassified ? "text-emerald-500" : "text-blue-500"}`}
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div className="text-sm">
            {hasReclassified ? (
              <p className="text-emerald-800 dark:text-emerald-300">
                Reclassificação concluída:{" "}
                {pendingReviewUpdate!.acceptedCount} oportunidades confirmadas
                {pendingReviewUpdate!.rejectedCount > 0 &&
                  `, ${pendingReviewUpdate!.rejectedCount} descartadas`}
                .
              </p>
            ) : (
              <p className="text-blue-800 dark:text-blue-300">
                {pendingReviewCount}{" "}
                {pendingReviewCount === 1
                  ? "oportunidade aguarda"
                  : "oportunidades aguardam"}{" "}
                reclassificação (IA temporariamente indisponível)
              </p>
            )}
          </div>
        </div>
      ),
    });
  }

  // ------------------------------------------------------------------
  // 6. LLM zero-match analysis banner — info about AI analysis
  // ------------------------------------------------------------------
  if (
    !loading &&
    result.filter_stats &&
    (result.filter_stats.llm_zero_match_calls ?? 0) > 0
  ) {
    banners.push({
      id: "llm-analysis",
      type: "info",
      priority: 1,
      content: (
        <div
          className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-200"
          data-testid="llm-analysis-banner"
        >
          <svg
            className="w-4 h-4 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          <span>
            {`IA analisou ${result.filter_stats.llm_zero_match_calls} licitações adicionais`}
            {(result.filter_stats.llm_zero_match_aprovadas ?? 0) > 0 && (
              <> — {result.filter_stats.llm_zero_match_aprovadas} aprovadas</>
            )}
          </span>
        </div>
      ),
    });
  }

  // ------------------------------------------------------------------
  // 7. Zero-match budget exceeded — warning about skipped analysis
  // ------------------------------------------------------------------
  if (
    !loading &&
    result.filter_stats &&
    (result.filter_stats.zero_match_budget_exceeded ?? 0) > 0
  ) {
    banners.push({
      id: "zero-match-budget",
      type: "warning",
      priority: 2,
      content: (
        <div
          className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-200"
          data-testid="zero-match-budget-banner"
        >
          <svg
            className="w-4 h-4 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>
            Algumas oportunidades estão em revisão e podem aparecer em breve
          </span>
        </div>
      ),
    });
  }

  if (banners.length === 0) return null;

  return <BannerStack banners={banners} maxVisible={2} />;
}
