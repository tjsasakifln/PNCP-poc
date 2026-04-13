"use client";

import useSWR from "swr";
import { useAuth } from "../app/components/AuthProvider";
import { FetchError } from "../lib/fetcher";

/**
 * TD-008 AC7: SWR-based sessions hook for historico page.
 * Supports pagination and auto-polling for active sessions.
 */

const fetchSessionsWithAuth = async (url: string, token: string) => {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new FetchError("Erro ao carregar histórico", res.status);
  }
  return res.json();
};

interface UseSessionsOptions {
  page: number;
  limit?: number;
  /** Polling interval in ms (0 to disable) */
  refreshInterval?: number;
  /** Server-side status filter (completed, failed, all) */
  status?: string;
  /**
   * UX-433 AC3: When true (default), the backend hides failed/timed_out entries
   * older than 7 days. Pass false to see the full unfiltered history ("Mostrar todas").
   */
  hideOldFailures?: boolean;
}

export function useSessions({ page, limit = 20, refreshInterval = 0, status, hideOldFailures = true }: UseSessionsOptions) {
  const { session } = useAuth();
  const accessToken = session?.access_token;

  const statusParam = status && status !== 'all' ? `&status=${status}` : '';
  // Only send hide_old_failures=false when explicitly disabled — backend defaults to true.
  const hideOldFailuresParam = hideOldFailures === false ? '&hide_old_failures=false' : '';
  const { data, error, isLoading, mutate } = useSWR(
    accessToken
      ? [`/api/sessions?limit=${limit}&offset=${page * limit}${statusParam}${hideOldFailuresParam}`, accessToken]
      : null,
    ([url, token]: [string, string]) => fetchSessionsWithAuth(url, token),
    {
      revalidateOnFocus: false,
      dedupingInterval: 3000,
      errorRetryCount: 2,
      refreshInterval: refreshInterval > 0 ? refreshInterval : undefined,
    }
  );

  return {
    sessions: data?.sessions || [],
    total: data?.total || 0,
    loading: isLoading,
    error: error ? "Não foi possível carregar seu histórico." : null,
    errorTimestamp: error ? new Date().toISOString() : null,
    refresh: () => mutate(),
    silentRefresh: () => mutate(undefined, { revalidate: true }),
  };
}
