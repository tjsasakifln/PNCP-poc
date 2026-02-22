"use client";

import type { UfStatus, UfStatusType } from "../../../hooks/useSearchSSE";

// ---------------------------------------------------------------------------
// STORY-257B AC1-AC3: UF progress grid with real-time SSE updates
// ---------------------------------------------------------------------------

interface UfProgressGridProps {
  /** Map of UF abbreviations to their current status */
  ufStatuses: Map<string, UfStatus>;
  /** Total opportunities found across all UFs (for counter animation) */
  totalFound: number;
}

/** Visual configuration for each status type */
interface StatusConfig {
  bg: string;
  text: string;
  border: string;
  icon: React.ReactNode;
  label: (status: UfStatus) => string;
}

const statusConfigs: Record<UfStatusType, StatusConfig> = {
  pending: {
    bg: "bg-gray-50 dark:bg-gray-900/30",
    text: "text-gray-400 dark:text-gray-500",
    border: "border-gray-200 dark:border-gray-700",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    label: () => "Aguardando...",
  },
  fetching: {
    bg: "bg-blue-50 dark:bg-blue-900/20",
    text: "text-blue-600 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-700/40",
    icon: (
      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    ),
    label: () => "Consultando...",
  },
  retrying: {
    bg: "bg-amber-50 dark:bg-amber-900/20",
    text: "text-amber-600 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-700/40",
    icon: (
      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
    ),
    label: (status: UfStatus) => status.attempt ? `Tentativa ${status.attempt}...` : "Tentando novamente...",
  },
  success: {
    bg: "bg-emerald-50 dark:bg-emerald-900/20",
    text: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-700/40",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    label: (status: UfStatus) => {
      const count = status.count || 0;
      return count === 1 ? "1 oportunidade" : `${count} oportunidades`;
    },
  },
  failed: {
    bg: "bg-red-50 dark:bg-red-900/20",
    text: "text-red-400 dark:text-red-500",
    border: "border-red-200 dark:border-red-700/40",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    label: () => "Indisponível",
  },
  recovered: {
    bg: "bg-emerald-50 dark:bg-emerald-900/20",
    text: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-300 dark:border-emerald-600 border-2", // Thicker border to indicate recovery
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    label: (status: UfStatus) => {
      const count = status.count || 0;
      const countText = count === 1 ? "1 oportunidade" : `${count} oportunidades`;
      return `${countText} (recuperado)`;
    },
  },
};

export function UfProgressGrid({ ufStatuses, totalFound }: UfProgressGridProps) {
  // Convert Map to array for rendering, sorted by UF abbreviation
  const ufArray = Array.from(ufStatuses.entries()).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="mt-6 sm:mt-8 animate-fade-in-up">
      {/* Progressive results counter (AC3) */}
      <div className="mb-4 text-center">
        <p className="text-base sm:text-lg text-ink">
          Encontradas:{" "}
          <span className="font-display font-bold text-2xl sm:text-3xl text-ink tabular-nums transition-all duration-300">
            {totalFound.toLocaleString("pt-BR")}
          </span>
          {" "}
          <span className="text-ink-secondary">
            {totalFound === 1 ? "oportunidade" : "oportunidades"}
          </span>
          {" "}
          até agora
        </p>
      </div>

      {/* UF status grid (AC1) */}
      <div
        className="grid grid-cols-3 sm:grid-cols-6 xl:grid-cols-9 gap-2 sm:gap-3"
        role="status"
        aria-live="polite"
        aria-atomic="false"
      >
        {ufArray.map(([uf, status]) => {
          const config = statusConfigs[status.status] ?? statusConfigs.pending;

          return (
            <div
              key={uf}
              className={`
                rounded-card p-3 sm:p-4 border transition-all duration-200
                ${config.bg} ${config.border}
                hover:shadow-md hover:scale-105
              `}
              aria-label={`${uf}: ${config.label(status)}`}
            >
              <div className="flex flex-col items-center gap-2">
                {/* UF abbreviation */}
                <div className={`font-display font-bold text-lg sm:text-xl ${config.text}`}>
                  {uf}
                </div>

                {/* Status icon */}
                <div className={config.text}>
                  {config.icon}
                </div>

                {/* Status label */}
                <div className={`text-xs sm:text-sm text-center ${config.text} font-medium min-h-[2.5rem] flex items-center`}>
                  {config.label(status)}
                </div>

                {/* Badge for recovered status */}
                {status.status === 'recovered' && (
                  <div className="mt-1 px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-800/30 border border-emerald-300 dark:border-emerald-600">
                    <span className="text-[10px] sm:text-xs font-medium text-emerald-700 dark:text-emerald-300">
                      ✓ Recuperado
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default UfProgressGrid;
