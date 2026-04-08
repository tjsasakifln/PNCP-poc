"use client";

import type { BuscaResult } from "../../../types";
import { recoverPartialSearch } from "../../../../lib/searchPartialCache";

interface ViewPartialResultsParams {
  result: BuscaResult | null;
  searchId: string | null;
  asyncSearchIdRef: React.MutableRefObject<string | null>;
  setResult: React.Dispatch<React.SetStateAction<BuscaResult | null>>;
  setShowingPartialResults: (v: boolean) => void;
  setLoading: (v: boolean) => void;
  setSearchId: (id: string | null) => void;
  setUseRealProgress: (v: boolean) => void;
  setAsyncSearchActive: (v: boolean) => void;
  asyncSearchActiveRef: React.MutableRefObject<boolean>;
  abortControllerRef: React.MutableRefObject<AbortController | null>;
  llmTimeoutRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  finalizingTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  setIsFinalizing: (v: boolean) => void;
  skeletonTimeoutTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>;
  setSkeletonTimeoutReached: (v: boolean) => void;
}

/**
 * View partial results — clears timers, recovers partial cache if needed.
 * Called as a plain function (not a hook) to avoid ref-sharing issues.
 */
export function viewPartialResultsFn(params: ViewPartialResultsParams): void {
  const {
    result, searchId, asyncSearchIdRef,
    setResult, setShowingPartialResults,
    setLoading, setSearchId, setUseRealProgress,
    setAsyncSearchActive, asyncSearchActiveRef,
    abortControllerRef, llmTimeoutRef, finalizingTimerRef, setIsFinalizing,
    skeletonTimeoutTimerRef, setSkeletonTimeoutReached,
  } = params;

  // Clear all timers
  abortControllerRef.current?.abort();
  if (llmTimeoutRef.current) { clearTimeout(llmTimeoutRef.current); llmTimeoutRef.current = null; }
  if (finalizingTimerRef.current) { clearTimeout(finalizingTimerRef.current); finalizingTimerRef.current = null; }
  setIsFinalizing(false);
  if (skeletonTimeoutTimerRef.current) { clearTimeout(skeletonTimeoutTimerRef.current); skeletonTimeoutTimerRef.current = null; }
  setSkeletonTimeoutReached(false);

  // If we already have results, just stop loading
  if (result && result.licitacoes && result.licitacoes.length > 0) {
    setLoading(false);
    setSearchId(null);
    setUseRealProgress(false);
    return;
  }

  // Try to recover from partial cache
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
}

/**
 * Estimates search time in seconds based on UF count and date range.
 * Pure function — no side effects.
 */
export function estimateSearchTimeFn(ufCount: number, dateRangeDays: number): number {
  const baseTime = 10;
  const parallelUfs = Math.min(ufCount, 10);
  const queuedUfs = Math.max(0, ufCount - 10);
  const fetchTime = parallelUfs * 3 + queuedUfs * 2;
  const dateMultiplier = dateRangeDays > 14 ? 1.3 : dateRangeDays > 7 ? 1.1 : 1.0;
  return Math.ceil(baseTime + fetchTime * dateMultiplier + 3 + 5 + 3);
}
