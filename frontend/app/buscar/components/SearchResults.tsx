"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { BuscaResult } from "../../types";
import type { SearchProgressEvent } from "../../../hooks/useSearchProgress";
import { EnhancedLoadingProgress } from "../../../components/EnhancedLoadingProgress";
import { LoadingResultsSkeleton } from "../../components/LoadingResultsSkeleton";
import { EmptyState } from "../../components/EmptyState";
import { DegradationBanner } from "./DegradationBanner";
import { UfProgressGrid } from "./UfProgressGrid";
import type { UfStatus } from "../hooks/useUfProgress";
import { PartialResultsPrompt, PartialResultsBanner, FailedUfsBanner } from "./PartialResultsPrompt";
import { CacheBanner } from "./CacheBanner";
import { SourcesUnavailable } from "./SourcesUnavailable";
import { TruncationWarningBanner } from "./TruncationWarningBanner";
import { QuotaCounter } from "../../components/QuotaCounter";
import { LicitacoesPreview } from "../../components/LicitacoesPreview";
import { OrdenacaoSelect, type OrdenacaoOption } from "../../components/OrdenacaoSelect";
import GoogleSheetsExportButton from "../../../components/GoogleSheetsExportButton";

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
  onStageChange: (stage: number) => void;

  // Error state
  error: string | null;
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

  // Plan & auth
  planInfo: {
    plan_id: string;
    plan_name: string;
    quota_used: number;
    quota_reset_date: string;
    trial_expires_at?: string | null;
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
}

export default function SearchResults({
  loading, loadingStep, estimatedTime, stateCount, statesProcessed,
  onCancel, sseEvent, useRealProgress, sseAvailable, onStageChange,
  error, quotaError,
  result, rawCount,
  ufsSelecionadas, sectorName,
  searchMode, termosArray, ordenacao, onOrdenacaoChange,
  downloadLoading, downloadError, onDownload, onSearch,
  planInfo, session, onShowUpgradeModal, onTrackEvent,
  // STORY-257B props
  ufStatuses, ufTotalFound = 0, ufAllComplete,
  searchElapsedSeconds = 0, onViewPartial, partialDismissed, onDismissPartial,
  onRetryForceFresh,
  hasLastSearch = false, onLoadLastSearch,
}: SearchResultsProps) {
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

  // STORY-257B AC13: 30-second cooldown for retry button
  const [retryCooldown, setRetryCooldown] = useState(0);

  useEffect(() => {
    if (error && !quotaError && retryCooldown === 0) {
      setRetryCooldown(30);
    }
  }, [error, quotaError]);

  useEffect(() => {
    if (retryCooldown > 0) {
      const timer = setTimeout(() => setRetryCooldown(retryCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [retryCooldown]);

  useEffect(() => {
    if (!error) {
      setRetryCooldown(0);
    }
  }, [error]);

  const formatCooldownTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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

      {/* Loading State */}
      {loading && (
        <div aria-live="polite">
          <EnhancedLoadingProgress
            currentStep={loadingStep}
            estimatedTime={estimatedTime}
            stateCount={stateCount}
            statesProcessed={statesProcessed}
            onCancel={onCancel}
            sseEvent={sseEvent}
            useRealProgress={useRealProgress && sseAvailable}
            onStageChange={onStageChange}
          />
          <LoadingResultsSkeleton count={1} />

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

      {/* Error Display with Retry */}
      {error && !quotaError && (
        <div className="mt-6 sm:mt-8 p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card animate-fade-in-up" role="alert">
          <p className="text-sm sm:text-base font-medium text-error mb-3">{error}</p>
          <button
            onClick={onSearch}
            disabled={loading || retryCooldown > 0}
            className="px-4 py-2 bg-error text-white rounded-button text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Tentando...
              </>
            ) : retryCooldown > 0 ? (
              <>
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" strokeWidth="2" />
                  <path strokeLinecap="round" strokeWidth="2" d="M12 6v6l4 2" />
                </svg>
                Tentar novamente ({formatCooldownTime(retryCooldown)})
              </>
            ) : "Tentar novamente"}
          </button>
        </div>
      )}

      {/* Quota Exceeded Display */}
      {quotaError && (
        <div className="mt-6 sm:mt-8 p-4 sm:p-5 bg-warning-subtle border border-warning/20 rounded-card animate-fade-in-up" role="alert">
          <div className="flex items-start gap-3">
            <svg role="img" aria-label="Aviso" className="w-6 h-6 text-warning flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p className="text-sm sm:text-base font-medium text-warning mb-2">{quotaError}</p>
              <p className="text-sm text-ink-secondary mb-4">
                Escolha um plano para continuar buscando oportunidades de licitação.
              </p>
              <a
                href="/planos"
                className="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white rounded-button text-sm font-medium
                           hover:bg-brand-blue-hover transition-colors"
              >
                <svg role="img" aria-label="Ícone" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                Ver Planos
              </a>
            </div>
          </div>
        </div>
      )}

      {/* STORY-257B AC10: All sources down — friendly fallback (total_raw=0, total_filtrado=0, is_partial=true, no cache) */}
      {result && result.is_partial && (result.total_raw || 0) === 0 && result.resumo.total_oportunidades === 0 && !result.cached && (
        <SourcesUnavailable
          onRetry={onSearch}
          onLoadLastSearch={onLoadLastSearch || (() => {})}
          hasLastSearch={hasLastSearch}
          retrying={loading}
        />
      )}

      {/* STORY-252 AC23: Partial results, but all filtered out (total_raw>0, total_filtrado=0, is_partial=true) */}
      {result && result.is_partial && (result.total_raw || 0) > 0 && result.resumo.total_oportunidades === 0 && (
        <>
          <DegradationBanner
            variant="warning"
            message="Resultados parciais — algumas fontes não responderam e nenhum resultado passou nos filtros."
            detail="Os dados disponíveis não continham licitações compatíveis com os critérios selecionados. Tente ampliar o período ou selecionar mais estados."
            dataSources={result.data_sources}
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

      {/* Empty State — legitimate zero results (not caused by API failure) */}
      {result && !result.is_partial && result.resumo.total_oportunidades === 0 && (
        <EmptyState
          onAdjustSearch={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          rawCount={rawCount}
          stateCount={ufsSelecionadas.size}
          filterStats={result.filter_stats}
          sectorName={sectorName}
        />
      )}

      {/* STORY-257B AC8: Cache banner when results come from cache */}
      {result && result.cached && result.cached_at && (
        <CacheBanner
          cachedAt={result.cached_at}
          onRefresh={onRetryForceFresh || onSearch}
          refreshing={loading}
        />
      )}

      {/* Result Display */}
      {result && result.resumo.total_oportunidades > 0 && (
        <div className={`mt-6 sm:mt-8 space-y-4 sm:space-y-6 ${!showGrid ? 'animate-fade-in-up' : ''}`}>
          {/* STORY-257B AC7: Failed UFs banner */}
          {result.failed_ufs && result.failed_ufs.length > 0 && (
            <FailedUfsBanner
              successCount={ufsSelecionadas.size - result.failed_ufs.length}
              failedUfs={result.failed_ufs}
              onRetryFailed={onSearch}
              loading={loading}
            />
          )}

          {/* GTM-FIX-004: Truncation warning banner */}
          {result.is_truncated && (
            <TruncationWarningBanner truncatedUfs={result.truncated_ufs} />
          )}

          {/* STORY-257B AC6: Partial results mini-banner */}
          {result.is_partial && result.failed_ufs && result.failed_ufs.length > 0 && (
            <PartialResultsBanner
              visibleCount={ufsSelecionadas.size - result.failed_ufs.length}
              totalCount={ufsSelecionadas.size}
              searching={loading}
            />
          )}

          {/* STORY-252 AC21: Yellow banner for partial results (data source level) */}
          {result.is_partial && !result.cached && (
            <DegradationBanner
              variant="warning"
              message="Resultados parciais — algumas fontes de dados não responderam."
              detail={result.degradation_reason}
              dataSources={result.data_sources}
            />
          )}

          {/* Results header with ordering */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-strong">
            <h2 className="text-lg font-semibold text-ink">
              Resultados da Busca
            </h2>
            <OrdenacaoSelect
              value={ordenacao}
              onChange={onOrdenacaoChange}
              disabled={loading}
            />
          </div>

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
                    Termos utilizados na busca:
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
          <div className="p-4 sm:p-6 bg-brand-blue-subtle border border-accent rounded-card">
            <p className="text-base sm:text-lg leading-relaxed text-ink">
              {result.resumo.resumo_executivo}
            </p>

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
                  <span aria-hidden="true">Atenção: </span>
                  {result.resumo.alerta_urgencia}
                </p>
              </div>
            ) : null}

            {/* AC10: Recommendation Cards */}
            {result.resumo.recomendacoes && result.resumo.recomendacoes.length > 0 && (
              <div className="mt-4 sm:mt-6">
                <h4 className="text-base sm:text-lg font-semibold font-display text-ink mb-3 sm:mb-4">Recomendações do Consultor:</h4>
                <div className="space-y-3">
                  {result.resumo.recomendacoes.map((rec, i) => (
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
                    </div>
                  ))}
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

          {/* Licitacoes Preview */}
          {result.licitacoes && result.licitacoes.length > 0 && (
            <LicitacoesPreview
              licitacoes={result.licitacoes}
              previewCount={5}
              excelAvailable={planInfo?.capabilities.allow_excel ?? false}
              searchTerms={searchMode === "termos" ? termosArray : (result.termos_utilizados || [])}
              onUpgradeClick={() => {
                onShowUpgradeModal("smartlic_pro", "licitacoes_preview");
              }}
            />
          )}

          {/* Download Button */}
          {planInfo?.capabilities.allow_excel ? (
            <button
              onClick={onDownload}
              disabled={downloadLoading}
              aria-label={`Baixar Excel com ${result.resumo.total_oportunidades} ${result.resumo.total_oportunidades === 1 ? 'licitação' : 'licitações'}`}
              className="w-full bg-brand-navy text-white py-3 sm:py-4 rounded-button text-base sm:text-lg font-semibold
                         hover:bg-brand-blue-hover active:bg-brand-blue
                         disabled:bg-ink-faint disabled:text-ink-muted disabled:cursor-not-allowed
                         transition-all duration-200
                         flex items-center justify-center gap-3"
            >
              {downloadLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-label="Carregando" role="img">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Preparando download...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Baixar Excel ({result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'licitação' : 'licitações'})
                </>
              )}
            </button>
          ) : (
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
          )}

          {/* Google Sheets Export */}
          {planInfo?.capabilities.allow_excel && (
            <GoogleSheetsExportButton
              licitacoes={result.licitacoes}
              searchLabel={`${sectorName} - ${Array.from(ufsSelecionadas).join(', ')}`}
              disabled={downloadLoading}
              session={session}
            />
          )}

          {/* Download Error */}
          {downloadError && (
            <div className="p-4 sm:p-5 bg-error-subtle border border-error/20 rounded-card" role="alert">
              <p className="text-sm sm:text-base font-medium text-error">{downloadError}</p>
            </div>
          )}

          {/* Stats + Timestamp */}
          <div className="text-xs sm:text-sm text-ink-muted text-center space-y-1">
            {rawCount > 0 && (
              <p>
                {result.resumo.total_oportunidades} de {rawCount.toLocaleString("pt-BR")} {rawCount === 1 ? 'licitação compatível' : 'licitações compatíveis'} com os filtros selecionados nesta busca
                {searchMode === "setor" && sectorName !== "Licitações" ? ` para o setor ${sectorName.toLowerCase()}` : ''}
              </p>
            )}
            {result.source_stats && result.source_stats.length > 1 && (
              <p className="text-ink-faint">
                Fontes: {result.source_stats
                  .filter((s: { status: string }) => s.status === "success")
                  .map((s: { source_code: string; record_count: number }) => `${s.source_code}: ${s.record_count}`)
                  .join(", ")}
              </p>
            )}
            {result.ultima_atualizacao && (
              <p className="text-ink-faint">
                <svg className="w-3.5 h-3.5 inline mr-1 -mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Última atualização: {new Date(result.ultima_atualizacao).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })}
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
