"use client";

import useSWR from "swr";
import { useAuth } from "../app/components/AuthProvider";
import { FetchError } from "../lib/fetcher";

/**
 * FE-007: SWR-based alerts hook.
 * Replaces manual fetch + useState + useEffect in alertas/page.tsx and AlertPreferences.tsx.
 */

export interface AlertFilters {
  setor: string;
  ufs: string[];
  valor_min: number | null;
  valor_max: number | null;
  keywords: string[];
}

export interface Alert {
  id: string;
  name: string;
  active: boolean;
  filters: AlertFilters;
  created_at: string;
  updated_at: string;
}

const fetchAlertsWithAuth = async (url: string, token: string) => {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  // UX-434: 404 means alerts feature is disabled — return empty array silently
  if (res.status === 404) {
    return [];
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new FetchError(
      data.message || `Erro ${res.status} ao carregar alertas`,
      res.status
    );
  }
  const data = await res.json();
  // Backend may return { alerts: [...] } or just [...]
  return Array.isArray(data) ? data : data.alerts || [];
};

export function useAlerts() {
  const { session } = useAuth();
  const accessToken = session?.access_token;

  const { data, error, isLoading, mutate } = useSWR(
    accessToken ? ["/api/alerts", accessToken] : null,
    ([url, token]: [string, string]) => fetchAlertsWithAuth(url, token),
    {
      revalidateOnFocus: false,
      dedupingInterval: 30_000,
      errorRetryCount: 2,
      // UX-434: Don't retry on 404 (feature disabled) — it's not transient
      shouldRetryOnError: (err: unknown) =>
        !(err instanceof FetchError && err.status === 404),
    }
  );

  return {
    alerts: (data ?? []) as Alert[],
    error: error instanceof FetchError ? error.message : error ? String(error) : null,
    isLoading,
    mutate,
    refresh: () => mutate(),
  };
}
