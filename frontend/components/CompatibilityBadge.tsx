import React from "react";

interface CompatibilityBadgeProps {
  compatibilidade_pct?: number | null;
}

/**
 * STORY-259: Badge showing compatibility percentage for a bid.
 * Green (emerald) >= 70%, Yellow (amber) 40-69%, Gray (slate) < 40%.
 */
export default function CompatibilityBadge({ compatibilidade_pct }: CompatibilityBadgeProps) {
  if (compatibilidade_pct == null) return null;

  const pct = Math.round(compatibilidade_pct);

  let colorClasses: string;
  let label: string;

  if (pct >= 70) {
    colorClasses =
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300";
    label = "Alta compatibilidade";
  } else if (pct >= 40) {
    colorClasses =
      "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300";
    label = "Média compatibilidade";
  } else {
    colorClasses =
      "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400";
    label = "Baixa compatibilidade";
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-semibold ${colorClasses}`}
      title={`Compatibilidade: ${pct}% — ${label}`}
      aria-label={`${pct}% de compatibilidade — ${label}`}
      role="img"
      data-testid="compatibility-badge"
      data-compatibility-pct={pct}
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
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      {pct}% compat.
    </span>
  );
}
