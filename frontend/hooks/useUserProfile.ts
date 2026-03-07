"use client";

import useSWR from "swr";
import { useAuth } from "../app/components/AuthProvider";
import { FetchError } from "../lib/fetcher";
import { safeSetItem } from "../lib/storage";

/**
 * TD-008 AC3: SWR-based /api/me hook.
 * Replaces manual fetch in usePlan + useQuota with SWR deduplication.
 * Preserves CRIT-028 "fail to last known plan" behavior via onError fallback.
 */

const CACHE_KEY = "smartlic_cached_plan";
const CACHE_TTL = 3600000; // 1 hour

interface CachedProfile {
  data: Record<string, unknown>;
  timestamp: number;
}

function getCachedProfile(): CachedProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;
    const parsed: CachedProfile = JSON.parse(cached);
    if (Date.now() - parsed.timestamp >= CACHE_TTL) return null;
    return parsed;
  } catch {
    return null;
  }
}

function setCachedProfile(data: Record<string, unknown>): void {
  if (typeof window === "undefined") return;
  try {
    safeSetItem(
      CACHE_KEY,
      JSON.stringify({ data, timestamp: Date.now() })
    );
  } catch {
    // Ignore storage errors
  }
}

const fetchWithAuth = async (url: string, token: string) => {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new FetchError(`HTTP ${res.status}`, res.status);
  }
  return res.json();
};

export function useUserProfile() {
  const { session, user } = useAuth();
  const accessToken = session?.access_token;
  const userId = user?.id;

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    accessToken && userId ? ["/api/me", accessToken] : null,
    ([url, token]: [string, string]) => fetchWithAuth(url, token),
    {
      revalidateOnFocus: false,
      dedupingInterval: 10000,
      errorRetryCount: 3,
      onSuccess: (data) => {
        // CRIT-028: Cache paid plans for fallback
        if (data?.plan_id && data.plan_id !== "free_trial" && data.plan_id !== "free") {
          setCachedProfile(data);
        }
      },
      onError: () => {
        // Fallback handled via fallbackData pattern below
      },
    }
  );

  // CRIT-028 AC1-AC2: On error, fall back to cached profile
  const isFromCache = !data && !!error;
  const cachedProfile = isFromCache ? getCachedProfile() : null;
  const effectiveData = data || cachedProfile?.data || null;

  // CRIT-028: Degradation detection — backend returned free_trial but cached paid plan exists
  const resolvedData = (() => {
    if (!effectiveData) return null;
    if (
      (effectiveData as Record<string, unknown>).plan_id === "free_trial"
    ) {
      const cached = getCachedProfile();
      if (
        cached &&
        cached.data.plan_id !== "free_trial" &&
        cached.data.plan_id !== "free"
      ) {
        return cached.data;
      }
    }
    return effectiveData;
  })();

  return {
    data: resolvedData as Record<string, unknown> | null,
    error: error as FetchError | null,
    isLoading,
    isValidating,
    isFromCache: !!cachedProfile && !data,
    cachedAt: cachedProfile?.timestamp ?? null,
    mutate,
  };
}
