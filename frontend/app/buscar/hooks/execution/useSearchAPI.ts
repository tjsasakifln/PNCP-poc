"use client";

import { useState, useRef, useCallback } from "react";
import type { BuscaResult } from "../../../types";
import type { SearchError, SearchFiltersSnapshot } from "../useSearch";
import type { RefreshAvailableInfo } from "../../../../hooks/useSearchSSE";
import { useAnalytics } from "../../../../hooks/useAnalytics";
import { useAuth } from "../../../components/AuthProvider";
import { useQuota } from "../../../../hooks/useQuota";
import { CLIENT_TIMEOUT_STATUS } from "../../../../lib/error-messages";
import { clearPartialSearch, recoverPartialSearch } from "../../../../lib/searchPartialCache";
import { saveSearchState } from "../../../../lib/searchStatePersistence";
import { toast } from "sonner";
import { dateDiffInDays } from "../../../../lib/utils/dateDiffInDays";
import { getCorrelationId, logCorrelatedRequest } from "../../../../lib/utils/correlationId";
import { supabase } from "../../../../lib/supabase";
import {
  attachErrorMeta,
  buildSearchError,
  recoverPartialOnTimeout,
  isTimeoutError,
} from "./useSearchErrorHandling";

interface UseSearchAPIFilters {
  ufsSelecionadas: Set<string>;
  dataInicial: string;
  dataFinal: string;
  searchMode: "setor" | "termos";
  modoBusca: "abertas" | "publicacao";
  setorId: string;
  termosArray: string[];
  status: import("../../components/StatusFilter").StatusLicitacao;
  modalidades: number[];
  valorMin: number | null;
  valorMax: number | null;
  esferas: import("../../../components/EsferaFilter").Esfera[];
  municipios: import("../../../components/MunicipioFilter").Municipio[];
  ordenacao: import("../../../components/OrdenacaoSelect").OrdenacaoOption;
  canSearch: boolean;
  setOrdenacao: (ord: import("../../../components/OrdenacaoSelect").OrdenacaoOption) => void;
}

export interface UseSearchAPIParams {
  filters: UseSearchAPIFilters;
  result: BuscaResult | null;
  setResult: React.Dispatch<React.SetStateAction<BuscaResult | null>>;
  setRawCount: (n: number) => void;
  error: SearchError | null;
  setError: (e: SearchError | null) => void;
  // Shared state/setters (owned by useSearchExecution)
  setLoading: (v: boolean) => void;
  setLoadingStep: (v: number) => void;
  setStatesProcessed: React.Dispatch<React.SetStateAction<number>>;
  setSearchId: (id: string | null) => void;
  setUseRealProgress: (v: boolean) => void;
  setIsFinalizing: (v: boolean) => void;
  setAsyncSearchActive: (v: boolean) => void;
  asyncSearchActiveRef: React.MutableRefObject<boolean>;
  asyncSearchIdRef: React.MutableRefObject<string | null>;
  abortControllerRef: React.MutableRefObject<AbortController | null>;
  llmTimeoutRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  sseTerminalReceivedRef: React.MutableRefObject<boolean>;
  sseReconnectAttemptsRef: React.MutableRefObject<number>;
  skeletonTimeoutTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  setSkeletonTimeoutReached: (v: boolean) => void;
  // Retry
  autoRetryInProgressRef: React.MutableRefObject<boolean>;
  buscarRef: React.MutableRefObject<((options?: { forceFresh?: boolean }) => Promise<void>) | null>;
  resetRetryForNewSearch: () => void;
  startAutoRetry: (searchError: SearchError, setError: (e: SearchError | null) => void) => void;
  setRetryCountdown: (v: number | null) => void;
  setRetryMessage: (v: string | null) => void;
  setRetryExhausted: (v: boolean) => void;
  excelFailCountRef: React.MutableRefObject<number>;
  excelToastFiredRef: React.MutableRefObject<boolean>;
  lastSearchParamsRef: React.MutableRefObject<SearchFiltersSnapshot | null>;
  setShowingPartialResults: (v: boolean) => void;
  refreshAvailableRef: React.MutableRefObject<RefreshAvailableInfo | null>;
}

export interface UseSearchAPIReturn {
  quotaError: string | null;
  liveFetchInProgress: boolean;
  liveFetchSearchIdRef: React.MutableRefObject<string | null>;
  finalizingTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  buscar: (options?: { forceFresh?: boolean }) => Promise<void>;
  handleRefreshResults: () => Promise<void>;
  /** STORY-422: User-initiated cancellation — marks abort reason USER_CANCELLED. */
  cancelSearch: () => void;
}

export function useSearchAPI(params: UseSearchAPIParams): UseSearchAPIReturn {
  const {
    filters, result, setResult, setRawCount, error, setError,
    setLoading, setLoadingStep, setStatesProcessed, setSearchId,
    setUseRealProgress, setIsFinalizing, setAsyncSearchActive,
    asyncSearchActiveRef, asyncSearchIdRef,
    abortControllerRef, llmTimeoutRef, sseTerminalReceivedRef, sseReconnectAttemptsRef,
    skeletonTimeoutTimerRef, setSkeletonTimeoutReached,
    buscarRef, resetRetryForNewSearch, startAutoRetry,
    setRetryCountdown, setRetryMessage, setRetryExhausted,
    excelFailCountRef, excelToastFiredRef,
    lastSearchParamsRef, setShowingPartialResults, refreshAvailableRef,
  } = params;

  const { session } = useAuth();
  const { refresh: refreshQuota } = useQuota();
  const { trackEvent } = useAnalytics();

  // Private state (owned by this hook)
  const [quotaError, setQuotaError] = useState<string | null>(null);
  const [liveFetchInProgress, setLiveFetchInProgress] = useState(false);
  const liveFetchSearchIdRef = useRef<string | null>(null);
  const finalizingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchStartTimeRef = useRef<number>(0);

  const buscar = useCallback(async (options?: { forceFresh?: boolean }) => {
    if (!filters.canSearch) return;

    resetRetryForNewSearch();
    const forceFresh = options?.forceFresh ?? false;
    const previousResult = forceFresh ? result : null;

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

    const previousResultFallback = result;
    setResult(null);
    setRawCount(0);
    setError(null);
    setQuotaError(null);
    excelFailCountRef.current = 0;
    excelToastFiredRef.current = false;
    setLiveFetchInProgress(false);
    liveFetchSearchIdRef.current = null;
    setAsyncSearchActive(false);
    asyncSearchActiveRef.current = false;
    asyncSearchIdRef.current = null;
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
    skeletonTimeoutTimerRef.current = setTimeout(() => setSkeletonTimeoutReached(true), 30_000);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // STORY-422 (EPIC-INCIDENT-2026-04-10): Mark the abort reason so the Sentry
    // beforeSend filter can distinguish TIMEOUT from USER_CANCELLED and drop
    // the latter. AbortSignal.reason is widely supported (Chrome 100+, FF 97+,
    // Safari 15.4+); older browsers fall back to the legacy AbortError + the
    // breadcrumb below so we still route the event correctly.
    const clientTimeoutId = setTimeout(() => {
      const timeoutReason = new DOMException("TIMEOUT", "AbortError");
      try {
        abortController.abort(timeoutReason);
      } catch {
        abortController.abort();
      }
    }, 65_000);

    searchStartTimeRef.current = Date.now();
    if (finalizingTimerRef.current) clearTimeout(finalizingTimerRef.current);
    finalizingTimerRef.current = setTimeout(() => setIsFinalizing(true), 50_000);

    const searchStartTime = Date.now();
    const totalStates = filters.ufsSelecionadas.size;
    let stateIntervalId: ReturnType<typeof setInterval> | null = null;
    stateIntervalId = setInterval(() => {
      setStatesProcessed(prev => {
        if (prev >= totalStates) { if (stateIntervalId) clearInterval(stateIntervalId); return totalStates; }
        return prev + 1;
      });
    }, totalStates > 0 ? Math.max(10000, (totalStates * 10000) / (totalStates + 1)) : 10000);
    const cleanupInterval = () => { if (stateIntervalId) { clearInterval(stateIntervalId); stateIntervalId = null; } };

    trackEvent("search_started", {
      ufs: Array.from(filters.ufsSelecionadas),
      uf_count: filters.ufsSelecionadas.size,
      date_range: { inicial: filters.dataInicial, final: filters.dataFinal, days: dateDiffInDays(filters.dataInicial, filters.dataFinal) },
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
          try {
            const { data: { session: refreshed } } = await supabase.auth.refreshSession();
            if (refreshed?.access_token) activeToken = refreshed.access_token;
          } catch { /* proceed with current token */ }
        }
      }

      const correlationId = getCorrelationId();
      const headers: Record<string, string> = { "Content-Type": "application/json", "X-Correlation-ID": correlationId };
      if (activeToken) headers["Authorization"] = `Bearer ${activeToken}`;

      // STORY-419: Clamp monetary inputs to the backend ceiling (1e15, R$ 1
      // quatrilhão) that matches search_sessions.valor_total NUMERIC(18,2).
      // Anything above that raises SQLSTATE 22003 server-side (Sentry issue
      // 7369847734). We clamp silently here and let the FilterPanel show
      // the user-facing toast — the clamp is defensive so that raw URL
      // params / restored state cannot bypass the UI validation.
      const VALOR_CEILING = 1e15;
      const valorMinClamped =
        typeof filters.valorMin === "number" && isFinite(filters.valorMin)
          ? Math.min(Math.max(filters.valorMin, 0), VALOR_CEILING)
          : filters.valorMin;
      const valorMaxClamped =
        typeof filters.valorMax === "number" && isFinite(filters.valorMax)
          ? Math.min(Math.max(filters.valorMax, 0), VALOR_CEILING)
          : filters.valorMax;

      logCorrelatedRequest("POST", "/api/buscar", correlationId);
      const response = await fetch("/api/buscar", {
        method: "POST", headers, signal: abortController.signal,
        body: JSON.stringify({
          ufs: Array.from(filters.ufsSelecionadas),
          data_inicial: filters.dataInicial, data_final: filters.dataFinal,
          setor_id: filters.searchMode === "setor" ? filters.setorId : null,
          termos_busca: filters.searchMode === "termos" ? filters.termosArray.join(", ") : null,
          search_id: newSearchId, modo_busca: filters.modoBusca, status: filters.status,
          modalidades: filters.modalidades.length > 0 ? filters.modalidades : undefined,
          valor_minimo: valorMinClamped, valor_maximo: valorMaxClamped,
          esferas: filters.esferas.length > 0 && filters.esferas.length < 3 ? filters.esferas : undefined,
          municipios: filters.municipios.length > 0 ? filters.municipios.map(m => m.codigo) : undefined,
          ordenacao: filters.ordenacao, force_fresh: forceFresh || undefined,
        }),
      });

      if (response.status === 202) {
        const queued = await response.json();
        setAsyncSearchActive(true);
        asyncSearchActiveRef.current = true;
        asyncSearchIdRef.current = queued.search_id || newSearchId;
        data = null;
      } else if (!response.ok) {
        const err = await response.json().catch(() => ({ message: null, error_code: null, data: null }));

        const buildMeta = (rawMessage: string, overrides: Partial<Parameters<typeof attachErrorMeta>[1]> = {}) =>
          attachErrorMeta(new Error(rawMessage), {
            errorCode: err.error_code || null,
            searchId: err.search_id || newSearchId,
            correlationId: err.correlation_id || null,
            requestId: err.request_id || null,
            httpStatus: response.status,
            rawMessage,
            ...overrides,
          });

        if (response.status === 401) {
          if (result && result.download_id) {
            saveSearchState(result, result.download_id, {
              ufs: Array.from(filters.ufsSelecionadas), startDate: filters.dataInicial, endDate: filters.dataFinal,
              setor: filters.searchMode === "setor" ? filters.setorId : undefined,
              includeKeywords: filters.searchMode === "termos" ? filters.termosArray : undefined,
            });
          }
          setError({ message: "Sua sessão expirou. Reconectando...", rawMessage: err.message || "Session expired", errorCode: "SESSION_EXPIRED", searchId: newSearchId, correlationId, requestId: err.request_id || null, httpStatus: 401, timestamp: new Date().toISOString() });
          const returnTo = err.returnTo || "/buscar";
          setTimeout(() => { window.location.href = `/login?returnTo=${encodeURIComponent(returnTo)}`; }, 1500);
          throw buildMeta("Sua sessão expirou. Reconectando...", { errorCode: "SESSION_EXPIRED", rawMessage: err.message || "Session expired" });
        }

        if (response.status === 403) {
          const isTrialExpired = err.error === "trial_expired" || err.detail?.error === "trial_expired";
          const errorMessage = err.detail?.message || err.message || "Suas análises acabaram.";
          setQuotaError(isTrialExpired ? "trial_expired" : errorMessage);
          throw buildMeta(errorMessage);
        }

        if (err.error_code === "DATE_RANGE_EXCEEDED") {
          const { requested_days, max_allowed_days } = err.data || {};
          throw buildMeta(`O período de busca não pode exceder ${max_allowed_days} dias (seu acesso atual). Você tentou buscar ${requested_days} dias. Reduza o período e tente novamente.`);
        }

        if (err.error_code === "RATE_LIMIT") {
          throw buildMeta(`Limite de requisições excedido (2/min). Aguarde ${err.data?.wait_seconds || 60} segundos e tente novamente.`);
        }

        throw buildMeta(err.message || "Erro ao buscar licitações");
      } else {
        const parsed = await response.json().catch(() => null);
        if (!parsed) throw new Error("Resposta inesperada do servidor. Tente novamente.");
        data = parsed as BuscaResult;
      }

      if (!data && asyncSearchActiveRef.current) return;
      if (!data) throw new Error("Não foi possível obter os resultados. Tente novamente.");

      setResult(data);
      setRawCount(data.total_raw || 0);

      if (data.licitacoes?.length > 0 && error) {
        setError(null); setRetryCountdown(null); setRetryMessage(null); setRetryExhausted(false);
      }

      clearPartialSearch(newSearchId);
      try { sessionStorage.removeItem(`partial_search_${newSearchId}`); } catch {}

      if (data.llm_status === "processing") {
        if (llmTimeoutRef.current) clearTimeout(llmTimeoutRef.current);
        llmTimeoutRef.current = setTimeout(() => {
          setResult(prev => prev && prev.llm_source === "processing" ? { ...prev, llm_source: "fallback" as const, llm_status: "ready" as const } : prev);
          llmTimeoutRef.current = null;
        }, 30_000);
      }

      if (data.live_fetch_in_progress) {
        setLiveFetchInProgress(true);
        liveFetchSearchIdRef.current = newSearchId;
      }

      if (filters.searchMode === "termos" && filters.termosArray.length > 0) {
        filters.setOrdenacao("relevancia");
        trackEvent("custom_term_search", { terms_count: filters.termosArray.length, terms: filters.termosArray, total_results: data.total_filtrado || 0, hidden_by_min_match: data.hidden_by_min_match || 0, filter_relaxed: data.filter_relaxed || false });
      } else if (data.licitacoes && data.licitacoes.length > 20) {
        const lowCount = data.licitacoes.filter(l => l.confidence === "low").length;
        if (lowCount > data.licitacoes.length * 0.5) filters.setOrdenacao("relevancia");
      }

      if (session?.access_token) await refreshQuota();

      trackEvent("search_completed", { time_elapsed_ms: Date.now() - searchStartTime, total_raw: data.total_raw || 0, total_filtered: data.total_filtrado || 0, search_mode: filters.searchMode, sources_used: data.sources_used || [], is_partial: data.is_partial || false, cached: data.cached || false });

      if (typeof window !== "undefined" && !localStorage.getItem("sl_first_search_tracked")) {
        trackEvent("first_search", { setor_id: filters.searchMode === "setor" ? filters.setorId : null, ufs: Array.from(filters.ufsSelecionadas), results_count: data.total_filtrado || 0, search_mode: filters.searchMode });
        localStorage.setItem("sl_first_search_tracked", "1");
      }

    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") {
        // STORY-422 AC1/AC4: Derive a structured close reason so we can
        // distinguish user cancellations (drop) from timeouts (retry + report).
        // AbortSignal.reason is preferred; the fallback inspects message.
        type AbortableSignal = { reason?: unknown };
        const signalReason = (abortController.signal as AbortableSignal).reason;
        const reasonString =
          signalReason instanceof DOMException
            ? signalReason.message
            : typeof signalReason === "string"
              ? signalReason
              : signalReason instanceof Error
                ? signalReason.message
                : "";
        const closeReason =
          reasonString === "TIMEOUT" || reasonString === "USER_CANCELLED" || reasonString === "NAVIGATION"
            ? reasonString
            : reasonString
              ? "UNKNOWN"
              : "TIMEOUT"; // legacy path: setTimeout fired without .reason support

        // Fire-and-forget breadcrumb so Sentry beforeSend can filter by tag.
        try {
          import("@sentry/nextjs").then((Sentry) => {
            Sentry.addBreadcrumb({
              category: "search",
              message: `search abort reason=${closeReason} search_id=${newSearchId}`,
              level: closeReason === "TIMEOUT" || closeReason === "UNKNOWN" ? "warning" : "info",
              data: {
                search_id: newSearchId,
                close_reason: closeReason,
                elapsed_ms: Date.now() - searchStartTimeRef.current,
              },
            });
            Sentry.setTag("close_reason", closeReason);
          }).catch(() => { /* Sentry optional */ });
        } catch { /* Sentry not available */ }

        // USER_CANCELLED / NAVIGATION: exit silently — no error, no retry.
        if (closeReason === "USER_CANCELLED" || closeReason === "NAVIGATION") {
          return;
        }

        const partialResult = recoverPartialOnTimeout(newSearchId);
        if (partialResult) {
          setResult(partialResult); setShowingPartialResults(true); setLoading(false);
          toast.info("Mostrando resultados parciais salvos");
        } else {
          try {
            const partialKey = `partial_search_${newSearchId}`;
            const partialRaw = sessionStorage.getItem(partialKey);
            if (partialRaw) {
              const partialData = JSON.parse(partialRaw) as { rawCount: number; timestamp: number };
              if (partialData.rawCount > 0 && Date.now() - partialData.timestamp < 300000) {
                toast.info(`${partialData.rawCount.toLocaleString("pt-BR")} licitações foram encontradas antes do timeout. Tente novamente — os resultados estarão em cache.`);
                sessionStorage.removeItem(partialKey);
              }
            }
          } catch { /* ignore */ }
          const abortError: SearchError = { message: "A busca esta demorando. Estamos tentando novamente automaticamente.", rawMessage: "Client timeout triggered after 65s", errorCode: "CLIENT_TIMEOUT", searchId: newSearchId, correlationId: null, requestId: null, httpStatus: CLIENT_TIMEOUT_STATUS, timestamp: new Date().toISOString() };
          setError(abortError);
          startAutoRetry(abortError, setError);
        }
        return;
      }

      const searchError = buildSearchError(e, newSearchId);
      if (forceFresh && previousResult) {
        setResult(previousResult); setError(null);
        toast.info("Não foi possível atualizar os dados. Mostrando resultados anteriores.");
      } else if (isTimeoutError(searchError)) {
        const partial = recoverPartialSearch(newSearchId);
        if (partial && partial.partialResult) {
          setResult(partial.partialResult as BuscaResult); setShowingPartialResults(true); setError(null);
          toast.info("Mostrando resultados parciais salvos");
          return;
        }
        if (previousResultFallback && previousResultFallback.licitacoes?.length > 0) {
          setResult(previousResultFallback); setError(null); toast.error(searchError.message);
        } else {
          setError(searchError); startAutoRetry(searchError, setError);
        }
      } else if (previousResultFallback && previousResultFallback.licitacoes?.length > 0) {
        setResult(previousResultFallback); setError(null); toast.error(searchError.message);
      } else {
        setError(searchError); startAutoRetry(searchError, setError);
      }
      trackEvent("search_failed", { error_message: searchError.message, error_code: searchError.errorCode, search_mode: filters.searchMode, force_fresh: forceFresh });
    } finally {
      cleanupInterval();
      clearTimeout(clientTimeoutId);
      if (finalizingTimerRef.current) { clearTimeout(finalizingTimerRef.current); finalizingTimerRef.current = null; }
      setIsFinalizing(false);
      if (skeletonTimeoutTimerRef.current) { clearTimeout(skeletonTimeoutTimerRef.current); skeletonTimeoutTimerRef.current = null; }
      setSkeletonTimeoutReached(false);
      const isAsync = asyncSearchActiveRef.current;
      if (!isAsync && !asyncSearchIdRef.current) setLoading(false);
      setLoadingStep(1);
      setStatesProcessed(0);
      const hasJobsRunning = data?.llm_status === "processing" || data?.excel_status === "processing" || data?.bid_analysis_status === "processing";
      const sseStillActive = !sseTerminalReceivedRef.current;
      if (!liveFetchInProgress && !liveFetchSearchIdRef.current && !hasJobsRunning && !isAsync && !sseStillActive) {
        setSearchId(null);
      } else if (sseStillActive && !hasJobsRunning && !isAsync && !liveFetchInProgress) {
        setTimeout(() => { sseTerminalReceivedRef.current = true; setSearchId(null); }, 5000);
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
    setLoading, setLoadingStep, setStatesProcessed, setSearchId,
    setUseRealProgress, setIsFinalizing, setAsyncSearchActive,
    asyncSearchActiveRef, asyncSearchIdRef,
    abortControllerRef, llmTimeoutRef, sseTerminalReceivedRef, sseReconnectAttemptsRef,
    skeletonTimeoutTimerRef, setSkeletonTimeoutReached,
    liveFetchInProgress,
  ]);

  buscarRef.current = buscar;

  const handleRefreshResults = useCallback(async () => {
    const sid = liveFetchSearchIdRef.current;
    if (!sid) return;
    try {
      const headers: Record<string, string> = {};
      if (session?.access_token) headers["Authorization"] = `Bearer ${session.access_token}`;
      const response = await fetch(`/api/buscar-results/${encodeURIComponent(sid)}`, { headers });
      if (!response.ok) {
        toast.info("Não foi possível carregar os dados atualizados. Tente uma nova análise.");
        return;
      }
      const fetchedData = await response.json();
      setResult(fetchedData as BuscaResult);
      setRawCount(fetchedData.total_raw || 0);
      trackEvent("progressive_refresh_applied", { search_id: sid, new_count: refreshAvailableRef.current?.newCount ?? 0 });
    } catch { /* silently fail */ } finally {
      setLiveFetchInProgress(false);
      liveFetchSearchIdRef.current = null;
      setSearchId(null);
    }
  }, [session, setResult, setRawCount, trackEvent, refreshAvailableRef, setSearchId]);

  // STORY-422 (EPIC-INCIDENT-2026-04-10): Explicit user-initiated cancellation
  // of an in-flight search. Marks the abort with reason=USER_CANCELLED so the
  // Sentry beforeSend filter drops the resulting AbortError instead of
  // logging it as a crash.
  const cancelSearch = useCallback(() => {
    const ac = abortControllerRef.current;
    if (!ac) return;
    try {
      ac.abort(new DOMException("USER_CANCELLED", "AbortError"));
    } catch {
      ac.abort();
    }
  }, [abortControllerRef]);

  return { quotaError, liveFetchInProgress, liveFetchSearchIdRef, finalizingTimerRef, buscar, handleRefreshResults, cancelSearch };
}
