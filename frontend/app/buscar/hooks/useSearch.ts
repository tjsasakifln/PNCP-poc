"use client";

import { useState, useRef } from "react";
import type { BuscaResult } from "../../types";
import type { StatusLicitacao } from "../../../components/StatusFilter";
import type { Esfera } from "../../components/EsferaFilter";
import type { Municipio } from "../../components/MunicipioFilter";
import type { OrdenacaoOption } from "../../components/OrdenacaoSelect";
import type { SavedSearch } from "../../../lib/savedSearches";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { useAuth } from "../../components/AuthProvider";
import { useQuota } from "../../../hooks/useQuota";
import { useSearchProgress, type SearchProgressEvent, type PartialProgress, type RefreshAvailableInfo } from "../../../hooks/useSearchProgress";
import { useSearchPolling } from "../../../hooks/useSearchPolling";
import { useSavedSearches } from "../../../hooks/useSavedSearches";
import { getUserFriendlyError, getMessageFromErrorCode, isTransientError } from "../../../lib/error-messages";
import { saveSearchState, restoreSearchState } from "../../../lib/searchStatePersistence";
import { toast } from "sonner";
import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";
import { getCorrelationId, logCorrelatedRequest } from "../../../lib/utils/correlationId";

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
  rawCount: number;
  searchId: string | null;
  useRealProgress: boolean;
  sseEvent: SearchProgressEvent | null;
  sseAvailable: boolean;
  /** GTM-FIX-033 AC2: true when SSE disconnected after retry */
  sseDisconnected: boolean;
  /** A-02 AC8: true when search completed with degraded data */
  isDegraded: boolean;
  /** A-02 AC10: metadata from degraded SSE event */
  degradedDetail: SearchProgressEvent['detail'] | null;
  /** A-04 AC7: Partial progress from background fetch */
  partialProgress: PartialProgress | null;
  /** A-04 AC4: Refresh available info from background fetch */
  refreshAvailable: RefreshAvailableInfo | null;
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
  handleDownload: () => Promise<void>;
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
  /** CRIT-008 AC5: Trigger immediate retry during countdown */
  retryNow: () => void;
  /** CRIT-008 AC5: Cancel auto-retry countdown */
  cancelRetry: () => void;
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

  // F-01 AC21: Handle background job completion via SSE
  const handleSseEvent = (event: SearchProgressEvent) => {
    if (event.stage === 'llm_ready' && event.detail.resumo) {
      // Update the result's resumo with the AI-generated summary
      setResult(prev => prev ? {
        ...prev,
        resumo: event.detail.resumo as BuscaResult['resumo'],
        llm_status: 'ready' as const,
      } : prev);
    } else if (event.stage === 'excel_ready') {
      // Update the result's download_url when Excel is ready
      setResult(prev => prev ? {
        ...prev,
        download_url: event.detail.download_url || null,
        excel_status: (event.detail.excel_status === 'failed' ? 'failed' : 'ready') as BuscaResult['excel_status'],
      } : prev);
    }
  };

  // SSE hook — GTM-FIX-033 AC2: sseDisconnected for resilience
  // A-04: Keep SSE open during background fetch (enabled when loading OR liveFetchInProgress)
  // F-01: Keep SSE open when llm_status/excel_status is "processing" (background jobs running)
  const hasProcessingJobs = !!(result?.llm_status === 'processing' || result?.excel_status === 'processing');
  const { currentEvent: sseEvent, sseAvailable, sseDisconnected, isDegraded, degradedDetail, partialProgress, refreshAvailable } = useSearchProgress({
    searchId: liveFetchInProgress ? liveFetchSearchIdRef.current : searchId,
    enabled: (loading && !!searchId) || liveFetchInProgress || hasProcessingJobs,
    authToken: session?.access_token,
    onEvent: handleSseEvent,
    onError: () => setUseRealProgress(false),
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
    // CRIT-006 AC16: Notify backend of cancellation
    if (searchId && session?.access_token) {
      fetch(`/api/v1/search/${encodeURIComponent(searchId)}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      }).catch(() => {}); // Fire-and-forget
    }
    setLoading(false);
    setSearchId(null);
    setUseRealProgress(false);
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

    setLoading(true);
    setLoadingStep(1);
    setStatesProcessed(0);
    setError(null);
    setQuotaError(null);
    // CRIT-005 AC23: Preserve previous result as visual fallback
    // Don't clear immediately — only replace when new data arrives or on non-recoverable error
    const previousResultFallback = result;
    if (!forceFresh) {
      // Don't setResult(null) here — keep previous results visible during loading
      setRawCount(0);
    }

    const newSearchId = crypto.randomUUID();
    setSearchId(newSearchId);
    setUseRealProgress(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const searchStartTime = Date.now();
    const totalStates = filters.ufsSelecionadas.size;
    let stateIntervalId: ReturnType<typeof setInterval> | null = null;

    stateIntervalId = setInterval(() => {
      setStatesProcessed(prev => {
        if (prev >= totalStates) {
          if (stateIntervalId) clearInterval(stateIntervalId);
          return totalStates;
        }
        return prev + 1;
      });
    }, totalStates > 0 ? Math.max(2000, (totalStates * 6000) / (totalStates + 1)) : 3000);

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
      // STORY-226 AC24: Attach session correlation ID for distributed tracing
      const correlationId = getCorrelationId();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        "X-Correlation-ID": correlationId,
      };
      if (session?.access_token) headers["Authorization"] = `Bearer ${session.access_token}`;

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
            window.location.href = "/login";
            throw attachMeta(new Error("Faca login para continuar"));
          }

          if (response.status === 403) {
            setQuotaError(err.message || "Suas buscas acabaram.");
            throw attachMeta(new Error(err.message || "Quota excedida"));
          }

          if (err.error_code === 'DATE_RANGE_EXCEEDED') {
            const { requested_days, max_allowed_days, plan_name } = err.data || {};
            throw attachMeta(new Error(
              `O periodo de busca nao pode exceder ${max_allowed_days} dias (seu plano: ${plan_name}). Voce tentou buscar ${requested_days} dias. Reduza o periodo e tente novamente.`
            ));
          }

          if (err.error_code === 'RATE_LIMIT') {
            throw attachMeta(new Error(`Limite de requisicoes excedido (2/min). Aguarde ${err.data?.wait_seconds || 60} segundos e tente novamente.`));
          }

          throw attachMeta(new Error(err.message || "Erro ao buscar licitacoes"));
        }

        const parsed = await response.json().catch(() => null);
        if (!parsed) {
          if (clientAttempt < MAX_CLIENT_RETRIES) continue;
          throw new Error("Resposta inesperada do servidor. Tente novamente.");
        }

        data = parsed as BuscaResult;
        break;
      }

      if (!data) throw new Error("Nao foi possivel obter os resultados. Tente novamente.");

      setResult(data);
      setRawCount(data.total_raw || 0);

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
      if (e instanceof DOMException && e.name === 'AbortError') return;
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
        toast.info("Nao foi possivel atualizar os dados. Mostrando resultados anteriores.");
      } else {
        // CRIT-005 AC23: On error, if we have previous results, show them with error toast
        if (previousResultFallback && previousResultFallback.licitacoes?.length > 0) {
          setResult(previousResultFallback);
          setError(null);
          toast.error(friendlyMessage);
        } else {
          setError(searchError);

          // CRIT-008 AC4-AC5: Start auto-retry countdown for transient errors
          if (isTransientError(searchError.httpStatus, searchError.rawMessage) && retryAttemptRef.current < 3) {
            const RETRY_DELAYS = [10, 20, 30];
            const delaySeconds = RETRY_DELAYS[retryAttemptRef.current] ?? 30;
            let remaining = delaySeconds;
            setRetryCountdown(remaining);

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
                buscarRef.current?.();
              } else {
                setRetryCountdown(remaining);
              }
            }, 1000);
          }
        }
      }
      trackEvent('search_failed', { error_message: friendlyMessage, error_code: errorCode, search_mode: filters.searchMode, force_fresh: forceFresh });
    } finally {
      cleanupInterval();
      setLoading(false);
      setLoadingStep(1);
      setStatesProcessed(0);
      // A-04: Don't kill searchId when live fetch is running in background
      // F-01: Don't kill searchId when background jobs are still processing
      const hasJobsRunning = data?.llm_status === 'processing' || data?.excel_status === 'processing';
      if (!liveFetchInProgress && !liveFetchSearchIdRef.current && !hasJobsRunning) {
        setSearchId(null);
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
    // Keep the error displayed — user chose to stop retrying
  };

  const handleDownload = async () => {
    // STORY-202 CROSS-C02: Support both download_url (object storage) and download_id (filesystem)
    if (!result?.download_id && !result?.download_url) return;
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
        if (response.status === 401) { window.location.href = "/login"; throw new Error('Faca login para continuar'); }
        if (response.status === 404) throw new Error('Arquivo expirado. Faca uma nova busca para gerar o Excel.');
        throw new Error('Nao foi possivel baixar o arquivo. Tente novamente.');
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
      setDownloadError(getUserFriendlyError(e instanceof Error ? e : 'Nao foi possivel baixar o arquivo.'));
    } finally {
      setDownloadLoading(false);
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
        toast.info("Nao foi possivel carregar os dados atualizados. Tente uma nova busca.");
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

  return {
    loading, loadingStep, statesProcessed, error, quotaError,
    result, setResult, rawCount,
    searchId, useRealProgress, sseEvent: effectiveEvent, sseAvailable, sseDisconnected, isDegraded, degradedDetail,
    partialProgress, refreshAvailable, liveFetchInProgress, handleRefreshResults,
    downloadLoading, downloadError,
    searchButtonRef: searchButtonRef as React.RefObject<HTMLButtonElement>,
    showSaveDialog, setShowSaveDialog,
    saveSearchName, setSaveSearchName,
    saveError, isMaxCapacity,
    buscar, buscarForceFresh, cancelSearch, handleDownload,
    handleSaveSearch, confirmSaveSearch, handleLoadSearch, handleRefresh,
    estimateSearchTime, restoreSearchStateOnMount,
    getRetryCooldown,
    retryCountdown,
    retryNow,
    cancelRetry,
  };
}
