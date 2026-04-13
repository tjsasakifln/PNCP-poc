"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type { BuscaResult } from "../../types";
import type { StatusLicitacao } from "../components/StatusFilter";
import type { Esfera } from "../../components/EsferaFilter";
import type { Municipio } from "../../components/MunicipioFilter";
import type { OrdenacaoOption } from "../../components/OrdenacaoSelect";
import type { SavedSearch } from "../../../lib/savedSearches";
import type { SearchProgressEvent, PartialProgress, RefreshAvailableInfo, UfStatus, BatchProgress, SourceStatus, FilterSummary, PendingReviewUpdate, ZeroMatchProgress } from "../../../hooks/useSearchSSE";
import { useAuth } from "../../components/AuthProvider";
import { useSearchSSE } from "../../../hooks/useSearchSSE";
import { useSearchPolling } from "../../../hooks/useSearchPolling";
import { getHumanizedError, type HumanizedError } from "../../../lib/error-messages";
import { cleanupExpiredPartials } from "../../../lib/searchPartialCache";

import { useSearchRetry } from "./useSearchRetry";
import { useSearchExport } from "./useSearchExport";
import { useSearchPersistence } from "./useSearchPersistence";
import { useSearchSSEHandler } from "./useSearchSSEHandler";
import { useSearchExecution } from "./useSearchExecution";

// ── Exported interfaces (consumed by other components) ──────────────────

export interface SearchFiltersSnapshot {
  ufs: Set<string>;
  dataInicial: string;
  dataFinal: string;
  searchMode: "setor" | "termos";
  setorId?: string;
  termosArray?: string[];
  status: StatusLicitacao;
  modalidades: number[];
  valorMin: number | null;
  valorMax: number | null;
  esferas: Esfera[];
  municipios: Municipio[];
  ordenacao: OrdenacaoOption;
}

interface UseSearchParams {
  ufsSelecionadas: Set<string>;
  dataInicial: string;
  dataFinal: string;
  searchMode: "setor" | "termos";
  modoBusca: "abertas" | "publicacao";
  setorId: string;
  termosArray: string[];
  status: StatusLicitacao;
  modalidades: number[];
  valorMin: number | null;
  valorMax: number | null;
  esferas: Esfera[];
  municipios: Municipio[];
  ordenacao: OrdenacaoOption;
  sectorName: string;
  canSearch: boolean;
  setOrdenacao: (ord: OrdenacaoOption) => void;
  setUfsSelecionadas: (ufs: Set<string>) => void;
  setDataInicial: (d: string) => void;
  setDataFinal: (d: string) => void;
  setSearchMode: (m: "setor" | "termos") => void;
  setSetorId: (id: string) => void;
  setTermosArray: (t: string[]) => void;
  setStatus: (s: StatusLicitacao) => void;
  setModalidades: (m: number[]) => void;
  setValorMin: (v: number | null) => void;
  setValorMax: (v: number | null) => void;
  setEsferas: (e: Esfera[]) => void;
  setMunicipios: (m: Municipio[]) => void;
}

/**
 * CRIT-009 AC6: Structured error object preserving all metadata from backend/proxy.
 */
export interface SearchError {
  message: string;
  rawMessage: string;
  errorCode: string | null;
  searchId: string | null;
  correlationId: string | null;
  requestId: string | null;
  httpStatus: number | null;
  timestamp: string;
}

export interface UseSearchReturn {
  loading: boolean;
  loadingStep: number;
  statesProcessed: number;
  error: SearchError | null;
  quotaError: string | null;
  result: BuscaResult | null;
  setResult: (r: BuscaResult | null) => void;
  setError: (e: SearchError | null) => void;
  rawCount: number;
  searchId: string | null;
  useRealProgress: boolean;
  sseEvent: SearchProgressEvent | null;
  sseAvailable: boolean;
  sseDisconnected: boolean;
  isReconnecting: boolean;
  isDegraded: boolean;
  degradedDetail: SearchProgressEvent['detail'] | null;
  partialProgress: PartialProgress | null;
  refreshAvailable: RefreshAvailableInfo | null;
  ufStatuses: Map<string, UfStatus>;
  ufTotalFound: number;
  ufAllComplete: boolean;
  batchProgress: BatchProgress | null;
  sourceStatuses: Map<string, SourceStatus>;
  filterSummary: FilterSummary | null;
  pendingReviewUpdate: PendingReviewUpdate | null;
  zeroMatchProgress: ZeroMatchProgress | null;
  liveFetchInProgress: boolean;
  handleRefreshResults: () => Promise<void>;
  downloadLoading: boolean;
  downloadError: string | null;
  searchButtonRef: React.RefObject<HTMLButtonElement>;
  showSaveDialog: boolean;
  setShowSaveDialog: (show: boolean) => void;
  saveSearchName: string;
  setSaveSearchName: (name: string) => void;
  saveError: string | null;
  isMaxCapacity: boolean;
  buscar: (options?: { forceFresh?: boolean }) => Promise<void>;
  buscarForceFresh: () => Promise<void>;
  cancelSearch: () => void;
  viewPartialResults: () => void;
  handleDownload: () => Promise<void>;
  handleRegenerateExcel: () => Promise<void>;
  handleSaveSearch: () => void;
  confirmSaveSearch: () => void;
  handleLoadSearch: (search: SavedSearch) => void;
  handleRefresh: () => Promise<void>;
  estimateSearchTime: (ufCount: number, dateRangeDays: number) => number;
  restoreSearchStateOnMount: () => void;
  getRetryCooldown: (errorMessage: string | null, httpStatus?: number) => number;
  retryCountdown: number | null;
  retryMessage: string | null;
  retryExhausted: boolean;
  retryNow: () => void;
  cancelRetry: () => void;
  humanizedError: HumanizedError | null;
  showingPartialResults: boolean;
  dismissPartialResults: () => void;
  excelFailCount: number;
  isFinalizing: boolean;
  asyncSearchActive: boolean;
  sseReconnectAttempts: number;
  skeletonTimeoutReached: boolean;
  // UX-432: Navigation persistence
  isRestoredFromNav: boolean;
  restoredNavMeta: import('../../../lib/navSearchCache').NavSearchMeta | null;
  handleNovaBusca: () => void;
}

// ── Orchestrator ────────────────────────────────────────────────────────

export function useSearch(filters: UseSearchParams): UseSearchReturn {
  const { session } = useAuth();

  // ── Shared state (orchestrator owns, sub-hooks read/write via params) ──
  const [result, setResult] = useState<BuscaResult | null>(null);
  const [rawCount, setRawCount] = useState(0);
  const [error, setError] = useState<SearchError | null>(null);

  // Shared refs for cross-hook communication (break circular deps)
  const excelFailCountRef = useRef(0);
  const excelToastFiredRef = useRef(false);
  const handleExcelFailureRef = useRef<((isRegenerateAttempt: boolean) => void) | null>(null);
  const refreshAvailableRef = useRef<RefreshAvailableInfo | null>(null);

  // ── 1. Retry ──
  const retry = useSearchRetry();
  // Wire clearError ref so retryNow() can clear the error state
  retry.clearErrorRef.current = () => setError(null);

  // ── 2. Persistence (needs buscar — we wire it via ref after execution is created) ──
  const buscarProxyRef = useRef<((options?: { forceFresh?: boolean }) => Promise<void>) | null>(null);
  const buscarProxy = useCallback(async (options?: { forceFresh?: boolean }) => {
    await buscarProxyRef.current?.(options);
  }, []);

  const persistence = useSearchPersistence({
    filters,
    result,
    setResult,
    buscar: buscarProxy,
  });

  // ── 3. Execution ──
  const execution = useSearchExecution({
    filters,
    result,
    setResult,
    setRawCount,
    error,
    setError,
    autoRetryInProgressRef: retry.autoRetryInProgressRef,
    buscarRef: retry.buscarRef,
    resetRetryForNewSearch: retry.resetForNewSearch,
    startAutoRetry: retry.startAutoRetry,
    setRetryCountdown: retry.setRetryCountdown,
    setRetryMessage: retry.setRetryMessage,
    setRetryExhausted: retry.setRetryExhausted,
    excelFailCountRef,
    excelToastFiredRef,
    lastSearchParamsRef: persistence.lastSearchParamsRef,
    showingPartialResults: persistence.showingPartialResults,
    setShowingPartialResults: persistence.setShowingPartialResults,
    refreshAvailableRef,
  });

  // Wire buscar proxy for persistence.handleRefresh
  buscarProxyRef.current = execution.buscar;

  // ── 4. SSE event handler ──
  const sseHandler = useSearchSSEHandler({
    session,
    searchId: execution.searchId,
    searchMode: filters.searchMode,
    ufsSelecionadasSize: filters.ufsSelecionadas.size,
    result,
    setResult,
    setRawCount,
    setError,
    setLoading: execution.setLoading,
    setSearchId: execution.setSearchId,
    setAsyncSearchActive: execution.setAsyncSearchActive,
    asyncSearchActiveRef: execution.asyncSearchActiveRef,
    asyncSearchIdRef: execution.asyncSearchIdRef,
    sseTerminalReceivedRef: execution.sseTerminalReceivedRef,
    llmTimeoutRef: execution.llmTimeoutRef,
    setRetryCountdown: retry.setRetryCountdown,
    setRetryMessage: retry.setRetryMessage,
    setRetryExhausted: retry.setRetryExhausted,
    retryTimerRef: retry.retryTimerRef,
    handleExcelFailureRef,
    excelFailCountRef,
    excelToastFiredRef,
    setLiveFetchInProgress: execution.setLiveFetchInProgress,
    liveFetchSearchIdRef: execution.liveFetchSearchIdRef,
  });

  // ── 5. SSE connection ──
  const hasProcessingJobs = !!(result?.llm_status === 'processing' || result?.excel_status === 'processing' || result?.bid_analysis_status === 'processing');
  const {
    currentEvent: sseEvent, sseAvailable, sseDisconnected,
    isReconnecting,
    isDegraded, degradedDetail, partialProgress, refreshAvailable,
    ufStatuses, ufTotalFound, ufAllComplete, batchProgress,
    sourceStatuses, filterSummary, pendingReviewUpdate, zeroMatchProgress,
  } = useSearchSSE({
    searchId: execution.asyncSearchActive ? execution.asyncSearchIdRef.current : (execution.liveFetchInProgress ? execution.liveFetchSearchIdRef.current : execution.searchId),
    enabled: (execution.loading && !!execution.searchId) || execution.liveFetchInProgress || hasProcessingJobs || execution.asyncSearchActive,
    authToken: session?.access_token,
    selectedUfs: Array.from(filters.ufsSelecionadas),
    onEvent: sseHandler.handleSseEvent,
    onError: () => {
      execution.setUseRealProgress(false);
      execution.sseReconnectAttemptsRef.current += 1;
    },
  });

  // ── 6. Polling fallback ──
  const activeSearchId = execution.liveFetchInProgress ? execution.liveFetchSearchIdRef.current : execution.searchId;
  const { asProgressEvent: pollingEvent } = useSearchPolling({
    searchId: activeSearchId,
    enabled: sseDisconnected && execution.loading && !!activeSearchId,
    authToken: session?.access_token,
    onStatusUpdate: async (status) => {
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'timed_out') {
        execution.setUseRealProgress(false);
      }

      // CRIT-CORE-001: When polling detects completed, fetch actual results.
      // This is the critical fallback when SSE dies — without this, the user
      // stays in loading forever because polling only updated progress, never fetched results.
      if (status.status === 'completed' && execution.asyncSearchActive) {
        const sid = execution.asyncSearchIdRef.current || activeSearchId;
        if (sid) {
          try {
            const headers: Record<string, string> = {};
            if (session?.access_token) headers["Authorization"] = `Bearer ${session.access_token}`;

            const response = await fetch(`/api/buscar-results/${encodeURIComponent(sid)}`, { headers });
            if (response.ok) {
              const fetchedData = await response.json();
              setResult(fetchedData);
              if (fetchedData.total_raw) setRawCount(fetchedData.total_raw);
              setError(null);
            }
          } catch (e) {
            console.warn('[CRIT-CORE-001] Polling: failed to fetch results after completed status:', e);
          } finally {
            execution.setAsyncSearchActive(false);
            execution.asyncSearchActiveRef.current = false;
            execution.asyncSearchIdRef.current = null;
            execution.setLoading(false);
            execution.setSearchId(null);
          }
        }
      }

      // CRIT-CORE-001: When polling detects failure, exit loading with error.
      if ((status.status === 'failed' || status.status === 'timed_out') && execution.asyncSearchActive) {
        execution.setAsyncSearchActive(false);
        execution.asyncSearchActiveRef.current = false;
        execution.asyncSearchIdRef.current = null;
        execution.setLoading(false);
        setError({
          message: status.error_message || "A análise não pôde ser concluída. Tente novamente.",
          rawMessage: status.error_message || `Search ${status.status}`,
          errorCode: status.error_code || "SEARCH_FAILED",
          searchId: status.search_id,
          correlationId: null,
          requestId: null,
          httpStatus: status.status === 'timed_out' ? 504 : 500,
          timestamp: new Date().toISOString(),
        });
      }
    },
  });

  // AC21: Use polling event when SSE is disconnected
  const effectiveEvent = sseDisconnected && pollingEvent ? pollingEvent : sseEvent;

  // ── 7. Export ──
  const exportHook = useSearchExport({
    result,
    setResult: (updater) => setResult(updater),
    searchId: execution.searchId,
    asyncSearchIdRef: execution.asyncSearchIdRef,
    sseDisconnected,
    sseAvailable,
    loading: execution.loading,
    session,
    sectorName: filters.sectorName,
    dataInicial: filters.dataInicial,
    dataFinal: filters.dataFinal,
    excelFailCountRef,
    excelToastFiredRef,
  });

  // Wire handleExcelFailure ref for SSE handler
  handleExcelFailureRef.current = exportHook.handleExcelFailure;
  // Wire refreshAvailable ref for execution's handleRefreshResults
  refreshAvailableRef.current = refreshAvailable;

  // ── Effects (orchestrator-level) ──

  // P2.1: Sync statesProcessed from real SSE uf_index
  useEffect(() => {
    const ufIndex = effectiveEvent?.detail?.uf_index;
    if (typeof ufIndex === 'number' && ufIndex > 0) {
      execution.setStatesProcessed(prev => Math.max(prev, ufIndex));
    }
  }, [effectiveEvent?.detail?.uf_index, execution.setStatesProcessed]);

  // SAB-005 AC1: Reset skeleton timeout whenever SSE event arrives (data update)
  useEffect(() => {
    if (execution.loading && effectiveEvent) {
      if (execution.skeletonTimeoutTimerRef.current) {
        clearTimeout(execution.skeletonTimeoutTimerRef.current);
      }
      execution.setSkeletonTimeoutReached(false);
      execution.skeletonTimeoutTimerRef.current = setTimeout(() => {
        execution.setSkeletonTimeoutReached(true);
      }, 30_000);
    }
  }, [execution.loading, effectiveEvent, execution.skeletonTimeoutTimerRef, execution.setSkeletonTimeoutReached]);

  // STAB-006 AC4: Clean up expired partials on mount
  useEffect(() => {
    cleanupExpiredPartials();
  }, []);

  // P4-FIX: Persist running UF raw count to sessionStorage during SSE progress.
  // Enables timeout recovery — if search times out, the AbortError handler can
  // show the user how many results were found before the timeout.
  useEffect(() => {
    if (execution.loading && execution.searchId && ufTotalFound > 0) {
      try {
        sessionStorage.setItem(`partial_search_${execution.searchId}`, JSON.stringify({
          timestamp: Date.now(),
          rawCount: ufTotalFound,
          searchId: execution.searchId,
        }));
      } catch { /* ignore quota errors */ }
    }
  }, [execution.loading, execution.searchId, ufTotalFound]);

  // ── Computed ──
  const humanizedError: HumanizedError | null = error
    ? getHumanizedError(error.httpStatus, error.rawMessage)
    : null;

  // ── Return ──
  return {
    loading: execution.loading,
    loadingStep: execution.loadingStep,
    statesProcessed: execution.statesProcessed,
    error,
    quotaError: execution.quotaError,
    result,
    setResult,
    setError,
    rawCount,
    searchId: execution.searchId,
    useRealProgress: execution.useRealProgress,
    sseEvent: effectiveEvent,
    sseAvailable,
    sseDisconnected,
    isReconnecting,
    isDegraded,
    degradedDetail,
    partialProgress,
    refreshAvailable,
    ufStatuses,
    ufTotalFound,
    ufAllComplete,
    batchProgress,
    sourceStatuses,
    filterSummary,
    pendingReviewUpdate,
    zeroMatchProgress,
    liveFetchInProgress: execution.liveFetchInProgress,
    handleRefreshResults: execution.handleRefreshResults,
    downloadLoading: exportHook.downloadLoading,
    downloadError: exportHook.downloadError,
    searchButtonRef: execution.searchButtonRef,
    showSaveDialog: persistence.showSaveDialog,
    setShowSaveDialog: persistence.setShowSaveDialog,
    saveSearchName: persistence.saveSearchName,
    setSaveSearchName: persistence.setSaveSearchName,
    saveError: persistence.saveError,
    isMaxCapacity: persistence.isMaxCapacity,
    buscar: execution.buscar,
    buscarForceFresh: persistence.buscarForceFresh,
    cancelSearch: execution.cancelSearch,
    viewPartialResults: execution.viewPartialResults,
    handleDownload: exportHook.handleDownload,
    handleRegenerateExcel: exportHook.handleRegenerateExcel,
    handleSaveSearch: persistence.handleSaveSearch,
    confirmSaveSearch: persistence.confirmSaveSearch,
    handleLoadSearch: persistence.handleLoadSearch,
    handleRefresh: persistence.handleRefresh,
    estimateSearchTime: execution.estimateSearchTime,
    restoreSearchStateOnMount: persistence.restoreSearchStateOnMount,
    getRetryCooldown: retry.getRetryCooldown,
    retryCountdown: retry.retryCountdown,
    retryMessage: retry.retryMessage,
    retryExhausted: retry.retryExhausted,
    retryNow: retry.retryNow,
    cancelRetry: retry.cancelRetry,
    humanizedError,
    showingPartialResults: persistence.showingPartialResults,
    dismissPartialResults: persistence.dismissPartialResults,
    excelFailCount: excelFailCountRef.current,
    isFinalizing: execution.isFinalizing,
    asyncSearchActive: execution.asyncSearchActive,
    sseReconnectAttempts: execution.sseReconnectAttemptsRef.current,
    skeletonTimeoutReached: execution.skeletonTimeoutReached,
    // UX-432
    isRestoredFromNav: persistence.isRestoredFromNav,
    restoredNavMeta: persistence.restoredNavMeta,
    handleNovaBusca: persistence.handleNovaBusca,
  };
}
