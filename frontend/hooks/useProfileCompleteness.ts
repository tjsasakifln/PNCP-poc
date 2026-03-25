"use client";

import useSWR from "swr";
import { useAuth } from "../app/components/AuthProvider";
import { FetchError } from "../lib/fetcher";

/**
 * FE-007: SWR-based profile completeness hook.
 * Replaces manual fetch in dashboard/page.tsx.
 */

const fetchProfileCompletenessWithAuth = async (url: string, token: string) => {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  // UX-434: 404 means endpoint unavailable — return default data silently
  if (res.status === 404) {
    return { completeness_pct: null };
  }
  if (!res.ok) {
    throw new FetchError(`Erro ${res.status}`, res.status);
  }
  return res.json();
};

export function useProfileCompleteness() {
  const { session } = useAuth();
  const accessToken = session?.access_token;

  const { data, error, isLoading } = useSWR(
    accessToken ? ["/api/profile-completeness", accessToken] : null,
    ([url, token]: [string, string]) => fetchProfileCompletenessWithAuth(url, token),
    {
      revalidateOnFocus: false,
      dedupingInterval: 60_000, // 1 min — completeness rarely changes mid-session
      errorRetryCount: 1,
      // UX-434: Don't retry on 404 — it's not transient
      shouldRetryOnError: (err: unknown) =>
        !(err instanceof FetchError && err.status === 404),
    }
  );

  return {
    completenessPct: data?.completeness_pct ?? null,
    isLoading,
    error: error ? String(error) : null,
  };
}
