"use client";

import { useUserProfile } from "./useUserProfile";
import type { components } from "../app/api-types.generated";

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
 * STORY-2.1 (EPIC-TD-2026Q2): Base on the generated UserProfileResponse so
 * fields stay in sync with backend/schemas/user.py::UserProfileResponse,
 * then layer on the billing/dunning fields that the /api/me endpoint
 * returns (routes/user.py adds dunning_phase, days_since_failure,
 * subscription_end_date alongside the response_model). Fields are all
 * optional on the frontend side to tolerate the partial fallback payloads
 * served from localStorage cache (CRIT-028).
 */
type UserProfileResponse = components["schemas"]["UserProfileResponse"];

export type PlanInfo = Partial<Omit<UserProfileResponse, "capabilities" | "user_id" | "email" | "plan_id" | "plan_name">> & {
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
  dunning_phase: string;
  days_since_failure: number | null;
  subscription_end_date: string | null;
};

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

/**
 * TD-008 AC3: SWR-based plan hook.
 * Preserves CRIT-028 "fail to last known plan" + CRIT-031 exponential backoff via SWR retry.
 */
export function usePlan(): UsePlanReturn {
  const { data, error, isLoading, isFromCache, cachedAt, mutate } =
    useUserProfile();

  const planInfo: PlanInfo | null = data
    ? {
        user_id: (data.user_id as string) || "",
        email: (data.email as string) || "",
        plan_id: (data.plan_id as string) || "free_trial",
        plan_name: (data.plan_name as string) || "",
        capabilities: (data.capabilities as PlanCapabilities) || {
          max_history_days: 0,
          allow_excel: false,
          max_requests_per_month: 0,
          max_requests_per_min: 0,
          max_summary_tokens: 0,
          priority: "low",
        },
        quota_used: (data.quota_used as number) || 0,
        quota_remaining: (data.quota_remaining as number) || 0,
        quota_reset_date: (data.quota_reset_date as string) || "",
        trial_expires_at: (data.trial_expires_at as string) || null,
        subscription_status: (data.subscription_status as string) || "",
        dunning_phase: (data.dunning_phase as string) || "",
        days_since_failure: (data.days_since_failure as number) ?? null,
        subscription_end_date: (data.subscription_end_date as string) || null,
      }
    : null;

  return {
    planInfo,
    loading: isLoading,
    error: error ? "Erro ao carregar informações do plano" : null,
    isFromCache,
    cachedAt,
    refresh: () => mutate(),
  };
}
