"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../app/components/AuthProvider";

interface QuotaInfo {
  planId: string | null;
  planName: string | null;
  creditsRemaining: number | null; // null = unlimited
  totalSearches: number;
  isUnlimited: boolean;
  isFreeUser: boolean;
  isAdmin: boolean;
}

interface UseQuotaReturn {
  quota: QuotaInfo | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const FREE_SEARCHES_LIMIT = 3;
const UNLIMITED_THRESHOLD = 999990; // Lowered threshold to catch near-unlimited values

export function useQuota(): UseQuotaReturn {
  const { session, user } = useAuth();
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuota = useCallback(async () => {
    if (!session?.access_token || !user) {
      setQuota(null);
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
        throw new Error("Erro ao carregar informacoes de quota");
      }

      const data = await response.json();

      // New format: UserProfileResponse has fields at root level
      const planId = data.plan_id;
      const planName = data.plan_name;
      const quotaRemaining = data.quota_remaining;
      const quotaUsed = data.quota_used || 0;
      const isAdmin = data.is_admin === true;

      // Free user detection: plan_id starts with "free" and not admin
      const isFreeUser = !isAdmin && (planId === "free" || planId === "free_trial");

      // Detect unlimited users (admins, masters, sala_guerra, or very high quota)
      // NOTE: Free users are NEVER unlimited - they have 3 free searches
      const isUnlimited = !isFreeUser && (quotaRemaining >= UNLIMITED_THRESHOLD || isAdmin);

      // Calculate credits remaining for display:
      // - Unlimited users: null (show plan badge instead of count)
      // - Free users: Always show FREE_SEARCHES_LIMIT - quotaUsed (handles stale backend data)
      // - Paid users: Show actual quotaRemaining from backend
      let creditsRemaining: number | null = null;
      if (isFreeUser) {
        // Free users always get 3 free searches, calculate remaining based on usage
        // This handles both correctly configured backend (max=3) and stale data (max=999999)
        creditsRemaining = Math.max(0, FREE_SEARCHES_LIMIT - quotaUsed);
      } else if (!isUnlimited) {
        creditsRemaining = quotaRemaining;
      }

      setQuota({
        planId,
        planName,
        creditsRemaining,
        totalSearches: quotaUsed,
        isUnlimited,
        isFreeUser,
        isAdmin,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
      setQuota(null);
    } finally {
      setLoading(false);
    }
  }, [session, user]);

  useEffect(() => {
    fetchQuota();
  }, [fetchQuota]);

  return { quota, loading, error, refresh: fetchQuota };
}
