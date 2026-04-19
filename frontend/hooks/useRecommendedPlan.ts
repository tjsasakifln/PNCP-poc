/**
 * STORY-BIZ-002: fetch the authenticated user's plan recommendation.
 *
 * Wraps GET /api/user/recommended-plan (which proxies /v1/user/recommended-plan).
 * Backend response is cached in Redis for 24h per user, so it's safe to call
 * on every mount — latency is < 20ms after first call.
 */
import { useEffect, useState } from 'react';

export type RecommendedPlan = {
  plan_key: 'consultoria' | 'smartlic_pro';
  reason: 'cnae_consultoria' | 'default';
};

interface UseRecommendedPlanResult {
  data: RecommendedPlan | null;
  loading: boolean;
  error: string | null;
}

export function useRecommendedPlan(): UseRecommendedPlanResult {
  const [data, setData] = useState<RecommendedPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch('/api/user/recommended-plan', { credentials: 'include' })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as RecommendedPlan;
      })
      .then((json) => {
        if (cancelled) return;
        setData(json);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'unknown');
        setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error };
}
