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

/**
 * Hook to fetch user's plan information and capabilities.
 * Replaces useQuota for new plan-based pricing system.
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
