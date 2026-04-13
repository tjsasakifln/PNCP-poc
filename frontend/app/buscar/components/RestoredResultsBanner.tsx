"use client";

/**
 * UX-432: Banner shown when search results are automatically restored after
 * the user navigates away from /buscar and returns within the 30-minute TTL.
 *
 * Provides a "Nova busca" escape hatch to discard the restored state and
 * start fresh.
 */

interface RestoredResultsBannerProps {
  sectorName: string;
  ufsLabel: string;
  onNovaBusca: () => void;
}

export function RestoredResultsBanner({
  sectorName,
  ufsLabel,
  onNovaBusca,
}: RestoredResultsBannerProps) {
  const label = sectorName && ufsLabel
    ? `${sectorName} em ${ufsLabel}`
    : sectorName || ufsLabel || "busca anterior";

  return (
    <div
      role="status"
      aria-live="polite"
      className="mb-4 p-4 rounded-lg bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 flex items-center justify-between gap-3"
    >
      <div className="flex items-center gap-3 min-w-0">
        {/* Clock icon */}
        <svg
          className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-sm font-medium text-blue-800 dark:text-blue-200 truncate">
          Resultados da busca anterior —{" "}
          <span className="font-semibold">{label}</span>
        </p>
      </div>
      <button
        onClick={onNovaBusca}
        className="px-3 py-1 text-xs font-medium rounded bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-700 transition-colors whitespace-nowrap flex-shrink-0"
        aria-label="Descartar resultados anteriores e iniciar nova busca"
      >
        Nova busca
      </button>
    </div>
  );
}
