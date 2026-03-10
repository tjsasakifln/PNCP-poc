"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type { BuscaResult } from "../../types";
import type { SearchError, SearchFiltersSnapshot } from "./useSearch";
import type { RefreshAvailableInfo } from "../../../hooks/useSearchSSE";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { useAuth } from "../../components/AuthProvider";
import { useQuota } from "../../../hooks/useQuota";
import { getUserFriendlyError, getMessageFromErrorCode } from "../../../lib/error-messages";
import { saveSearchState } from "../../../lib/searchStatePersistence";
import { saveLastSearch } from "../../../lib/lastSearchCache";
import { recoverPartialSearch, clearPartialSearch } from "../../../lib/searchPartialCache";
import { toast } from "sonner";
import { dateDiffInDays } from "../../../lib/utils/dateDiffInDays";
import { getCorrelationId, logCorrelatedRequest } from "../../../lib/utils/correlationId";
import { supabase } from "../../../lib/supabase";

interface UseSearchExecutionFilters {
  ufsSelecionadas: Set<string>;
  dataInicial: string;
  dataFinal: string;
  searchMode: "setor" | "termos";
  modoBusca: "abertas" | "publicacao";
  setorId: string;
  termosArray: string[];
  status: import("../components/StatusFilter").StatusLicitacao;
  modalidades: number[];
  valorMin: number | null;
  valorMax: number | null;
  esferas: import("../../components/EsferaFilter").Esfera[];
  municipios: import("../../components/MunicipioFilter").Municipio[];
  ordenacao: import("../../components/OrdenacaoSelect").OrdenacaoOption;
  canSearch: boolean;
  setOrdenacao: (ord: import("../../components/OrdenacaoSelect").OrdenacaoOption) => void;
}

interface UseSearchExecutionParams {
  filters: UseSearchExecutionFilters;
  // Shared state from orchestrator
  result: BuscaResult | null;
  setResult: React.Dispatch<React.SetStateAction<BuscaResult | null>>;
  setRawCount: (n: number) => void;
  error: SearchError | null;
  setError: (e: SearchError | null) => void;
  // Retry refs from useSearchRetry
  autoRetryInProgressRef: React.MutableRefObject<boolean>;
  buscarRef: React.MutableRefObject<((options?: { forceFresh?: boolean }) => Promise<void>) | null>;
  resetRetryForNewSearch: () => void;
  startAutoRetry: (searchError: SearchError, setError: (e: SearchError | null) => void) => void;
  setRetryCountdown: (v: number | null) => void;
  setRetryMessage: (v: string | null) => void;
  setRetryExhausted: (v: boolean) => void;
  // Export refs — owned by orchestrator, shared with export hook
  excelFailCountRef: React.MutableRefObject<number>;
  excelToastFiredRef: React.MutableRefObject<boolean>;
  // Persistence refs — owned by orchestrator, shared with persistence hook
  lastSearchParamsRef: React.MutableRefObject<SearchFiltersSnapshot | null>;
  showingPartialResults: boolean;
  setShowingPartialResults: (v: boolean) => void;
  // SSE info for handleRefreshResults — ref so it always has latest value
  refreshAvailableRef: React.MutableRefObject<RefreshAvailableInfo | null>;
}

export interface UseSearchExecutionReturn {
  loading: boolean;
  setLoading: (b: boolean) => void;
  loadingStep: number;
  statesProcessed: number;
  setStatesProcessed: React.Dispatch<React.SetStateAction<number>>;
  searchId: string | null;
  setSearchId: (id: string | null) => void;
  useRealProgress: boolean;
  setUseRealProgress: (b: boolean) => void;
  quotaError: string | null;
  isFinalizing: boolean;
  asyncSearchActive: boolean;
  setAsyncSearchActive: (b: boolean) => void;
  asyncSearchActiveRef: React.MutableRefObject<boolean>;
  asyncSearchIdRef: React.MutableRefObject<string | null>;
  abortControllerRef: React.MutableRefObject<AbortController | null>;
  llmTimeoutRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  sseTerminalReceivedRef: React.MutableRefObject<boolean>;
  sseReconnectAttemptsRef: React.MutableRefObject<number>;
  liveFetchInProgress: boolean;
  liveFetchSearchIdRef: React.MutableRefObject<string | null>;
  skeletonTimeoutReached: boolean;
  setSkeletonTimeoutReached: (b: boolean) => void;
  skeletonTimeoutTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  searchButtonRef: React.RefObject<HTMLButtonElement>;
  buscar: (options?: { forceFresh?: boolean }) => Promise<void>;
  cancelSearch: () => void;
  viewPartialResults: () => void;
  estimateSearchTime: (ufCount: number, dateRangeDays: number) => number;
  handleRefreshResults: () => Promise<void>;
}

export function useSearchExecution(params: UseSearchExecutionParams): UseSearchExecutionReturn {
  const {
    filters, result, setResult, setRawCount, error, setError,
    autoRetryInProgressRef, buscarRef,
    resetRetryForNewSearch, startAutoRetry,
    setRetryCountdown, setRetryMessage, setRetryExhausted,
    excelFailCountRef, excelToastFiredRef,
    lastSearchParamsRef, setShowingPartialResults,
    refreshAvailableRef,
  } = params;

  const { session } = useAuth();
  const { refresh: refreshQuota } = useQuota();
  const { trackEvent } = useAnalytics();

  // Loading states
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [statesProcessed, setStatesProcessed] = useState(0);
  const [quotaError, setQuotaError] = useState<string | null>(null);

  // SSE progress
  const [searchId, setSearchId] = useState<string | null>(null);
  const [useRealProgress, setUseRealProgress] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Refs
  const searchButtonRef = useRef<HTMLButtonElement>(null);

  // A-04: Live fetch in progress state
  const [liveFetchInProgress, setLiveFetchInProgress] = useState(false);
  const liveFetchSearchIdRef = useRef<string | null>(null);

  // GTM-ARCH-001: Async search mode (202 Accepted — results via SSE)
  const [asyncSearchActive, setAsyncSearchActive] = useState(false);
  const asyncSearchIdRef = useRef<string | null>(null);
  // SAB-001 AC4: Ref mirror of asyncSearchActive
  const asyncSearchActiveRef = useRef(false);

  // UX-350 AC1-AC4: LLM summary timeout
  const llmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // CRIT-SSE-FIX AC2: Track whether SSE terminal event was received.
  const sseTerminalReceivedRef = useRef(false);

  // STAB-003 AC5: Finalizing indicator (>100s elapsed)
  const [isFinalizing, setIsFinalizing] = useState(false);
  const searchStartTimeRef = useRef<number>(0);
  const finalizingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // STAB-009 AC7: SSE reconnection tracking
  const sseReconnectAttemptsRef = useRef(0);

  // SAB-001 AC6: Safety timeout
  const resultSafetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // SAB-005 AC1: Skeleton timeout
  const [skeletonTimeoutReached, setSkeletonTimeoutReached] = useState(false);
  const skeletonTimeoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // SAB-001 AC4: Keep ref in sync with state for closure-safe reads
  useEffect(() => {
    asyncSearchActiveRef.current = asyncSearchActive;
  }, [asyncSearchActive]);

  // SAB-001 AC6: Safety timeout — if result is set but loading is still true after 5s,
  // force transition to results.
  useEffect(() => {
    if (loading && result && result.licitacoes && result.licitacoes.length > 0) {
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

  const estimateSearchTime = useCallback((ufCount: number, dateRangeDays: number): number => {
    const baseTime = 10;
    const parallelUfs = Math.min(ufCount, 10);
    const queuedUfs = Math.max(0, ufCount - 10);
    const fetchTime = parallelUfs * 3 + queuedUfs * 2;
    const dateMultiplier = dateRangeDays > 14 ? 1.3 : dateRangeDays > 7 ? 1.1 : 1.0;
    return Math.ceil(baseTime + (fetchTime * dateMultiplier) + 3 + 5 + 3);
  }, []);

  const cancelSearch = useCallback(() => {
    abortControllerRef.current?.abort();
    if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }
    if (finalizingTimerRef.current) { clearTimeout(finalizingTimerRef.current); finalizingTimerRef.current = null; }
    setIsFinalizing(false);
    if (skeletonTimeoutTimerRef.current) { clearTimeout(skeletonTimeoutTimerRef.current); skeletonTimeoutTimerRef.current = null; }
    setSkeletonTimeoutReached(false);
    const activeId = asyncSearchIdRef.current || searchId;
    if (activeId && session?.access_token) {
      fetch(`/api/v1/search/${encodeURIComponent(activeId)}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      }).catch(() => {});
    }
    setLoading(false);
    setSearchId(null);
    setUseRealProgress(false);
    setAsyncSearchActive(false);
    asyncSearchActiveRef.current = false;
    asyncSearchIdRef.current = null;
  }, [searchId, session]);

  // CRIT-SSE-FIX AC1: View partial results without destroying search state.
  const viewPartialResults = useCallback(() => {
    abortControllerRef.current?.abort();
    if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }
    if (finalizingTimerRef.current) { clearTimeout(finalizingTimerRef.current); finalizingTimerRef.current = null; }
    setIsFinalizing(false);
    if (skeletonTimeoutTimerRef.current) { clearTimeout(skeletonTimeoutTimerRef.current); skeletonTimeoutTimerRef.current = null; }
    setSkeletonTimeoutReached(false);

    if (result && result.licitacoes && result.licitacoes.length > 0) {
      setLoading(false);
      setSearchId(null);
      setUseRealProgress(false);
      return;
    }

    const sid = asyncSearchIdRef.current || searchId;
    if (sid) {
      const partial = recoverPartialSearch(sid);
      if (partial && partial.partialResult) {
        setResult(partial.partialResult as BuscaResult);
        setShowingPartialResults(true);
      }
    }

    setLoading(false);
    setSearchId(null);
    setUseRealProgress(false);
    setAsyncSearchActive(false);
    asyncSearchActiveRef.current = false;
    asyncSearchIdRef.current = null;
  }, [result, searchId, setResult, setShowingPartialResults]);

  const buscar = useCallback(async (options?: { forceFresh?: boolean }) => {
    if (!filters.canSearch) return;

    resetRetryForNewSearch();

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

    if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }

    // CRIT-030 AC1: Clear ALL previous state FIRST — prevents stale empty state
    // from previous search bleeding into loading state of new search.
    // Save reference for error recovery (CRIT-005 AC23) before clearing.
    const previousResultFallback = result;
    setResult(null);
    setRawCount(0);
    setError(null);
    setQuotaError(null);
    // UX-405: Reset Excel failure tracking on new search
    excelFailCountRef.current = 0;
    excelToastFiredRef.current = false;
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
    sseTerminalReceivedRef.current = false;

    setSkeletonTimeoutReached(false);
    if (skeletonTimeoutTimerRef.current) clearTimeout(skeletonTimeoutTimerRef.current);
    skeletonTimeoutTimerRef.current = setTimeout(() => {
      setSkeletonTimeoutReached(true);
    }, 30_000);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // CRIT-070: Client timeout >= proxy (180s). Chain: Railway(300s) > Gunicorn(180s) > Proxy(180s) >= Client(185s)
    const clientTimeoutId = setTimeout(() => {
      abortController.abort();
    }, 185_000);

    searchStartTimeRef.current = Date.now();
    if (finalizingTimerRef.current) clearTimeout(finalizingTimerRef.current);
    // CRIT-070 AC3: Finalizing shows ~25s before client timeout (185s - 25s = 160s)
    finalizingTimerRef.current = setTimeout(() => {
      setIsFinalizing(true);
    }, 160_000);

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

    let data: BuscaResult | null = null;

    try {
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
            esferas: filters.esferas.length > 0 && filters.esferas.length < 3 ? filters.esferas : undefined,
            municipios: filters.municipios.length > 0 ? filters.municipios.map(m => m.codigo) : undefined,
            ordenacao: filters.ordenacao,
            force_fresh: forceFresh || undefined,
          })
        });

        if (response.status === 202) {
          const queued = await response.json();
          setAsyncSearchActive(true);
          asyncSearchActiveRef.current = true;
          asyncSearchIdRef.current = queued.search_id || newSearchId;
          data = null;
          break;
        }

        if (!response.ok) {
          if ((response.status === 500 || response.status === 502 || response.status === 503) && clientAttempt < MAX_CLIENT_RETRIES) continue;

          const err = await response.json().catch(() => ({ message: null, error_code: null, data: null }));

          interface SearchErrorMeta {
            errorCode: string | null;
            searchId: string;
            correlationId: string | null;
            requestId: string | null;
            httpStatus: number;
            rawMessage: string;
          }
          type ErrorWithMeta = Error & { _searchErrorMeta?: SearchErrorMeta };
          const attachMeta = (error: Error): ErrorWithMeta => {
            (error as ErrorWithMeta)._searchErrorMeta = {
              errorCode: err.error_code || null,
              searchId: err.search_id || newSearchId,
              correlationId: err.correlation_id || null,
              requestId: err.request_id || null,
              httpStatus: response.status,
              rawMessage: err.message || error.message,
            };
            return error as ErrorWithMeta;
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
            const returnTo = err.returnTo || "/buscar";
            setTimeout(() => { window.location.href = `/login?returnTo=${encodeURIComponent(returnTo)}`; }, 1500);
            const authError = attachMeta(new Error("Sua sessão expirou. Reconectando..."));
            if (authError._searchErrorMeta) {
              authError._searchErrorMeta.errorCode = "SESSION_EXPIRED";
            }
            throw authError;
          }

          if (response.status === 403) {
            const isTrialExpired = err.error === "trial_expired" || err.detail?.error === "trial_expired";
            const errorMessage = err.detail?.message || err.message || "Suas análises acabaram.";
            if (isTrialExpired) {
              setQuotaError("trial_expired");
            } else {
              setQuotaError(errorMessage);
            }
            throw attachMeta(new Error(errorMessage));
          }

          if (err.error_code === 'DATE_RANGE_EXCEEDED') {
            const { requested_days, max_allowed_days } = err.data || {};
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

      if (!data && asyncSearchActiveRef.current) {
        return;
      }
      if (!data) throw new Error("Não foi possível obter os resultados. Tente novamente.");

      console.info(`[SAB-001] POST /buscar returned: ${data.licitacoes?.length ?? 0} results, total_raw=${data.total_raw}, total_filtrado=${data.total_filtrado}`);

      setResult(data);
      setRawCount(data.total_raw || 0);

      if (data.licitacoes?.length > 0 && error) {
        setError(null);
        setRetryCountdown(null);
        setRetryMessage(null);
        setRetryExhausted(false);
      }

      clearPartialSearch(newSearchId);

      if (data.licitacoes?.length > 0) {
        saveLastSearch(data);
      }

      if (data.llm_status === 'processing') {
        if (llmTimeoutRef.current) clearTimeout(llmTimeoutRef.current);
        llmTimeoutRef.current = setTimeout(() => {
          setResult(prev => prev && prev.llm_source === 'processing' ? {
            ...prev,
            llm_source: 'fallback' as const,
            llm_status: 'ready' as const,
          } : prev);
          llmTimeoutRef.current = null;
        }, 30_000);
      }

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

      trackEvent('search_completed', {
        time_elapsed_ms: Date.now() - searchStartTime,
        total_raw: data.total_raw || 0,
        total_filtered: data.total_filtrado || 0,
        search_mode: filters.searchMode,
        sources_used: data.sources_used || [],
        is_partial: data.is_partial || false,
        cached: data.cached || false,
      });

    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        // CRIT-070 AC4: Log for traceability
        console.warn('[CRIT-070] Client timeout triggered', { searchId: newSearchId, elapsed: Date.now() - searchStartTime });
        const partial = recoverPartialSearch(newSearchId);
        if (partial && partial.partialResult) {
          setResult(partial.partialResult as BuscaResult);
          setShowingPartialResults(true);
          setLoading(false);
          toast.info("Mostrando resultados parciais salvos");
        } else {
          // CRIT-070 AC2: Abort without partial must show error, never return silently
          const abortError: SearchError = {
            message: "A análise demorou mais que o esperado. Tente com menos estados.",
            rawMessage: "Client timeout triggered after 185s",
            errorCode: "CLIENT_TIMEOUT",
            searchId: newSearchId,
            correlationId: null,
            requestId: null,
            httpStatus: 524,
            timestamp: new Date().toISOString(),
          };
          setError(abortError);
          startAutoRetry(abortError, setError);
        }
        return;
      }
      const rawMsg = e instanceof Error ? e.message : String(e);
      const errMeta = (e !== null && typeof e === 'object' && '_searchErrorMeta' in e)
        ? (e as { _searchErrorMeta?: { errorCode?: string; searchId?: string; correlationId?: string; requestId?: string; httpStatus?: number; rawMessage?: string } })._searchErrorMeta
        : undefined;
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
        setResult(previousResult);
        setError(null);
        toast.info("Não foi possível atualizar os dados. Mostrando resultados anteriores.");
      } else {
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
          startAutoRetry(searchError, setError);
        }
      }
      trackEvent('search_failed', { error_message: friendlyMessage, error_code: errorCode, search_mode: filters.searchMode, force_fresh: forceFresh });
    } finally {
      cleanupInterval();
      clearTimeout(clientTimeoutId);
      if (finalizingTimerRef.current) {
        clearTimeout(finalizingTimerRef.current);
        finalizingTimerRef.current = null;
      }
      setIsFinalizing(false);
      if (skeletonTimeoutTimerRef.current) {
        clearTimeout(skeletonTimeoutTimerRef.current);
        skeletonTimeoutTimerRef.current = null;
      }
      setSkeletonTimeoutReached(false);
      const isAsync = asyncSearchActiveRef.current;
      console.info(`[SAB-001] finally: isAsync=${isAsync}, asyncIdRef=${asyncSearchIdRef.current}, data=${!!data}`);
      if (!isAsync && !asyncSearchIdRef.current) {
        setLoading(false);
      } else {
        console.info(`[SAB-001] Keeping loading=true for async mode (isAsync=${isAsync})`);
      }
      setLoadingStep(1);
      setStatesProcessed(0);
      const hasJobsRunning = data?.llm_status === 'processing'
        || data?.excel_status === 'processing'
        || data?.bid_analysis_status === 'processing';
      const sseStillActive = !sseTerminalReceivedRef.current;
      if (!liveFetchInProgress && !liveFetchSearchIdRef.current && !hasJobsRunning && !isAsync && !sseStillActive) {
        setSearchId(null);
      } else if (sseStillActive && !hasJobsRunning && !isAsync && !liveFetchInProgress) {
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
  }, [
    filters, result, error, session, setResult, setRawCount, setError,
    resetRetryForNewSearch, startAutoRetry,
    setRetryCountdown, setRetryMessage, setRetryExhausted,
    excelFailCountRef, excelToastFiredRef,
    lastSearchParamsRef, setShowingPartialResults,
    refreshQuota, trackEvent,
  ]);

  // Keep buscarRef current for auto-retry interval callbacks
  buscarRef.current = buscar;

  // A-04 AC9: Fetch live results from background fetch and replace cached data
  const handleRefreshResults = useCallback(async () => {
    const sid = liveFetchSearchIdRef.current;
    if (!sid) return;

    try {
      const headers: Record<string, string> = {};
      if (session?.access_token) headers["Authorization"] = `Bearer ${session.access_token}`;

      const response = await fetch(`/api/buscar-results/${encodeURIComponent(sid)}`, { headers });
      if (!response.ok) {
        console.warn(`[A-04] Failed to fetch live results: ${response.status}`);
        toast.info("Não foi possível carregar os dados atualizados. Tente uma nova análise.");
        return;
      }

      const fetchedData = await response.json();
      setResult(fetchedData as BuscaResult);
      setRawCount(fetchedData.total_raw || 0);
      trackEvent('progressive_refresh_applied', {
        search_id: sid,
        new_count: refreshAvailableRef.current?.newCount ?? 0,
      });
    } catch (e) {
      console.warn('[A-04] Error fetching refresh results:', e);
    } finally {
      setLiveFetchInProgress(false);
      liveFetchSearchIdRef.current = null;
      setSearchId(null);
    }
  }, [session, setResult, setRawCount, trackEvent, refreshAvailableRef]);

  return {
    loading,
    setLoading,
    loadingStep,
    statesProcessed,
    setStatesProcessed,
    searchId,
    setSearchId,
    useRealProgress,
    setUseRealProgress,
    quotaError,
    isFinalizing,
    asyncSearchActive,
    setAsyncSearchActive,
    asyncSearchActiveRef,
    asyncSearchIdRef,
    abortControllerRef,
    llmTimeoutRef,
    sseTerminalReceivedRef,
    sseReconnectAttemptsRef,
    liveFetchInProgress,
    liveFetchSearchIdRef,
    skeletonTimeoutReached,
    setSkeletonTimeoutReached,
    skeletonTimeoutTimerRef,
    searchButtonRef: searchButtonRef as React.RefObject<HTMLButtonElement>,
    buscar,
    cancelSearch,
    viewPartialResults,
    estimateSearchTime,
    handleRefreshResults,
  };
}
