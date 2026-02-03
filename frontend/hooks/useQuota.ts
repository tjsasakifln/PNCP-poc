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
}

interface UseQuotaReturn {
  quota: QuotaInfo | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const FREE_SEARCHES_LIMIT = 3;

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

      const subscription = data.subscription;
      const totalSearches = data.total_searches || 0;

      if (subscription) {
        const plan = subscription.plans;
        const creditsRemaining = subscription.credits_remaining;
        const isUnlimited = creditsRemaining === null;

        setQuota({
          planId: subscription.plan_id,
          planName: plan?.name || subscription.plan_id,
          creditsRemaining: creditsRemaining,
          totalSearches,
          isUnlimited,
          isFreeUser: false,
        });
      } else {
        // Free tier
        const remaining = Math.max(0, FREE_SEARCHES_LIMIT - totalSearches);
        setQuota({
          planId: "free",
          planName: "Gratuito",
          creditsRemaining: remaining,
          totalSearches,
          isUnlimited: false,
          isFreeUser: true,
        });
      }
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
