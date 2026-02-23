"use client";

import { useCallback, useMemo, useEffect } from "react";
import { useAuth } from "../app/components/AuthProvider";
import { useFetchWithBackoff } from "./useFetchWithBackoff";

/**
 * Plan capabilities from backend PLAN_CAPABILITIES
 */
export interface PlanCapabilities {
  max_history_days: number;
  allow_excel: boolean;
  max_requests_per_month: number;
  max_requests_per_min: number;
  max_summary_tokens: number;
  priority: string;
}

/**
 * User plan information from /api/me endpoint
 */
export interface PlanInfo {
  user_id: string;
  email: string;
  plan_id: string;
  plan_name: string;
  capabilities: PlanCapabilities;
  quota_used: number;
  quota_remaining: number;
  quota_reset_date: string;
  trial_expires_at: string | null;
  subscription_status: string;
}

interface UsePlanReturn {
  planInfo: PlanInfo | null;
  loading: boolean;
  error: string | null;
  /** GTM-UX-004 AC2: true when planInfo came from localStorage cache fallback */
  isFromCache: boolean;
  /** GTM-UX-004 AC2: timestamp of when cached data was written (ms since epoch) */
  cachedAt: number | null;
  refresh: () => void;
}

const CACHE_KEY = "smartlic_cached_plan";
const CACHE_TTL = 3600000; // 1 hour in milliseconds

interface CachedPlan {
  data: PlanInfo;
  timestamp: number;
}

/** Read cached plan from localStorage (returns null if expired or missing) */
function getCachedPlan(): CachedPlan | null {
  if (typeof window === "undefined") return null;
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;
    const parsed: CachedPlan = JSON.parse(cached);
    if (Date.now() - parsed.timestamp >= CACHE_TTL) return null;
    return parsed;
  } catch {
    return null;
  }
}

/** Write plan to localStorage cache */
function setCachedPlan(plan: PlanInfo): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ data: plan, timestamp: Date.now() }));
  } catch {
    // Ignore storage errors
  }
}

/**
 * Hook to fetch user's plan information and capabilities.
 * CRIT-031 AC5-AC7: Uses useFetchWithBackoff for exponential backoff (max 3 retries, 2s→4s→8s).
 * CRIT-028: Falls back to cached plan on error (fail to last known plan).
 */
export function usePlan(): UsePlanReturn {
  const { session, user } = useAuth();

  // Use stable primitives to avoid re-fetch on object identity changes
  const accessToken = session?.access_token;
  const userId = user?.id;

  const fetchPlan = useCallback(
    async (signal: AbortSignal): Promise<PlanInfo | null> => {
      if (!accessToken || !userId) return null;

      const response = await fetch("/api/me", {
        headers: { Authorization: `Bearer ${accessToken}` },
        signal,
      });

      if (!response.ok) {
        throw new Error("Erro ao carregar informações do plano");
      }

      const data: PlanInfo = await response.json();

      // CRIT-028: Degradation detection — backend returned free_trial but cached paid plan exists
      if (data.plan_id === "free_trial") {
        const cached = getCachedPlan();
        if (cached && cached.data.plan_id !== "free_trial" && cached.data.plan_id !== "free") {
          console.warn(
            "[usePlan] Backend returned free_trial but cached paid plan exists. Using cached.",
            { cachedPlan: cached.data.plan_id }
          );
          return cached.data;
        }
      }

      // Cache paid plans for fallback
      if (data.plan_id !== "free_trial" && data.plan_id !== "free") {
        setCachedPlan(data);
      }

      return data;
    },
    [accessToken, userId]
  );

  // CRIT-031 AC5-AC7: Exponential backoff — max 3 retries (2s → 4s → 8s)
  const {
    data,
    loading,
    error: fetchError,
    manualRetry,
  } = useFetchWithBackoff<PlanInfo | null>(fetchPlan, {
    enabled: !!accessToken && !!userId,
    maxRetries: 3,
    initialDelayMs: 2000,
    maxDelayMs: 8000,
    timeoutMs: 10000,
  });

  // CRIT-028 AC1-AC2: On error, fall back to cached plan (fail to last known plan)
  // GTM-UX-004 AC2: Track whether data comes from cache + when it was cached
  const { effectivePlanInfo, isFromCache, cachedAt } = useMemo(() => {
    if (data) return { effectivePlanInfo: data, isFromCache: false, cachedAt: null };
    if (fetchError) {
      const cached = getCachedPlan();
      if (cached) {
        return { effectivePlanInfo: cached.data, isFromCache: true, cachedAt: cached.timestamp };
      }
    }
    return { effectivePlanInfo: null, isFromCache: false, cachedAt: null };
  }, [data, fetchError]);

  // CRIT-031 AC7: Limited console warnings (max 1 per error state change, not 12)
  useEffect(() => {
    if (fetchError && !data) {
      const cached = getCachedPlan();
      if (cached) {
        console.warn("[usePlan] Backend error — using cached plan info:", cached.data.plan_id);
      } else {
        // CRIT-028 AC6: Downgrade to warn to avoid console error spam
        console.warn("[usePlan] Failed to fetch plan info:", fetchError);
      }
    }
  }, [fetchError, data]);

  return {
    planInfo: effectivePlanInfo,
    loading,
    error: fetchError,
    isFromCache,
    cachedAt,
    refresh: manualRetry,
  };
}
