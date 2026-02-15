/**
 * useUfProgress - React hook for tracking per-UF search progress via SSE.
 *
 * Maintains a Map of UF statuses (pending → fetching → retrying → success/failed/recovered)
 * and computes aggregated metrics (total found, all complete).
 */

import { useEffect, useState, useRef, useCallback } from 'react';

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

interface UseUfProgressOptions {
  searchId: string | null;
  enabled: boolean;
  authToken?: string;
  selectedUfs: string[];
}

interface UseUfProgressReturn {
  ufStatuses: Map<string, UfStatus>;
  totalFound: number;
  allComplete: boolean;
}

export function useUfProgress({
  searchId,
  enabled,
  authToken,
  selectedUfs,
}: UseUfProgressOptions): UseUfProgressReturn {
  const [ufStatuses, setUfStatuses] = useState<Map<string, UfStatus>>(new Map());
  const eventSourceRef = useRef<EventSource | null>(null);
  const selectedUfsRef = useRef(selectedUfs);

  // Serialize selectedUfs for stable dependency comparison
  const selectedUfsKey = selectedUfs.join(',');

  // Keep ref updated for use in callbacks
  useEffect(() => {
    selectedUfsRef.current = selectedUfs;
  }, [selectedUfsKey]);

  // Initialize all selected UFs with 'pending' status when search starts
  useEffect(() => {
    if (!enabled || !searchId) {
      setUfStatuses(new Map());
      return;
    }

    const initialStatuses = new Map<string, UfStatus>();
    selectedUfsRef.current.forEach(uf => {
      initialStatuses.set(uf, { status: 'pending' });
    });
    setUfStatuses(initialStatuses);
  }, [searchId, enabled, selectedUfsKey]);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!enabled || !searchId) {
      cleanup();
      return;
    }

    // Build SSE URL through Next.js proxy
    let url = `/api/buscar-progress?search_id=${encodeURIComponent(searchId)}`;
    if (authToken) {
      url += `&token=${encodeURIComponent(authToken)}`;
    }

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // Listen for 'uf_status' events specifically
    eventSource.addEventListener('uf_status', (e: MessageEvent) => {
      try {
        const event: UfStatusEvent = JSON.parse(e.data);

        setUfStatuses(prev => {
          const next = new Map(prev);
          next.set(event.uf, {
            status: event.status,
            count: event.count,
            attempt: event.attempt,
          });
          return next;
        });
      } catch (err) {
        console.warn('Failed to parse uf_status event:', err);
      }
    });

    eventSource.onerror = () => {
      console.warn('SSE connection error in useUfProgress');
      cleanup();
    };

    return cleanup;
  }, [searchId, enabled, authToken, cleanup]);

  // Compute derived values
  const totalFound = Array.from(ufStatuses.values())
    .filter(status => status.status === 'success' || status.status === 'recovered')
    .reduce((sum, status) => sum + (status.count || 0), 0);

  const allComplete = ufStatuses.size > 0 &&
    Array.from(ufStatuses.values()).every(
      status => status.status === 'success' ||
                status.status === 'failed' ||
                status.status === 'recovered'
    );

  return {
    ufStatuses,
    totalFound,
    allComplete,
  };
}
