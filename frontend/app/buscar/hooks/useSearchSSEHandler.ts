"use client";

import { useCallback, useRef } from "react";
import type { BuscaResult } from "../../types";
import type { SearchProgressEvent } from "../../../hooks/useSearchSSE";
import type { SearchError } from "./useSearch";
import { useAnalytics } from "../../../hooks/useAnalytics";
import { useQuota } from "../../../hooks/useQuota";
import { savePartialSearch } from "../../../lib/searchPartialCache";

interface UseSearchSSEHandlerParams {
  session: { access_token?: string | null } | null;
  searchId: string | null;
  searchMode: "setor" | "termos";
  ufsSelecionadasSize: number;
  result: BuscaResult | null;
  setResult: React.Dispatch<React.SetStateAction<BuscaResult | null>>;
  setRawCount: (n: number) => void;
  setError: (e: SearchError | null) => void;
  setLoading: (b: boolean) => void;
  setSearchId: (id: string | null) => void;
  setAsyncSearchActive: (b: boolean) => void;
  asyncSearchActiveRef: React.MutableRefObject<boolean>;
  asyncSearchIdRef: React.MutableRefObject<string | null>;
  sseTerminalReceivedRef: React.MutableRefObject<boolean>;
  llmTimeoutRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  // Retry state
  setRetryCountdown: (v: number | null) => void;
  setRetryMessage: (v: string | null) => void;
  setRetryExhausted: (v: boolean) => void;
  retryTimerRef: React.MutableRefObject<ReturnType<typeof setInterval> | null>;
  // Excel state — use ref so it always has latest function
  handleExcelFailureRef: React.MutableRefObject<((isRegenerateAttempt: boolean) => void) | null>;
  excelFailCountRef: React.MutableRefObject<number>;
  excelToastFiredRef: React.MutableRefObject<boolean>;
}

export function useSearchSSEHandler(params: UseSearchSSEHandlerParams) {
  const {
    session, searchId, searchMode, ufsSelecionadasSize,
    result, setResult, setRawCount, setError, setLoading, setSearchId,
    setAsyncSearchActive, asyncSearchActiveRef, asyncSearchIdRef,
    sseTerminalReceivedRef, llmTimeoutRef,
    setRetryCountdown, setRetryMessage, setRetryExhausted, retryTimerRef,
    handleExcelFailureRef, excelFailCountRef, excelToastFiredRef,
  } = params;

  const { refresh: refreshQuota } = useQuota();
  const { trackEvent } = useAnalytics();

  // F-01 AC21: Handle background job completion via SSE
  // GTM-ARCH-001 AC3/AC4: Also handles search_complete from async Worker
  const handleSseEvent = useCallback(async (event: SearchProgressEvent) => {
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
              search_mode: searchMode,
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
      const analysisData = event.detail.bid_analysis as BuscaResult['bid_analysis'];
      setResult(prev => prev ? {
        ...prev,
        bid_analysis: analysisData,
        bid_analysis_status: 'ready' as const,
      } : prev);
    } else if (event.stage === 'excel_ready') {
      // Update the result's download_url when Excel is ready
      if (event.detail.excel_status === 'failed') {
        handleExcelFailureRef.current?.(false);
      } else {
        // Reset failure tracking on success
        excelFailCountRef.current = 0;
        excelToastFiredRef.current = false;
        setResult(prev => prev ? {
          ...prev,
          download_url: event.detail.download_url || null,
          excel_status: 'ready' as BuscaResult['excel_status'],
        } : prev);
      }
    } else if (event.stage === 'zero_match_ready') {
      // CRIT-059 AC5: Zero-match classification completed — fetch and merge results
      const sid = asyncSearchIdRef.current || searchId;
      if (sid) {
        try {
          const headers: Record<string, string> = {};
          if (session?.access_token) headers["Authorization"] = `Bearer ${session.access_token}`;
          const response = await fetch(`/api/search-zero-match/${encodeURIComponent(sid)}`, { headers });
          if (response.ok) {
            const data = await response.json() as { results: BuscaResult['licitacoes']; count: number };
            if (data.results?.length > 0) {
              setResult(prev => {
                if (!prev) return prev;
                // Merge zero-match results with existing results
                const existingIds = new Set(prev.licitacoes.map(l => l.pncp_id));
                const newResults = data.results.filter((l: any) => !existingIds.has(l.pncp_id));
                return {
                  ...prev,
                  licitacoes: [...prev.licitacoes, ...newResults],
                  total_filtrado: prev.total_filtrado + newResults.length,
                  zero_match_candidates_count: 0,
                  zero_match_job_id: null,
                };
              });
            }
          }
        } catch (e) {
          console.warn('[CRIT-059] Error fetching zero-match results:', e);
        }
      }
    } else if (event.stage === 'uf_complete' || event.stage === 'partial_results') {
      // STAB-006 AC4: Save partial results to localStorage on each SSE update
      const sid = asyncSearchIdRef.current || searchId;
      if (sid) {
        const ufsCompleted = event.detail.ufs_completed ?? [];
        const totalUfs = event.detail.uf_total ?? ufsSelecionadasSize;
        savePartialSearch(sid, result, ufsCompleted, totalUfs);
      }
    } else if (event.stage === 'error' && asyncSearchActiveRef.current) {
      // GTM-ARCH-001: Worker error during async search
      setAsyncSearchActive(false);
      asyncSearchActiveRef.current = false;
      asyncSearchIdRef.current = null;
      setLoading(false);
      setError({
        message: event.detail.error || event.message || 'Erro no processamento da análise',
        rawMessage: event.detail.error || event.message || '',
        errorCode: event.detail.error_code || null,
        searchId: searchId,
        correlationId: null,
        requestId: null,
        httpStatus: null,
        timestamp: new Date().toISOString(),
      });
    }
  }, [
    session, searchId, searchMode, ufsSelecionadasSize,
    result, setResult, setRawCount, setError, setLoading, setSearchId,
    setAsyncSearchActive, asyncSearchActiveRef, asyncSearchIdRef,
    sseTerminalReceivedRef, llmTimeoutRef, refreshQuota, trackEvent,
    setRetryCountdown, setRetryMessage, setRetryExhausted, retryTimerRef,
    handleExcelFailureRef, excelFailCountRef, excelToastFiredRef,
  ]);

  return { handleSseEvent };
}
