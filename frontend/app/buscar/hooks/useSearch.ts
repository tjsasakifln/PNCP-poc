"use client";

import { useState, useRef, useEffect } from "react";
import type { BuscaResult } from "../../types";
import type { StatusLicitacao } from "../../../components/StatusFilter";
import type { Esfera } from "../../components/EsferaFilter";
import type { Municipio } from "../../components/MunicipioFilter";
import type { OrdenacaoOption } from "../../components/OrdenacaoSelect";
import type { SavedSearch } from "../../../lib/savedSearches";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { useAuth } from "../../components/AuthProvider";
import { useQuota } from "../../../hooks/useQuota";
import { useSearchSSE, type SearchProgressEvent, type PartialProgress, type RefreshAvailableInfo, type UfStatus, type BatchProgress, type SourceStatus, type FilterSummary, type PendingReviewUpdate } from "../../../hooks/useSearchSSE";
import { useSearchPolling } from "../../../hooks/useSearchPolling";
import { useSavedSearches } from "../../../hooks/useSavedSearches";
import { getUserFriendlyError, getMessageFromErrorCode, isTransientError, getRetryMessage, getHumanizedError, type HumanizedError } from "../../../lib/error-messages";
import { saveSearchState, restoreSearchState } from "../../../lib/searchStatePersistence";
import { saveLastSearch } from "../../../lib/lastSearchCache";
import { savePartialSearch, recoverPartialSearch, clearPartialSearch, cleanupExpiredPartials } from "../../../lib/searchPartialCache";
import { toast } from "sonner";
import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";
import { getCorrelationId, logCorrelatedRequest } from "../../../lib/utils/correlationId";
import { supabase } from "../../../lib/supabase";

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
  // Setters needed for handleLoadSearch/handleRefresh
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
  message: string;         // User-friendly message (mapped from error_code or getUserFriendlyError)
  rawMessage: string;      // Original message from backend
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
  /** GTM-FIX-033 AC2: true when SSE disconnected after retry */
  sseDisconnected: boolean;
  /** STORY-297 AC9: true during SSE reconnection attempt */
  isReconnecting: boolean;
  /** A-02 AC8: true when search completed with degraded data */
  isDegraded: boolean;
  /** A-02 AC10: metadata from degraded SSE event */
  degradedDetail: SearchProgressEvent['detail'] | null;
  /** A-04 AC7: Partial progress from background fetch */
  partialProgress: PartialProgress | null;
  /** A-04 AC4: Refresh available info from background fetch */
  refreshAvailable: RefreshAvailableInfo | null;
  /** CRIT-003 AC19-AC20: Consolidated UF progress from single SSE connection */
  ufStatuses: Map<string, UfStatus>;
  ufTotalFound: number;
  ufAllComplete: boolean;
  batchProgress: BatchProgress | null;
  /** STORY-295 AC10: Per-source status for progressive results */
  sourceStatuses: Map<string, SourceStatus>;
  /** STORY-327 AC5: Filter summary with raw vs filtered counts */
  filterSummary: FilterSummary | null;
  /** STORY-354 AC6: Pending review reclassification update from SSE */
  pendingReviewUpdate: PendingReviewUpdate | null;
  /** A-04 AC1: True when cached data shown with live fetch in background */
  liveFetchInProgress: boolean;
  /** A-04 AC9: Fetch live results and replace cached data */
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
  /** CRIT-SSE-FIX AC1: View partial results without destroying search state */
  viewPartialResults: () => void;
  handleDownload: () => Promise<void>;
  /** STORY-364 AC7: Regenerate Excel from stored results without re-running search */
  handleRegenerateExcel: () => Promise<void>;
  handleSaveSearch: () => void;
  confirmSaveSearch: () => void;
  handleLoadSearch: (search: SavedSearch) => void;
  handleRefresh: () => Promise<void>;
  estimateSearchTime: (ufCount: number, dateRangeDays: number) => number;
  restoreSearchStateOnMount: () => void;
  /** CRIT-006 AC18: Retry cooldown scaling by error type */
  getRetryCooldown: (errorMessage: string | null, httpStatus?: number) => number;
  /** CRIT-008 AC5: Auto-retry countdown (seconds remaining, null when inactive) */
  retryCountdown: number | null;
  /** GTM-UX-003 AC4-AC7: Contextual retry message (not "servidor reiniciando") */
  retryMessage: string | null;
  /** GTM-UX-003 AC9: True when all 3 auto-retry attempts have been exhausted */
  retryExhausted: boolean;
  /** CRIT-008 AC5: Trigger immediate retry during countdown */
  retryNow: () => void;
  /** CRIT-008 AC5: Cancel auto-retry countdown */
  cancelRetry: () => void;
  /** STAB-006 AC2: Humanized error with action suggestions */
  humanizedError: HumanizedError | null;
  /** STAB-006 AC3: True when showing partial results from localStorage */
  showingPartialResults: boolean;
  /** STAB-006 AC3: Dismiss partial results banner */
  dismissPartialResults: () => void;
  /** STAB-003 AC5: True when search elapsed >100s (finalizing) */
  isFinalizing: boolean;
  /** STAB-009 AC5: True when async 202 mode is active */
  asyncSearchActive: boolean;
  /** STAB-009 AC7: Number of SSE reconnection attempts */
  sseReconnectAttempts: number;
  /** SAB-005 AC1: True when skeletons visible >30s without data update */
  skeletonTimeoutReached: boolean;
}

export function useSearch(filters: UseSearchParams): UseSearchReturn {
  const { session } = useAuth();
  const { refresh: refreshQuota } = useQuota();
  const { trackEvent } = useAnalytics();
  const { saveNewSearch, isMaxCapacity } = useSavedSearches();

  // Loading states
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [statesProcessed, setStatesProcessed] = useState(0);
  const [error, setError] = useState<SearchError | null>(null);
  const [quotaError, setQuotaError] = useState<string | null>(null);

  // CRIT-008 AC5: Auto-retry for transient errors
  const [retryCountdown, setRetryCountdown] = useState<number | null>(null);
  // GTM-UX-003 AC4-AC7: Contextual retry message
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  // GTM-UX-003 AC9: All retry attempts exhausted
  const [retryExhausted, setRetryExhausted] = useState(false);
  const retryAttemptRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const buscarRef = useRef<((options?: { forceFresh?: boolean }) => Promise<void>) | null>(null);
  const autoRetryInProgressRef = useRef(false);

  // SSE progress
  const [searchId, setSearchId] = useState<string | null>(null);
  const [useRealProgress, setUseRealProgress] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Result
  const [result, setResult] = useState<BuscaResult | null>(null);
  const [rawCount, setRawCount] = useState(0);

  // Download
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Save search
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  // Refs
  const searchButtonRef = useRef<HTMLButtonElement>(null);
  const lastSearchParamsRef = useRef<SearchFiltersSnapshot | null>(null);

  // A-04: Live fetch in progress state
  const [liveFetchInProgress, setLiveFetchInProgress] = useState(false);
  // A-04: Keep searchId alive for SSE after cache-first
  const liveFetchSearchIdRef = useRef<string | null>(null);

  // GTM-ARCH-001: Async search mode (202 Accepted — results via SSE)
  const [asyncSearchActive, setAsyncSearchActive] = useState(false);
  const asyncSearchIdRef = useRef<string | null>(null);
  // SAB-001 AC4: Ref mirror of asyncSearchActive — prevents stale closure in buscar() finally block
  const asyncSearchActiveRef = useRef(false);

  // UX-350 AC1-AC4: LLM summary timeout — show fallback after 30s if AI summary not ready
  const llmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // STAB-006 AC3: Partial results recovery from localStorage
  const [showingPartialResults, setShowingPartialResults] = useState(false);

  // CRIT-SSE-FIX AC2: Track whether SSE terminal event was received.
  // Prevents finally block from killing searchId before SSE delivers terminal event.
  const sseTerminalReceivedRef = useRef(false);

  // STAB-003 AC5: Finalizing indicator (>100s elapsed)
  const [isFinalizing, setIsFinalizing] = useState(false);
  const searchStartTimeRef = useRef<number>(0);
  const finalizingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // STAB-009 AC7: SSE reconnection tracking
  const sseReconnectAttemptsRef = useRef(0);

  // SAB-001 AC6: Safety timeout — forces loading=false when result is set but loading stuck
  const resultSafetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // SAB-005 AC1: Skeleton timeout — shows banner after 30s without data update
  const [skeletonTimeoutReached, setSkeletonTimeoutReached] = useState(false);
  const skeletonTimeoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // SAB-001 AC4: Keep ref in sync with state for closure-safe reads
  useEffect(() => {
    asyncSearchActiveRef.current = asyncSearchActive;
  }, [asyncSearchActive]);

  // SAB-001 AC6: Safety timeout — if result is set but loading is still true after 5s,
  // force transition to results. Prevents permanent loading state from any state machine bug.
  useEffect(() => {
    if (loading && result && result.licitacoes && result.licitacoes.length > 0) {
      // Result is set but loading is still true — start safety timer
      console.warn('[SAB-001] Result set but loading=true — safety timer started (5s)');
      resultSafetyTimerRef.current = setTimeout(() => {
        console.error('[SAB-001] Safety timeout triggered — forcing loading=false with result already set');
        setLoading(false);
      }, 5000);
      return () => {
        if (resultSafetyTimerRef.current) {
          clearTimeout(resultSafetyTimerRef.current);
          resultSafetyTimerRef.current = null;
        }
      };
    }
  }, [loading, result]);

  // STAB-006 AC4: Clean up expired partials on mount
  useEffect(() => {
    cleanupExpiredPartials();
  }, []);

  // F-01 AC21: Handle background job completion via SSE
  // GTM-ARCH-001 AC3/AC4: Also handles search_complete from async Worker
  const handleSseEvent = async (event: SearchProgressEvent) => {
    // CRIT-SSE-FIX AC2: Track terminal SSE events so finally block knows when SSE is done
    if (['complete', 'error', 'degraded', 'search_complete'].includes(event.stage)) {
      sseTerminalReceivedRef.current = true;
    }

    if (event.stage === 'search_complete' && event.detail.has_results) {
      // GTM-ARCH-001 AC3: Async search completed — fetch results from /buscar-results
      const sid = event.detail.search_id || asyncSearchIdRef.current;
      if (sid) {
        try {
          const headers: Record<string, string> = {};
          if (session?.access_token) headers["Authorization"] = `Bearer ${session.access_token}`;

          const response = await fetch(`/api/buscar-results/${encodeURIComponent(sid)}`, { headers });
          if (response.ok) {
            const fetchedData = await response.json() as BuscaResult;
            setResult(fetchedData);
            setRawCount(fetchedData.total_raw || 0);

            // GTM-FIX-040 AC1: Clear error state when valid results arrive
            if (fetchedData.licitacoes?.length > 0) {
              setError(null);
              setRetryCountdown(null);
              setRetryMessage(null);
              setRetryExhausted(false);
              if (retryTimerRef.current) {
                clearInterval(retryTimerRef.current);
                retryTimerRef.current = null;
              }
            }

            if (session?.access_token) await refreshQuota();

            trackEvent('search_completed', {
              time_elapsed_ms: Date.now() - (fetchedData as any)?._searchStartTime || 0,
              total_raw: fetchedData.total_raw || 0,
              total_filtered: fetchedData.total_filtrado || 0,
              search_mode: filters.searchMode,
              async_mode: true,
            });
          }
        } catch (e) {
          console.warn('[ARCH-001] Error fetching async search results:', e);
        } finally {
          setAsyncSearchActive(false);
          asyncSearchActiveRef.current = false;
          asyncSearchIdRef.current = null;
          setLoading(false);
          setSearchId(null);
        }
      }
    } else if (event.stage === 'llm_ready' && event.detail.resumo) {
      // AC3: AI summary arrived — clear timeout and update silently
      if (llmTimeoutRef.current) {
        clearTimeout(llmTimeoutRef.current);
        llmTimeoutRef.current = null;
      }
      setResult(prev => prev ? {
        ...prev,
        resumo: event.detail.resumo as BuscaResult['resumo'],
        llm_status: 'ready' as const,
        llm_source: 'ai' as const,
      } : prev);
    } else if (event.stage === 'bid_analysis_ready' && event.detail.bid_analysis) {
      // STORY-259 AC4: Per-bid intelligence analysis arrived
      // Cast to BidAnalysisItem[] — backend guarantees the enum constraint
      const analysisData = event.detail.bid_analysis as BuscaResult['bid_analysis'];
      setResult(prev => prev ? {
        ...prev,
        bid_analysis: analysisData,
        bid_analysis_status: 'ready' as const,
      } : prev);
    } else if (event.stage === 'excel_ready') {
      // Update the result's download_url when Excel is ready
      setResult(prev => prev ? {
        ...prev,
        download_url: event.detail.download_url || null,
        excel_status: (event.detail.excel_status === 'failed' ? 'failed' : 'ready') as BuscaResult['excel_status'],
      } : prev);
    } else if (event.stage === 'uf_complete' || event.stage === 'partial_results') {
      // STAB-006 AC4: Save partial results to localStorage on each SSE update
      const sid = asyncSearchIdRef.current || searchId;
      if (sid) {
        const ufsCompleted = event.detail.ufs_completed ?? [];
        const totalUfs = event.detail.uf_total ?? filters.ufsSelecionadas.size;
        savePartialSearch(sid, result, ufsCompleted, totalUfs);
      }
    } else if (event.stage === 'error' && asyncSearchActiveRef.current) {
      // GTM-ARCH-001: Worker error during async search
      setAsyncSearchActive(false);
      asyncSearchActiveRef.current = false;
      asyncSearchIdRef.current = null;
      setLoading(false);
      setError({
        message: event.detail.error || event.message || 'Erro no processamento da busca',
        rawMessage: event.detail.error || event.message || '',
        errorCode: event.detail.error_code || null,
        searchId: searchId,
        correlationId: null,
        requestId: null,
        httpStatus: null,
        timestamp: new Date().toISOString(),
      });
    }
  };

  // SSE hook — GTM-FIX-033 AC2: sseDisconnected for resilience
  // A-04: Keep SSE open during background fetch (enabled when loading OR liveFetchInProgress)
  // F-01: Keep SSE open when llm_status/excel_status is "processing" (background jobs running)
  // CRIT-SSE-FIX AC2: Include bid_analysis_status in processing check
  const hasProcessingJobs = !!(result?.llm_status === 'processing' || result?.excel_status === 'processing' || result?.bid_analysis_status === 'processing');
  // CRIT-003 AC19-AC20: Single consolidated SSE connection (replaces useSearchProgress + useUfProgress)
  const {
    currentEvent: sseEvent, sseAvailable, sseDisconnected,
    isReconnecting,
    isDegraded, degradedDetail, partialProgress, refreshAvailable,
    ufStatuses, ufTotalFound, ufAllComplete, batchProgress,
    sourceStatuses, filterSummary, pendingReviewUpdate,
  } = useSearchSSE({
    searchId: asyncSearchActive ? asyncSearchIdRef.current : (liveFetchInProgress ? liveFetchSearchIdRef.current : searchId),
    enabled: (loading && !!searchId) || liveFetchInProgress || hasProcessingJobs || asyncSearchActive,
    authToken: session?.access_token,
    selectedUfs: Array.from(filters.ufsSelecionadas),
    onEvent: handleSseEvent,
    onError: () => {
      setUseRealProgress(false);
      // STAB-009 AC7: Track SSE reconnection attempts
      sseReconnectAttemptsRef.current += 1;
    },
  });

  // CRIT-003 AC12-AC13, AC21: Polling fallback when SSE disconnects
  const activeSearchId = liveFetchInProgress ? liveFetchSearchIdRef.current : searchId;
  const { asProgressEvent: pollingEvent } = useSearchPolling({
    searchId: activeSearchId,
    enabled: sseDisconnected && loading && !!activeSearchId,
    authToken: session?.access_token,
    onStatusUpdate: (status) => {
      // Update loading step based on polled state
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'timed_out') {
        setUseRealProgress(false);
      }
    },
  });

  // AC21: Use polling event when SSE is disconnected
  const effectiveEvent = sseDisconnected && pollingEvent ? pollingEvent : sseEvent;

  // P2.1: Sync statesProcessed from real SSE uf_index — always prefer real data over timer.
  // Takes the max of current value and SSE value so progress never goes backwards.
  useEffect(() => {
    const ufIndex = effectiveEvent?.detail?.uf_index;
    if (typeof ufIndex === 'number' && ufIndex > 0) {
      setStatesProcessed(prev => Math.max(prev, ufIndex));
    }
  }, [effectiveEvent?.detail?.uf_index]);

  // SAB-005 AC1: Reset skeleton timeout whenever SSE event arrives (data update)
  useEffect(() => {
    if (loading && effectiveEvent) {
      if (skeletonTimeoutTimerRef.current) {
        clearTimeout(skeletonTimeoutTimerRef.current);
      }
      setSkeletonTimeoutReached(false);
      skeletonTimeoutTimerRef.current = setTimeout(() => {
        setSkeletonTimeoutReached(true);
      }, 30_000);
    }
  }, [loading, effectiveEvent]);

  // =========================================================================
  // STORY-364 AC4-AC6: Excel polling fallback when SSE disconnects
  // =========================================================================
  const excelPollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const excelPollingCountRef = useRef(0);

  useEffect(() => {
    const shouldPoll = !!(
      result
      && result.excel_status === 'processing'
      && !result.download_url
      && !result.download_id
      && (sseDisconnected || !sseAvailable)
      && !loading
    );

    if (!shouldPoll) {
      if (excelPollingRef.current) {
        clearInterval(excelPollingRef.current);
        excelPollingRef.current = null;
      }
      // Reset counter when Excel is resolved
      if (result?.excel_status !== 'processing') {
        excelPollingCountRef.current = 0;
      }
      return;
    }

    const pollExcelStatus = async () => {
      // AC6: Max 12 attempts (60s total)
      if (excelPollingCountRef.current >= 12) {
        if (excelPollingRef.current) {
          clearInterval(excelPollingRef.current);
          excelPollingRef.current = null;
        }
        return;
      }

      excelPollingCountRef.current++;

      try {
        const headers: Record<string, string> = {};
        if (session?.access_token) headers['Authorization'] = `Bearer ${session.access_token}`;

        const sid = asyncSearchIdRef.current || searchId;
        if (!sid) return;

        const res = await fetch(
          `/api/search-status?search_id=${encodeURIComponent(sid)}`,
          { headers },
        );
        if (!res.ok) return;

        const data = await res.json();
        // AC5: When polling returns excel_url, update result
        if (data.excel_url) {
          setResult(prev => prev ? {
            ...prev,
            download_url: data.excel_url,
            excel_status: 'ready' as const,
          } : prev);
          if (excelPollingRef.current) {
            clearInterval(excelPollingRef.current);
            excelPollingRef.current = null;
          }
          excelPollingCountRef.current = 0;
        }
      } catch (e) {
        console.warn('[STORY-364] Excel polling failed:', e);
      }
    };

    // Start polling: immediate first check + every 5s
    pollExcelStatus();
    excelPollingRef.current = setInterval(pollExcelStatus, 5000);

    return () => {
      if (excelPollingRef.current) {
        clearInterval(excelPollingRef.current);
        excelPollingRef.current = null;
      }
    };
  }, [result?.excel_status, result?.download_url, result?.download_id, sseDisconnected, sseAvailable, loading, searchId, session?.access_token]);

  const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech";

  const estimateSearchTime = (ufCount: number, dateRangeDays: number): number => {
    // GTM-FIX-027 T4 AC23: Recalibrated for tamanhoPagina=500 (was 20)
    // With 500 items/page, ~25x fewer requests per modality
    const baseTime = 10; // Base overhead (was 20)
    const parallelUfs = Math.min(ufCount, 10);
    const queuedUfs = Math.max(0, ufCount - 10);
    const fetchTime = parallelUfs * 3 + queuedUfs * 2; // ~4x faster per UF (was 12+6)
    const dateMultiplier = dateRangeDays > 14 ? 1.3 : dateRangeDays > 7 ? 1.1 : 1.0;
    return Math.ceil(baseTime + (fetchTime * dateMultiplier) + 3 + 5 + 3); // filter+LLM+Excel
  };

  const cancelSearch = () => {
    abortControllerRef.current?.abort();
    // UX-350: Clear LLM timeout on cancel
    if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }
    // STAB-003: Clear finalizing state on cancel
    if (finalizingTimerRef.current) { clearTimeout(finalizingTimerRef.current); finalizingTimerRef.current = null; }
    setIsFinalizing(false);
    // SAB-005: Clear skeleton timeout on cancel
    if (skeletonTimeoutTimerRef.current) { clearTimeout(skeletonTimeoutTimerRef.current); skeletonTimeoutTimerRef.current = null; }
    setSkeletonTimeoutReached(false);
    // CRIT-006 AC16: Notify backend of cancellation
    const activeId = asyncSearchIdRef.current || searchId;
    if (activeId && session?.access_token) {
      fetch(`/api/v1/search/${encodeURIComponent(activeId)}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      }).catch(() => {}); // Fire-and-forget
    }
    setLoading(false);
    setSearchId(null);
    setUseRealProgress(false);
    // GTM-ARCH-001: Clean up async state on cancel
    setAsyncSearchActive(false);
    asyncSearchActiveRef.current = false;
    asyncSearchIdRef.current = null;
  };

  // CRIT-SSE-FIX AC1: View partial results without destroying search state.
  // Unlike cancelSearch(), this preserves accumulated results and shows them immediately.
  const viewPartialResults = () => {
    // Abort the POST fetch in flight — we don't need to wait for full results
    abortControllerRef.current?.abort();

    // Clear timers
    if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }
    if (finalizingTimerRef.current) { clearTimeout(finalizingTimerRef.current); finalizingTimerRef.current = null; }
    setIsFinalizing(false);
    if (skeletonTimeoutTimerRef.current) { clearTimeout(skeletonTimeoutTimerRef.current); skeletonTimeoutTimerRef.current = null; }
    setSkeletonTimeoutReached(false);

    // If we already have a result (from POST returning before user clicked), just show it
    if (result && result.licitacoes && result.licitacoes.length > 0) {
      setLoading(false);
      setSearchId(null);
      setUseRealProgress(false);
      return;
    }

    // Otherwise, recover partial results from localStorage (STAB-006)
    const sid = asyncSearchIdRef.current || searchId;
    if (sid) {
      const partial = recoverPartialSearch(sid);
      if (partial && partial.partialResult) {
        setResult(partial.partialResult as BuscaResult);
        setShowingPartialResults(true);
      }
    }

    // Stop loading and clean up SSE
    setLoading(false);
    setSearchId(null);
    setUseRealProgress(false);
    setAsyncSearchActive(false);
    asyncSearchActiveRef.current = false;
    asyncSearchIdRef.current = null;
  };

  // CRIT-006 AC18: Retry cooldown scaling by error type
  const getRetryCooldown = (errorMessage: string | null, httpStatus?: number): number => {
    if (httpStatus === 429) return 30; // Rate limit
    if (httpStatus === 500) return 20; // Server error
    if (errorMessage?.includes('demorou demais') || errorMessage?.includes('timeout') || errorMessage?.includes('TIMEOUT') || httpStatus === 504) return 15; // Timeout
    return 10; // Network error default
  };

  const buscar = async (options?: { forceFresh?: boolean }) => {
    if (!filters.canSearch) return;

    // CRIT-008 AC5: Reset retry state on new user-initiated search (not auto-retry)
    if (!autoRetryInProgressRef.current) {
      retryAttemptRef.current = 0;
      if (retryTimerRef.current) {
        clearInterval(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      setRetryCountdown(null);
      setRetryMessage(null);
      setRetryExhausted(false);
    }
    autoRetryInProgressRef.current = false;

    const forceFresh = options?.forceFresh ?? false;
    const previousResult = forceFresh ? result : null;

    // Save params for pull-to-refresh
    lastSearchParamsRef.current = {
      ufs: new Set(filters.ufsSelecionadas),
      dataInicial: filters.dataInicial,
      dataFinal: filters.dataFinal,
      searchMode: filters.searchMode,
      setorId: filters.searchMode === "setor" ? filters.setorId : undefined,
      termosArray: filters.searchMode === "termos" ? [...filters.termosArray] : undefined,
      status: filters.status,
      modalidades: [...filters.modalidades],
      valorMin: filters.valorMin,
      valorMax: filters.valorMax,
      esferas: [...filters.esferas],
      municipios: [...filters.municipios],
      ordenacao: filters.ordenacao,
    };

    // UX-350: Clear any existing LLM timeout from previous search
    if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }

    // CRIT-030 AC1: Clear ALL previous state FIRST — prevents stale empty state
    // from previous search bleeding into loading state of new search.
    // Save reference for error recovery (CRIT-005 AC23) before clearing.
    const previousResultFallback = result;
    setResult(null);
    setRawCount(0);
    setError(null);
    setQuotaError(null);
    // CRIT-030 AC4: Clear live fetch state from previous search
    setLiveFetchInProgress(false);
    liveFetchSearchIdRef.current = null;
    // GTM-ARCH-001: Clear async state from previous search
    // SAB-001 AC4: Also update ref to prevent stale closure in finally block
    setAsyncSearchActive(false);
    asyncSearchActiveRef.current = false;
    asyncSearchIdRef.current = null;
    // CRIT-027 AC1 + CRIT-030 AC1: Set loading AFTER clearing result
    setLoading(true);
    setLoadingStep(1);
    setStatesProcessed(0);

    const newSearchId = crypto.randomUUID();
    setSearchId(newSearchId);
    setUseRealProgress(true);
    setShowingPartialResults(false);
    setIsFinalizing(false);
    sseReconnectAttemptsRef.current = 0;
    // CRIT-SSE-FIX AC2: Reset terminal tracking for new search
    sseTerminalReceivedRef.current = false;

    // SAB-005 AC1: Start 30s skeleton timeout
    setSkeletonTimeoutReached(false);
    if (skeletonTimeoutTimerRef.current) clearTimeout(skeletonTimeoutTimerRef.current);
    skeletonTimeoutTimerRef.current = setTimeout(() => {
      setSkeletonTimeoutReached(true);
    }, 30_000);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // STAB-003 AC1: Client-side 115s timeout (pipeline 110s + 5s margin)
    const clientTimeoutId = setTimeout(() => {
      abortController.abort();
    }, 115_000);

    // STAB-003 AC5: Show "Finalizando busca..." after 100s
    searchStartTimeRef.current = Date.now();
    if (finalizingTimerRef.current) clearTimeout(finalizingTimerRef.current);
    finalizingTimerRef.current = setTimeout(() => {
      setIsFinalizing(true);
    }, 100_000);

    const searchStartTime = Date.now();
    const totalStates = filters.ufsSelecionadas.size;
    let stateIntervalId: ReturnType<typeof setInterval> | null = null;

    // Slow fallback timer — only advances when SSE is not providing real uf_index data.
    // Interval is 10s per UF (intentionally slow) so real SSE data always wins.
    stateIntervalId = setInterval(() => {
      setStatesProcessed(prev => {
        if (prev >= totalStates) {
          if (stateIntervalId) clearInterval(stateIntervalId);
          return totalStates;
        }
        return prev + 1;
      });
    }, totalStates > 0 ? Math.max(10000, (totalStates * 10000) / (totalStates + 1)) : 10000);

    const cleanupInterval = () => {
      if (stateIntervalId) {
        clearInterval(stateIntervalId);
        stateIntervalId = null;
      }
    };

    trackEvent('search_started', {
      ufs: Array.from(filters.ufsSelecionadas),
      uf_count: filters.ufsSelecionadas.size,
      date_range: {
        inicial: filters.dataInicial, final: filters.dataFinal,
        days: dateDiffInDays(filters.dataInicial, filters.dataFinal),
      },
      search_mode: filters.searchMode,
      setor_id: filters.searchMode === "setor" ? filters.setorId : null,
      termos_busca: filters.searchMode === "termos" ? filters.termosArray.join(", ") : null,
      termos_count: filters.termosArray.length,
    });

    // F-01: Declared outside try so finally block can check llm_status/excel_status
    let data: BuscaResult | null = null;

    try {
      // STORY-357 AC5: Pre-emptive token refresh if token expires within 5 minutes.
      // Prevents 401 during long searches (60-110s) by ensuring a fresh token upfront.
      let activeToken = session?.access_token || null;
      if (session?.expires_at) {
        const expiresInSeconds = session.expires_at - Math.floor(Date.now() / 1000);
        if (expiresInSeconds < 300) {
          console.info(`[buscar] Token expires in ${expiresInSeconds}s — pre-emptive refresh`);
          try {
            const { data: { session: refreshed } } = await supabase.auth.refreshSession();
            if (refreshed?.access_token) {
              activeToken = refreshed.access_token;
              console.info("[buscar] Pre-emptive token refresh succeeded");
            }
          } catch (refreshErr) {
            console.warn("[buscar] Pre-emptive refresh failed, proceeding with current token", refreshErr);
          }
        }
      }

      // STORY-226 AC24: Attach session correlation ID for distributed tracing
      const correlationId = getCorrelationId();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        "X-Correlation-ID": correlationId,
      };
      if (activeToken) headers["Authorization"] = `Bearer ${activeToken}`;

      const MAX_CLIENT_RETRIES = 2;
      const CLIENT_RETRY_DELAYS = [3000, 8000];

      for (let clientAttempt = 0; clientAttempt <= MAX_CLIENT_RETRIES; clientAttempt++) {
        if (clientAttempt > 0) {
          console.warn(`[buscar] Client retry ${clientAttempt}/${MAX_CLIENT_RETRIES}...`);
          await new Promise(resolve => setTimeout(resolve, CLIENT_RETRY_DELAYS[clientAttempt - 1]));
        }

        logCorrelatedRequest("POST", "/api/buscar", correlationId);
        const response = await fetch("/api/buscar", {
          method: "POST",
          headers,
          signal: abortController.signal,
          body: JSON.stringify({
            ufs: Array.from(filters.ufsSelecionadas),
            data_inicial: filters.dataInicial,
            data_final: filters.dataFinal,
            setor_id: filters.searchMode === "setor" ? filters.setorId : null,
            termos_busca: filters.searchMode === "termos" ? filters.termosArray.join(", ") : null,
            search_id: newSearchId,
            modo_busca: filters.modoBusca,
            status: filters.status,
            modalidades: filters.modalidades.length > 0 ? filters.modalidades : undefined,
            valor_minimo: filters.valorMin,
            valor_maximo: filters.valorMax,
            esferas: filters.esferas.length > 0 ? filters.esferas : undefined,
            municipios: filters.municipios.length > 0 ? filters.municipios.map(m => m.codigo) : undefined,
            ordenacao: filters.ordenacao,
            force_fresh: forceFresh || undefined,
          })
        });

        // GTM-ARCH-001 AC4: Handle 202 Accepted (async search queued)
        if (response.status === 202) {
          const queued = await response.json();
          // Search is queued — results will arrive via SSE search_complete event
          setAsyncSearchActive(true);
          asyncSearchActiveRef.current = true;
          asyncSearchIdRef.current = queued.search_id || newSearchId;
          // Keep loading=true, SSE will drive completion
          data = null;
          break;
        }

        if (!response.ok) {
          if ((response.status === 500 || response.status === 502 || response.status === 503) && clientAttempt < MAX_CLIENT_RETRIES) continue;

          const err = await response.json().catch(() => ({ message: null, error_code: null, data: null }));

          // CRIT-009 AC6: Attach structured metadata to thrown errors
          const attachMeta = (error: Error) => {
            (error as any)._searchErrorMeta = {
              errorCode: err.error_code || null,
              searchId: err.search_id || newSearchId,
              correlationId: err.correlation_id || null,
              requestId: err.request_id || null,
              httpStatus: response.status,
              rawMessage: err.message || error.message,
            };
            return error;
          };

          if (response.status === 401) {
            if (result && result.download_id) {
              saveSearchState(result, result.download_id, {
                ufs: Array.from(filters.ufsSelecionadas),
                startDate: filters.dataInicial,
                endDate: filters.dataFinal,
                setor: filters.searchMode === 'setor' ? filters.setorId : undefined,
                includeKeywords: filters.searchMode === 'termos' ? filters.termosArray : undefined,
              });
            }
            // STORY-357 AC4: Show friendly message before redirect
            setError({
              message: "Sua sessão expirou. Reconectando...",
              rawMessage: err.message || "Session expired",
              errorCode: "SESSION_EXPIRED",
              searchId: newSearchId,
              correlationId: correlationId,
              requestId: err.request_id || null,
              httpStatus: 401,
              timestamp: new Date().toISOString(),
            });
            // STORY-357 AC3: Redirect with returnTo for post-login navigation
            const returnTo = err.returnTo || "/buscar";
            setTimeout(() => { window.location.href = `/login?returnTo=${encodeURIComponent(returnTo)}`; }, 1500);
            const authError = attachMeta(new Error("Sua sessão expirou. Reconectando..."));
            (authError as any)._searchErrorMeta.errorCode = "SESSION_EXPIRED";
            throw authError;
          }

          if (response.status === 403) {
            // STORY-265 AC13: Detect trial_expired specifically
            const isTrialExpired = err.error === "trial_expired" || err.detail?.error === "trial_expired";
            const errorMessage = err.detail?.message || err.message || "Suas buscas acabaram.";
            if (isTrialExpired) {
              setQuotaError("trial_expired");
            } else {
              setQuotaError(errorMessage);
            }
            throw attachMeta(new Error(errorMessage));
          }

          if (err.error_code === 'DATE_RANGE_EXCEEDED') {
            const { requested_days, max_allowed_days, plan_name } = err.data || {};
            throw attachMeta(new Error(
              `O período de busca não pode exceder ${max_allowed_days} dias (seu acesso atual). Você tentou buscar ${requested_days} dias. Reduza o período e tente novamente.`
            ));
          }

          if (err.error_code === 'RATE_LIMIT') {
            throw attachMeta(new Error(`Limite de requisições excedido (2/min). Aguarde ${err.data?.wait_seconds || 60} segundos e tente novamente.`));
          }

          throw attachMeta(new Error(err.message || "Erro ao buscar licitações"));
        }

        const parsed = await response.json().catch(() => null);
        if (!parsed) {
          if (clientAttempt < MAX_CLIENT_RETRIES) continue;
          throw new Error("Resposta inesperada do servidor. Tente novamente.");
        }

        data = parsed as BuscaResult;
        break;
      }

      // GTM-ARCH-001: null data is expected for 202 async mode — results come via SSE
      // SAB-001 AC4: Use ref (not stale closure state) for async check
      if (!data && asyncSearchActiveRef.current) {
        // Async mode — skip result processing, SSE will handle it
        return;
      }
      if (!data) throw new Error("Não foi possível obter os resultados. Tente novamente.");

      // SAB-001 AC2: Diagnostic log — POST returned with data
      console.info(`[SAB-001] POST /buscar returned: ${data.licitacoes?.length ?? 0} results, total_raw=${data.total_raw}, total_filtrado=${data.total_filtrado}`);

      setResult(data);
      setRawCount(data.total_raw || 0);

      // GTM-FIX-040 AC1: Clear error state when valid results arrive (safety net for auto-retry)
      if (data.licitacoes?.length > 0 && error) {
        setError(null);
        setRetryCountdown(null);
        setRetryMessage(null);
        setRetryExhausted(false);
      }

      // STAB-006 AC4: Clear partial cache on successful complete search
      clearPartialSearch(newSearchId);

      // GTM-UX-004 AC5: Persist last successful search for SourcesUnavailable fallback
      if (data.licitacoes?.length > 0) {
        saveLastSearch(data);
      }

      // UX-350 AC1-AC2: Start 30s timeout for LLM summary when processing
      if (data.llm_status === 'processing') {
        if (llmTimeoutRef.current) clearTimeout(llmTimeoutRef.current);
        llmTimeoutRef.current = setTimeout(() => {
          // AC2: Timeout expired — transition to fallback label (resumo data already exists)
          // AC4: No "preparando" message remains — fallback is the final result
          setResult(prev => prev && prev.llm_source === 'processing' ? {
            ...prev,
            llm_source: 'fallback' as const,
            llm_status: 'ready' as const,
          } : prev);
          llmTimeoutRef.current = null;
        }, 30_000);
      }

      // A-04 AC1/AC6: Cache-first — keep SSE open for background fetch
      if (data.live_fetch_in_progress) {
        setLiveFetchInProgress(true);
        liveFetchSearchIdRef.current = newSearchId;
      }

      if (filters.searchMode === "termos" && filters.termosArray.length > 0) {
        filters.setOrdenacao("relevancia");
        trackEvent("custom_term_search", {
          terms_count: filters.termosArray.length,
          terms: filters.termosArray,
          total_results: data.total_filtrado || 0,
          hidden_by_min_match: data.hidden_by_min_match || 0,
          filter_relaxed: data.filter_relaxed || false,
        });
      }

      if (session?.access_token) await refreshQuota();

      // GTM-FIX-002 AC10: Include sources_used for multi-source analytics
      trackEvent('search_completed', {
        time_elapsed_ms: Date.now() - searchStartTime,
        total_raw: data.total_raw || 0,
        total_filtered: data.total_filtrado || 0,
        search_mode: filters.searchMode,
        sources_used: data.sources_used || [],  // AC10: Track which sources returned data
        is_partial: data.is_partial || false,
        cached: data.cached || false,
      });

    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        // STAB-006 AC3: On timeout/abort, try to recover partial results from localStorage
        const partial = recoverPartialSearch(newSearchId);
        if (partial && partial.partialResult) {
          setResult(partial.partialResult as BuscaResult);
          setShowingPartialResults(true);
          setLoading(false);
          toast.info("Mostrando resultados parciais salvos");
        }
        return;
      }
      // CRIT-009 AC6: Build structured SearchError preserving all metadata
      const rawMsg = e instanceof Error ? e.message : String(e);
      const errMeta = (e as any)?._searchErrorMeta as {
        errorCode?: string; searchId?: string; correlationId?: string;
        requestId?: string; httpStatus?: number; rawMessage?: string;
      } | undefined;
      const errorCode = errMeta?.errorCode || null;
      const friendlyFromCode = getMessageFromErrorCode(errorCode);
      const friendlyMessage = friendlyFromCode || getUserFriendlyError(e);
      const searchError: SearchError = {
        message: friendlyMessage,
        rawMessage: errMeta?.rawMessage || rawMsg,
        errorCode,
        searchId: errMeta?.searchId || newSearchId,
        correlationId: errMeta?.correlationId || null,
        requestId: errMeta?.requestId || null,
        httpStatus: errMeta?.httpStatus || null,
        timestamp: new Date().toISOString(),
      };
      if (forceFresh && previousResult) {
        // AC9: Keep cached data visible, show toast instead of error
        setResult(previousResult);
        setError(null);
        toast.info("Não foi possível atualizar os dados. Mostrando resultados anteriores.");
      } else {
        // STAB-006 AC3: On timeout, check localStorage for partial results
        const isTimeoutError = searchError.httpStatus === 524 || searchError.httpStatus === 504 ||
          searchError.rawMessage?.toLowerCase().includes('timeout') ||
          searchError.rawMessage?.toLowerCase().includes('demorou');
        if (isTimeoutError) {
          const partial = recoverPartialSearch(newSearchId);
          if (partial && partial.partialResult) {
            setResult(partial.partialResult as BuscaResult);
            setShowingPartialResults(true);
            setError(null);
            toast.info("Mostrando resultados parciais salvos");
            return;
          }
        }
        // CRIT-005 AC23: On error, if we have previous results, show them with error toast
        if (previousResultFallback && previousResultFallback.licitacoes?.length > 0) {
          setResult(previousResultFallback);
          setError(null);
          toast.error(friendlyMessage);
        } else {
          setError(searchError);

          // CRIT-008 AC4-AC5 + GTM-UX-003 AC1-AC7: Auto-retry with contextual messages
          if (isTransientError(searchError.httpStatus, searchError.rawMessage) && retryAttemptRef.current < 3) {
            // GTM-UX-003 AC2: Reduced cooldown 5s→10s→15s (was 10s→20s→30s)
            const RETRY_DELAYS = [5, 10, 15];
            const delaySeconds = RETRY_DELAYS[retryAttemptRef.current] ?? 15;
            let remaining = delaySeconds;
            setRetryCountdown(remaining);
            // GTM-UX-003 AC4-AC7: Contextual message (never "reiniciando")
            setRetryMessage(getRetryMessage(searchError.httpStatus, searchError.rawMessage));
            setRetryExhausted(false);

            if (retryTimerRef.current) clearInterval(retryTimerRef.current);
            retryTimerRef.current = setInterval(() => {
              remaining--;
              if (remaining <= 0) {
                if (retryTimerRef.current) clearInterval(retryTimerRef.current);
                retryTimerRef.current = null;
                setRetryCountdown(null);
                retryAttemptRef.current++;
                autoRetryInProgressRef.current = true;
                setError(null);
                setRetryMessage(null);
                buscarRef.current?.();
              } else {
                setRetryCountdown(remaining);
              }
            }, 1000);
          } else if (isTransientError(searchError.httpStatus, searchError.rawMessage) && retryAttemptRef.current >= 3) {
            // GTM-UX-003 AC9: All 3 attempts exhausted
            setRetryExhausted(true);
            setRetryMessage(null);
          }
        }
      }
      trackEvent('search_failed', { error_message: friendlyMessage, error_code: errorCode, search_mode: filters.searchMode, force_fresh: forceFresh });
    } finally {
      cleanupInterval();
      // STAB-003: Clear client timeout and finalizing timer
      clearTimeout(clientTimeoutId);
      if (finalizingTimerRef.current) {
        clearTimeout(finalizingTimerRef.current);
        finalizingTimerRef.current = null;
      }
      setIsFinalizing(false);
      // SAB-005: Clear skeleton timeout when search completes
      if (skeletonTimeoutTimerRef.current) {
        clearTimeout(skeletonTimeoutTimerRef.current);
        skeletonTimeoutTimerRef.current = null;
      }
      setSkeletonTimeoutReached(false);
      // SAB-001 AC4: Use REF (not stale closure state) to check async mode.
      // The state variable `asyncSearchActive` captures the value from the render
      // that created buscar(), which may be stale. The ref always has current value.
      const isAsync = asyncSearchActiveRef.current;
      // SAB-001 AC2: Diagnostic log — finally block transition
      console.info(`[SAB-001] finally: isAsync=${isAsync}, asyncIdRef=${asyncSearchIdRef.current}, data=${!!data}`);
      // GTM-ARCH-001: Keep loading active for async mode (SSE will complete it)
      if (!isAsync && !asyncSearchIdRef.current) {
        setLoading(false);
      } else {
        console.info(`[SAB-001] Keeping loading=true for async mode (isAsync=${isAsync})`);
      }
      setLoadingStep(1);
      setStatesProcessed(0);
      // A-04: Don't kill searchId when live fetch is running in background
      // F-01: Don't kill searchId when background jobs are still processing
      // GTM-ARCH-001: Don't kill searchId when async search is active
      // CRIT-SSE-FIX AC2: Include bid_analysis_status + wait for SSE terminal event
      const hasJobsRunning = data?.llm_status === 'processing'
        || data?.excel_status === 'processing'
        || data?.bid_analysis_status === 'processing';
      // CRIT-SSE-FIX AC2: Don't kill searchId if SSE hasn't delivered terminal event yet.
      // When POST returns before SSE emits 'complete', killing searchId closes the
      // EventSource mid-stream, causing the AbortError at ~43.5s (CRIT-048).
      // Note: We check sseTerminalReceivedRef (not `searchId` which is a stale closure value).
      // Safety: if SSE terminal never arrives, a 5s timeout below cleans up.
      const sseStillActive = !sseTerminalReceivedRef.current;
      if (!liveFetchInProgress && !liveFetchSearchIdRef.current && !hasJobsRunning && !isAsync && !sseStillActive) {
        setSearchId(null);
      } else if (sseStillActive && !hasJobsRunning && !isAsync && !liveFetchInProgress) {
        // CRIT-SSE-FIX AC2: Deferred cleanup — keep SSE alive for 5s after POST returns
        // so background job events (llm_ready, excel_ready, bid_analysis_ready) can arrive.
        // After 5s, clean up regardless of SSE terminal status.
        setTimeout(() => {
          if (!sseTerminalReceivedRef.current) {
            console.info('[CRIT-SSE-FIX] SSE terminal timeout (5s) — cleaning up searchId');
          }
          sseTerminalReceivedRef.current = true;
          setSearchId(null);
        }, 5000);
      }
      setUseRealProgress(false);
      abortControllerRef.current = null;
    }
  };

  // Keep buscarRef current for auto-retry interval callbacks
  buscarRef.current = buscar;

  // CRIT-008 AC5: Immediate retry during countdown
  const retryNow = () => {
    if (retryTimerRef.current) {
      clearInterval(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    setRetryCountdown(null);
    setRetryMessage(null);
    retryAttemptRef.current++;
    autoRetryInProgressRef.current = true;
    setError(null);
    buscarRef.current?.();
  };

  // CRIT-008 AC5: Cancel auto-retry countdown
  const cancelRetry = () => {
    if (retryTimerRef.current) {
      clearInterval(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    setRetryCountdown(null);
    setRetryMessage(null);
    // Keep the error displayed — user chose to stop retrying
  };

  const handleDownload = async () => {
    // STORY-202 CROSS-C02: Support both download_url (object storage) and download_id (filesystem)
    // UX-349 AC1: Show error instead of silently returning when no download available
    if (!result?.download_id && !result?.download_url) {
      setDownloadError("Excel ainda não disponível. Faça uma nova busca para gerar a planilha.");
      return;
    }
    setDownloadError(null);
    setDownloadLoading(true);

    const downloadIdentifier = result.download_url ? 'url' : result.download_id;
    trackEvent('download_started', { download_id: result.download_id, has_url: !!result.download_url });

    try {
      // STORY-226 AC24: Attach session correlation ID for distributed tracing
      const dlCorrelationId = getCorrelationId();
      const downloadHeaders: Record<string, string> = {
        "X-Correlation-ID": dlCorrelationId,
      };
      if (session?.access_token) downloadHeaders["Authorization"] = `Bearer ${session.access_token}`;

      // Priority 1: Use signed URL from object storage (pass as query param for redirect)
      // Priority 2: Use legacy download_id (filesystem)
      const downloadEndpoint = result.download_url
        ? `/api/download?url=${encodeURIComponent(result.download_url)}`
        : `/api/download?id=${result.download_id}`;

      logCorrelatedRequest("GET", downloadEndpoint, dlCorrelationId);
      const response = await fetch(downloadEndpoint, { headers: downloadHeaders });

      if (!response.ok) {
        if (response.status === 401) { window.location.href = "/login"; throw new Error('Faça login para continuar'); }
        if (response.status === 404) throw new Error('Arquivo expirado. Faça uma nova busca para gerar o Excel.');
        throw new Error('Não foi possível baixar o arquivo. Tente novamente.');
      }

      const blob = await response.blob();
      const setorLabel = filters.sectorName.replace(/\s+/g, '_');
      const appNameSlug = APP_NAME.replace(/\s+/g, '_');
      const filename = `${appNameSlug}_${setorLabel}_${filters.dataInicial}_a_${filters.dataFinal}.xlsx`;

      const anchor = document.createElement('a');
      if ('download' in anchor) {
        const url = URL.createObjectURL(blob);
        anchor.href = url;
        anchor.download = filename;
        anchor.style.display = 'none';
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        setTimeout(() => URL.revokeObjectURL(url), 100);
      } else {
        const url = URL.createObjectURL(blob);
        const newWindow = window.open(url, '_blank');
        if (!newWindow) window.location.href = url;
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }

      trackEvent('download_completed', {
        download_id: result.download_id,
        file_size_bytes: blob.size,
        source: result.download_url ? 'object_storage' : 'filesystem'
      });
    } catch (e) {
      setDownloadError(getUserFriendlyError(e instanceof Error ? e : 'Não foi possível baixar o arquivo.'));
    } finally {
      setDownloadLoading(false);
    }
  };

  // STORY-364 AC7: Regenerate Excel without re-running search
  const handleRegenerateExcel = async () => {
    const sid = asyncSearchIdRef.current || searchId;
    if (!sid) {
      setDownloadError("Sem ID de busca para regenerar Excel.");
      return;
    }

    // Set processing state
    setResult(prev => prev ? { ...prev, excel_status: 'processing' as const, download_url: null } : prev);
    excelPollingCountRef.current = 0;

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (session?.access_token) headers['Authorization'] = `Bearer ${session.access_token}`;

      const res = await fetch(`/api/regenerate-excel/${encodeURIComponent(sid)}`, {
        method: 'POST',
        headers,
      });

      if (res.status === 404) {
        setDownloadError("Resultados expirados. Faça uma nova busca.");
        setResult(prev => prev ? { ...prev, excel_status: 'failed' as const } : prev);
        return;
      }

      if (!res.ok) {
        setDownloadError("Erro ao regenerar Excel. Tente novamente.");
        setResult(prev => prev ? { ...prev, excel_status: 'failed' as const } : prev);
        return;
      }

      const data = await res.json();

      // If inline generation returned ready result
      if (data.excel_status === 'ready' && data.download_url) {
        setResult(prev => prev ? {
          ...prev,
          download_url: data.download_url,
          excel_status: 'ready' as const,
        } : prev);
        return;
      }

      // 202 — job queued, polling will pick it up via the effect above
      // excel_status is already 'processing'
    } catch (e) {
      console.error('[STORY-364] Regenerate Excel failed:', e);
      setDownloadError("Erro de rede ao regenerar Excel.");
      setResult(prev => prev ? { ...prev, excel_status: 'failed' as const } : prev);
    }
  };

  const handleSaveSearch = () => {
    if (!result) return;
    const defaultName = filters.searchMode === "setor"
      ? (filters.sectorName || "Busca personalizada")
      : filters.termosArray.length > 0
        ? `Busca: "${filters.termosArray.join(', ')}"`
        : "Busca personalizada";
    setSaveSearchName(defaultName);
    setSaveError(null);
    setShowSaveDialog(true);
  };

  const confirmSaveSearch = () => {
    try {
      saveNewSearch(saveSearchName || "Busca sem nome", {
        ufs: Array.from(filters.ufsSelecionadas),
        dataInicial: filters.dataInicial,
        dataFinal: filters.dataFinal,
        searchMode: filters.searchMode,
        setorId: filters.searchMode === "setor" ? filters.setorId : undefined,
        termosBusca: filters.searchMode === "termos" ? filters.termosArray.join(", ") : undefined,
      });
      trackEvent('saved_search_created', { search_name: saveSearchName, search_mode: filters.searchMode });
      toast.success(`Busca "${saveSearchName || "Busca sem nome"}" salva com sucesso!`);
      setShowSaveDialog(false);
      setSaveSearchName("");
      setSaveError(null);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Erro ao salvar busca");
      toast.error(`Erro ao salvar: ${error instanceof Error ? error.message : "Erro desconhecido"}`);
    }
  };

  const handleLoadSearch = (search: SavedSearch) => {
    filters.setUfsSelecionadas(new Set(search.searchParams.ufs));
    filters.setDataInicial(search.searchParams.dataInicial);
    filters.setDataFinal(search.searchParams.dataFinal);
    filters.setSearchMode(search.searchParams.searchMode);
    if (search.searchParams.searchMode === "setor" && search.searchParams.setorId) {
      filters.setSetorId(search.searchParams.setorId);
    } else if (search.searchParams.searchMode === "termos" && search.searchParams.termosBusca) {
      const savedTerms = search.searchParams.termosBusca;
      if (savedTerms.includes(",")) {
        filters.setTermosArray(savedTerms.split(",").map((t: string) => t.trim()).filter(Boolean));
      } else {
        filters.setTermosArray(savedTerms.split(" ").filter(Boolean));
      }
    }
    setResult(null);
  };

  const handleRefresh = async (): Promise<void> => {
    if (!lastSearchParamsRef.current) return;
    const params = lastSearchParamsRef.current;
    filters.setUfsSelecionadas(new Set(params.ufs));
    filters.setDataInicial(params.dataInicial);
    filters.setDataFinal(params.dataFinal);
    filters.setSearchMode(params.searchMode);
    if (params.searchMode === "setor" && params.setorId) filters.setSetorId(params.setorId);
    else if (params.searchMode === "termos" && params.termosArray) filters.setTermosArray(params.termosArray);
    filters.setStatus(params.status);
    filters.setModalidades(params.modalidades);
    filters.setValorMin(params.valorMin);
    filters.setValorMax(params.valorMax);
    filters.setEsferas(params.esferas);
    filters.setMunicipios(params.municipios);
    trackEvent('pull_to_refresh_triggered', { search_mode: params.searchMode });
    await buscar();
  };

  const restoreSearchStateOnMount = () => {
    const restored = restoreSearchState();
    if (restored) {
      if (restored.result) setResult(restored.result);
      const { formState } = restored;
      if (formState.ufs?.length) filters.setUfsSelecionadas(new Set(formState.ufs));
      if (formState.startDate) filters.setDataInicial(formState.startDate);
      if (formState.endDate) filters.setDataFinal(formState.endDate);
      if (formState.setor) { filters.setSearchMode('setor'); filters.setSetorId(formState.setor); }
      if (formState.includeKeywords?.length) { filters.setSearchMode('termos'); filters.setTermosArray(formState.includeKeywords); }
      toast.success('Resultados da busca restaurados! Voce pode fazer o download agora.');
      trackEvent('search_state_auto_restored', { download_id: restored.downloadId });
    }
  };

  // A-04 AC9: Fetch live results from background fetch and replace cached data
  const handleRefreshResults = async () => {
    const sid = liveFetchSearchIdRef.current;
    if (!sid) return;

    try {
      const headers: Record<string, string> = {};
      if (session?.access_token) headers["Authorization"] = `Bearer ${session.access_token}`;

      const response = await fetch(`/api/buscar-results/${encodeURIComponent(sid)}`, { headers });
      if (!response.ok) {
        console.warn(`[A-04] Failed to fetch live results: ${response.status}`);
        toast.info("Não foi possível carregar os dados atualizados. Tente uma nova busca.");
        return;
      }

      const data = await response.json();
      setResult(data as BuscaResult);
      setRawCount(data.total_raw || 0);
      trackEvent('progressive_refresh_applied', {
        search_id: sid,
        new_count: refreshAvailable?.newCount ?? 0,
      });
    } catch (e) {
      console.warn('[A-04] Error fetching refresh results:', e);
    } finally {
      // Clean up live fetch state
      setLiveFetchInProgress(false);
      liveFetchSearchIdRef.current = null;
      setSearchId(null);
    }
  };

  const buscarForceFresh = async () => buscar({ forceFresh: true });

  /** STAB-006 AC3: Dismiss partial results banner */
  const dismissPartialResults = () => {
    setShowingPartialResults(false);
  };

  /** STAB-006 AC2: Compute humanized error from current error state */
  const humanizedError: HumanizedError | null = error
    ? getHumanizedError(error.httpStatus, error.rawMessage)
    : null;

  return {
    loading, loadingStep, statesProcessed, error, quotaError,
    result, setResult, setError, rawCount,
    searchId, useRealProgress, sseEvent: effectiveEvent, sseAvailable, sseDisconnected, isReconnecting, isDegraded, degradedDetail,
    partialProgress, refreshAvailable,
    ufStatuses, ufTotalFound, ufAllComplete, batchProgress,
    sourceStatuses, filterSummary, pendingReviewUpdate,
    liveFetchInProgress, handleRefreshResults,
    downloadLoading, downloadError,
    searchButtonRef: searchButtonRef as React.RefObject<HTMLButtonElement>,
    showSaveDialog, setShowSaveDialog,
    saveSearchName, setSaveSearchName,
    saveError, isMaxCapacity,
    buscar, buscarForceFresh, cancelSearch, viewPartialResults, handleDownload, handleRegenerateExcel,
    handleSaveSearch, confirmSaveSearch, handleLoadSearch, handleRefresh,
    estimateSearchTime, restoreSearchStateOnMount,
    getRetryCooldown,
    retryCountdown,
    retryMessage,
    retryExhausted,
    retryNow,
    cancelRetry,
    humanizedError,
    showingPartialResults,
    dismissPartialResults,
    isFinalizing,
    asyncSearchActive,
    sseReconnectAttempts: sseReconnectAttemptsRef.current,
    skeletonTimeoutReached,
  };
}
