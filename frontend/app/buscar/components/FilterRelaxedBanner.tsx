"use client";

import { useState } from "react";

export interface FilterRelaxedBannerProps {
  /** What level of relaxation was applied */
  relaxationLevel?: string;
  /** How many results existed before relaxation */
  originalCount: number;
  /** How many results exist after relaxation */
  relaxedCount: number;
}

/**
 * STAB-005 AC4: Blue informational banner shown when filter relaxation was applied.
 * Dismissible via X button.
 */
export function FilterRelaxedBanner({
  relaxationLevel,
  originalCount,
  relaxedCount,
}: FilterRelaxedBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const relaxationMessage = getRelaxationMessage(relaxationLevel);

  return (
    <div
      className="mt-4 p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 flex items-start gap-3"
      role="status"
      data-testid="filter-relaxed-banner"
    >
      {/* Info icon */}
      <svg
        className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
          Resultados com filtro ampliado
        </p>
        <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
          {relaxationMessage}
        </p>
        {originalCount === 0 && relaxedCount > 0 && (
          <p className="text-xs text-blue-500 dark:text-blue-500 mt-1">
            {relaxedCount} {relaxedCount === 1 ? "resultado encontrado" : "resultados encontrados"} com critérios ampliados.
          </p>
        )}
      </div>

      {/* Dismiss button */}
      <button
        onClick={() => setDismissed(true)}
        className="flex-shrink-0 p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-800/30 transition-colors"
        aria-label="Fechar banner"
        data-testid="filter-relaxed-dismiss"
      >
        <svg
          className="w-4 h-4 text-blue-500 dark:text-blue-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}

function getRelaxationMessage(level?: string): string {
  switch (level) {
    case "keywords_relaxed":
      return "Incluímos licitações com menor correspondência de palavras-chave para ampliar seus resultados.";
    case "value_range_expanded":
      return "A faixa de valor foi ampliada para incluir mais oportunidades.";
    case "min_match_lowered":
      return "O limite mínimo de correspondência foi reduzido para mostrar mais resultados.";
    default:
      return "Os critérios de filtragem foram ampliados para incluir mais oportunidades relevantes.";
  }
}
