"use client";

/**
 * useSearchSSE — Consolidated SSE hook for all search progress events.
 *
 * Replaces useSearchProgress (GTM-FIX-033) + useUfProgress (STORY-365).
 * Single EventSource connection per search_id with unified resilience strategy.
 *
 * ## Resilience Strategy (STORY-367)
 *
 * | Layer         | Strategy                               | Origin      |
 * |---------------|----------------------------------------|-------------|
 * | Reconnect     | Exponential backoff [1s, 2s, 4s]       | STORY-365   |
 * | Max retries   | 3 attempts                             | STAB-006    |
 * | Terminal guard| isTerminalRef prevents post-complete   | STORY-365   |
 * | Polling       | GET /v1/search/{id}/status every 5s    | STORY-365   |
 * | Last-Event-ID | Forwarded on reconnect for replay      | STORY-297   |
 * | High-water    | Progress never decreases (monotonic)   | CRIT-052    |
 *
 * ## Constants
 *
 * | Constant                  | Value         | Rationale                    |
 * |---------------------------|---------------|------------------------------|
 * | SSE_RECONNECT_BACKOFF_MS  | [1000,2000,4000] | Conservative (STORY-365)  |
 * | SSE_MAX_RETRIES           | 3             | Enough for transient errors  |
 * | SSE_POLLING_INTERVAL_MS   | 5000          | Light load on backend        |
 */

import { useEffect, useRef, useCallback, useState } from 'react';

// STORY-367 AC1: Named constants for SSE reconnection strategy
export const SSE_RECONNECT_BACKOFF_MS = [1000, 2000, 4000];
export const SSE_MAX_RETRIES = 3;
export const SSE_POLLING_INTERVAL_MS = 5000;
// CRIT-072 AC7: SSE inactivity timeout — if no event for 120s, trigger error
export const SSE_INACTIVITY_TIMEOUT_MS = 120_000;

// Terminal SSE stages that signal search is done — no reconnect after these
const TERMINAL_STAGES = new Set([
  'complete', 'error', 'degraded', 'refresh_available', 'search_complete',
]);

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
    /** GTM-ARCH-001 AC3 + CRIT-072 AC4: Async search completion metadata */
    search_id?: string;
    total_results?: number;
    has_results?: boolean;
    results_ready?: boolean;
    results_url?: string;
    is_partial?: boolean;
    /** GTM-ARCH-001: Error code from async search worker */
    error_code?: string;
    /** STORY-329 AC4: Long-running filter indicator (>30s filtering) */
    is_long_running?: boolean;
    /** CRIT-071: Partial data SSE event fields */
    licitacoes?: Array<Record<string, unknown>>;
    batch_index?: number;
    is_final?: boolean;
    truncated?: boolean;
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

export type UfStatusType = 'pending' | 'fetching' | 'retrying' | 'success' | 'failed' | 'recovered' | 'partial';

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

/** CRIT-059 AC5: Zero-match background classification progress */
export interface ZeroMatchProgress {
  candidates: number;
  willClassify: number;
  classified: number;
  approved: number;
  status: 'started' | 'classifying' | 'ready' | 'error';
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
  /** CRIT-059 AC5: Zero-match background classification progress */
  zeroMatchProgress: ZeroMatchProgress | null;
  /** CRIT-072 AC7: True when no SSE event received for 120s */
  sseInactivityTimeout: boolean;
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
  // CRIT-059 AC5: Zero-match classification progress
  const [zeroMatchProgress, setZeroMatchProgress] = useState<ZeroMatchProgress | null>(null);

  // CRIT-052 AC1: High-water mark — progress must never decrease
  const progressHighWaterRef = useRef(0);

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
  // STORY-367 AC3: Terminal guard — prevents reconnect after complete/error/degraded
  const isTerminalRef = useRef(false);
  // STORY-367: Timer refs for cleanup
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // CRIT-072 AC7: SSE inactivity timeout
  const inactivityTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [sseInactivityTimeout, setSseInactivityTimeout] = useState(false);

  // Serialize selectedUfs for stable dependency comparison
  const selectedUfsKey = selectedUfs.join(',');

  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);
  useEffect(() => { onUfStatusRef.current = onUfStatus; }, [onUfStatus]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);
  useEffect(() => { selectedUfsRef.current = selectedUfs; }, [selectedUfsKey]);
  // CRIT-SSE-FIX AC3: Keep searchId ref in sync
  useEffect(() => { searchIdRef.current = searchId; }, [searchId]);

  const cleanupPolling = useCallback(() => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  const cleanupInactivity = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
  }, []);

  const resetInactivityTimer = useCallback(() => {
    cleanupInactivity();
    // CRIT-072 AC7: Don't start inactivity timer if search is terminal
    if (isTerminalRef.current) return;
    inactivityTimerRef.current = setTimeout(() => {
      console.warn('[CRIT-072] SSE inactivity timeout — no event received for 120s');
      setSseInactivityTimeout(true);
      onErrorRef.current?.();
    }, SSE_INACTIVITY_TIMEOUT_MS);
  }, [cleanupInactivity]);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    cleanupPolling();
    cleanupInactivity();
    setIsConnected(false);
  }, [cleanupPolling, cleanupInactivity]);

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
          const existing = next.get(ufEvent.uf);
          // BUG-004: Aggregate multi-source results. If a source already succeeded for this UF,
          // a subsequent failure from another source should not overwrite to "failed".
          // Instead show "partial" (yellow) to indicate at least one source delivered data.
          let resolvedStatus = ufEvent.status;
          if (existing) {
            const existingSucceeded = existing.status === 'success' || existing.status === 'recovered' || existing.status === 'partial';
            const incomingFailed = ufEvent.status === 'failed';
            const existingFailed = existing.status === 'failed' || existing.status === 'partial';
            const incomingSucceeded = ufEvent.status === 'success' || ufEvent.status === 'recovered';
            if (existingSucceeded && incomingFailed) {
              resolvedStatus = 'partial';
            } else if (existingFailed && incomingSucceeded) {
              resolvedStatus = 'partial';
            }
          }
          next.set(ufEvent.uf, { status: resolvedStatus, count: ufEvent.count ?? existing?.count, attempt: ufEvent.attempt });
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

      // CRIT-052 AC1: Enforce monotonic progress — never show a value lower than the max seen.
      // Update high-water mark and clamp progress for non-negative values.
      if (event.progress >= 0) {
        progressHighWaterRef.current = Math.max(progressHighWaterRef.current, event.progress);
        event.progress = progressHighWaterRef.current;
      }

      // CRIT-052 AC3: Don't update currentEvent for metadata-only events with progress=-1.
      // These are informational (source status, filter stats) and would cause the progress
      // bar to fall back to simulated progress, potentially showing a lower value.
      const isMetadataEvent = event.progress === -1 && (
        event.stage === 'source_complete' ||
        event.stage === 'source_error' ||
        event.stage === 'filter_summary' ||
        event.stage === 'pending_review' ||
        event.stage === 'zero_match_started' ||
        event.stage === 'zero_match_progress' ||
        event.stage === 'zero_match_ready' ||
        event.stage === 'zero_match_error'
      );

      if (!isMetadataEvent) {
        // Set as current event for progress-bearing and terminal stages
        setCurrentEvent(event);
        onEventRef.current?.(event);
      }

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

      // CRIT-059 AC5: Handle zero-match classification progress events
      if (event.stage === 'zero_match_started') {
        const detail = event.detail as Record<string, unknown>;
        setZeroMatchProgress({
          candidates: (detail.candidates as number) || 0,
          willClassify: (detail.will_classify as number) || 0,
          classified: 0,
          approved: 0,
          status: 'started',
        });
      } else if (event.stage === 'zero_match_progress') {
        const detail = event.detail as Record<string, unknown>;
        setZeroMatchProgress(prev => prev ? {
          ...prev,
          classified: (detail.classified as number) || 0,
          approved: (detail.approved as number) || 0,
          status: 'classifying',
        } : prev);
      } else if (event.stage === 'zero_match_ready') {
        const detail = event.detail as Record<string, unknown>;
        setZeroMatchProgress(prev => prev ? {
          ...prev,
          classified: (detail.total_classified as number) || prev.classified,
          approved: (detail.approved as number) || 0,
          status: 'ready',
        } : prev);
        // Trigger SSE handler to fetch results
        onEventRef.current?.(event);
      } else if (event.stage === 'zero_match_error') {
        setZeroMatchProgress(prev => prev ? {
          ...prev,
          status: 'error',
        } : prev);
      }

      // STORY-367 AC3: Mark terminal events to prevent reconnect
      if (TERMINAL_STAGES.has(event.stage)) {
        isTerminalRef.current = true;
        // CRIT-072 AC7: Stop inactivity timer on terminal event
        cleanupInactivity();
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

  // STORY-367 AC1: Polling fallback when all SSE reconnect attempts exhausted
  const startPollingFallback = useCallback((sid: string, token?: string) => {
    if (pollingTimerRef.current || isTerminalRef.current) return;

    pollingTimerRef.current = setInterval(async () => {
      try {
        const headers: Record<string, string> = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        const res = await fetch(`/api/search-status?search_id=${encodeURIComponent(sid)}`, {
          headers,
        });
        if (!res.ok) return;

        const data = await res.json();
        const status = data?.status;

        if (status && TERMINAL_STAGES.has(status === 'completed' ? 'complete' : status)) {
          cleanupPolling();
          isTerminalRef.current = true;
        }
      } catch {
        // Polling error — continue polling
      }
    }, SSE_POLLING_INTERVAL_MS);
  }, [cleanupPolling]);

  const connectSSE = useCallback((url: string) => {
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setSseAvailable(true);
      setIsReconnecting(false);
      // CRIT-072 AC7: Start inactivity timer on connect
      resetInactivityTimer();
    };

    eventSource.onmessage = (e) => {
      // STORY-297 AC6: Track last event ID for reconnection
      if (e.lastEventId) {
        lastEventIdRef.current = e.lastEventId;
      }
      // CRIT-072 AC7: Reset inactivity timer on each message
      resetInactivityTimer();
      handleMessage(e.data);
    };

    // Also listen for named events (uf_status, batch_progress)
    eventSource.addEventListener('uf_status', (e: MessageEvent) => {
      try {
        const ufEvent: UfStatusEvent = JSON.parse(e.data);
        setUfStatuses(prev => {
          const next = new Map(prev);
          const existing = next.get(ufEvent.uf);
          // BUG-004: Same aggregation logic as handleMessage — preserve best-case status
          let resolvedStatus = ufEvent.status;
          if (existing) {
            const existingSucceeded = existing.status === 'success' || existing.status === 'recovered' || existing.status === 'partial';
            const incomingFailed = ufEvent.status === 'failed';
            const existingFailed = existing.status === 'failed' || existing.status === 'partial';
            const incomingSucceeded = ufEvent.status === 'success' || ufEvent.status === 'recovered';
            if (existingSucceeded && incomingFailed) {
              resolvedStatus = 'partial';
            } else if (existingFailed && incomingSucceeded) {
              resolvedStatus = 'partial';
            }
          }
          next.set(ufEvent.uf, { status: resolvedStatus, count: ufEvent.count ?? existing?.count, attempt: ufEvent.attempt });
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
    // CRIT-072 AC7: Reset inactivity timeout for new search
    setSseInactivityTimeout(false);
    retryAttemptRef.current = 0;
    lastEventIdRef.current = '';
    // STORY-367 AC3: Reset terminal guard for new search
    isTerminalRef.current = false;
    // CRIT-052 AC1: Reset high-water mark for new search
    progressHighWaterRef.current = 0;

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

    // STORY-367 AC1: Unified reconnection strategy (backoff from STORY-365)
    const scheduleRetry = () => {
      // STORY-367 AC3: Don't reconnect after terminal event
      if (isTerminalRef.current) return;

      // CRIT-SSE-FIX AC3: Use ref instead of closure searchId to avoid stale value
      const currentSearchId = searchIdRef.current;
      if (retryAttemptRef.current >= SSE_MAX_RETRIES || !currentSearchId) {
        console.warn(`SSE all ${SSE_MAX_RETRIES} retries exhausted — activating polling fallback`);
        setSseAvailable(false);
        setSseDisconnected(true);
        setIsReconnecting(false);
        // STORY-359 AC4: Report fallback to simulated progress (fire-and-forget)
        if (typeof fetch !== 'undefined') {
          fetch('/api/metrics/sse-fallback', { method: 'POST' }).catch(() => {});
        }
        // STORY-367 AC1: Start polling fallback
        if (currentSearchId) startPollingFallback(currentSearchId, authToken);
        onErrorRef.current?.();
        return;
      }

      const delay = SSE_RECONNECT_BACKOFF_MS[retryAttemptRef.current] ?? 4000;
      retryAttemptRef.current += 1;
      // STORY-297 AC9: Show reconnecting indicator
      setIsReconnecting(true);
      console.info(`SSE reconnecting in ${delay}ms (attempt ${retryAttemptRef.current}/${SSE_MAX_RETRIES})`);

      reconnectTimerRef.current = setTimeout(() => {
        reconnectTimerRef.current = null;
        // STORY-367 AC3: Re-check terminal guard at execution time
        if (isTerminalRef.current) return;
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
      // STORY-367 AC3: Don't reconnect after terminal event
      if (isTerminalRef.current) return;

      console.warn(`SSE connection failed (attempt ${retryAttemptRef.current})`);
      cleanup();
      scheduleRetry();
    };

    return () => {
      retryAttemptRef.current = 0;
      isTerminalRef.current = false;
      cleanup();
    };
  }, [searchId, enabled, authToken, cleanup, connectSSE, startPollingFallback, resetInactivityTimer]);

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
    sourceStatuses, filterSummary, pendingReviewUpdate, zeroMatchProgress,
    sseInactivityTimeout,
  };
}
