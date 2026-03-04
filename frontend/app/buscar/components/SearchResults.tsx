"use client";

import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import Link from "next/link";
import type { BuscaResult } from "../../types";
import type { SearchProgressEvent, RefreshAvailableInfo, SourceStatus, PartialProgress, FilterSummary } from "../../../hooks/useSearchSSE";
import RefreshBanner from "./RefreshBanner";
import { EnhancedLoadingProgress } from "../../../components/EnhancedLoadingProgress";
import { LoadingResultsSkeleton } from "../../components/LoadingResultsSkeleton";
import { EmptyState } from "../../components/EmptyState";
import { UfProgressGrid } from "./UfProgressGrid";
import type { UfStatus } from "../../../hooks/useSearchSSE";
import { PartialResultsPrompt } from "./PartialResultsPrompt";
import { SourcesUnavailable } from "./SourcesUnavailable";
import { DataQualityBanner } from "./DataQualityBanner";
import { QuotaCounter } from "../../components/QuotaCounter";
import { LicitacoesPreview } from "../../components/LicitacoesPreview";
import { OrdenacaoSelect, type OrdenacaoOption } from "../../components/OrdenacaoSelect";
import GoogleSheetsExportButton from "../../../components/GoogleSheetsExportButton";
import { LlmSourceBadge } from "./LlmSourceBadge";
import { ErrorDetail } from "./ErrorDetail";
import type { SearchError } from "../hooks/useSearch";
import { ZeroResultsSuggestions } from "./ZeroResultsSuggestions";
import { FilterRelaxedBanner } from "./FilterRelaxedBanner";
import { ExpiredCacheBanner } from "./ExpiredCacheBanner";
import SourceStatusGrid from "./SourceStatusGrid";
import { SearchStateManager } from "./SearchStateManager";
import { deriveSearchPhase } from "../types/searchPhase";
import { TrialUpsellCTA } from "../../../components/billing/TrialUpsellCTA";
import { TrialPaywall } from "../../../components/billing/TrialPaywall";
import { Pagination, useInitPagination } from "../../../components/ui/Pagination";
// GTM-UX-001: PartialTimeoutBanner replaced by DataQualityBanner

// UX-404: Inline tour invite banner (AC2-AC5)
export function TourInviteBanner({
  isCompleted,
  onStartTour,
}: {
  isCompleted?: () => boolean;
  onStartTour?: () => void;
}) {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // AC2: Show banner only when tour not yet completed
  useEffect(() => {
    if (!isCompleted || isCompleted() || dismissed) return;
    setVisible(true);
  }, [isCompleted, dismissed]);

  // AC3: Auto-dismiss after 10s
  useEffect(() => {
    if (!visible) return;
    timerRef.current = setTimeout(() => {
      setVisible(false);
      setDismissed(true);
    }, 10_000);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [visible]);

  // AC3: Dismiss on scroll
  useEffect(() => {
    if (!visible) return;
    const handler = () => {
      setVisible(false);
      setDismissed(true);
    };
    window.addEventListener("scroll", handler, { once: true, passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, [visible]);

  const handleStart = useCallback(() => {
    setVisible(false);
    setDismissed(true);
    onStartTour?.();
  }, [onStartTour]);

  const handleClose = useCallback(() => {
    setVisible(false);
    setDismissed(true);
  }, []);

  if (!visible) return null;

  return (
    <div
      className="flex items-center justify-between gap-3 px-4 py-2.5 rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/50 text-sm text-blue-800 dark:text-blue-200 animate-fade-in-up"
      data-testid="tour-invite-banner"
      role="status"
    >
      <span>Primeira vez vendo resultados? Clique aqui para um tour rápido.</span>
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={handleStart}
          className="px-3 py-1 text-xs font-medium bg-blue-600 text-white rounded-button hover:bg-blue-700 transition-colors"
          data-testid="tour-invite-start"
        >
          Iniciar tour
        </button>
        <button
          onClick={handleClose}
          className="p-1 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
          aria-label="Fechar"
          data-testid="tour-invite-close"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export interface SearchResultsProps {
  // Loading state
  loading: boolean;
  loadingStep: number;
  estimatedTime: number;
  stateCount: number;
  statesProcessed: number;
  onCancel: () => void;
  sseEvent: SearchProgressEvent | null;
  useRealProgress: boolean;
  sseAvailable: boolean;
  /** GTM-FIX-033 AC3: SSE disconnected flag */
  sseDisconnected?: boolean;
  /** STORY-297 AC9: SSE reconnecting indicator */
  isReconnecting?: boolean;
  /** A-02 AC8: search completed with degraded data */
  isDegraded?: boolean;
  /** A-02 AC10: metadata from SSE degraded event */
  degradedDetail?: SearchProgressEvent['detail'] | null;
  onStageChange: (stage: number) => void;

  // Error state — CRIT-009 AC7: structured SearchError
  error: SearchError | null;
  quotaError: string | null;

  // Result
  result: BuscaResult | null;
  rawCount: number;

  // Empty state
  ufsSelecionadas: Set<string>;
  sectorName: string;

  // Results display
  searchMode: "setor" | "termos";
  termosArray: string[];
  ordenacao: OrdenacaoOption;
  onOrdenacaoChange: (ord: OrdenacaoOption) => void;

  // Download
  downloadLoading: boolean;
  downloadError: string | null;
  onDownload: () => void;
  onSearch: () => void;
  onRegenerateExcel?: () => void;

  // Plan & auth
  planInfo: {
    plan_id: string;
    plan_name: string;
    quota_used: number;
    quota_reset_date: string;
    trial_expires_at?: string | null;
    subscription_status?: string;
    capabilities: {
      max_history_days: number;
      max_requests_per_month: number;
      allow_excel: boolean;
    };
  } | null;
  session: { access_token: string } | null;
  onShowUpgradeModal: (plan?: string, source?: string) => void;

  // Analytics
  onTrackEvent: (name: string, data: Record<string, any>) => void;

  // STORY-257B: UF Progress Grid (AC1-4)
  ufStatuses?: Map<string, UfStatus>;
  ufTotalFound?: number;
  ufAllComplete?: boolean;

  // STORY-257B: Partial results (AC5-6)
  searchElapsedSeconds?: number;
  onViewPartial?: () => void;
  partialDismissed?: boolean;
  onDismissPartial?: () => void;

  // STORY-257B: Cache refresh (AC8-9)
  onRetryForceFresh?: () => void;

  // STORY-257B: Sources unavailable (AC10)
  hasLastSearch?: boolean;
  onLoadLastSearch?: () => void;

  // A-04: Progressive delivery
  liveFetchInProgress?: boolean;
  refreshAvailable?: RefreshAvailableInfo | null;
  onRefreshResults?: () => void;

  // D-05: Feedback loop
  searchId?: string;
  setorId?: string;

  // UX-350 AC6: Profile completeness for recommendation context
  isProfileComplete?: boolean;

  // CRIT-008 AC5 + GTM-UX-003: Unified retry mechanism
  retryCountdown?: number | null;
  /** GTM-UX-003 AC4-AC7: Contextual retry message */
  retryMessage?: string | null;
  /** GTM-UX-003 AC9: All retry attempts exhausted */
  retryExhausted?: boolean;
  onRetryNow?: () => void;
  onCancelRetry?: () => void;

  // GTM-UX-002 AC10-12: Zero results actionable suggestions
  onAdjustPeriod?: () => void;
  onAddNeighborStates?: () => void;
  nearbyResultsCount?: number;
  onViewNearbyResults?: () => void;

  // STORY-265 AC16: Trial expired — disable Excel download
  isTrialExpired?: boolean;

  // STORY-295: Progressive results
  sourceStatuses?: Map<string, SourceStatus>;
  partialProgress?: PartialProgress | null;

  // STORY-327: Filter summary (raw vs filtered)
  filterSummary?: FilterSummary | null;

  // STORY-320: Trial paywall
  trialPhase?: "full_access" | "limited_access" | "not_trial";
  paywallApplied?: boolean;
  totalBeforePaywall?: number | null;

  // STORY-325: PDF Diagnostico
  onGeneratePdf?: (options: { clientName: string; maxItems: number }) => void;
  pdfLoading?: boolean;

  // SAB-005 AC1: Skeleton timeout
  skeletonTimeoutReached?: boolean;

  // STORY-354 AC3: Pending review bids count
  pendingReviewCount?: number;
  /** STORY-354 AC6: Pending review reclassification update from SSE */
  pendingReviewUpdate?: { reclassifiedCount: number; acceptedCount: number; rejectedCount: number } | null;

  // UX-404: Tour invite banner
  isResultsTourCompleted?: () => boolean;
  onStartResultsTour?: () => void;
}

export default function SearchResults({
  loading, loadingStep, estimatedTime, stateCount, statesProcessed,
  onCancel, sseEvent, useRealProgress, sseAvailable, sseDisconnected, isReconnecting, isDegraded, degradedDetail, onStageChange,
  error, quotaError,
  result, rawCount,
  ufsSelecionadas, sectorName,
  searchMode, termosArray, ordenacao, onOrdenacaoChange,
  downloadLoading, downloadError, onDownload, onSearch, onRegenerateExcel,
  planInfo, session, onShowUpgradeModal, onTrackEvent,
  // STORY-257B props
  ufStatuses, ufTotalFound = 0, ufAllComplete,
  searchElapsedSeconds = 0, onViewPartial, partialDismissed, onDismissPartial,
  onRetryForceFresh,
  hasLastSearch = false, onLoadLastSearch,
  // A-04
  liveFetchInProgress, refreshAvailable, onRefreshResults,
  // D-05
  searchId, setorId,
  // UX-350
  isProfileComplete = true,
  // CRIT-008 + GTM-UX-003
  retryCountdown, retryMessage, retryExhausted, onRetryNow, onCancelRetry,
  // GTM-UX-002 AC10-12
  onAdjustPeriod, onAddNeighborStates, nearbyResultsCount, onViewNearbyResults,
  // STORY-265 AC16
  isTrialExpired,
  // STORY-295: Progressive results
  sourceStatuses, partialProgress,
  // STORY-327: Filter summary
  filterSummary,
  // STORY-320: Trial paywall
  trialPhase, paywallApplied, totalBeforePaywall,
  // STORY-325: PDF Diagnostico
  onGeneratePdf, pdfLoading,
  // SAB-005 AC1: Skeleton timeout
  skeletonTimeoutReached,
  // STORY-354
  pendingReviewCount = 0, pendingReviewUpdate,
  // UX-404
  isResultsTourCompleted, onStartResultsTour,
}: SearchResultsProps) {
  // STORY-333: Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState<10 | 20 | 50>(() => {
    if (typeof window === "undefined") return 20;
    const stored = localStorage.getItem("smartlic_page_size");
    if (stored && [10, 20, 50].includes(Number(stored))) return Number(stored) as 10 | 20 | 50;
    return 20;
  });

  // STORY-333 AC6: Reset page on new search result or sort change
  useEffect(() => {
    setCurrentPage(1);
  }, [result, ordenacao]);

  // STORY-333 AC8: Sync page with URL query param
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    const pageParam = url.searchParams.get("page");
    if (pageParam && Number(pageParam) > 0) {
      setCurrentPage(Number(pageParam));
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || !result) return;
    const url = new URL(window.location.href);
    if (currentPage > 1) {
      url.searchParams.set("page", String(currentPage));
    } else {
      url.searchParams.delete("page");
    }
    window.history.replaceState({}, "", url.toString());
  }, [currentPage, result]);

  // STORY-257B AC4: Track transition from grid to results
  const [showGrid, setShowGrid] = useState(false);
  const [gridFading, setGridFading] = useState(false);

  // Show grid when loading starts, fade out when loading ends
  useEffect(() => {
    if (loading && ufStatuses && ufStatuses.size > 0) {
      setShowGrid(true);
      setGridFading(false);
    } else if (!loading && showGrid) {
      setGridFading(true);
      const fadeTimer = setTimeout(() => {
        setShowGrid(false);
        setGridFading(false);
      }, 400); // Match animation duration
      return () => clearTimeout(fadeTimer);
    }
  }, [loading, ufStatuses?.size]);

  // STORY-257B: Compute UF counts for partial results
  const succeededUfCount = ufStatuses
    ? Array.from(ufStatuses.values()).filter(s => s.status === 'success' || s.status === 'recovered').length
    : 0;
  const pendingUfCount = ufStatuses
    ? Array.from(ufStatuses.values()).filter(s => s.status === 'pending' || s.status === 'fetching' || s.status === 'retrying').length
    : 0;

  // UX-349 AC2/AC4: Excel processing timeout — auto-transition to retry after 60s
  const [excelTimedOut, setExcelTimedOut] = useState(false);

  useEffect(() => {
    if (result?.excel_status === 'processing' && !result?.download_url && !result?.download_id) {
      setExcelTimedOut(false);
      const timer = setTimeout(() => setExcelTimedOut(true), 60_000);
      return () => clearTimeout(timer);
    }
    setExcelTimedOut(false);
  }, [result?.excel_status, result?.download_url, result?.download_id]);

  // GTM-FIX-011 AC22: Toggle source badges for power users
  const [showSourceBadges, setShowSourceBadges] = useState(false);

  // STORY-312 AC2: Track when download completes to show post-download CTA
  const [downloadCompleted, setDownloadCompleted] = useState(false);
  const [prevDownloadLoading, setPrevDownloadLoading] = useState(false);

  useEffect(() => {
    if (prevDownloadLoading && !downloadLoading && !downloadError) {
      setDownloadCompleted(true);
    }
    setPrevDownloadLoading(downloadLoading);
  }, [downloadLoading, downloadError, prevDownloadLoading]);

  // GTM-UX-003 AC11: 30-second cooldown REMOVED — single unified retry mechanism

  // GTM-UX-001: succeededUfs derivation removed — DataQualityBanner computes internally

  // STORY-298 AC1+AC2: Derive search phase from current state (single source of truth)
  const searchPhase = useMemo(() => deriveSearchPhase({
    loading,
    error,
    quotaError,
    result,
    retryCountdown: retryCountdown ?? null,
    retryExhausted: !!retryExhausted,
    sourceStatuses: sourceStatuses ?? new Map(),
    partialProgress: partialProgress ?? null,
    ufTotalFound,
    searchElapsedSeconds,
  }), [loading, error, quotaError, result, retryCountdown, retryExhausted, sourceStatuses, partialProgress, ufTotalFound, searchElapsedSeconds]);

  // STORY-333: Paginated licitacoes slice for display
  const paginatedLicitacoes = useMemo(() => {
    if (!result?.licitacoes) return [];
    const start = (currentPage - 1) * pageSize;
    return result.licitacoes.slice(start, start + pageSize);
  }, [result?.licitacoes, currentPage, pageSize]);

  const totalLicitacoes = result?.licitacoes?.length ?? 0;

  // STORY-260 AC16: Dismissible profile incomplete banner (localStorage, 3-day TTL)
  const [bannerDismissed, setBannerDismissed] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem('profile_banner_dismissed');
    if (dismissed) {
      const days = (Date.now() - parseInt(dismissed)) / (1000 * 60 * 60 * 24);
      if (days < 3) setBannerDismissed(true);
    }
  }, []);

  const handleDismissBanner = () => {
    localStorage.setItem('profile_banner_dismissed', String(Date.now()));
    setBannerDismissed(true);
  };

  return (
    <>
      {/* STORY-257B AC1-3: UF Progress Grid (shown during loading) */}
      {showGrid && ufStatuses && ufStatuses.size > 0 && (
        <div
          className={`transition-all duration-400 ${gridFading ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`}
          style={{ minHeight: gridFading ? 0 : undefined }}
        >
          <UfProgressGrid ufStatuses={ufStatuses} totalFound={ufTotalFound} />
        </div>
      )}

      {/* STORY-297 AC9: Reconnecting indicator during SSE gap */}
      {isReconnecting && loading && (
        <div className="mb-2 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 animate-fade-in-up" role="status" data-testid="sse-reconnecting-banner">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-amber-600 dark:text-amber-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="text-sm text-amber-800 dark:text-amber-200">
              Reconectando...
            </span>
          </div>
        </div>
      )}

      {/* Loading State — GTM-FIX-035 AC2: sticky progress tracker */}
      {loading && (
        <div aria-live="polite">
          <div className="sticky top-[68px] z-30 bg-[var(--canvas)] pb-2">
            <EnhancedLoadingProgress
              currentStep={loadingStep}
              estimatedTime={estimatedTime}
              stateCount={stateCount}
              statesProcessed={statesProcessed}
              onCancel={onCancel}
              sseEvent={sseEvent}
              useRealProgress={useRealProgress && sseAvailable}
              sseDisconnected={sseDisconnected}
              isReconnecting={isReconnecting}
              onStageChange={onStageChange}
              ufAllComplete={ufAllComplete}
              isDegraded={isDegraded}
              degradedMessage={sseEvent?.stage === 'degraded' ? sseEvent.message : undefined}
            />
          </div>
          <LoadingResultsSkeleton count={1} />

          {/* SAB-005 AC1-AC3: Timeout banner when skeleton visible >30s without data update */}
          {skeletonTimeoutReached && (
            <div
              className="mt-4 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 animate-fade-in-up"
              role="alert"
              data-testid="skeleton-timeout-banner"
            >
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                    A análise está demorando mais que o esperado
                  </p>
                  <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                    O servidor pode estar processando um volume alto de dados.
                  </p>
                  <div className="flex flex-col sm:flex-row items-start gap-2 mt-3">
                    <button
                      onClick={() => { onCancel(); onSearch(); }}
                      className="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-medium hover:bg-amber-700 transition-colors"
                      type="button"
                      data-testid="skeleton-timeout-retry"
                    >
                      Tentar novamente
                    </button>
                    <Link
                      href="/historico"
                      className="px-4 py-2 text-sm font-medium text-amber-700 dark:text-amber-300 hover:underline"
                      data-testid="skeleton-timeout-historico"
                    >
                      Ver análises anteriores
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STORY-295 AC10: Per-source status indicators */}
          {sourceStatuses && sourceStatuses.size > 0 && (
            <SourceStatusGrid sourceStatuses={sourceStatuses} className="mt-3" />
          )}

          {/* STORY-327 AC1+AC2+AC7: Unified counter banner — "X relevantes de Y analisadas" */}
          {(filterSummary || (partialProgress && partialProgress.totalSoFar > 0)) && (
            <div className="mt-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 animate-fade-in-up">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="text-sm font-medium text-blue-800 dark:text-blue-200" data-testid="unified-counter-banner">
                    {filterSummary
                      ? `${filterSummary.totalFiltered} ${filterSummary.totalFiltered === 1 ? "relevante" : "relevantes"} de ${filterSummary.totalRaw.toLocaleString("pt-BR")} analisadas`
                      : `Analisando ${partialProgress!.totalSoFar.toLocaleString("pt-BR")} licitações encontradas — aplicando filtros do setor...`}
                  </span>
                </div>
                <span className="text-xs text-blue-600 dark:text-blue-400">
                  {filterSummary ? "Filtragem concluída" : "Análise em andamento"}
                </span>
              </div>
            </div>
          )}

          {/* STORY-327 AC3: Zero filtered results with raw > 0 — actionable suggestion */}
          {filterSummary && filterSummary.totalFiltered === 0 && filterSummary.totalRaw > 0 && (
            <div className="mt-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 animate-fade-in-up" data-testid="zero-filtered-suggestion">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Nenhuma oportunidade relevante entre {filterSummary.totalRaw.toLocaleString("pt-BR")} licitações. Tente ampliar o período ou selecionar mais estados.
              </p>
            </div>
          )}

          {/* STORY-257B AC5: Partial results prompt after 15s */}
          {searchElapsedSeconds >= 15 && ufTotalFound > 0 && !partialDismissed && onViewPartial && onDismissPartial && (
            <PartialResultsPrompt
              totalFound={ufTotalFound}
              succeededCount={succeededUfCount}
              pendingCount={pendingUfCount}
              elapsedSeconds={searchElapsedSeconds}
              onViewPartial={onViewPartial}
              onWaitComplete={onDismissPartial}
              dismissed={!!partialDismissed}
            />
          )}
        </div>
      )}

      {/* STORY-298 AC5+AC6: Unified error/offline/quota state manager
          Replaces 4 separate error conditionals with single SearchStateManager.
          AC2: Zero limbo states — phase is derived from a single decision tree.
          AC7: Framer Motion AnimatePresence for smooth transitions. */}
      <SearchStateManager
        phase={searchPhase}
        error={error}
        quotaError={quotaError}
        retryCountdown={retryCountdown ?? null}
        retryMessage={retryMessage ?? null}
        retryExhausted={!!retryExhausted}
        onRetry={onSearch}
        onRetryNow={onRetryNow || onSearch}
        onCancelRetry={onCancelRetry || (() => {})}
        onCancel={onCancel}
        loading={loading}
        hasPartialResults={!!(result && result.resumo && result.resumo.total_oportunidades > 0)}
      />

      {/* CRIT-027 AC2-AC3: Only show result states AFTER search completes (not during loading) */}
      {/* CRIT-005 AC5-7: Route by response_state — empty_failure gets SourcesUnavailable */}
      {/* P2.2: degraded_expired is excluded — it has data and gets its own banner below */}
      {!loading && result && result.response_state === "empty_failure" && (
        <SourcesUnavailable
          onRetry={onSearch}
          onLoadLastSearch={onLoadLastSearch || (() => {})}
          hasLastSearch={hasLastSearch}
          retrying={loading}
          degradationGuidance={result.degradation_guidance}
        />
      )}

      {/* GTM-RESILIENCE-A01 AC7 + STORY-257B AC10: All sources down (partial with zero results, not empty_failure or degraded_expired) */}
      {!loading && result && result.response_state !== "empty_failure" && result.response_state !== "degraded_expired" && result.is_partial && (result.total_raw || 0) === 0 && result.resumo.total_oportunidades === 0 && !result.cached && (
        <SourcesUnavailable
          onRetry={onSearch}
          onLoadLastSearch={onLoadLastSearch || (() => {})}
          hasLastSearch={hasLastSearch}
          retrying={loading}
          degradationGuidance={result.degradation_guidance}
        />
      )}

      {/* P2.2: Expired cache fallback — all sources failed but backend has stale cached data.
           Show a prominent amber warning banner above the results.
           The main result display block below handles rendering the licitacoes as normal.
           This banner REPLACES the SourcesUnavailable blank error screen for this state. */}
      {!loading && result && result.response_state === "degraded_expired" && result.cached_at && (
        <ExpiredCacheBanner
          cachedAt={result.cached_at}
          onRetry={onSearch}
          loading={loading}
        />
      )}

      {/* STORY-252 AC23: Partial results, but all filtered out (total_raw>0, total_filtrado=0, is_partial=true) */}
      {!loading && result && result.is_partial && (result.total_raw || 0) > 0 && result.resumo.total_oportunidades === 0 && (
        <>
          {/* GTM-UX-001: DataQualityBanner replaces OperationalStateBanner */}
          <DataQualityBanner
            totalUfs={ufsSelecionadas.size}
            succeededUfs={ufsSelecionadas.size - (result.failed_ufs?.length ?? 0)}
            failedUfs={result.failed_ufs ?? []}
            isCached={!!result.cached && !liveFetchInProgress && !refreshAvailable}
            cachedAt={result.cached_at}
            cacheStatus={result.cache_status}
            isTruncated={!!result.is_truncated}
            cacheFallback={result.cache_fallback}
            cacheDateRange={result.cache_date_range}
            sourcesTotal={result.source_stats?.length ?? 1}
            sourcesAvailable={result.source_stats?.filter((s: { status: string }) => s.status === "success" || s.status === "partial").length ?? (result.source_stats?.length ?? 1)}
            sourceNames={result.source_stats?.map((s: { source_code: string }) => s.source_code)}
            responseState={result.response_state}
            coveragePct={result.coverage_pct}
            onRefresh={onRetryForceFresh || onSearch}
            onRetry={onSearch}
            loading={loading}
          />
          <EmptyState
            onAdjustSearch={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            rawCount={rawCount}
            stateCount={ufsSelecionadas.size}
            filterStats={result.filter_stats}
            sectorName={sectorName}
          />
        </>
      )}

      {/* GTM-UX-002 AC10-12 + STAB-005 AC2: Zero results with actionable suggestions — legitimate zero results (not caused by API failure) */}
      {!loading && result && !result.is_partial && result.response_state !== "empty_failure" && result.resumo.total_oportunidades === 0 && (
        <ZeroResultsSuggestions
          sectorName={sectorName}
          ufCount={ufsSelecionadas.size}
          ufNames={Array.from(ufsSelecionadas)}
          dayRange={30}
          onAdjustPeriod={onAdjustPeriod}
          onAddNeighborStates={onAddNeighborStates}
          onChangeSector={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          nearbyResultsCount={nearbyResultsCount}
          onViewNearbyResults={onViewNearbyResults}
          totalFromSources={result.total_raw}
          filterStats={result.filter_stats}
        />
      )}

      {/* STAB-005 AC4: Filter relaxation banner — shown when filter was relaxed and we have results */}
      {!loading && result && result.filter_relaxed && result.resumo.total_oportunidades > 0 && (
        <FilterRelaxedBanner
          relaxationLevel={result.hidden_by_min_match != null && result.hidden_by_min_match > 0 ? "min_match_lowered" : undefined}
          originalCount={0}
          relaxedCount={result.resumo.total_oportunidades}
        />
      )}

      {/* A-04 AC8: Refresh banner when background fetch completes */}
      {/* CRIT-030 AC4: Guard with !loading to prevent bleed from previous search */}
      {!loading && refreshAvailable && onRefreshResults && (
        <div className="mt-4">
          <RefreshBanner
            refreshInfo={refreshAvailable}
            onRefresh={onRefreshResults}
          />
        </div>
      )}

      {/* CRIT-027 AC7: "Atualizando..." only when live fetch actually in progress AND not loading a new search */}
      {!loading && liveFetchInProgress && !refreshAvailable && result && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-200" role="status">
          <svg className="h-4 w-4 animate-spin flex-shrink-0" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Atualizando dados em tempo real...</span>
        </div>
      )}

      {/* Result Display — CRIT-027 AC2: only after loading completes */}
      {!loading && result && result.resumo.total_oportunidades > 0 && (
        <div className={`mt-6 sm:mt-8 space-y-4 sm:space-y-6 ${!showGrid ? 'animate-fade-in-up' : ''}`}>
          {/* STORY-320 AC12: Persistent non-dismissable banner for limited_access (days 8-14) */}
          {trialPhase === "limited_access" && (
            <div
              className="p-3 rounded-card bg-gradient-to-r from-blue-600 to-purple-600 text-white flex items-center justify-between"
              data-testid="trial-paywall-banner"
              role="banner"
            >
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-sm font-medium">
                  Voce esta no modo preview. Desbloqueie acesso completo ao SmartLic.
                </span>
              </div>
              <Link
                href="/planos"
                className="text-sm font-bold bg-white/20 hover:bg-white/30 px-4 py-1.5 rounded-button transition-colors whitespace-nowrap"
                data-testid="trial-paywall-banner-cta"
              >
                Ver planos
              </Link>
            </div>
          )}

          {/* GTM-UX-001: Single unified DataQualityBanner replaces FailedUfsBanner,
              TruncationWarningBanner, PartialResultsBanner, OperationalStateBanner, CacheBanner
              P2.2: Skip for degraded_expired — ExpiredCacheBanner is already shown above */}
          {result.response_state !== "degraded_expired" && (
            <DataQualityBanner
              totalUfs={ufsSelecionadas.size}
              succeededUfs={ufsSelecionadas.size - (result.failed_ufs?.length ?? 0)}
              failedUfs={result.failed_ufs ?? []}
              isCached={!!result.cached && !liveFetchInProgress && !refreshAvailable}
              cachedAt={result.cached_at}
              cacheStatus={result.cache_status}
              isTruncated={!!result.is_truncated}
              cacheFallback={result.cache_fallback}
              cacheDateRange={result.cache_date_range}
              sourcesTotal={result.source_stats?.length ?? 1}
              sourcesAvailable={result.source_stats?.filter((s: { status: string }) => s.status === "success" || s.status === "partial").length ?? (result.source_stats?.length ?? 1)}
              sourceNames={result.source_stats?.map((s: { source_code: string }) => s.source_code)}
              responseState={result.response_state}
              coveragePct={result.coverage_pct}
              onRefresh={onRetryForceFresh || onSearch}
              onRetry={onSearch}
              loading={loading}
            />
          )}

          {/* STORY-354 AC3: Pending review banner */}
          {(pendingReviewCount > 0 || (pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0)) && (
            <div
              className={`flex items-start gap-3 p-3 rounded-lg border ${
                pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0
                  ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800"
                  : "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
              }`}
              data-testid="pending-review-banner"
            >
              <svg className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0
                  ? "text-emerald-500"
                  : "text-blue-500"
              }`} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div className="text-sm">
                {pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0 ? (
                  <p className="text-emerald-800 dark:text-emerald-300">
                    Reclassificação concluída: {pendingReviewUpdate.acceptedCount} oportunidades confirmadas
                    {pendingReviewUpdate.rejectedCount > 0 && `, ${pendingReviewUpdate.rejectedCount} descartadas`}.
                  </p>
                ) : (
                  <p className="text-blue-800 dark:text-blue-300">
                    {pendingReviewCount} {pendingReviewCount === 1 ? 'oportunidade aguarda' : 'oportunidades aguardam'} reclassificação (IA temporariamente indisponível)
                  </p>
                )}
              </div>
            </div>
          )}

          {/* UX-348 AC7-AC8: Results header with positive framing */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-strong">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-lg font-semibold text-ink" data-testid="results-header">
                  {result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'oportunidade selecionada' : 'oportunidades selecionadas'}{rawCount > 0 ? ` de ${rawCount.toLocaleString("pt-BR")} analisadas` : ''}
                </h2>
                {/* STORY-260 AC17: "Análise personalizada" badge when profile is complete */}
                {isProfileComplete && result.resumo.total_oportunidades > 0 && (
                  <div
                    className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 text-xs rounded-full"
                    title="Resultados otimizados para o perfil da sua empresa"
                    data-testid="personalized-analysis-badge"
                  >
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    {`Análise personalizada`}
                  </div>
                )}
              </div>
              {filterSummary && filterSummary.totalRaw > 0 && (
                <p className="text-sm text-ink-secondary mt-0.5" data-testid="filter-context-line">
                  Analisamos {filterSummary.totalRaw.toLocaleString("pt-BR")} oportunidades e selecionamos {result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'compatível' : 'compatíveis'} com seu perfil
                  {/* C-02 AC9: Confidence distribution counts */}
                  {(() => {
                    const counts = { high: 0, medium: 0, low: 0 };
                    let hasAny = false;
                    result.licitacoes.forEach(l => {
                      if (l.confidence === "high") { counts.high++; hasAny = true; }
                      else if (l.confidence === "medium") { counts.medium++; hasAny = true; }
                      else if (l.confidence === "low") { counts.low++; hasAny = true; }
                    });
                    if (!hasAny) return null;
                    const parts: string[] = [];
                    if (counts.high > 0) parts.push(`${counts.high} alta`);
                    if (counts.medium > 0) parts.push(`${counts.medium} média`);
                    if (counts.low > 0) parts.push(`${counts.low} baixa`);
                    return <span className="text-ink-muted"> ({parts.join(", ")})</span>;
                  })()}
                </p>
              )}
            </div>
          </div>

          {/* UX-404 AC2-AC5: Inline tour invite banner */}
          <TourInviteBanner
            isCompleted={isResultsTourCompleted}
            onStartTour={onStartResultsTour}
          />

          {/* STORY-333 AC9-AC13: Sticky Action Bar */}
          <div
            className="sticky top-0 z-30 bg-[var(--canvas)] border-b border-[var(--border)] -mx-1 px-1 py-3"
            data-testid="sticky-action-bar"
            id="results-top"
          >
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
              {/* Row 1: Sort + action buttons */}
              <div className="flex items-center gap-2 flex-wrap">
                <OrdenacaoSelect
                  value={ordenacao}
                  onChange={onOrdenacaoChange}
                  disabled={loading}
                />

                {/* Excel button (compact) */}
                {planInfo?.capabilities.allow_excel && !isTrialExpired && !(paywallApplied && totalBeforePaywall) && (
                  (() => {
                    const hasDownload = !!(result.download_url || result.download_id);
                    const isFailed = (result.excel_status === 'failed' || excelTimedOut) && !hasDownload;
                    const isProcessing = result.excel_status === 'processing' && !hasDownload && !isFailed;

                    if (isProcessing) {
                      return (
                        <button
                          disabled
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
                                     bg-[var(--brand-navy)]/70 text-white rounded-button cursor-wait"
                          data-testid="excel-processing-button"
                        >
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" aria-label="Gerando Excel" role="img">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Gerando Excel...
                        </button>
                      );
                    }

                    if (isFailed) {
                      return (
                        <button
                          onClick={onRegenerateExcel || onSearch}
                          disabled={loading}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
                                     bg-amber-600 hover:bg-amber-700 text-white rounded-button
                                     disabled:opacity-50 disabled:cursor-not-allowed"
                          data-testid="excel-retry-button"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Gerar novamente
                        </button>
                      );
                    }

                    return (
                      <button
                        onClick={onDownload}
                        disabled={downloadLoading}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
                                   bg-[var(--brand-navy)] text-white rounded-button
                                   hover:bg-[var(--brand-blue-hover)]
                                   disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        data-testid="excel-download-button"
                        aria-label={`Baixar Excel com ${result.resumo.total_oportunidades} licitações`}
                      >
                        {downloadLoading ? (
                          <>
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" aria-label="Preparando" role="img">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Preparando download...
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Baixar Excel ({result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'licitação' : 'licitações'})
                          </>
                        )}
                      </button>
                    );
                  })()
                )}

                {/* Google Sheets button (compact) — AC18 */}
                {planInfo?.capabilities.allow_excel && !isTrialExpired && (
                  <GoogleSheetsExportButton
                    licitacoes={result.licitacoes}
                    searchLabel={`${sectorName} - ${Array.from(ufsSelecionadas).join(', ')}`}
                    disabled={downloadLoading}
                    session={session}
                  />
                )}

                {/* PDF button (compact) */}
                {session?.access_token && result && !isTrialExpired && onGeneratePdf && (
                  <button
                    onClick={() => onGeneratePdf({ clientName: "", maxItems: 20 })}
                    disabled={pdfLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
                               border border-[var(--brand-navy)] text-[var(--brand-navy)]
                               dark:border-[var(--brand-blue)] dark:text-[var(--brand-blue)]
                               rounded-button hover:bg-[var(--brand-blue-subtle)] transition-colors
                               disabled:opacity-50 disabled:cursor-not-allowed"
                    data-testid="pdf-report-button"
                  >
                    {pdfLoading ? (
                      <>
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" aria-label="Gerando PDF" role="img">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Gerando PDF...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        Relatório PDF ({result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'oportunidade' : 'oportunidades'})
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Opportunity count — right side */}
              <span className="text-sm text-[var(--ink-secondary)] sm:ml-auto whitespace-nowrap" data-testid="sticky-count">
                {result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'oportunidade' : 'oportunidades'}
              </span>
            </div>

            {/* AC13: Skeleton state during loading */}
            {loading && (
              <div className="flex items-center gap-3 mt-2 animate-pulse">
                <div className="h-8 w-28 bg-[var(--surface-1)] rounded" />
                <div className="h-8 w-24 bg-[var(--surface-1)] rounded" />
                <div className="h-8 w-20 bg-[var(--surface-1)] rounded" />
                <div className="h-4 w-32 bg-[var(--surface-1)] rounded ml-auto" />
              </div>
            )}
          </div>

          {/* GTM-FIX-028 AC16: LLM zero-match analysis note */}
          {result.filter_stats && (result.filter_stats.llm_zero_match_calls ?? 0) > 0 && (
            <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/40 rounded-card text-sm text-blue-800 dark:text-blue-200 flex items-center gap-2">
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span>
                IA analisou {result.filter_stats.llm_zero_match_calls} licitações adicionais para identificar oportunidades relevantes
                {(result.filter_stats.llm_zero_match_aprovadas ?? 0) > 0 && (
                  <> — {result.filter_stats.llm_zero_match_aprovadas} aprovadas</>
                )}
              </span>
            </div>
          )}

          {/* STORY-246 AC10: Active filter summary */}
          <div className="flex flex-wrap items-center gap-2 text-sm text-ink-secondary">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <span className="font-medium text-ink">Filtros ativos:</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-brand-blue-subtle text-brand-navy text-xs font-medium">
              {ufsSelecionadas.size === 27 ? '27 UFs (todo o Brasil)' : `${ufsSelecionadas.size} UF${ufsSelecionadas.size !== 1 ? 's' : ''}`}
            </span>
            <span className="text-ink-faint">•</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-brand-blue-subtle text-brand-navy text-xs font-medium">
              Licitações abertas
            </span>
            {searchMode === 'setor' && (
              <>
                <span className="text-ink-faint">•</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-brand-blue-subtle text-brand-navy text-xs font-medium">
                  {sectorName}
                </span>
              </>
            )}
          </div>

          {/* Search terms metadata banner */}
          {(result.metadata || result.termos_utilizados || result.stopwords_removidas) && (
            <div className="bg-surface-1 border border-border rounded-card p-4">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-brand-blue flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-ink mb-2">
                    Termos utilizados na análise:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(result.metadata?.termos_utilizados || result.termos_utilizados || []).map(term => (
                      <span
                        key={term}
                        className="inline-flex items-center px-2.5 py-1 bg-brand-blue-subtle text-brand-navy rounded-full text-xs font-medium border border-brand-blue/20"
                      >
                        {term}
                      </span>
                    ))}
                  </div>

                  {result.metadata && result.metadata.termos_ignorados.length > 0 && (
                    <details className="mt-3 cursor-pointer group">
                      <summary className="text-sm text-ink-muted hover:text-ink transition-colors list-none flex items-center gap-2">
                        <svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="font-medium">
                          {result.metadata.termos_ignorados.length} termo{result.metadata.termos_ignorados.length > 1 ? 's' : ''} não utilizado{result.metadata.termos_ignorados.length > 1 ? 's' : ''}
                        </span>
                      </summary>
                      <div className="mt-2 pl-6 space-y-1">
                        {result.metadata.termos_ignorados.map(term => (
                          <div key={term} className="text-xs text-ink-secondary">
                            <strong className="text-ink">&quot;{term}&quot;</strong>: {result.metadata!.motivos_ignorados[term]}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                  {!result.metadata && result.stopwords_removidas && result.stopwords_removidas.length > 0 && (
                    <p className="text-xs text-ink-muted mt-2">
                      Termos ignorados (stopwords): {result.stopwords_removidas.join(", ")}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Filter relaxed banner */}
          {result.filter_relaxed && (
            <div className="px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 rounded-card text-sm text-amber-800 dark:text-amber-200 flex items-center gap-2">
              <svg role="img" aria-label="Aviso" className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>
                Nenhum resultado atendeu todos os critérios de relevância. Os filtros foram flexibilizados para exibir resultados parciais.
              </span>
            </div>
          )}

          {/* Hidden results indicator */}
          {result.hidden_by_min_match != null && result.hidden_by_min_match > 0 && (
            <div className="px-4 py-3 bg-surface-2 border border-border rounded-card text-sm text-ink-secondary flex items-center justify-between">
              <span>
                {result.hidden_by_min_match} resultado{result.hidden_by_min_match > 1 ? "s" : ""} com correspondência parcial {result.hidden_by_min_match > 1 ? "foram ocultados" : "foi ocultado"}.
              </span>
              <button
                onClick={() => {
                  onTrackEvent("show_hidden_results", {
                    hidden_count: result.hidden_by_min_match,
                  });
                }}
                className="text-brand-navy dark:text-brand-blue font-medium hover:underline shrink-0 ml-3"
              >
                Mostrar todos
              </button>
            </div>
          )}

          {/* Summary Card */}
          <div className="p-4 sm:p-6 bg-brand-blue-subtle border border-accent rounded-card relative">
            {/* CRIT-005 AC16: LLM source badge near the summary */}
            <div className="flex items-center gap-2 mb-3">
              <LlmSourceBadge llmSource={result.llm_source} />
            </div>

            {/* STORY-320 AC9: Truncate AI summary in limited_access */}
            <p className="text-base sm:text-lg leading-relaxed text-ink">
              {trialPhase === "limited_access"
                ? result.resumo.resumo_executivo.split('. ').slice(0, 2).join('. ') + '...'
                : result.resumo.resumo_executivo}
            </p>

            {/* STORY-320 AC9: Paywall overlay on summary */}
            {trialPhase === "limited_access" && (
              <div className="mt-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-700/40 rounded-lg flex items-center justify-between">
                <span className="text-sm text-blue-800 dark:text-blue-200">
                  Ver análise completa com SmartLic Pro
                </span>
                <Link
                  href="/planos"
                  className="text-sm font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                  data-testid="summary-paywall-cta"
                >
                  Assinar
                </Link>
              </div>
            )}

            <div className="flex flex-col sm:flex-row flex-wrap gap-4 sm:gap-8 mt-4 sm:mt-6">
              <div>
                <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
                  {result.resumo.total_oportunidades}
                </span>
                <span className="text-sm sm:text-base text-ink-secondary block mt-1">{result.resumo.total_oportunidades === 1 ? 'licitação' : 'licitações'}</span>
              </div>
              <div>
                <span className="text-3xl sm:text-4xl font-bold font-data tabular-nums text-brand-navy dark:text-brand-blue">
                  R$ {result.resumo.valor_total.toLocaleString("pt-BR")}
                </span>
                <span className="text-sm sm:text-base text-ink-secondary block mt-1">valor total</span>
              </div>
            </div>

            {/* AC11: Insight Setorial Banner */}
            {result.resumo.insight_setorial && (
              <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-brand-blue-subtle/50 border border-accent/30 rounded-card">
                <p className="text-sm sm:text-base text-ink-secondary leading-relaxed">
                  <span className="font-semibold text-brand-navy dark:text-brand-blue">Contexto do setor: </span>
                  {result.resumo.insight_setorial}
                </p>
              </div>
            )}

            {/* AC12: Multiple Urgency Alerts */}
            {result.resumo.alertas_urgencia && result.resumo.alertas_urgencia.length > 0 ? (
              <div className="mt-4 sm:mt-6 space-y-2" role="alert">
                {result.resumo.alertas_urgencia.map((alerta, i) => (
                  <div key={i} className="p-3 sm:p-4 bg-warning-subtle border border-warning/20 rounded-card">
                    <p className="text-sm sm:text-base font-medium text-warning">{alerta}</p>
                  </div>
                ))}
              </div>
            ) : result.resumo.alerta_urgencia ? (
              <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-warning-subtle border border-warning/20 rounded-card" role="alert">
                <p className="text-sm sm:text-base font-medium text-warning">
                  <span aria-hidden="true">Atencao: </span>
                  {result.resumo.alerta_urgencia}
                </p>
              </div>
            ) : null}

            {/* AC10 + UX-350 AC5-AC8: Recommendation Cards with strategic context */}
            {result.resumo.recomendacoes && result.resumo.recomendacoes.length > 0 && (
              <div className="mt-4 sm:mt-6">
                {/* AC5: Proper accents in title */}
                <h4 className="text-base sm:text-lg font-semibold font-display text-ink mb-3 sm:mb-4">Recomendações Estratégicas:</h4>

                {/* AC6/AC16: Incomplete profile banner with CTA — dismissible, localStorage 3-day TTL */}
                {!isProfileComplete && !bannerDismissed && (
                  <div className="mb-3 p-3 bg-amber-50 dark:bg-amber-900/15 border border-amber-200 dark:border-amber-700/40 rounded-card flex items-center gap-3" data-testid="profile-incomplete-banner">
                    <svg className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-amber-800 dark:text-amber-200 flex-1">
                      Complete seu perfil para recomendações mais precisas.{' '}
                      <Link href="/conta" className="font-semibold underline underline-offset-2 hover:text-amber-900 dark:hover:text-amber-100">
                        Completar perfil →
                      </Link>
                    </p>
                    <button
                      type="button"
                      onClick={handleDismissBanner}
                      className="ml-auto flex-shrink-0 text-amber-600 dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-100 transition-colors"
                      aria-label="Fechar aviso"
                      data-testid="profile-banner-dismiss"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )}

                {/* AC8: AI transparency label */}
                <p className="text-xs text-ink-muted mb-3" data-testid="ai-transparency-label">
                  Análise gerada por IA com base no seu perfil e no edital
                </p>

                <div className="space-y-3">
                  {result.resumo.recomendacoes.map((rec, i) => {
                    // AC7: Find matching licitacao to get its official link
                    const matchedBid = result.licitacoes.find(l =>
                      rec.oportunidade && (
                        l.orgao && rec.oportunidade.includes(l.orgao) ||
                        l.objeto && rec.oportunidade.includes(l.objeto.substring(0, 40))
                      )
                    );
                    return (
                      <div
                        key={i}
                        className="p-3 sm:p-4 bg-surface border border-border rounded-card animate-fade-in-up"
                        style={{ animationDelay: `${i * 80}ms` }}
                      >
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                            rec.urgencia === "alta"
                              ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                              : rec.urgencia === "media"
                              ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300"
                              : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                          }`}>
                            {rec.urgencia === "alta" ? "Urgente" : rec.urgencia === "media" ? "Atenção" : "Normal"}
                          </span>
                          <span className="text-sm font-semibold text-brand-navy dark:text-brand-blue">
                            R$ {rec.valor.toLocaleString("pt-BR")}
                          </span>
                        </div>
                        <p className="text-sm sm:text-base font-medium text-ink mb-1">{rec.oportunidade}</p>
                        <p className="text-sm text-brand-navy dark:text-brand-blue font-medium mb-1">{rec.acao_sugerida}</p>
                        <p className="text-xs sm:text-sm text-ink-secondary">{rec.justificativa}</p>
                        {/* AC7: Link to official source */}
                        {matchedBid?.link && (
                          <a
                            href={matchedBid.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-brand-navy dark:text-brand-blue hover:underline"
                            data-testid="rec-edital-link"
                          >
                            Ver edital na fonte oficial
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {result.resumo.destaques && result.resumo.destaques.length > 0 && (
              <div className="mt-4 sm:mt-6">
                <h4 className="text-base sm:text-lg font-semibold font-display text-ink mb-2 sm:mb-3">Destaques:</h4>
                <ul className="list-disc list-inside text-sm sm:text-base space-y-2 text-ink-secondary">
                  {result.resumo.destaques.map((d, i) => (
                    <li key={i} className="animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Quota Counter */}
          {planInfo && (
            <QuotaCounter
              quotaUsed={planInfo.quota_used}
              quotaLimit={planInfo.capabilities.max_requests_per_month}
              resetDate={planInfo.quota_reset_date}
              planId={planInfo.plan_id}
              onUpgradeClick={() => {
                onShowUpgradeModal(undefined, "quota_counter");
              }}
            />
          )}

          {/* STORY-312 AC5: Quota approaching CTA when >= 80% usage */}
          {planInfo && planInfo.capabilities.max_requests_per_month > 0 &&
           (planInfo.quota_used / planInfo.capabilities.max_requests_per_month) >= 0.8 && (
            <TrialUpsellCTA
              variant="quota"
              planId={planInfo.plan_id}
              subscriptionStatus={planInfo.subscription_status}
              contextData={{
                usageLabel: `${planInfo.quota_used}/${planInfo.capabilities.max_requests_per_month}`,
                usagePct: Math.round((planInfo.quota_used / planInfo.capabilities.max_requests_per_month) * 100),
              }}
            />
          )}

          {/* UX-352 AC6: Clear visual separator between summary and opportunities list */}
          {result.licitacoes && result.licitacoes.length > 0 && (
            <div className="border-t border-strong" />
          )}

          {/* STORY-333 AC3: Top Pagination */}
          {totalLicitacoes > 0 && (
            <Pagination
              totalItems={totalLicitacoes}
              currentPage={currentPage}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
              onPageSizeChange={setPageSize}
              scrollTargetId="results-top"
            />
          )}

          {/* STORY-333 AC2: Licitacoes Preview — paginated client-side */}
          {paginatedLicitacoes.length > 0 && (
            <LicitacoesPreview
              licitacoes={paginatedLicitacoes}
              previewCount={pageSize}
              excelAvailable={planInfo?.capabilities.allow_excel ?? false}
              searchTerms={searchMode === "termos" ? termosArray : (result.termos_utilizados || [])}
              onUpgradeClick={() => {
                onShowUpgradeModal("smartlic_pro", "licitacoes_preview");
              }}
              searchId={searchId}
              setorId={setorId}
              accessToken={session?.access_token}
              bidAnalysis={result.bid_analysis}
              bidAnalysisStatus={result.bid_analysis_status}
            />
          )}

          {/* STORY-333 AC3: Bottom Pagination */}
          {totalLicitacoes > 0 && (
            <Pagination
              totalItems={totalLicitacoes}
              currentPage={currentPage}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
              onPageSizeChange={setPageSize}
              scrollTargetId="results-top"
            />
          )}

          {/* STORY-320 AC7: Blurred results preview + paywall overlay for limited_access */}
          {paywallApplied && totalBeforePaywall && totalBeforePaywall > result.licitacoes.length && (
            <div className="relative mt-4" data-testid="paywall-blurred-results">
              {/* Blurred placeholder cards */}
              <div className="space-y-3 blur-sm pointer-events-none select-none" aria-hidden="true">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-4 bg-surface border border-border rounded-card">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded-full font-medium">Preview</span>
                    </div>
                    <div className="h-4 bg-[var(--surface-1)] rounded w-3/4 mb-2" />
                    <div className="h-3 bg-[var(--surface-1)] rounded w-1/2" />
                  </div>
                ))}
              </div>
              {/* Paywall overlay */}
              <TrialPaywall
                additionalCount={totalBeforePaywall - result.licitacoes.length}
                context="search_results"
              />
            </div>
          )}

          {/* STORY-333: Buttons moved to sticky action bar. Keep upgrade CTAs below. */}

          {/* STORY-320 AC8 / STORY-265: Paywall/trial expired upgrade CTAs */}
          {paywallApplied && totalBeforePaywall ? (
            <div className="relative">
              <button
                onClick={onDownload}
                disabled={downloadLoading}
                className="w-full bg-surface-0 border-2 border-blue-500 text-blue-700 dark:text-blue-300 py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                           hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-all duration-200
                           flex items-center justify-center gap-3
                           disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="excel-paywall-button"
                title={`Assine o SmartLic Pro para exportar todos os ${totalBeforePaywall} resultados`}
              >
                {downloadLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-label="Carregando" role="img">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Preparando preview...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    Baixar Preview ({result.licitacoes.length} resultados)
                  </>
                )}
              </button>
            </div>
          ) : isTrialExpired ? (
            <Link
              href="/planos"
              className="w-full bg-surface-0 border-2 border-amber-500 text-amber-700 dark:text-amber-300 py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                         hover:bg-amber-50 dark:hover:bg-amber-900/10 transition-all duration-200
                         flex items-center justify-center gap-3"
              data-testid="excel-trial-expired-button"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Ative seu plano para exportar
            </Link>
          ) : !planInfo?.capabilities.allow_excel ? (
            <Link
              href="/planos"
              className="w-full bg-surface-0 border-2 border-brand-navy text-brand-navy py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                         hover:bg-brand-blue-subtle transition-all duration-200
                         flex items-center justify-center gap-3"
              aria-label="Assine um plano para exportar resultados em Excel e Google Sheets"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Assine para exportar resultados e acessar funcionalidades premium
            </Link>
          ) : null}

          {/* STORY-301 AC11: Create alert from this search */}
          {session?.access_token && result && (
            <a
              href={`/alertas?from_search=1&setor=${encodeURIComponent(searchMode === "setor" ? (result as any).setor_id || "" : "")}&ufs=${encodeURIComponent(Array.from(ufsSelecionadas).join(","))}&keywords=${encodeURIComponent(termosArray.join(","))}`}
              className="w-full bg-surface-0 border-2 border-brand-navy text-brand-navy py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                         hover:bg-brand-blue-subtle transition-all duration-200
                         flex items-center justify-center gap-3"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
              Criar alerta a partir desta análise
            </a>
          )}

          {/* Download Error */}
          {downloadError && (
            <div className="p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card" role="alert">
              <p className="text-sm sm:text-base font-medium text-error">{downloadError}</p>
            </div>
          )}

          {/* Stats + Timestamp + Source Indicators (GTM-FIX-011) */}
          <div className="text-xs sm:text-sm text-ink-muted text-center space-y-1">
            {rawCount > 0 && (
              <p>
                {result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'oportunidade selecionada' : 'oportunidades selecionadas'} de {rawCount.toLocaleString("pt-BR")} analisadas
                {searchMode === "setor" && sectorName !== "Licitações" ? ` para o setor ${sectorName.toLowerCase()}` : ''}
                {/* AC19: Source count summary with tooltip */}
                {result.sources_used && result.sources_used.length > 1 && (
                  <span
                    className="ml-1 cursor-help border-b border-dotted border-ink-faint"
                    title={result.source_stats
                      ?.filter((s: { status: string }) => s.status === "success" || s.status === "partial")
                      .map((s: { source_code: string; record_count: number }) => `${s.source_code}: ${s.record_count} registros`)
                      .join('\n') || ''}
                  >
                    (dados de multiplas fontes)
                  </span>
                )}
              </p>
            )}
            {/* AC21: Partial failure — simple message without technical source names */}
            {result.is_partial && !result.cached && result.sources_used && result.sources_used.length > 0 && (
              <p className="text-amber-600 dark:text-amber-400">
                Análise concluída | Fonte temporariamente indisponível (dados podem estar incompletos)
              </p>
            )}
            {/* AC22: Source badges — hidden by default, toggle for power users */}
            {result.source_stats && result.source_stats.length > 1 && (
              <div className="space-y-1">
                <button
                  onClick={() => setShowSourceBadges(!showSourceBadges)}
                  className="text-ink-faint hover:text-ink-secondary transition-colors text-xs underline-offset-2 hover:underline"
                  aria-expanded={showSourceBadges}
                >
                  {showSourceBadges ? 'Ocultar fontes' : 'Mostrar fontes'}
                </button>
                {showSourceBadges && (
                  <div className="flex items-center justify-center gap-2 animate-fade-in">
                    {result.source_stats
                      .filter((s: { status: string }) => s.status === "success" || s.status === "partial")
                      .map((s: { source_code: string; record_count: number; status: string }) => (
                        <span
                          key={s.source_code}
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                            s.source_code === 'PNCP'
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                              : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                          }`}
                        >
                          {s.source_code === 'PNCP' ? (
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" /></svg>
                          ) : (
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" /></svg>
                          )}
                          {s.source_code}: {s.record_count}
                        </span>
                      ))}
                  </div>
                )}
              </div>
            )}
            {result.ultima_atualizacao && (
              <p className="text-ink-faint">
                <svg className="w-3.5 h-3.5 inline mr-1 -mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Atualizado em {new Date(result.ultima_atualizacao).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })}
              </p>
            )}
          </div>

          {/* STORY-312 AC1: Post-search CTA for trial users with >= 10 results */}
          {result.resumo.total_oportunidades >= 10 && (
            <TrialUpsellCTA
              variant="post-search"
              planId={planInfo?.plan_id}
              subscriptionStatus={planInfo?.subscription_status}
              contextData={{ opportunities: result.resumo.total_oportunidades }}
            />
          )}

          {/* STORY-312 AC2: Post-download CTA for trial users after Excel export */}
          {downloadCompleted && (
            <TrialUpsellCTA
              variant="post-download"
              planId={planInfo?.plan_id}
              subscriptionStatus={planInfo?.subscription_status}
              contextData={{ exportLimit: planInfo?.capabilities.max_requests_per_month ?? 1000 }}
            />
          )}

          {/* UX-352 AC11: Encouraging return message */}
          <p className="text-center text-sm text-ink-muted py-2" data-testid="return-invitation">
            Novas oportunidades são publicadas diariamente. Volte amanhã para conferir.
          </p>
        </div>
      )}
    </>
  );
}
