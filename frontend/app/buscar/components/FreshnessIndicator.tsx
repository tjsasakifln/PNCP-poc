"use client";

import { useState, useEffect } from "react";

export type FreshnessType = "live" | "cached_fresh" | "cached_stale";

export interface FreshnessIndicatorProps {
  /** ISO timestamp of when data was obtained */
  timestamp: string;
  /** Freshness type from CoverageMetadata */
  freshness?: FreshnessType;
  /** Whether CacheBanner is already visible */
  cacheBannerVisible?: boolean;
}

export function formatRelativeTimePtBr(isoTimestamp: string): string {
  const then = new Date(isoTimestamp).getTime();
  const now = Date.now();
  const diffMs = Math.max(0, now - then);
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return "agora";
  if (diffMin < 60) {
    return `há ${diffMin} minuto${diffMin > 1 ? "s" : ""}`;
  }
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) {
    return `há ${diffHours} hora${diffHours > 1 ? "s" : ""}`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `há ${diffDays} dia${diffDays > 1 ? "s" : ""}`;
}

function getFreshnessConfig(freshness: FreshnessType) {
  switch (freshness) {
    case "live":
      return {
        dotClass: "bg-green-500 animate-pulse",
        badgeClass: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
        label: "Dados de agora",
      };
    case "cached_fresh":
      return {
        dotClass: "bg-green-500",
        badgeClass: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
        label: null, // Will be "Dados de há X minutos"
      };
    case "cached_stale":
      return {
        dotClass: "bg-amber-500",
        badgeClass: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
        label: null, // Will be "Dados de há X horas"
      };
  }
}

export function FreshnessIndicator({
  timestamp,
  freshness = "live",
  cacheBannerVisible = false,
}: FreshnessIndicatorProps) {
  const [relativeTime, setRelativeTime] = useState(() => formatRelativeTimePtBr(timestamp));

  useEffect(() => {
    setRelativeTime(formatRelativeTimePtBr(timestamp));
    const interval = setInterval(() => {
      setRelativeTime(formatRelativeTimePtBr(timestamp));
    }, 60000);
    return () => clearInterval(interval);
  }, [timestamp]);

  const config = getFreshnessConfig(freshness);
  const displayLabel = config.label || `Dados de ${relativeTime}`;

  // AC8: When CacheBanner is visible for cache scenarios, show minimal indicator
  if (cacheBannerVisible && freshness !== "live") {
    return (
      <span
        className="inline-flex items-center gap-1.5 text-xs text-ink-secondary"
        data-testid="freshness-indicator"
        aria-label={`${displayLabel}`}
      >
        <span className={`w-2 h-2 rounded-full shrink-0 ${config.dotClass}`} aria-hidden="true" />
        Cache
      </span>
    );
  }

  const ariaLabel = freshness === "live"
    ? "Dados obtidos agora"
    : `Dados obtidos ${relativeTime}`;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.badgeClass}`}
      title={new Date(timestamp).toLocaleString("pt-BR")}
      data-testid="freshness-indicator"
      aria-label={ariaLabel}
    >
      <span
        className={`w-2 h-2 rounded-full shrink-0 ${config.dotClass}`}
        aria-hidden="true"
      />
      {displayLabel}
    </span>
  );
}
