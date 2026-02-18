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
  /** GTM-FIX-033 AC2: true when SSE disconnected after retry */
  sseDisconnected: boolean;
}

export function useUfProgress({
  searchId,
  enabled,
  authToken,
  selectedUfs,
}: UseUfProgressOptions): UseUfProgressReturn {
  const [ufStatuses, setUfStatuses] = useState<Map<string, UfStatus>>(new Map());
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);
  const [sseDisconnected, setSseDisconnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryAttemptRef = useRef(0);
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
      setSseDisconnected(false);
      retryAttemptRef.current = 0;
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

    // GTM-FIX-033 AC2: Retry 1x with 2s delay before giving up
    eventSource.onerror = () => {
      console.warn(`SSE connection error in useUfProgress (attempt ${retryAttemptRef.current})`);
      cleanup();

      if (retryAttemptRef.current < 1 && searchId) {
        retryAttemptRef.current += 1;
        const retryTimeout = setTimeout(() => {
          if (!eventSourceRef.current && searchId) {
            let retryUrl = `/api/buscar-progress?search_id=${encodeURIComponent(searchId)}`;
            if (authToken) {
              retryUrl += `&token=${encodeURIComponent(authToken)}`;
            }
            const retrySource = new EventSource(retryUrl);
            eventSourceRef.current = retrySource;

            retrySource.addEventListener('uf_status', (e: MessageEvent) => {
              try {
                const event: UfStatusEvent = JSON.parse(e.data);
                setUfStatuses(prev => {
                  const next = new Map(prev);
                  next.set(event.uf, { status: event.status, count: event.count, attempt: event.attempt });
                  return next;
                });
              } catch (err) {
                console.warn('Failed to parse uf_status event on retry:', err);
              }
            });

            retrySource.addEventListener('batch_progress', (e: MessageEvent) => {
              try {
                const data = JSON.parse(e.data);
                setBatchProgress({ batchNum: data.batch_num, totalBatches: data.total_batches, ufsInBatch: data.ufs_in_batch || [] });
              } catch (err) {
                console.warn('Failed to parse batch_progress on retry:', err);
              }
            });

            retrySource.onerror = () => {
              console.warn('SSE retry failed — marking disconnected');
              retrySource.close();
              eventSourceRef.current = null;
              setSseDisconnected(true);
            };
          }
        }, 2000);
        // Store timeout for cleanup
        return () => clearTimeout(retryTimeout);
      } else {
        setSseDisconnected(true);
      }
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
    sseDisconnected,
  };
}
