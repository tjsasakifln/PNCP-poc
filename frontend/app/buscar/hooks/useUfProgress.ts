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

/** GTM-FIX-031: Batch progress info for phased UF fetching */
export interface BatchProgress {
  batchNum: number;
  totalBatches: number;
  ufsInBatch: string[];
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
  batchProgress: BatchProgress | null;
}

export function useUfProgress({
  searchId,
  enabled,
  authToken,
  selectedUfs,
}: UseUfProgressOptions): UseUfProgressReturn {
  const [ufStatuses, setUfStatuses] = useState<Map<string, UfStatus>>(new Map());
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);
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

    // GTM-FIX-031: Listen for batch_progress events
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
    batchProgress,
  };
}
