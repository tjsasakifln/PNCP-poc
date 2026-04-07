"use client";

import useSWR from "swr";
import { useAuth } from "../app/components/AuthProvider";

interface ExperimentsResponse {
  experiments: Record<string, string>;
}

const fetcher = async (url: string, token: string): Promise<ExperimentsResponse> => {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return { experiments: {} };
  return res.json();
};

/**
 * Hook to fetch active A/B experiment variants for the current user.
 * Returns deterministic variant assignments (same user always gets same variant).
 */
export function useExperiments() {
  const { session } = useAuth();
  const token = session?.access_token;

  const { data } = useSWR<ExperimentsResponse>(
    token ? ["/api/experiments", token] : null,
    ([url, t]: [string, string]) => fetcher(url, t),
    {
      revalidateOnFocus: false,
      dedupingInterval: 300_000, // 5 min cache
    }
  );

  const experiments = data?.experiments ?? {};

  /**
   * Get the variant for a specific experiment.
   * Returns null if experiment is not active.
   */
  function getVariant(experiment: string): string | null {
    return experiments[experiment] ?? null;
  }

  /**
   * Get all experiment variants as a flat object for analytics enrichment.
   */
  function getExperimentProperties(): Record<string, string> {
    const props: Record<string, string> = {};
    for (const [exp, variant] of Object.entries(experiments)) {
      props[`exp_${exp}`] = variant;
    }
    return props;
  }

  return {
    experiments,
    getVariant,
    getExperimentProperties,
    isLoaded: !!data,
  };
}
