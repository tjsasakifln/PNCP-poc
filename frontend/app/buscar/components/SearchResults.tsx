"use client";

import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import Link from "next/link";
import type { BuscaResult } from "../../types";
import RefreshBanner from "./RefreshBanner";
import { UfProgressGrid } from "./UfProgressGrid";
import { SourcesUnavailable } from "./SourcesUnavailable";
import { DataQualityBanner } from "./DataQualityBanner";
import { QuotaCounter } from "../../components/QuotaCounter";
import { ZeroResultsSuggestions } from "./ZeroResultsSuggestions";
import { ZeroMatchBadge } from "./ZeroMatchBadge";
import type {
  SearchResultsProps,
  SearchResultsData,
  SearchLoadingState,
  SearchResultsFilters,
  SearchResultsActions,
  SearchDisplayState,
  SearchAuthState,
  SearchFeedbackState,
  SearchResultsGroupedProps,
} from "../types/search-results";
import { FilterRelaxedBanner } from "./FilterRelaxedBanner";
import { ExpiredCacheBanner } from "./ExpiredCacheBanner";
import { SearchStateManager } from "./SearchStateManager";
import { deriveSearchPhase } from "../types/searchPhase";
import { TrialUpsellCTA } from "../../../components/billing/TrialUpsellCTA";
import { EmptyState } from "../../components/EmptyState";

// TD-007: Decomposed sub-components
import { ResultsHeader } from "./search-results/ResultsHeader";
import { ResultsToolbar } from "./search-results/ResultsToolbar";
import { ResultsFilters } from "./search-results/ResultsFilters";
import { ResultCard } from "./search-results/ResultCard";
import { ResultsList } from "./search-results/ResultsList";
import { ResultsLoadingSection } from "./search-results/ResultsLoadingSection";
import { ResultsFooter } from "./search-results/ResultsFooter";

// Re-exports for backward compatibility
export type { SearchResultsProps } from "../types/search-results";
export type { SearchResultsData, SearchLoadingState, SearchResultsFilters, SearchResultsActions, SearchDisplayState, SearchAuthState, SearchFeedbackState, SearchResultsGroupedProps } from "../types/search-results";

// UX-404: Inline tour invite banner (AC2-AC5)
export function TourInviteBanner({ isCompleted, onStartTour }: { isCompleted?: () => boolean; onStartTour?: () => void }) {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { if (!isCompleted || isCompleted() || dismissed) return; setVisible(true); }, [isCompleted, dismissed]);
  useEffect(() => { if (!visible) return; timerRef.current = setTimeout(() => { setVisible(false); setDismissed(true); }, 10_000); return () => { if (timerRef.current) clearTimeout(timerRef.current); }; }, [visible]);
  useEffect(() => { if (!visible) return; const h = () => { setVisible(false); setDismissed(true); }; window.addEventListener("scroll", h, { once: true, passive: true }); return () => window.removeEventListener("scroll", h); }, [visible]);

  const handleStart = useCallback(() => { setVisible(false); setDismissed(true); onStartTour?.(); }, [onStartTour]);
  const handleClose = useCallback(() => { setVisible(false); setDismissed(true); }, []);

  if (!visible) return null;
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/50 text-sm text-blue-800 dark:text-blue-200 animate-fade-in-up" data-testid="tour-invite-banner" role="status">
      <span>Primeira vez vendo resultados? Clique aqui para um tour rápido.</span>
      <div className="flex items-center gap-2 flex-shrink-0">
        <button onClick={handleStart} className="px-3 py-1 text-xs font-medium bg-blue-600 text-white rounded-button hover:bg-blue-700 transition-colors" data-testid="tour-invite-start">Iniciar tour</button>
        <button onClick={handleClose} className="p-1 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors" aria-label="Fechar" data-testid="tour-invite-close">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
    </div>
  );
}

/**
 * TD-007 AC7: SearchResults layout orchestrator.
 * Composes: ResultsLoadingSection, ResultsHeader, ResultsToolbar, ResultsFilters,
 * ResultCard, ResultsList, ResultsFooter.
 */
export default function SearchResults(props: SearchResultsProps) {
  const { loading, result, ufsSelecionadas, sectorName, searchMode, ordenacao, rawCount,
    error, quotaError, onSearch, onCancel, onOrdenacaoChange,
    ufStatuses, ufTotalFound = 0, searchElapsedSeconds = 0,
    isReconnecting, retryCountdown, retryMessage, retryExhausted, onRetryNow, onCancelRetry,
    hasLastSearch = 0, onLoadLastSearch, liveFetchInProgress, refreshAvailable, onRefreshResults,
    onRetryForceFresh, sourceStatuses, partialProgress, filterSummary,
    isTrialExpired, trialPhase, paywallApplied, totalBeforePaywall,
    pendingReviewCount = 0, pendingReviewUpdate, zeroMatchProgress, onTrackEvent,
    isResultsTourCompleted, onStartResultsTour, isProfileComplete = true,
    downloadLoading, downloadError, onDownload, planInfo, session, termosArray,
    onShowUpgradeModal, searchId, setorId, onRegenerateExcel, excelFailCount = 0,
    onGeneratePdf, pdfLoading,
  } = props;

  // --- State ---
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState<10 | 20 | 50>(() => {
    if (typeof window === "undefined") return 20;
    const s = localStorage.getItem("smartlic_page_size");
    return s && [10, 20, 50].includes(Number(s)) ? Number(s) as 10 | 20 | 50 : 20;
  });
  const [showGrid, setShowGrid] = useState(false);
  const [gridFading, setGridFading] = useState(false);
  const [excelTimedOut, setExcelTimedOut] = useState(false);
  const [downloadCompleted, setDownloadCompleted] = useState(false);
  const [prevDownloadLoading, setPrevDownloadLoading] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  useEffect(() => { setCurrentPage(1); }, [result, ordenacao]);
  useEffect(() => { if (typeof window === "undefined") return; const p = new URL(window.location.href).searchParams.get("page"); if (p && Number(p) > 0) setCurrentPage(Number(p)); }, []);
  useEffect(() => { if (typeof window === "undefined" || !result) return; const u = new URL(window.location.href); currentPage > 1 ? u.searchParams.set("page", String(currentPage)) : u.searchParams.delete("page"); window.history.replaceState({}, "", u.toString()); }, [currentPage, result]);
  useEffect(() => { if (loading && ufStatuses && ufStatuses.size > 0) { setShowGrid(true); setGridFading(false); } else if (!loading && showGrid) { setGridFading(true); const t = setTimeout(() => { setShowGrid(false); setGridFading(false); }, 400); return () => clearTimeout(t); } }, [loading, ufStatuses?.size]);
  useEffect(() => { if (result?.excel_status === 'processing' && !result?.download_url && !result?.download_id) { setExcelTimedOut(false); const t = setTimeout(() => setExcelTimedOut(true), 60_000); return () => clearTimeout(t); } setExcelTimedOut(false); }, [result?.excel_status, result?.download_url, result?.download_id]);
  useEffect(() => { if (prevDownloadLoading && !downloadLoading && !downloadError) setDownloadCompleted(true); setPrevDownloadLoading(downloadLoading); }, [downloadLoading, downloadError, prevDownloadLoading]);
  useEffect(() => { const d = localStorage.getItem('profile_banner_dismissed'); if (d && (Date.now() - parseInt(d)) / 86400000 < 3) setBannerDismissed(true); }, []);
  const handleDismissBanner = () => { localStorage.setItem('profile_banner_dismissed', String(Date.now())); setBannerDismissed(true); };

  // --- Derived ---
  const succeededUfCount = ufStatuses ? Array.from(ufStatuses.values()).filter(s => s.status === 'success' || s.status === 'recovered').length : 0;
  const pendingUfCount = ufStatuses ? Array.from(ufStatuses.values()).filter(s => s.status === 'pending' || s.status === 'fetching' || s.status === 'retrying').length : 0;
  const searchPhase = useMemo(() => deriveSearchPhase({ loading, error, quotaError, result, retryCountdown: retryCountdown ?? null, retryExhausted: !!retryExhausted, sourceStatuses: sourceStatuses ?? new Map(), partialProgress: partialProgress ?? null, ufTotalFound, searchElapsedSeconds }), [loading, error, quotaError, result, retryCountdown, retryExhausted, sourceStatuses, partialProgress, ufTotalFound, searchElapsedSeconds]);
  const paginatedLicitacoes = useMemo(() => { if (!result?.licitacoes) return []; const s = (currentPage - 1) * pageSize; return result.licitacoes.slice(s, s + pageSize); }, [result?.licitacoes, currentPage, pageSize]);
  const totalLicitacoes = result?.licitacoes?.length ?? 0;

  const renderDataQualityBanner = () => result && (
    <DataQualityBanner totalUfs={ufsSelecionadas.size} succeededUfs={ufsSelecionadas.size - (result.failed_ufs?.length ?? 0)} failedUfs={result.failed_ufs ?? []} isCached={!!result.cached && !liveFetchInProgress && !refreshAvailable} cachedAt={result.cached_at} cacheStatus={result.cache_status} isTruncated={!!result.is_truncated} cacheFallback={result.cache_fallback} cacheDateRange={result.cache_date_range} sourcesTotal={result.source_stats?.length ?? 1} sourcesAvailable={result.source_stats?.filter((s: { status: string }) => s.status === "success" || s.status === "partial").length ?? (result.source_stats?.length ?? 1)} sourceNames={result.source_stats?.map((s: { source_code: string }) => s.source_code)} responseState={result.response_state} coveragePct={result.coverage_pct} sourcesDegraded={result.sources_degraded} onRefresh={onRetryForceFresh || onSearch} onRetry={onSearch} loading={loading} />
  );

  return (
    <>
      {/* UF Progress Grid */}
      {showGrid && ufStatuses && ufStatuses.size > 0 && (
        <div className={`transition-all duration-400 ${gridFading ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`} style={{ minHeight: gridFading ? 0 : undefined }}>
          <UfProgressGrid ufStatuses={ufStatuses} totalFound={ufTotalFound} />
        </div>
      )}

      {isReconnecting && loading && (
        <div className="mb-2 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 animate-fade-in-up" role="status" data-testid="sse-reconnecting-banner">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-amber-600 dark:text-amber-400 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            <span className="text-sm text-amber-800 dark:text-amber-200">Reconectando...</span>
          </div>
        </div>
      )}

      <ResultsLoadingSection {...props} searchElapsedSeconds={searchElapsedSeconds} ufTotalFound={ufTotalFound} succeededUfCount={succeededUfCount} pendingUfCount={pendingUfCount} />

      <SearchStateManager phase={searchPhase} error={error} quotaError={quotaError} retryCountdown={retryCountdown ?? null} retryMessage={retryMessage ?? null} retryExhausted={!!retryExhausted} onRetry={onSearch} onRetryNow={onRetryNow || onSearch} onCancelRetry={onCancelRetry || (() => {})} onCancel={onCancel} loading={loading} hasPartialResults={!!(result && result.resumo && result.resumo.total_oportunidades > 0)} />

      {/* Empty/error states */}
      {!loading && result && result.response_state === "empty_failure" && <SourcesUnavailable onRetry={onSearch} onLoadLastSearch={onLoadLastSearch || (() => {})} hasLastSearch={!!hasLastSearch} retrying={loading} degradationGuidance={result.degradation_guidance} />}
      {!loading && result && result.response_state !== "empty_failure" && result.response_state !== "degraded_expired" && result.is_partial && (result.total_raw || 0) === 0 && result.resumo.total_oportunidades === 0 && !result.cached && <SourcesUnavailable onRetry={onSearch} onLoadLastSearch={onLoadLastSearch || (() => {})} hasLastSearch={!!hasLastSearch} retrying={loading} degradationGuidance={result.degradation_guidance} />}
      {!loading && result && result.response_state === "degraded_expired" && result.cached_at && <ExpiredCacheBanner cachedAt={result.cached_at} onRetry={onSearch} loading={loading} />}
      {!loading && result && result.is_partial && (result.total_raw || 0) > 0 && result.resumo.total_oportunidades === 0 && <>{renderDataQualityBanner()}<EmptyState onAdjustSearch={() => window.scrollTo({ top: 0, behavior: "smooth" })} rawCount={rawCount} stateCount={ufsSelecionadas.size} filterStats={result.filter_stats} sectorName={sectorName} /></>}
      {/* CRIT-053 AC5: Contextual zero results — degraded sources get degradation message, not "nenhuma corresponde" */}
      {!loading && result && result.resumo.total_oportunidades === 0 && result.sources_degraded && result.sources_degraded.length > 0 && result.response_state !== "empty_failure" && (
        <div className="mt-6 text-center py-10" data-testid="degraded-zero-results">
          {renderDataQualityBanner()}
          <div className="mt-6">
            <svg className="mx-auto h-12 w-12 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            <p className="mt-3 text-base font-medium text-ink">A fonte principal de dados (PNCP) esta temporariamente indisponivel.</p>
            <p className="mt-1 text-sm text-ink-secondary">Tente novamente em alguns minutos para resultados completos.</p>
            <button onClick={onRetryForceFresh || onSearch} className="mt-4 px-5 py-2 bg-amber-600 text-white rounded-button text-sm font-medium hover:bg-amber-700 transition-colors" data-testid="degraded-retry-button">Tentar Novamente</button>
          </div>
        </div>
      )}
      {!loading && result && !result.is_partial && result.response_state !== "empty_failure" && result.resumo.total_oportunidades === 0 && (!result.sources_degraded || result.sources_degraded.length === 0) && <ZeroResultsSuggestions sectorName={sectorName} ufCount={ufsSelecionadas.size} ufNames={Array.from(ufsSelecionadas)} dayRange={30} onAdjustPeriod={props.onAdjustPeriod} onAddNeighborStates={props.onAddNeighborStates} onChangeSector={() => window.scrollTo({ top: 0, behavior: "smooth" })} nearbyResultsCount={props.nearbyResultsCount} onViewNearbyResults={props.onViewNearbyResults} totalFromSources={result.total_raw} filterStats={result.filter_stats} />}
      {!loading && result && result.filter_relaxed && result.resumo.total_oportunidades > 0 && <FilterRelaxedBanner relaxationLevel={result.hidden_by_min_match != null && result.hidden_by_min_match > 0 ? "min_match_lowered" : undefined} originalCount={0} relaxedCount={result.resumo.total_oportunidades} />}
      {!loading && refreshAvailable && props.onRefreshResults && <div className="mt-4"><RefreshBanner refreshInfo={refreshAvailable} onRefresh={props.onRefreshResults} /></div>}
      {!loading && liveFetchInProgress && !refreshAvailable && result && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-200" role="status">
          <svg className="h-4 w-4 animate-spin flex-shrink-0" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          <span>Atualizando dados em tempo real...</span>
        </div>
      )}

      {/* === Results === */}
      {!loading && result && result.resumo.total_oportunidades > 0 && (
        <div className={`mt-6 sm:mt-8 space-y-4 sm:space-y-6 ${!showGrid ? 'animate-fade-in-up' : ''}`}>
          {trialPhase === "limited_access" && (
            <div className="p-3 rounded-card bg-gradient-to-r from-blue-600 to-purple-600 text-white flex items-center justify-between" data-testid="trial-paywall-banner" role="banner">
              <div className="flex items-center gap-2"><svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg><span className="text-sm font-medium">Voce esta no modo preview. Desbloqueie acesso completo ao SmartLic.</span></div>
              <Link href="/planos" className="text-sm font-bold bg-white/20 hover:bg-white/30 px-4 py-1.5 rounded-button transition-colors whitespace-nowrap" data-testid="trial-paywall-banner-cta">Ver planos</Link>
            </div>
          )}
          {result.response_state !== "degraded_expired" && renderDataQualityBanner()}
          {(pendingReviewCount > 0 || (pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0)) && (
            <div className={`flex items-start gap-3 p-3 rounded-lg border ${pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0 ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800" : "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"}`} data-testid="pending-review-banner">
              <svg className={`w-5 h-5 mt-0.5 flex-shrink-0 ${pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0 ? "text-emerald-500" : "text-blue-500"}`} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>
              <div className="text-sm">{pendingReviewUpdate && pendingReviewUpdate.reclassifiedCount > 0 ? <p className="text-emerald-800 dark:text-emerald-300">Reclassificação concluída: {pendingReviewUpdate.acceptedCount} oportunidades confirmadas{pendingReviewUpdate.rejectedCount > 0 && `, ${pendingReviewUpdate.rejectedCount} descartadas`}.</p> : <p className="text-blue-800 dark:text-blue-300">{pendingReviewCount} {pendingReviewCount === 1 ? 'oportunidade aguarda' : 'oportunidades aguardam'} reclassificação (IA temporariamente indisponível)</p>}</div>
            </div>
          )}

          <ZeroMatchBadge progress={zeroMatchProgress ?? null} />
          <ResultsHeader result={result} rawCount={rawCount} isProfileComplete={isProfileComplete} filterSummary={filterSummary} />
          <TourInviteBanner isCompleted={isResultsTourCompleted} onStartTour={onStartResultsTour} />
          <ResultsToolbar result={result} ordenacao={ordenacao} onOrdenacaoChange={onOrdenacaoChange} loading={loading} onDownload={onDownload} downloadLoading={downloadLoading} onRegenerateExcel={onRegenerateExcel} excelFailCount={excelFailCount} excelTimedOut={excelTimedOut} planInfo={planInfo} session={session} isTrialExpired={isTrialExpired} paywallApplied={paywallApplied} totalBeforePaywall={totalBeforePaywall} sectorName={sectorName} ufsSelecionadas={ufsSelecionadas} onGeneratePdf={onGeneratePdf} pdfLoading={pdfLoading} onSearch={onSearch} />

          {result.filter_stats && (result.filter_stats.llm_zero_match_calls ?? 0) > 0 && (
            <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/40 rounded-card text-sm text-blue-800 dark:text-blue-200 flex items-center gap-2">
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
              <span>IA analisou {result.filter_stats.llm_zero_match_calls} licitações adicionais{(result.filter_stats.llm_zero_match_aprovadas ?? 0) > 0 && <> — {result.filter_stats.llm_zero_match_aprovadas} aprovadas</>}</span>
            </div>
          )}

          {/* CRIT-057 AC5: Inform user when zero-match budget was exceeded */}
          {result.filter_stats && (result.filter_stats.zero_match_budget_exceeded ?? 0) > 0 && (
            <div className="px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 rounded-card text-sm text-amber-800 dark:text-amber-200 flex items-center gap-2">
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span>Algumas oportunidades estão em revisão e podem aparecer em breve</span>
            </div>
          )}

          <ResultsFilters ufsSelecionadas={ufsSelecionadas} searchMode={searchMode} sectorName={sectorName} />

          {(result.metadata || result.termos_utilizados || result.stopwords_removidas) && (
            <div className="bg-surface-1 border border-border rounded-card p-4">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-brand-blue flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-ink mb-2">Termos utilizados na análise:</p>
                  <div className="flex flex-wrap gap-2">{(result.metadata?.termos_utilizados || result.termos_utilizados || []).map(t => <span key={t} className="inline-flex items-center px-2.5 py-1 bg-brand-blue-subtle text-brand-navy rounded-full text-xs font-medium border border-brand-blue/20">{t}</span>)}</div>
                  {result.metadata && result.metadata.termos_ignorados.length > 0 && (
                    <details className="mt-3 cursor-pointer group"><summary className="text-sm text-ink-muted hover:text-ink transition-colors list-none flex items-center gap-2"><svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg><span className="font-medium">{result.metadata.termos_ignorados.length} termo{result.metadata.termos_ignorados.length > 1 ? 's' : ''} não utilizado{result.metadata.termos_ignorados.length > 1 ? 's' : ''}</span></summary><div className="mt-2 pl-6 space-y-1">{result.metadata.termos_ignorados.map(t => <div key={t} className="text-xs text-ink-secondary"><strong className="text-ink">&quot;{t}&quot;</strong>: {result.metadata!.motivos_ignorados[t]}</div>)}</div></details>
                  )}
                  {!result.metadata && result.stopwords_removidas && result.stopwords_removidas.length > 0 && <p className="text-xs text-ink-muted mt-2">Termos ignorados (stopwords): {result.stopwords_removidas.join(", ")}</p>}
                </div>
              </div>
            </div>
          )}

          {result.filter_relaxed && <div className="px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 rounded-card text-sm text-amber-800 dark:text-amber-200 flex items-center gap-2"><svg role="img" aria-label="Aviso" className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg><span>Nenhum resultado atendeu todos os critérios de relevância. Os filtros foram flexibilizados para exibir resultados parciais.</span></div>}
          {result.hidden_by_min_match != null && result.hidden_by_min_match > 0 && <div className="px-4 py-3 bg-surface-2 border border-border rounded-card text-sm text-ink-secondary flex items-center justify-between"><span>{result.hidden_by_min_match} resultado{result.hidden_by_min_match > 1 ? "s" : ""} com correspondência parcial {result.hidden_by_min_match > 1 ? "foram ocultados" : "foi ocultado"}.</span><button onClick={() => onTrackEvent("show_hidden_results", { hidden_count: result.hidden_by_min_match })} className="text-brand-navy dark:text-brand-blue font-medium hover:underline shrink-0 ml-3">Mostrar todos</button></div>}

          <ResultCard result={result} trialPhase={trialPhase} isProfileComplete={isProfileComplete} bannerDismissed={bannerDismissed} onDismissBanner={handleDismissBanner} />
          {planInfo && <QuotaCounter quotaUsed={planInfo.quota_used} quotaLimit={planInfo.capabilities.max_requests_per_month} resetDate={planInfo.quota_reset_date} planId={planInfo.plan_id} onUpgradeClick={() => onShowUpgradeModal(undefined, "quota_counter")} />}
          {planInfo && planInfo.capabilities.max_requests_per_month > 0 && (planInfo.quota_used / planInfo.capabilities.max_requests_per_month) >= 0.8 && <TrialUpsellCTA variant="quota" planId={planInfo.plan_id} subscriptionStatus={planInfo.subscription_status} contextData={{ usageLabel: `${planInfo.quota_used}/${planInfo.capabilities.max_requests_per_month}`, usagePct: Math.round((planInfo.quota_used / planInfo.capabilities.max_requests_per_month) * 100) }} />}
          <ResultsList result={result} paginatedLicitacoes={paginatedLicitacoes} totalLicitacoes={totalLicitacoes} currentPage={currentPage} pageSize={pageSize} onPageChange={setCurrentPage} onPageSizeChange={setPageSize} searchMode={searchMode} termosArray={termosArray} planInfo={planInfo} session={session} onShowUpgradeModal={onShowUpgradeModal} searchId={searchId} setorId={setorId} paywallApplied={paywallApplied} totalBeforePaywall={totalBeforePaywall} />
          <ResultsFooter result={result} rawCount={rawCount} searchMode={searchMode} sectorName={sectorName} ufsSelecionadas={ufsSelecionadas} termosArray={termosArray} onDownload={onDownload} downloadLoading={downloadLoading} downloadError={downloadError} downloadCompleted={downloadCompleted} planInfo={planInfo} session={session} isTrialExpired={isTrialExpired} paywallApplied={paywallApplied} totalBeforePaywall={totalBeforePaywall} onShowUpgradeModal={onShowUpgradeModal} />
        </div>
      )}
    </>
  );
}
