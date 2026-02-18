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
  };
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

        if (event.stage === 'complete' || event.stage === 'error') {
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
                if (event.stage === 'complete' || event.stage === 'error') cleanup();
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

  return { currentEvent, isConnected, sseAvailable, sseDisconnected };
}
