/**
 * useSearchProgress - React hook for SSE-based real-time search progress.
 *
 * Opens an EventSource connection to /api/buscar-progress to receive
 * real-time progress events from the backend during PNCP searches.
 * Falls back gracefully when SSE is unavailable.
 */

import { useEffect, useRef, useCallback, useState } from 'react';

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

export interface UfStatusEvent {
  uf: string;
  status: string;
  count?: number;
  attempt?: number;
}

interface UseSearchProgressOptions {
  searchId: string | null;
  enabled: boolean;
  authToken?: string;
  onEvent?: (event: SearchProgressEvent) => void;
  onUfStatus?: (event: UfStatusEvent) => void;
  onError?: () => void;
}

interface UseSearchProgressReturn {
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
}

export function useSearchProgress({
  searchId,
  enabled,
  authToken,
  onEvent,
  onUfStatus,
  onError,
}: UseSearchProgressOptions): UseSearchProgressReturn {
  const [currentEvent, setCurrentEvent] = useState<SearchProgressEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sseAvailable, setSseAvailable] = useState(true);
  const [sseDisconnected, setSseDisconnected] = useState(false);
  const [isDegraded, setIsDegraded] = useState(false);
  const [degradedDetail, setDegradedDetail] = useState<SearchProgressEvent['detail'] | null>(null);
  const [partialProgress, setPartialProgress] = useState<PartialProgress | null>(null);
  const [refreshAvailable, setRefreshAvailable] = useState<RefreshAvailableInfo | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryAttemptRef = useRef(0);
  const onEventRef = useRef(onEvent);
  const onUfStatusRef = useRef(onUfStatus);
  const onErrorRef = useRef(onError);

  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);
  useEffect(() => { onUfStatusRef.current = onUfStatus; }, [onUfStatus]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (!enabled || !searchId) {
      cleanup();
      return;
    }

    // Reset state for new search
    setIsDegraded(false);
    setDegradedDetail(null);
    setPartialProgress(null);
    setRefreshAvailable(null);

    // Build SSE URL through Next.js proxy
    // Auth token passed as query param since EventSource doesn't support custom headers
    let url = `/api/buscar-progress?search_id=${encodeURIComponent(searchId)}`;
    if (authToken) {
      url += `&token=${encodeURIComponent(authToken)}`;
    }

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setSseAvailable(true);
    };

    eventSource.onmessage = (e) => {
      try {
        const event: SearchProgressEvent = JSON.parse(e.data);
        setCurrentEvent(event);
        onEventRef.current?.(event);

        // A-04 AC7: partial_results is NON-terminal — SSE stays open
        if (event.stage === 'partial_results') {
          setPartialProgress({
            newCount: event.detail.new_results_count ?? 0,
            totalSoFar: event.detail.total_so_far ?? 0,
            ufsCompleted: event.detail.ufs_completed ?? [],
            ufsPending: event.detail.ufs_pending ?? [],
          });
        // A-04 AC4: refresh_available IS terminal — SSE closes
        } else if (event.stage === 'refresh_available') {
          setRefreshAvailable({
            totalLive: event.detail.total_live ?? 0,
            totalCached: event.detail.total_cached ?? 0,
            newCount: event.detail.new_count ?? 0,
            updatedCount: event.detail.updated_count ?? 0,
            removedCount: event.detail.removed_count ?? 0,
          });
          cleanup();
        // A-02 AC7: "degraded" is terminal (close SSE) but NOT sseDisconnected
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
    };

    // Listen for uf_status events (STORY-257B AC2)
    eventSource.addEventListener('uf_status', (e: MessageEvent) => {
      try {
        const event: UfStatusEvent = JSON.parse(e.data);
        onUfStatusRef.current?.(event);
      } catch (err) {
        console.warn('Failed to parse uf_status event:', err);
      }
    });

    // GTM-FIX-033 AC2: Retry 1x with 2s delay before falling back
    eventSource.onerror = () => {
      console.warn(`SSE connection failed (attempt ${retryAttemptRef.current})`);
      cleanup();

      if (retryAttemptRef.current < 1 && searchId) {
        retryAttemptRef.current += 1;
        setTimeout(() => {
          if (!eventSourceRef.current && searchId) {
            let retryUrl = `/api/buscar-progress?search_id=${encodeURIComponent(searchId)}`;
            if (authToken) {
              retryUrl += `&token=${encodeURIComponent(authToken)}`;
            }
            const retrySource = new EventSource(retryUrl);
            eventSourceRef.current = retrySource;

            retrySource.onopen = () => {
              setIsConnected(true);
              setSseAvailable(true);
            };

            retrySource.onmessage = (e) => {
              try {
                const event: SearchProgressEvent = JSON.parse(e.data);
                setCurrentEvent(event);
                onEventRef.current?.(event);
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
                console.warn('Failed to parse SSE event on retry:', err);
              }
            };

            retrySource.addEventListener('uf_status', (e: MessageEvent) => {
              try {
                const event: UfStatusEvent = JSON.parse(e.data);
                onUfStatusRef.current?.(event);
              } catch (err) {
                console.warn('Failed to parse uf_status on retry:', err);
              }
            });

            retrySource.onerror = () => {
              console.warn('SSE retry failed — falling back to simulated progress');
              retrySource.close();
              eventSourceRef.current = null;
              setSseAvailable(false);
              setSseDisconnected(true);
              onErrorRef.current?.();
            };
          }
        }, 2000);
      } else {
        setSseAvailable(false);
        setSseDisconnected(true);
        onErrorRef.current?.();
      }
    };

    return () => {
      retryAttemptRef.current = 0;
      cleanup();
    };
  }, [searchId, enabled, authToken, cleanup]);

  return { currentEvent, isConnected, sseAvailable, sseDisconnected, isDegraded, degradedDetail, partialProgress, refreshAvailable };
}
