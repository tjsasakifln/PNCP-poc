/**
 * Reliability score calculation for search results (GTM-RESILIENCE-A05 AC9).
 *
 * Score = coverage (50%) + freshness (30%) + method (20%)
 * Labels: "Alta" (>0.8), "Media" (0.5-0.8), "Baixa" (<0.5)
 */

export type ReliabilityLevel = "Alta" | "Media" | "Baixa";

export type ResponseMethod = "live" | "cache_fresh" | "cache_stale";

export interface ReliabilityResult {
  score: number;
  level: ReliabilityLevel;
}

/**
 * Calculate freshness score based on minutes since last update.
 * < 5 min = 1.0, < 60 min = 0.7, < 360 min (6h) = 0.4, > 360 min = 0.1
 */
export function freshnessScore(minutesSinceUpdate: number): number {
  if (minutesSinceUpdate < 5) return 1.0;
  if (minutesSinceUpdate < 60) return 0.7;
  if (minutesSinceUpdate < 360) return 0.4;
  return 0.1;
}

/**
 * Calculate method score based on how data was obtained.
 * live = 1.0, cache_fresh = 0.8, cache_stale = 0.4
 */
export function methodScore(method: ResponseMethod): number {
  switch (method) {
    case "live": return 1.0;
    case "cache_fresh": return 0.8;
    case "cache_stale": return 0.4;
    default: return 0.4;
  }
}

/**
 * Map response_state + cache_status to a ResponseMethod.
 */
export function deriveMethod(
  responseState?: string,
  cacheStatus?: string,
): ResponseMethod {
  if (!responseState || responseState === "live" || responseState === "degraded") {
    return "live";
  }
  if (responseState === "cached") {
    return cacheStatus === "fresh" ? "cache_fresh" : "cache_stale";
  }
  // empty_failure — worst case
  return "cache_stale";
}

/**
 * Calculate reliability score and level.
 *
 * @param coveragePct Coverage percentage (0-100)
 * @param minutesSinceUpdate Minutes since last data update
 * @param method How data was obtained
 */
export function calculateReliability(
  coveragePct: number,
  minutesSinceUpdate: number,
  method: ResponseMethod,
): ReliabilityResult {
  const coverageNorm = Math.min(Math.max(coveragePct, 0), 100) / 100;
  const fresh = freshnessScore(minutesSinceUpdate);
  const meth = methodScore(method);

  const score = coverageNorm * 0.5 + fresh * 0.3 + meth * 0.2;

  let level: ReliabilityLevel;
  if (score > 0.8) {
    level = "Alta";
  } else if (score >= 0.5) {
    level = "Media";
  } else {
    level = "Baixa";
  }

  return { score: Math.round(score * 100) / 100, level };
}

/**
 * Calculate minutes since a given ISO timestamp.
 */
export function minutesSince(isoTimestamp: string): number {
  const then = new Date(isoTimestamp).getTime();
  const now = Date.now();
  return Math.max(0, Math.floor((now - then) / 60000));
}
