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

interface UseSearchProgressOptions {
  searchId: string | null;
  enabled: boolean;
  authToken?: string;
  onEvent?: (event: SearchProgressEvent) => void;
  onError?: () => void;
}

interface UseSearchProgressReturn {
  currentEvent: SearchProgressEvent | null;
  isConnected: boolean;
  sseAvailable: boolean;
}

export function useSearchProgress({
  searchId,
  enabled,
  authToken,
  onEvent,
  onError,
}: UseSearchProgressOptions): UseSearchProgressReturn {
  const [currentEvent, setCurrentEvent] = useState<SearchProgressEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sseAvailable, setSseAvailable] = useState(true);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onEventRef = useRef(onEvent);
  const onErrorRef = useRef(onError);

  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);
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

    eventSource.onerror = () => {
      console.warn('SSE connection failed, falling back to simulated progress');
      setSseAvailable(false);
      onErrorRef.current?.();
      cleanup();
    };

    return cleanup;
  }, [searchId, enabled, authToken, cleanup]);

  return { currentEvent, isConnected, sseAvailable };
}
