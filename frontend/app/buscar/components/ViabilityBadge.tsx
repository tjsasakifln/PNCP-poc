"use client";

import React from "react";

/** D-04 AC1: Viability factor breakdown */
export interface ViabilityFactors {
  modalidade: number;
  modalidade_label: string;
  timeline: number;
  timeline_label: string;
  value_fit: number;
  value_fit_label: string;
  geography: number;
  geography_label: string;
}

interface ViabilityBadgeProps {
  level?: "alta" | "media" | "baixa" | null;
  score?: number | null;
  factors?: ViabilityFactors | null;
}

/** Factor label for tooltip display */
function factorLine(name: string, score: number, label: string): string {
  return `${name}: ${label} (${score}/100)`;
}

/** D-04 AC8: Viability badge with tooltip showing factor breakdown */
export default function ViabilityBadge({
  level,
  score,
  factors,
}: ViabilityBadgeProps) {
  if (!level) return null;

  const config: Record<
    string,
    {
      label: string;
      ariaLabel: string;
      bg: string;
    }
  > = {
    alta: {
      label: "Viabilidade alta",
      ariaLabel: "Viabilidade alta para sua empresa",
      bg: "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300",
    },
    media: {
      label: "Viabilidade média",
      ariaLabel: "Viabilidade média para sua empresa",
      bg: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300",
    },
    baixa: {
      label: "Viabilidade baixa",
      ariaLabel: "Viabilidade baixa para sua empresa",
      bg: "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400",
    },
  };

  const c = config[level];
  if (!c) return null;

  // Build tooltip with factor breakdown
  let tooltip = `Viabilidade: ${score ?? "?"}/100`;
  if (factors) {
    tooltip =
      `Viabilidade: ${score ?? "?"}/100\n` +
      factorLine("Modalidade", factors.modalidade, factors.modalidade_label) +
      "\n" +
      factorLine("Prazo", factors.timeline, factors.timeline_label) +
      "\n" +
      factorLine("Valor", factors.value_fit, factors.value_fit_label) +
      "\n" +
      factorLine("UF", factors.geography, factors.geography_label);
  }

  // Icon: chart bar for viability (distinct from shield for confidence)
  const icon = (
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
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  );

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${c.bg}`}
      title={tooltip}
      aria-label={c.ariaLabel}
      tabIndex={0}
      role="img"
      data-testid="viability-badge"
      data-viability-level={level}
    >
      {icon}
      {c.label}
    </span>
  );
}
