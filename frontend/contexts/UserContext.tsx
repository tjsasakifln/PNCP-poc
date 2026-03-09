"use client";

import { createContext, useContext, useMemo, useCallback } from "react";
import { useAuth } from "../app/components/AuthProvider";
import { usePlan, type PlanInfo } from "../hooks/usePlan";
import { useQuota } from "../hooks/useQuota";
import { useTrialPhase, type TrialPhaseInfo } from "../hooks/useTrialPhase";

/**
 * DEBT-011 FE-006: Unified user context.
 * Composes auth + plan + quota + trial into a single context,
 * eliminating the need for pages to import 3-4 separate hooks.
 *
 * State updates propagate to all consumers via React Context.
 * SSE/search hooks remain as custom hooks (not global state).
 */

interface QuotaInfo {
  planId: string | null;
  planName: string | null;
  creditsRemaining: number | null;
  totalSearches: number;
  isUnlimited: boolean;
  isFreeUser: boolean;
  isAdmin: boolean;
  subscriptionStatus?: string;
  subscriptionEndDate?: string;
}

interface UserContextType {
  // Auth
  user: ReturnType<typeof useAuth>["user"];
  session: ReturnType<typeof useAuth>["session"];
  authLoading: boolean;
  isAdmin: boolean;
  sessionExpired: boolean;
  signOut: () => Promise<void>;

  // Plan
  planInfo: PlanInfo | null;
  planLoading: boolean;
  planError: string | null;
  isFromCache: boolean;
  cachedAt: number | null;

  // Quota
  quota: QuotaInfo | null;
  quotaLoading: boolean;

  // Trial
  trial: TrialPhaseInfo;

  // Unified refresh
  refresh: () => Promise<void>;
}

const UserContext = createContext<UserContextType | null>(null);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const plan = usePlan();
  const quota = useQuota();
  const trial = useTrialPhase();

  const refresh = useCallback(async () => {
    plan.refresh();
    await quota.refresh();
  }, [plan, quota]);

  const value = useMemo<UserContextType>(
    () => ({
      // Auth
      user: auth.user,
      session: auth.session,
      authLoading: auth.loading,
      isAdmin: auth.isAdmin,
      sessionExpired: auth.sessionExpired,
      signOut: auth.signOut,

      // Plan
      planInfo: plan.planInfo,
      planLoading: plan.loading,
      planError: plan.error,
      isFromCache: plan.isFromCache,
      cachedAt: plan.cachedAt,

      // Quota
      quota: quota.quota,
      quotaLoading: quota.loading,

      // Trial
      trial,

      // Unified refresh
      refresh,
    }),
    [auth, plan, quota, trial, refresh]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

/**
 * DEBT-011 FE-006: Single hook for all user state.
 * Replaces importing useAuth + usePlan + useQuota + useTrialPhase individually.
 */
export function useUser(): UserContextType {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}
