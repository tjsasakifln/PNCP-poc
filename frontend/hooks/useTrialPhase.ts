"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../app/components/AuthProvider";

/**
 * STORY-320 AC11: Trial phase information for soft paywall.
 */
export interface TrialPhaseInfo {
  /** "full_access" (days 1-7) | "limited_access" (days 8-14) | "not_trial" (paid user) */
  phase: "full_access" | "limited_access" | "not_trial";
  /** Current day of trial (1-indexed) */
  day: number;
  /** Days remaining in trial */
  daysRemaining: number;
  /** Whether data is loading */
  loading: boolean;
}

const SESSION_CACHE_KEY = "smartlic_trial_phase";
const CACHE_TTL = 300_000; // 5 minutes

interface CachedPhase {
  phase: string;
  day: number;
  daysRemaining: number;
  cachedAt: number;
}

function getCachedPhase(): CachedPhase | null {
  if (typeof window === "undefined") return null;
  try {
    const cached = sessionStorage.getItem(SESSION_CACHE_KEY);
    if (!cached) return null;
    const parsed: CachedPhase = JSON.parse(cached);
    if (Date.now() - parsed.cachedAt >= CACHE_TTL) return null;
    return parsed;
  } catch {
    return null;
  }
}

function setCachedPhase(phase: string, day: number, daysRemaining: number): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(
      SESSION_CACHE_KEY,
      JSON.stringify({ phase, day, daysRemaining, cachedAt: Date.now() })
    );
  } catch {
    // ignore
  }
}

/**
 * Hook that fetches trial phase from /v1/trial-status and caches in sessionStorage.
 * Returns "not_trial" for paid users, "full_access" for days 1-7, "limited_access" for days 8+.
 */
export function useTrialPhase(): TrialPhaseInfo {
  const { session } = useAuth();
  const [info, setInfo] = useState<TrialPhaseInfo>({
    phase: "full_access",
    day: 0,
    daysRemaining: 999,
    loading: true,
  });

  const fetchPhase = useCallback(async () => {
    if (!session?.access_token) {
      setInfo({ phase: "full_access", day: 0, daysRemaining: 999, loading: false });
      return;
    }

    // Check sessionStorage cache first
    const cached = getCachedPhase();
    if (cached) {
      setInfo({
        phase: cached.phase as TrialPhaseInfo["phase"],
        day: cached.day,
        daysRemaining: cached.daysRemaining,
        loading: false,
      });
      return;
    }

    try {
      const res = await fetch("/api/trial-status", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!res.ok) {
        setInfo({ phase: "full_access", day: 0, daysRemaining: 999, loading: false });
        return;
      }

      const data = await res.json();
      const phase = data.trial_phase || "full_access";
      const day = data.trial_day || 0;
      const daysRemaining = data.days_remaining || 0;

      setCachedPhase(phase, day, daysRemaining);

      setInfo({
        phase: phase as TrialPhaseInfo["phase"],
        day,
        daysRemaining,
        loading: false,
      });
    } catch {
      setInfo({ phase: "full_access", day: 0, daysRemaining: 999, loading: false });
    }
  }, [session?.access_token]);

  useEffect(() => {
    fetchPhase();
  }, [fetchPhase]);

  return info;
}
