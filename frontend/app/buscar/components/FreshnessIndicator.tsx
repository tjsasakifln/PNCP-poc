"use client";

import { useState, useEffect } from "react";

export interface FreshnessIndicatorProps {
  timestamp: string;
}

function formatRelativeTime(isoTimestamp: string): string {
  const then = new Date(isoTimestamp).getTime();
  const now = Date.now();
  const diffMs = Math.max(0, now - then);
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return "agora";
  if (diffMin < 60) return `há ${diffMin} min`;

  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `há ${diffHours}h`;

  const diffDays = Math.floor(diffHours / 24);
  return `há ${diffDays} dia${diffDays > 1 ? "s" : ""}`;
}

export function FreshnessIndicator({ timestamp }: FreshnessIndicatorProps) {
  const [label, setLabel] = useState(() => formatRelativeTime(timestamp));

  useEffect(() => {
    setLabel(formatRelativeTime(timestamp));
    const interval = setInterval(() => {
      setLabel(formatRelativeTime(timestamp));
    }, 60000);
    return () => clearInterval(interval);
  }, [timestamp]);

  return (
    <span
      className="inline-flex items-center gap-1 text-xs text-ink-secondary"
      title={new Date(timestamp).toLocaleString("pt-BR")}
    >
      <svg
        className="w-3.5 h-3.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      {label}
    </span>
  );
}
