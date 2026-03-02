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
    /**
     * STORY-326: Number of items found per UF in uf_status events.
     * SSE contract for uf_status event detail:
     *   - uf: State code (e.g., "SP")
     *   - uf_status: "pending"|"fetching"|"retrying"|"success"|"failed"|"recovered"
     *   - count: Items found in this UF (success/recovered only)
     *   - attempt: Retry attempt number (retrying only)
     *   - reason: Failure reason (failed only, e.g., "timeout", "retry_failed")
     */
    count?: number;
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
    /** STORY-329 AC4: Long-running filter indicator (>30s filtering) */
    is_long_running?: boolean;
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

/** STORY-327 AC5: Filter summary from backend filter_summary SSE event */
export interface FilterSummary {
  totalRaw: number;
  totalFiltered: number;
  rejectedKeyword: number;
  rejectedValue: number;
  rejectedLlm: number;
}

/** STORY-354 AC6: Pending review reclassification update from SSE */
export interface PendingReviewUpdate {
  reclassifiedCount: number;
  acceptedCount: number;
  rejectedCount: number;
}

/** STORY-295 AC10: Per-source status for progressive results */
export type SourceStatusType = 'pending' | 'fetching' | 'success' | 'partial' | 'error' | 'timeout';

export interface SourceStatus {
  status: SourceStatusType;
  recordCount: number;
  durationMs: number;
  error?: string;
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
  /** STORY-297 AC9: true during reconnection attempt (between disconnect and reconnect) */
  isReconnecting: boolean;
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
  /** STORY-295 AC10: Per-source status for progressive results */
  sourceStatuses: Map<string, SourceStatus>;
  /** STORY-327 AC5: Filter summary with raw vs filtered counts */
  filterSummary: FilterSummary | null;
  /** STORY-354 AC6: Pending review reclassification update */
  pendingReviewUpdate: PendingReviewUpdate | null;
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
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [isDegraded, setIsDegraded] = useState(false);
  const [degradedDetail, setDegradedDetail] = useState<SearchProgressEvent['detail'] | null>(null);
  const [partialProgress, setPartialProgress] = useState<PartialProgress | null>(null);
  const [refreshAvailable, setRefreshAvailable] = useState<RefreshAvailableInfo | null>(null);

  // UF state (from useUfProgress)
  const [ufStatuses, setUfStatuses] = useState<Map<string, UfStatus>>(new Map());
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);

  // STORY-295: Per-source status for progressive results
  const [sourceStatuses, setSourceStatuses] = useState<Map<string, SourceStatus>>(new Map());
  // STORY-327 AC5: Filter summary from backend
  const [filterSummary, setFilterSummary] = useState<FilterSummary | null>(null);
  // STORY-354 AC6: Pending review reclassification update
  const [pendingReviewUpdate, setPendingReviewUpdate] = useState<PendingReviewUpdate | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const retryAttemptRef = useRef(0);
  // STORY-297 AC6: Track last received event ID for reconnection
  const lastEventIdRef = useRef<string>('');
  const onEventRef = useRef(onEvent);
  const onUfStatusRef = useRef(onUfStatus);
  const onErrorRef = useRef(onError);
  const selectedUfsRef = useRef(selectedUfs);
  // CRIT-SSE-FIX AC3: Ref for searchId to avoid stale closure in retry callbacks
  const searchIdRef = useRef(searchId);

  // Serialize selectedUfs for stable dependency comparison
  const selectedUfsKey = selectedUfs.join(',');

  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);
  useEffect(() => { onUfStatusRef.current = onUfStatus; }, [onUfStatus]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);
  useEffect(() => { selectedUfsRef.current = selectedUfs; }, [selectedUfsKey]);
  // CRIT-SSE-FIX AC3: Keep searchId ref in sync
  useEffect(() => { searchIdRef.current = searchId; }, [searchId]);

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
          count: event.detail.count,
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
      // STORY-268: Also set as currentEvent so progress bar advances during batch processing
      if (event.stage === 'batch_progress') {
        const detail = event.detail as Record<string, unknown>;
        setBatchProgress({
          batchNum: (detail.batch_num as number) || 0,
          totalBatches: (detail.total_batches as number) || 0,
          ufsInBatch: (detail.ufs_in_batch as string[]) || [],
        });
        // Fall through to setCurrentEvent — batch_progress carries progress=10-55%
      }

      // Set as current event for all other stages
      setCurrentEvent(event);
      onEventRef.current?.(event);

      // STORY-295: Handle source_complete and source_error events
      if (event.stage === 'source_complete' || event.stage === 'source_error') {
        const detail = event.detail as Record<string, unknown>;
        const source = detail.source as string;
        if (source) {
          setSourceStatuses(prev => {
            const next = new Map(prev);
            next.set(source, {
              status: (detail.source_status as SourceStatusType) || (event.stage === 'source_error' ? 'error' : 'success'),
              recordCount: (detail.record_count as number) || 0,
              durationMs: (detail.duration_ms as number) || 0,
              error: detail.error as string | undefined,
            });
            return next;
          });
        }
        return; // Don't set as current event — these are metadata events
      }

      // STORY-327 AC5: Handle filter_summary event
      if (event.stage === 'filter_summary') {
        const detail = event.detail as Record<string, unknown>;
        setFilterSummary({
          totalRaw: (detail.total_raw as number) || 0,
          totalFiltered: (detail.total_filtered as number) || 0,
          rejectedKeyword: (detail.rejected_keyword as number) || 0,
          rejectedValue: (detail.rejected_value as number) || 0,
          rejectedLlm: (detail.rejected_llm as number) || 0,
        });
        return; // Don't set as current event — this is metadata
      }

      // STORY-354 AC6: Handle pending_review reclassification event
      if (event.stage === 'pending_review') {
        const detail = event.detail as Record<string, unknown>;
        setPendingReviewUpdate({
          reclassifiedCount: (detail.reclassified_count as number) || 0,
          acceptedCount: (detail.accepted_count as number) || 0,
          rejectedCount: (detail.rejected_count as number) || 0,
        });
      }

      // Handle terminal and special events
      if (event.stage === 'partial_results') {
        const detail = event.detail as Record<string, unknown>;
        setPartialProgress({
          newCount: event.detail.new_results_count ?? 0,
          totalSoFar: event.detail.total_so_far ?? 0,
          ufsCompleted: event.detail.ufs_completed ?? [],
          ufsPending: event.detail.ufs_pending ?? [],
        });
        // STORY-295: Update source statuses from partial_results sources_completed/pending
        const sourcesCompleted = (detail.sources_completed as string[]) || [];
        const sourcesPending = (detail.sources_pending as string[]) || [];
        setSourceStatuses(prev => {
          const next = new Map(prev);
          for (const s of sourcesPending) {
            if (!next.has(s)) {
              next.set(s, { status: 'fetching', recordCount: 0, durationMs: 0 });
            }
          }
          // Source from this event is now complete (at least partially)
          const eventSource = detail.source as string;
          if (eventSource && !next.has(eventSource)) {
            next.set(eventSource, {
              status: 'success',
              recordCount: (detail.new_results_count as number) || 0,
              durationMs: 0,
            });
          }
          return next;
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
      setIsReconnecting(false);
    };

    eventSource.onmessage = (e) => {
      // STORY-297 AC6: Track last event ID for reconnection
      if (e.lastEventId) {
        lastEventIdRef.current = e.lastEventId;
      }
      handleMessage(e.data);
    };

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
    setSourceStatuses(new Map());
    setFilterSummary(null);
    setPendingReviewUpdate(null);
    setSseDisconnected(false);
    setIsReconnecting(false);
    setSseAvailable(true);
    retryAttemptRef.current = 0;
    lastEventIdRef.current = '';

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

    // GTM-STAB-006 AC5: Exponential backoff reconnection
    // GTM-FIX-043 AC2: First failure uses immediate retry (0ms) — expected race condition
    // in async mode where tracker exists but SSE connects before first event is emitted.
    const SSE_RETRY_DELAYS = [0, 3000, 6000];
    const SSE_MAX_RETRIES = 3;

    const scheduleRetry = () => {
      // CRIT-SSE-FIX AC3: Use ref instead of closure searchId to avoid stale value
      const currentSearchId = searchIdRef.current;
      if (retryAttemptRef.current >= SSE_MAX_RETRIES || !currentSearchId) {
        console.warn(`SSE all ${SSE_MAX_RETRIES} retries exhausted — falling back to simulated progress`);
        setSseAvailable(false);
        setSseDisconnected(true);
        setIsReconnecting(false);
        onErrorRef.current?.();
        return;
      }

      const delay = SSE_RETRY_DELAYS[retryAttemptRef.current] ?? 12000;
      retryAttemptRef.current += 1;
      // STORY-297 AC9: Show reconnecting indicator
      setIsReconnecting(true);
      console.info(`SSE reconnecting in ${delay}ms (attempt ${retryAttemptRef.current}/${SSE_MAX_RETRIES})`);

      setTimeout(() => {
        // CRIT-SSE-FIX AC3: Re-read ref at execution time (not capture time)
        const retrySearchId = searchIdRef.current;
        if (!eventSourceRef.current && retrySearchId) {
          let retryUrl = `/api/buscar-progress?search_id=${encodeURIComponent(retrySearchId)}`;
          if (authToken) {
            retryUrl += `&token=${encodeURIComponent(authToken)}`;
          }
          // STORY-297 AC6: Pass last event ID for replay on reconnection
          if (lastEventIdRef.current) {
            retryUrl += `&last_event_id=${encodeURIComponent(lastEventIdRef.current)}`;
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
      // GTM-FIX-043 AC4: First failure is expected (async race condition) — log as info
      if (retryAttemptRef.current === 0) {
        console.info('SSE initial connection: retrying immediately (expected async race)');
      } else {
        console.warn(`SSE connection failed (attempt ${retryAttemptRef.current})`);
      }
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
    isReconnecting,
    isDegraded, degradedDetail, partialProgress, refreshAvailable,
    ufStatuses, ufTotalFound, ufAllComplete, batchProgress,
    sourceStatuses, filterSummary, pendingReviewUpdate,
  };
}
