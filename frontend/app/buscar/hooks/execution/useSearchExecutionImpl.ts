"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type { BuscaResult } from "../../../types";
import type { SearchError, SearchFiltersSnapshot } from "../useSearch";
import type { RefreshAvailableInfo } from "../../../../hooks/useSearchSSE";
import { useSearchAPI } from "./useSearchAPI";
import { viewPartialResultsFn, estimateSearchTimeFn } from "./useSearchPartialResults";

interface UseSearchExecutionFilters {
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

interface UseSearchExecutionParams {
  filters: UseSearchExecutionFilters;
  result: BuscaResult | null;
  setResult: React.Dispatch<React.SetStateAction<BuscaResult | null>>;
  setRawCount: (n: number) => void;
  error: SearchError | null;
  setError: (e: SearchError | null) => void;
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
  showingPartialResults: boolean;
  setShowingPartialResults: (v: boolean) => void;
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
    lastSearchParamsRef, setShowingPartialResults, refreshAvailableRef,
  } = params;

  // ── State (owned here, passed down) ──────────────────────────────────
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [statesProcessed, setStatesProcessed] = useState(0);
  const [searchId, setSearchId] = useState<string | null>(null);
  const [useRealProgress, setUseRealProgress] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [asyncSearchActive, setAsyncSearchActive] = useState(false);
  const [skeletonTimeoutReached, setSkeletonTimeoutReached] = useState(false);

  // ── Refs (owned here, shared with sub-hooks) ──────────────────────────
  const asyncSearchActiveRef = useRef(false);
  const asyncSearchIdRef = useRef<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const llmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sseTerminalReceivedRef = useRef(false);
  const sseReconnectAttemptsRef = useRef(0);
  const skeletonTimeoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => { asyncSearchActiveRef.current = asyncSearchActive; }, [asyncSearchActive]);

  // ── Safety: force loading=false when result arrives but loading stays ─
  const resultSafetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (loading && result && result.licitacoes && result.licitacoes.length > 0) {
      resultSafetyTimerRef.current = setTimeout(() => setLoading(false), 5000);
      return () => { if (resultSafetyTimerRef.current) { clearTimeout(resultSafetyTimerRef.current); resultSafetyTimerRef.current = null; } };
    }
  }, [loading, result]);

  // ── CRIT-CORE-001: Async safety timeout 120s ──────────────────────────
  const asyncSafetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (asyncSearchActive && loading && !result) {
      asyncSafetyTimerRef.current = setTimeout(() => {
        setAsyncSearchActive(false);
        asyncSearchActiveRef.current = false;
        asyncSearchIdRef.current = null;
        setLoading(false);
        setError({ message: "A busca esta demorando. Tente novamente em alguns minutos.", rawMessage: "Async safety timeout after 120s", errorCode: "ASYNC_TIMEOUT", searchId: searchId || "", correlationId: null, requestId: null, httpStatus: 504, timestamp: new Date().toISOString() });
      }, 120_000);
      return () => { if (asyncSafetyTimerRef.current) { clearTimeout(asyncSafetyTimerRef.current); asyncSafetyTimerRef.current = null; } };
    }
    if (asyncSafetyTimerRef.current && (!asyncSearchActive || result)) {
      clearTimeout(asyncSafetyTimerRef.current);
      asyncSafetyTimerRef.current = null;
    }
  }, [asyncSearchActive, loading, result, searchId, setError]);

  // ── API sub-hook ──────────────────────────────────────────────────────
  const api = useSearchAPI({
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
    autoRetryInProgressRef,
  });

  // ── cancelSearch ──────────────────────────────────────────────────────
  // STORY-422 (EPIC-INCIDENT-2026-04-10): mark abort with USER_CANCELLED so
  // the Sentry beforeSend filter drops the resulting AbortError silently
  // instead of recording it as a crash.
  const cancelSearch = useCallback(() => {
    try {
      abortControllerRef.current?.abort(new DOMException("USER_CANCELLED", "AbortError"));
    } catch {
      abortControllerRef.current?.abort();
    }
    if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }
    if (api.finalizingTimerRef.current) { clearTimeout(api.finalizingTimerRef.current); api.finalizingTimerRef.current = null; }
    setIsFinalizing(false);
    if (skeletonTimeoutTimerRef.current) { clearTimeout(skeletonTimeoutTimerRef.current); skeletonTimeoutTimerRef.current = null; }
    setSkeletonTimeoutReached(false);
    const activeId = asyncSearchIdRef.current || searchId;
    if (activeId) { fetch(`/api/search-cancel?search_id=${encodeURIComponent(activeId)}`, { method: "POST" }).catch(() => {}); }
    setLoading(false);
    setSearchId(null);
    setUseRealProgress(false);
    setAsyncSearchActive(false);
    asyncSearchActiveRef.current = false;
    asyncSearchIdRef.current = null;
  }, [searchId, api.finalizingTimerRef]);

  // ── viewPartialResults (pure function, uses current closure values) ───
  const viewPartialResults = useCallback(
    () => viewPartialResultsFn({
      result, searchId, asyncSearchIdRef, setResult, setShowingPartialResults,
      setLoading, setSearchId, setUseRealProgress, setAsyncSearchActive, asyncSearchActiveRef,
      abortControllerRef, llmTimeoutRef, finalizingTimerRef: api.finalizingTimerRef, setIsFinalizing,
      skeletonTimeoutTimerRef, setSkeletonTimeoutReached,
    }),
    [result, searchId, asyncSearchIdRef, setResult, setShowingPartialResults, api.finalizingTimerRef],
  );

  return {
    loading, setLoading, loadingStep, statesProcessed, setStatesProcessed,
    searchId, setSearchId, useRealProgress, setUseRealProgress,
    quotaError: api.quotaError, isFinalizing,
    asyncSearchActive, setAsyncSearchActive, asyncSearchActiveRef, asyncSearchIdRef,
    abortControllerRef, llmTimeoutRef, sseTerminalReceivedRef, sseReconnectAttemptsRef,
    liveFetchInProgress: api.liveFetchInProgress,
    liveFetchSearchIdRef: api.liveFetchSearchIdRef,
    skeletonTimeoutReached, setSkeletonTimeoutReached, skeletonTimeoutTimerRef,
    searchButtonRef: searchButtonRef as React.RefObject<HTMLButtonElement>,
    buscar: api.buscar, cancelSearch, viewPartialResults,
    estimateSearchTime: estimateSearchTimeFn,
    handleRefreshResults: api.handleRefreshResults,
  };
}
