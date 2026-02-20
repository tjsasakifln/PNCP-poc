/**
 * useSearchPolling — CRIT-003 AC11-AC13: Polling fallback when SSE disconnects.
 *
 * Polls GET /api/search-status?search_id=xxx every 3 seconds to get current
 * search state from the database. Automatically stops when status is terminal
 * (completed/failed/timed_out/rate_limited).
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { SearchProgressEvent } from './useSearchProgress';

export interface SearchStatusResponse {
  search_id: string;
  status: string;
  progress: number;
  stage: string | null;
  started_at: string | null;
  elapsed_ms: number | null;
  ufs_completed: string[] | null;
  ufs_total: number | null;
  ufs_failed: string[] | null;
  llm_status: string;
  excel_status: string;
  error_message: string | null;
  error_code: string | null;
}

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'timed_out', 'rate_limited']);

const POLL_INTERVAL_MS = 3000;

interface UseSearchPollingOptions {
  searchId: string | null;
  /** AC21: Only poll when SSE has disconnected */
  enabled: boolean;
  authToken?: string;
  onStatusUpdate?: (status: SearchStatusResponse) => void;
}

interface UseSearchPollingReturn {
  status: SearchStatusResponse | null;
  isPolling: boolean;
  /** Converted to SearchProgressEvent format for seamless integration */
  asProgressEvent: SearchProgressEvent | null;
}

export function useSearchPolling({
  searchId,
  enabled,
  authToken,
  onStatusUpdate,
}: UseSearchPollingOptions): UseSearchPollingReturn {
  const [status, setStatus] = useState<SearchStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onStatusUpdateRef = useRef(onStatusUpdate);

  useEffect(() => { onStatusUpdateRef.current = onStatusUpdate; }, [onStatusUpdate]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!enabled || !searchId) {
      stopPolling();
      return;
    }

    const fetchStatus = async () => {
      try {
        const headers: Record<string, string> = {};
        if (authToken) {
          headers['Authorization'] = `Bearer ${authToken}`;
        }

        const res = await fetch(
          `/api/search-status?search_id=${encodeURIComponent(searchId)}`,
          { headers }
        );

        if (!res.ok) {
          console.warn(`Polling returned ${res.status}`);
          return;
        }

        const data: SearchStatusResponse = await res.json();
        setStatus(data);
        onStatusUpdateRef.current?.(data);

        // AC13: Stop polling when terminal
        if (TERMINAL_STATUSES.has(data.status)) {
          stopPolling();
        }
      } catch (err) {
        console.warn('Polling fetch failed:', err);
      }
    };

    // Start polling immediately + on interval
    setIsPolling(true);
    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);

    return stopPolling;
  }, [searchId, enabled, authToken, stopPolling]);

  // Convert to SearchProgressEvent format for drop-in use
  const asProgressEvent: SearchProgressEvent | null = status ? {
    stage: status.status === 'completed' ? 'complete'
         : status.status === 'failed' ? 'error'
         : status.status === 'timed_out' ? 'error'
         : status.status === 'rate_limited' ? 'error'
         : status.stage || status.status,
    progress: status.progress,
    message: status.error_message || _stageMessage(status.status, status.stage),
    detail: {
      error: status.error_message || undefined,
    },
  } : null;

  return { status, isPolling, asProgressEvent };
}

function _stageMessage(status: string, stage: string | null): string {
  if (status === 'completed') return 'Busca concluída!';
  if (status === 'failed') return 'Erro no processamento';
  if (status === 'timed_out') return 'Tempo limite excedido';
  if (status === 'rate_limited') return 'Limite de requisições excedido';

  const stageMessages: Record<string, string> = {
    // Long-form (state machine states)
    validating: 'Validando requisição...',
    fetching: 'Buscando dados...',
    filtering: 'Filtrando resultados...',
    enriching: 'Enriquecendo resultados...',
    generating: 'Gerando relatórios...',
    persisting: 'Salvando resultados...',
    // Short-form (pipeline stage names from backend)
    validate: 'Validando requisição...',
    prepare: 'Preparando busca...',
    execute: 'Buscando dados...',
    fetch: 'Buscando dados...',
    filter: 'Filtrando resultados...',
    enrich: 'Enriquecendo resultados...',
    generate: 'Gerando relatórios...',
    persist: 'Salvando resultados...',
  };
  return stageMessages[stage || status] || 'Processando...';
}
