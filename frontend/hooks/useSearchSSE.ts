"use client";

/**
 * useSearchSSE - Consolidated SSE hook replacing useSearchProgress + useUfProgress.
 *
 * CRIT-006 AC9-12: Single EventSource connection for all search progress events.
 * Dispatches events to appropriate consumers via callback pattern.
 */

import { useEffect, useRef, useCallback, useState } from 'react';

// Re-export types for backward compatibility
export interface SearchProgressEvent {
  stage: string;
  progress: number;
  message: string;
  detail: {
    uf?: string;
    uf_index?: number;
    uf_total?: number;
    items_found?: number;
    total_raw?: number;
    total_filtered?: number;
    error?: string;
    /** A-02 AC6: Degraded event metadata */
    reason?: string;
    cache_age_hours?: number;
    cache_level?: string;
    sources_failed?: string[];
    sources_ok?: string[];
    coverage_pct?: number;
    /** A-04 AC3: Partial results during background fetch */
    new_results_count?: number;
    total_so_far?: number;
    ufs_completed?: string[];
    ufs_pending?: string[];
    /** A-04 AC4: Refresh available when background fetch completes */
    total_live?: number;
    total_cached?: number;
    new_count?: number;
    updated_count?: number;
    removed_count?: number;
    /** F-01 AC19: LLM summary data from background job */
    resumo?: Record<string, unknown>;
    /** F-01 AC20: Excel download URL from background job */
    download_url?: string;
    /** F-01 AC20: Excel status from background job */
    excel_status?: string;
    /** GTM-ARCH-001 AC3: Async search completion metadata */
    search_id?: string;
    total_results?: number;
    has_results?: boolean;
    /** GTM-ARCH-001: Error code from async search worker */
    error_code?: string;
    /** STORY-259: Per-bid intelligence analysis from batch LLM job */
    bid_analysis?: Array<{
      bid_id: string;
      justificativas: string[];
      acao_recomendada: string;
      compatibilidade_pct: number;
    }>;
  };
}

/** A-04 AC7: Partial progress during background live fetch */
export interface PartialProgress {
  newCount: number;
  totalSoFar: number;
  ufsCompleted: string[];
  ufsPending: string[];
}

/** A-04 AC4: Refresh available summary from background fetch */
export interface RefreshAvailableInfo {
  totalLive: number;
  totalCached: number;
  newCount: number;
  updatedCount: number;
  removedCount: number;
}

export type UfStatusType = 'pending' | 'fetching' | 'retrying' | 'success' | 'failed' | 'recovered';

export interface UfStatus {
  status: UfStatusType;
  count?: number;
  attempt?: number;
}

export interface UfStatusEvent {
  uf: string;
  status: UfStatusType;
  count?: number;
  attempt?: number;
}

/** GTM-FIX-031: Batch progress info for phased UF fetching */
export interface BatchProgress {
  batchNum: number;
  totalBatches: number;
  ufsInBatch: string[];
}

interface UseSearchSSEOptions {
  searchId: string | null;
  enabled: boolean;
  authToken?: string;
  selectedUfs?: string[];
  onEvent?: (event: SearchProgressEvent) => void;
  onUfStatus?: (event: UfStatusEvent) => void;
  onError?: () => void;
}

interface UseSearchSSEReturn {
  // From useSearchProgress
  currentEvent: SearchProgressEvent | null;
  isConnected: boolean;
  sseAvailable: boolean;
  /** GTM-FIX-033 AC2: true when SSE disconnected after retry */
  sseDisconnected: boolean;
  /** A-02 AC8: true when last terminal SSE event was "degraded" */
  isDegraded: boolean;
  /** A-02 AC10: metadata from degraded SSE event detail */
  degradedDetail: SearchProgressEvent['detail'] | null;
  /** A-04 AC7: Partial progress during background fetch */
  partialProgress: PartialProgress | null;
  /** A-04 AC4: Refresh available info from background fetch */
  refreshAvailable: RefreshAvailableInfo | null;
  // From useUfProgress
  ufStatuses: Map<string, UfStatus>;
  ufTotalFound: number;
  ufAllComplete: boolean;
  batchProgress: BatchProgress | null;
}

export function useSearchSSE({
  searchId,
  enabled,
  authToken,
  selectedUfs = [],
  onEvent,
  onUfStatus,
  onError,
}: UseSearchSSEOptions): UseSearchSSEReturn {
  // Progress state (from useSearchProgress)
  const [currentEvent, setCurrentEvent] = useState<SearchProgressEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sseAvailable, setSseAvailable] = useState(true);
  const [sseDisconnected, setSseDisconnected] = useState(false);
  const [isDegraded, setIsDegraded] = useState(false);
  const [degradedDetail, setDegradedDetail] = useState<SearchProgressEvent['detail'] | null>(null);
  const [partialProgress, setPartialProgress] = useState<PartialProgress | null>(null);
  const [refreshAvailable, setRefreshAvailable] = useState<RefreshAvailableInfo | null>(null);

  // UF state (from useUfProgress)
  const [ufStatuses, setUfStatuses] = useState<Map<string, UfStatus>>(new Map());
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const retryAttemptRef = useRef(0);
  const onEventRef = useRef(onEvent);
  const onUfStatusRef = useRef(onUfStatus);
  const onErrorRef = useRef(onError);
  const selectedUfsRef = useRef(selectedUfs);

  // Serialize selectedUfs for stable dependency comparison
  const selectedUfsKey = selectedUfs.join(',');

  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);
  useEffect(() => { onUfStatusRef.current = onUfStatus; }, [onUfStatus]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);
  useEffect(() => { selectedUfsRef.current = selectedUfs; }, [selectedUfsKey]);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Initialize UF statuses when search starts
  useEffect(() => {
    if (!enabled || !searchId) {
      setUfStatuses(new Map());
      setBatchProgress(null);
      return;
    }
    const initialStatuses = new Map<string, UfStatus>();
    selectedUfsRef.current.forEach(uf => {
      initialStatuses.set(uf, { status: 'pending' });
    });
    setUfStatuses(initialStatuses);
    setBatchProgress(null);
  }, [searchId, enabled, selectedUfsKey]);

  const handleMessage = useCallback((data: string) => {
    try {
      const event: SearchProgressEvent = JSON.parse(data);

      // Handle UF status events dispatched via generic onmessage
      if (event.stage === 'uf_status' && event.detail?.uf) {
        const ufEvent: UfStatusEvent = {
          uf: event.detail.uf,
          status: ((event.detail as Record<string, unknown>).uf_status as UfStatusType) || 'pending',
          count: event.detail.items_found,
          attempt: (event.detail as Record<string, unknown>).attempt as number | undefined,
        };
        setUfStatuses(prev => {
          const next = new Map(prev);
          next.set(ufEvent.uf, { status: ufEvent.status, count: ufEvent.count, attempt: ufEvent.attempt });
          return next;
        });
        onUfStatusRef.current?.(ufEvent);
        return; // Don't set as current event
      }

      // Handle batch progress dispatched via generic onmessage
      if (event.stage === 'batch_progress') {
        const detail = event.detail as Record<string, unknown>;
        setBatchProgress({
          batchNum: (detail.batch_num as number) || 0,
          totalBatches: (detail.total_batches as number) || 0,
          ufsInBatch: (detail.ufs_in_batch as string[]) || [],
        });
        return;
      }

      // Set as current event for all other stages
      setCurrentEvent(event);
      onEventRef.current?.(event);

      // Handle terminal and special events
      if (event.stage === 'partial_results') {
        setPartialProgress({
          newCount: event.detail.new_results_count ?? 0,
          totalSoFar: event.detail.total_so_far ?? 0,
          ufsCompleted: event.detail.ufs_completed ?? [],
          ufsPending: event.detail.ufs_pending ?? [],
        });
      } else if (event.stage === 'refresh_available') {
        setRefreshAvailable({
          totalLive: event.detail.total_live ?? 0,
          totalCached: event.detail.total_cached ?? 0,
          newCount: event.detail.new_count ?? 0,
          updatedCount: event.detail.updated_count ?? 0,
          removedCount: event.detail.removed_count ?? 0,
        });
        cleanup();
      } else if (event.stage === 'degraded') {
        setIsDegraded(true);
        setDegradedDetail(event.detail || null);
        cleanup();
      } else if (event.stage === 'complete' || event.stage === 'error') {
        cleanup();
      }
    } catch (err) {
      console.warn('Failed to parse SSE event:', err);
    }
  }, [cleanup]);

  const connectSSE = useCallback((url: string) => {
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setSseAvailable(true);
    };

    eventSource.onmessage = (e) => handleMessage(e.data);

    // Also listen for named events (uf_status, batch_progress)
    eventSource.addEventListener('uf_status', (e: MessageEvent) => {
      try {
        const ufEvent: UfStatusEvent = JSON.parse(e.data);
        setUfStatuses(prev => {
          const next = new Map(prev);
          next.set(ufEvent.uf, { status: ufEvent.status, count: ufEvent.count, attempt: ufEvent.attempt });
          return next;
        });
        onUfStatusRef.current?.(ufEvent);
      } catch (err) {
        console.warn('Failed to parse uf_status event:', err);
      }
    });

    eventSource.addEventListener('batch_progress', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setBatchProgress({
          batchNum: data.batch_num,
          totalBatches: data.total_batches,
          ufsInBatch: data.ufs_in_batch || [],
        });
      } catch (err) {
        console.warn('Failed to parse batch_progress event:', err);
      }
    });

    return eventSource;
  }, [handleMessage]);

  useEffect(() => {
    if (!enabled || !searchId) {
      cleanup();
      setSseDisconnected(false);
      return;
    }

    // Reset state for new search
    setIsDegraded(false);
    setDegradedDetail(null);
    setPartialProgress(null);
    setRefreshAvailable(null);
    setSseDisconnected(false);
    setSseAvailable(true);
    retryAttemptRef.current = 0;

    // Build SSE URL through Next.js proxy
    // Auth token passed as query param since EventSource doesn't support custom headers
    let url = `/api/buscar-progress?search_id=${encodeURIComponent(searchId)}`;
    if (authToken) {
      url += `&token=${encodeURIComponent(authToken)}`;
    }

    // CRIT-026 AC9: Sentry breadcrumb before SSE connection
    try {
      // Dynamic import to avoid hard dependency in tests
      import("@sentry/nextjs").then((Sentry) => {
        Sentry.addBreadcrumb({
          category: "sse",
          message: `SSE connecting: search_id=${searchId}`,
          level: "info",
          data: {
            search_id: searchId,
            timestamp_ms: Date.now(),
          },
        });
      }).catch(() => { /* Sentry not available */ });
    } catch { /* Sentry not available */ }

    const es = connectSSE(url);

    // GTM-STAB-006 AC5: Exponential backoff reconnection (3s/6s/12s, max 3 attempts)
    const SSE_RETRY_DELAYS = [3000, 6000, 12000];
    const SSE_MAX_RETRIES = 3;

    const scheduleRetry = () => {
      if (retryAttemptRef.current >= SSE_MAX_RETRIES || !searchId) {
        console.warn(`SSE all ${SSE_MAX_RETRIES} retries exhausted — falling back to simulated progress`);
        setSseAvailable(false);
        setSseDisconnected(true);
        onErrorRef.current?.();
        return;
      }

      const delay = SSE_RETRY_DELAYS[retryAttemptRef.current] ?? 12000;
      retryAttemptRef.current += 1;
      console.info(`SSE reconnecting in ${delay}ms (attempt ${retryAttemptRef.current}/${SSE_MAX_RETRIES})`);

      setTimeout(() => {
        if (!eventSourceRef.current && searchId) {
          let retryUrl = `/api/buscar-progress?search_id=${encodeURIComponent(searchId)}`;
          if (authToken) {
            retryUrl += `&token=${encodeURIComponent(authToken)}`;
          }
          const retryEs = connectSSE(retryUrl);
          retryEs.onerror = () => {
            console.warn(`SSE retry ${retryAttemptRef.current}/${SSE_MAX_RETRIES} failed`);
            retryEs.close();
            eventSourceRef.current = null;
            scheduleRetry(); // Recursive: schedule next retry with backoff
          };
        }
      }, delay);
    };

    es.onerror = () => {
      console.warn(`SSE initial connection failed`);
      cleanup();
      scheduleRetry();
    };

    return () => {
      retryAttemptRef.current = 0;
      cleanup();
    };
  }, [searchId, enabled, authToken, cleanup, connectSSE]);

  // Compute derived UF values
  const ufTotalFound = Array.from(ufStatuses.values())
    .filter(s => s.status === 'success' || s.status === 'recovered')
    .reduce((sum, s) => sum + (s.count || 0), 0);

  const ufAllComplete = ufStatuses.size > 0 &&
    Array.from(ufStatuses.values()).every(
      s => s.status === 'success' || s.status === 'failed' || s.status === 'recovered'
    );

  return {
    currentEvent, isConnected, sseAvailable, sseDisconnected,
    isDegraded, degradedDetail, partialProgress, refreshAvailable,
    ufStatuses, ufTotalFound, ufAllComplete, batchProgress,
  };
}
