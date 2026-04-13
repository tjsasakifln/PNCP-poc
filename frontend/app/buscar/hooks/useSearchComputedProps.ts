"use client";

import { useMemo } from "react";
import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";
import type { SearchResultsProps } from "../types/search-results";
import type { SearchFiltersState } from "./useSearchFilters";
import type { SearchBillingState } from "./useSearchBillingState";
import type { UseSearchReturn } from "./useSearch";

interface UseSearchComputedPropsParams {
  search: UseSearchReturn;
  filters: SearchFiltersState;
  billing: Pick<SearchBillingState, "planInfo" | "trialPhase">;
  session: { access_token: string } | null;
  isTrialExpiredOrQuota: boolean;
  isProfileComplete: boolean;
  searchElapsed: number;
  partialDismissed: boolean;
  lastSearchAvailable: boolean;
  pdfLoading: boolean;
  handleShowUpgradeModal: (plan?: string, source?: string) => void;
  handleLoadLastSearch: () => void;
  handleRetryWithUfs: (ufs: string[]) => void;
  startResultsTour: () => void;
  isResultsTourCompleted: () => boolean;
  setPdfModalOpen: (open: boolean) => void;
  setPartialDismissed: (dismissed: boolean) => void;
  trackEvent: (name: string, data: Record<string, unknown>) => void;
}

/**
 * DEBT-FE-001: Extracted from useSearchOrchestration (was lines ~424-536, 113 LOC).
 * Owns the large searchResultsProps useMemo computation.
 */
export function useSearchComputedProps(
  params: UseSearchComputedPropsParams
): { searchResultsProps: SearchResultsProps } {
  const {
    search,
    filters,
    billing,
    session,
    isTrialExpiredOrQuota,
    isProfileComplete,
    searchElapsed,
    partialDismissed,
    lastSearchAvailable,
    pdfLoading,
    handleShowUpgradeModal,
    handleLoadLastSearch,
    handleRetryWithUfs,
    startResultsTour,
    isResultsTourCompleted,
    setPdfModalOpen,
    setPartialDismissed,
    trackEvent,
  } = params;

  const searchResultsProps = useMemo((): SearchResultsProps => ({
    // Group 1: SearchResultsData
    result: search.result,
    rawCount: search.rawCount,
    filterSummary: search.filterSummary,
    pendingReviewCount: search.result?.pending_review_count ?? 0,
    pendingReviewUpdate: search.pendingReviewUpdate,
    zeroMatchProgress: search.zeroMatchProgress,

    // Group 2: SearchLoadingState
    loading: search.loading,
    loadingStep: search.loadingStep,
    estimatedTime: search.estimateSearchTime(
      filters.ufsSelecionadas.size,
      dateDiffInDays(filters.dataInicial, filters.dataFinal)
    ),
    stateCount: filters.ufsSelecionadas.size,
    statesProcessed: search.statesProcessed,
    sseEvent: search.sseEvent,
    useRealProgress: search.useRealProgress,
    sseAvailable: search.sseAvailable,
    sseDisconnected: search.sseDisconnected,
    isReconnecting: search.isReconnecting,
    isDegraded: search.isDegraded,
    degradedDetail: search.degradedDetail,
    skeletonTimeoutReached: search.skeletonTimeoutReached,
    ufStatuses: search.ufStatuses,
    ufStatusesSnapshot: search.ufStatusesSnapshot,
    ufTotalFound: search.ufTotalFound,
    ufAllComplete: search.ufAllComplete,
    sourceStatuses: search.sourceStatuses,
    partialProgress: search.partialProgress,

    // Group 3: SearchResultsFilters
    ufsSelecionadas: filters.ufsSelecionadas,
    sectorName: filters.sectorName,
    searchMode: filters.searchMode,
    termosArray: filters.termosArray,
    ordenacao: filters.ordenacao,
    status: filters.status,

    // Group 4: SearchResultsActions
    onCancel: search.cancelSearch,
    onStageChange: (stage: number) =>
      trackEvent("search_progress_stage", {
        stage,
        is_sse: search.useRealProgress && search.sseAvailable,
      }),
    onOrdenacaoChange: filters.setOrdenacao,
    onDownload: search.handleDownload,
    onSearch: search.buscar,
    onRegenerateExcel: search.handleRegenerateExcel,
    onShowUpgradeModal: handleShowUpgradeModal,
    onTrackEvent: trackEvent,
    onViewPartial: search.viewPartialResults,
    onDismissPartial: () => setPartialDismissed(true),
    onRetryForceFresh: search.buscarForceFresh,
    onRetryWithUfs: handleRetryWithUfs,
    onLoadLastSearch: handleLoadLastSearch,
    onRefreshResults: search.handleRefreshResults,
    onRetryNow: search.retryNow,
    onCancelRetry: search.cancelRetry,
    onAdjustPeriod: undefined,
    onAddNeighborStates: undefined,
    onViewNearbyResults: undefined,
    onGeneratePdf: () => setPdfModalOpen(true),
    onStartResultsTour: () => {
      startResultsTour();
      trackEvent("onboarding_tour_started", { tour: "results" });
    },

    // Group 5: SearchDisplayState
    error: search.error,
    quotaError: search.quotaError,
    downloadLoading: search.downloadLoading,
    downloadError: search.downloadError,
    excelFailCount: search.excelFailCount,
    searchElapsedSeconds: searchElapsed,
    partialDismissed,
    liveFetchInProgress: search.liveFetchInProgress,
    refreshAvailable: search.refreshAvailable,
    hasLastSearch: lastSearchAvailable,
    retryCountdown: search.retryCountdown,
    retryMessage: search.retryMessage,
    retryExhausted: search.retryExhausted,
    nearbyResultsCount: undefined,
    pdfLoading,

    // Group 6: SearchAuthState
    planInfo: billing.planInfo,
    session,
    isTrialExpired: isTrialExpiredOrQuota,
    trialPhase: billing.trialPhase,
    paywallApplied: search.result?.paywall_applied,
    totalBeforePaywall: search.result?.total_before_paywall,
    isProfileComplete,

    // Group 7: SearchFeedbackState
    searchId: search.searchId || undefined,
    setorId: filters.setorId,
    isResultsTourCompleted,
  }), [
    search.result, search.rawCount, search.filterSummary, search.pendingReviewUpdate,
    search.zeroMatchProgress, search.loading, search.loadingStep, search.statesProcessed,
    search.sseEvent, search.useRealProgress, search.sseAvailable, search.sseDisconnected,
    search.isReconnecting, search.isDegraded, search.degradedDetail, search.skeletonTimeoutReached,
    search.ufStatuses, search.ufStatusesSnapshot, search.ufTotalFound, search.ufAllComplete, search.sourceStatuses,
    search.partialProgress, search.cancelSearch, search.buscar, search.handleDownload,
    search.handleRegenerateExcel, search.viewPartialResults, search.buscarForceFresh,
    search.handleRefreshResults, search.retryNow, search.cancelRetry,
    search.error, search.quotaError, search.downloadLoading, search.downloadError,
    search.excelFailCount, search.liveFetchInProgress, search.refreshAvailable,
    search.retryCountdown, search.retryMessage, search.retryExhausted, search.searchId,
    search.estimateSearchTime,
    filters.ufsSelecionadas, filters.sectorName, filters.searchMode, filters.termosArray,
    filters.ordenacao, filters.setOrdenacao, filters.dataInicial, filters.dataFinal,
    filters.setorId, filters.status,
    trackEvent, handleShowUpgradeModal, handleLoadLastSearch, handleRetryWithUfs, startResultsTour,
    isResultsTourCompleted, searchElapsed, partialDismissed, lastSearchAvailable,
    pdfLoading, billing.planInfo, session, isTrialExpiredOrQuota, billing.trialPhase, isProfileComplete,
    setPdfModalOpen, setPartialDismissed,
  ]);

  return { searchResultsProps };
}
