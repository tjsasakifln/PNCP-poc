"use client";

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
  Media: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
  Baixa: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
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
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${levelStyles[level]}`}
      title={`Confiabilidade: ${level} (${Math.round(score * 100)}%)`}
    >
      <svg
        className="w-3 h-3"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
        />
      </svg>
      {level}
    </span>
  );
}
