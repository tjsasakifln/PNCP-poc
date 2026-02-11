"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../app/components/AuthProvider";

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
  refresh: () => Promise<void>;
}

const CACHE_KEY = "smartlic_cached_plan";
const CACHE_TTL = 3600000; // 1 hour in milliseconds

interface CachedPlan {
  data: PlanInfo;
  timestamp: number;
}

/**
 * Hook to fetch user's plan information and capabilities.
 * Replaces useQuota for new plan-based pricing system.
 * Includes localStorage caching to prevent transient backend errors from downgrading paid users.
 */
export function usePlan(): UsePlanReturn {
  const { session, user } = useAuth();
  const [planInfo, setPlanInfo] = useState<PlanInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlanInfo = useCallback(async () => {
    if (!session?.access_token || !user) {
      setPlanInfo(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/me", {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Erro ao carregar informações do plano");
      }

      const data: PlanInfo = await response.json();

      // Check if backend returned degraded data (free_trial) but we have a cached paid plan
      if (data.plan_id === "free_trial" && typeof window !== "undefined") {
        try {
          const cached = localStorage.getItem(CACHE_KEY);
          if (cached) {
            const parsedCache: CachedPlan = JSON.parse(cached);
            const cacheAge = Date.now() - parsedCache.timestamp;

            // If cache is valid (< 1 hour) and contains a paid plan, use cached data
            if (
              cacheAge < CACHE_TTL &&
              parsedCache.data.plan_id !== "free_trial" &&
              parsedCache.data.plan_id !== "free"
            ) {
              console.warn(
                "[usePlan] Backend returned free_trial but cached paid plan exists. Using cached data to prevent transient downgrade.",
                {
                  cachedPlan: parsedCache.data.plan_id,
                  cacheAge: Math.round(cacheAge / 1000) + "s",
                }
              );
              setPlanInfo(parsedCache.data);
              setLoading(false);
              return;
            }
          }
        } catch (cacheErr) {
          console.error("[usePlan] Error reading cache:", cacheErr);
        }
      }

      // If data is from a paid plan (not free_trial, not free), cache it
      if (data.plan_id !== "free_trial" && data.plan_id !== "free" && typeof window !== "undefined") {
        try {
          const cacheData: CachedPlan = {
            data,
            timestamp: Date.now(),
          };
          localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
        } catch (cacheErr) {
          console.error("[usePlan] Error writing cache:", cacheErr);
        }
      }

      setPlanInfo(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Erro desconhecido";
      setError(errorMessage);
      setPlanInfo(null);
      console.error("Error fetching plan info:", err);
    } finally {
      setLoading(false);
    }
  }, [session, user]);

  useEffect(() => {
    fetchPlanInfo();
  }, [fetchPlanInfo]);

  return { planInfo, loading, error, refresh: fetchPlanInfo };
}
