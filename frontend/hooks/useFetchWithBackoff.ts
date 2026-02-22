/**
 * CRIT-018 AC1-AC4: Reusable hook with exponential backoff + abort on unmount.
 *
 * Backoff sequence: 2s → 4s → 8s → 16s → 30s (cap).
 * After maxRetries (default 5), stops automatic retries.
 * manualRetry() resets count and makes one fresh attempt.
 */

import { useState, useEffect, useRef, useCallback } from "react";

export interface FetchWithBackoffOptions {
  /** Whether fetching is enabled. When false, no requests are made. Default: true */
  enabled?: boolean;
  /** Maximum automatic retry attempts before giving up. Default: 5 */
  maxRetries?: number;
  /** Initial backoff delay in ms. Default: 2000 */
  initialDelayMs?: number;
  /** Maximum backoff delay in ms. Default: 30000 */
  maxDelayMs?: number;
  /** Backoff multiplier. Default: 2 */
  backoffMultiplier?: number;
  /** Per-attempt timeout in ms. Default: 10000 */
  timeoutMs?: number;
}

export interface FetchWithBackoffResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  retryCount: number;
  hasExhaustedRetries: boolean;
  manualRetry: () => void;
}

// Exported for testing
export const BACKOFF_DEFAULTS = {
  maxRetries: 5,
  initialDelayMs: 2000,
  maxDelayMs: 30000,
  backoffMultiplier: 2,
  timeoutMs: 10000,
} as const;

export function useFetchWithBackoff<T>(
  fetchFn: (signal: AbortSignal) => Promise<T>,
  options?: FetchWithBackoffOptions
): FetchWithBackoffResult<T> {
  const {
    enabled = true,
    maxRetries = BACKOFF_DEFAULTS.maxRetries,
    initialDelayMs = BACKOFF_DEFAULTS.initialDelayMs,
    maxDelayMs = BACKOFF_DEFAULTS.maxDelayMs,
    backoffMultiplier = BACKOFF_DEFAULTS.backoffMultiplier,
    timeoutMs = BACKOFF_DEFAULTS.timeoutMs,
  } = options ?? {};

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [hasExhaustedRetries, setHasExhaustedRetries] = useState(false);

  // Refs for cleanup
  const abortRef = useRef<AbortController | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const timeoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const fetchFnRef = useRef(fetchFn);
  const retryCountRef = useRef(0);
  // Track generation to detect stale callbacks
  const generationRef = useRef(0);

  // Keep fetchFn ref current
  fetchFnRef.current = fetchFn;

  /** Calculate backoff delay for a given retry attempt */
  const getBackoffDelay = useCallback(
    (attempt: number): number => {
      const delay = initialDelayMs * Math.pow(backoffMultiplier, attempt);
      return Math.min(delay, maxDelayMs);
    },
    [initialDelayMs, backoffMultiplier, maxDelayMs]
  );

  /** Cancel any in-flight request and pending retry timer */
  const cancelPending = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort("cancelled");
      abortRef.current = null;
    }
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    if (timeoutTimerRef.current) {
      clearTimeout(timeoutTimerRef.current);
      timeoutTimerRef.current = null;
    }
  }, []);

  /** Core fetch logic — executes one attempt, schedules retry on failure */
  const doFetch = useCallback(
    (attempt: number, generation: number) => {
      if (!mountedRef.current) return;

      // Abort any previous in-flight request (but not the new one we're about to create)
      if (abortRef.current) {
        abortRef.current.abort("cancelled");
        abortRef.current = null;
      }
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      if (timeoutTimerRef.current) {
        clearTimeout(timeoutTimerRef.current);
        timeoutTimerRef.current = null;
      }

      const controller = new AbortController();
      abortRef.current = controller;
      let timedOut = false;

      // Per-attempt timeout
      timeoutTimerRef.current = setTimeout(() => {
        timedOut = true;
        controller.abort("timeout");
      }, timeoutMs);

      setLoading(true);
      if (attempt === 0) {
        setError(null);
        setHasExhaustedRetries(false);
      }

      fetchFnRef
        .current(controller.signal)
        .then((result) => {
          if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
          if (!mountedRef.current || generation !== generationRef.current) return;
          setData(result);
          setError(null);
          setLoading(false);
          setRetryCount(0);
          retryCountRef.current = 0;
          setHasExhaustedRetries(false);
        })
        .catch((err: unknown) => {
          if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
          if (!mountedRef.current || generation !== generationRef.current) return;

          // AbortError from our own cancellation (not timeout) — ignore silently
          if (err instanceof DOMException && err.name === "AbortError" && !timedOut) {
            return;
          }

          // Timeout or real error
          const msg = timedOut
            ? "O painel demorou demais para carregar. Verifique sua conexão."
            : err instanceof Error
              ? err.message
              : "Erro ao carregar dados";
          handleFailure(msg, attempt, generation);
        });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [timeoutMs, maxRetries, getBackoffDelay]
  );

  /** Handle a failed attempt — schedule retry or give up */
  const handleFailure = useCallback(
    (msg: string, attempt: number, generation: number) => {
      if (!mountedRef.current || generation !== generationRef.current) return;

      const nextAttempt = attempt + 1;
      setRetryCount(nextAttempt);
      retryCountRef.current = nextAttempt;
      setError(msg);

      if (nextAttempt >= maxRetries) {
        // Exhausted retries — stop
        setLoading(false);
        setHasExhaustedRetries(true);
        return;
      }

      // Schedule next retry with backoff
      const delay = getBackoffDelay(attempt);
      retryTimerRef.current = setTimeout(() => {
        if (mountedRef.current && generation === generationRef.current) {
          doFetch(nextAttempt, generation);
        }
      }, delay);
    },
    [maxRetries, getBackoffDelay, doFetch]
  );

  /** Manual retry — resets everything and starts fresh */
  const manualRetry = useCallback(() => {
    cancelPending();
    setRetryCount(0);
    retryCountRef.current = 0;
    setHasExhaustedRetries(false);
    setError(null);
    generationRef.current += 1;
    doFetch(0, generationRef.current);
  }, [cancelPending, doFetch]);

  // Main effect: start fetch when enabled, cancel when disabled or on unmount.
  // Also re-runs when fetchFn changes (e.g. period change in dashboard).
  useEffect(() => {
    mountedRef.current = true;

    if (!enabled) {
      cancelPending();
      setLoading(false);
      return;
    }

    // New generation — invalidates stale callbacks from previous runs
    generationRef.current += 1;
    const gen = generationRef.current;

    // Reset state for fresh fetch
    setRetryCount(0);
    retryCountRef.current = 0;
    setHasExhaustedRetries(false);

    doFetch(0, gen);

    return () => {
      mountedRef.current = false;
      cancelPending();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, fetchFn]);

  return {
    data,
    loading,
    error,
    retryCount,
    hasExhaustedRetries,
    manualRetry,
  };
}
