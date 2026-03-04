/**
 * useUfProgress — Thin wrapper over useSearchSSE for backward compatibility.
 *
 * STORY-367 AC3: All SSE logic consolidated in useSearchSSE.
 * This wrapper maps the useSearchSSE return to the legacy useUfProgress interface.
 */

import { useSearchSSE } from '../../../hooks/useSearchSSE';

// Re-export types for backward compatibility
export type { UfStatusType, UfStatus, UfStatusEvent, BatchProgress } from '../../../hooks/useSearchSSE';

interface UseUfProgressOptions {
  searchId: string | null;
  enabled: boolean;
  authToken?: string;
  selectedUfs: string[];
}

interface UseUfProgressReturn {
  ufStatuses: Map<string, import('../../../hooks/useSearchSSE').UfStatus>;
  totalFound: number;
  allComplete: boolean;
  batchProgress: import('../../../hooks/useSearchSSE').BatchProgress | null;
  /** GTM-FIX-033 AC2: true when SSE disconnected after retry */
  sseDisconnected: boolean;
}

export function useUfProgress({
  searchId,
  enabled,
  authToken,
  selectedUfs,
}: UseUfProgressOptions): UseUfProgressReturn {
  const sse = useSearchSSE({
    searchId,
    enabled,
    authToken,
    selectedUfs,
  });

  return {
    ufStatuses: sse.ufStatuses,
    totalFound: sse.ufTotalFound,
    allComplete: sse.ufAllComplete,
    batchProgress: sse.batchProgress,
    sseDisconnected: sse.sseDisconnected,
  };
}
