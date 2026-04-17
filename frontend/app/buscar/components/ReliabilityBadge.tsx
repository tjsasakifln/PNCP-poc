import React from "react";

import {
  calculateReliability,
  deriveMethod,
  minutesSince,
  type ReliabilityLevel,
} from "../utils/reliability";

export interface ReliabilityBadgeProps {
  coveragePct: number;
  timestamp?: string;
  responseState?: "live" | "cached" | "degraded" | "empty_failure";
  cacheStatus?: "fresh" | "stale";
}

const levelStyles: Record<ReliabilityLevel, string> = {
  Alta: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
  "Média": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  Baixa: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
};

/** DEBT-FE-018: Level-specific icons for WCAG 1.4.1 (Use of Color) compliance */
const levelIcons: Record<ReliabilityLevel, React.ReactNode> = {
  Alta: (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  "Média": (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M12 3l9.66 16.59A1 1 0 0120.66 21H3.34a1 1 0 01-.86-1.41L12 3z" />
    </svg>
  ),
  Baixa: (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
};

export function ReliabilityBadge({
  coveragePct,
  timestamp,
  responseState,
  cacheStatus,
}: ReliabilityBadgeProps) {
  const minutes = timestamp ? minutesSince(timestamp) : 0;
  const method = deriveMethod(responseState, cacheStatus);
  const { score, level } = calculateReliability(coveragePct, minutes, method);

  return (
    <span
      role="img"
      aria-label={`Relevancia ${level} (${Math.round(score * 100)}%)`}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${levelStyles[level]}`}
      data-testid="reliability-badge"
      data-reliability-level={level}
    >
      {levelIcons[level]}
      {level}
    </span>
  );
}
