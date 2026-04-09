"use client";

import { useEffect } from "react";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useClarity } from "@/hooks/useClarity";

/**
 * SEO-PLAYBOOK P6: Client island to track analysis_viewed event on page load.
 *
 * Also emits `first_analysis_viewed` exactly once per browser (localStorage
 * flag) — this is the "aha moment" event defined in the playbook §Day-3
 * activation. It is the single strongest predictor of trial→paid conversion.
 */
const FIRST_ANALYSIS_FLAG = "smartlic-first-analysis-fired";

export function AnalysisViewTracker({
  hash,
  viabilityScore,
  bidUf,
}: {
  hash: string;
  viabilityScore: number;
  bidUf: string | null;
}) {
  const { trackEvent } = useAnalytics();
  const { clarityEvent, claritySet } = useClarity();

  useEffect(() => {
    trackEvent("analysis_viewed", {
      hash,
      viability_score: viabilityScore,
      uf: bidUf || "",
    });
    claritySet("viability_score", String(viabilityScore));

    // Emit first_analysis_viewed exactly once per browser — the Day-3
    // activation predictor. localStorage is acceptable here because the
    // event is directional (first-time signal), not a strict audit trail.
    try {
      if (typeof window !== "undefined" && !localStorage.getItem(FIRST_ANALYSIS_FLAG)) {
        trackEvent("first_analysis_viewed", {
          hash,
          viability_score: viabilityScore,
          uf: bidUf || "",
        });
        clarityEvent("first_analysis_viewed");
        localStorage.setItem(FIRST_ANALYSIS_FLAG, new Date().toISOString());
      }
    } catch {
      // localStorage disabled (Safari private mode, strict cookies) — skip.
    }
  }, [hash, viabilityScore, bidUf, trackEvent, clarityEvent, claritySet]);

  return null;
}
