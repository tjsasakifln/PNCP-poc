"use client";

import { useState } from "react";
import type { DataSourceStatus } from "../../types";

// ---------------------------------------------------------------------------
// STORY-252 AC21-AC23: Degradation banners for partial / failed data sources
// ---------------------------------------------------------------------------

interface DegradationBannerProps {
  /** Banner variant */
  variant: "warning" | "error";
  /** Primary message to display */
  message: string;
  /** Optional secondary explanation */
  detail?: string;
  /** Per-source status breakdown (for collapsible details) */
  dataSources?: DataSourceStatus[];
  /** Show retry button (AC22) */
  showRetry?: boolean;
  /** Retry handler */
  onRetry?: () => void;
  /** Whether a search is currently in progress */
  loading?: boolean;
}

/** Human-readable labels for source status */
function sourceStatusLabel(status: DataSourceStatus["status"]): {
  label: string;
  className: string;
} {
  switch (status) {
    case "ok":
      return { label: "Respondeu", className: "text-green-700 dark:text-green-400" };
    case "timeout":
      return { label: "Timeout", className: "text-yellow-700 dark:text-yellow-400" };
    case "error":
      return { label: "Erro", className: "text-red-700 dark:text-red-400" };
    case "skipped":
      return { label: "Ignorada", className: "text-gray-500 dark:text-gray-400" };
    default:
      return { label: status, className: "text-ink-secondary" };
  }
}

/** Human-readable name for data source codes */
function sourceDisplayName(source: string): string {
  const names: Record<string, string> = {
    pncp: "Fonte principal",
    compras_gov: "Fonte secundária",
    transparencia: "Fonte complementar",
    querido_diario: "Diários oficiais",
  };
  return names[source] || "Fonte de dados";
}

export function DegradationBanner({
  variant,
  message,
  detail,
  dataSources,
  showRetry = false,
  onRetry,
  loading = false,
}: DegradationBannerProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  const isWarning = variant === "warning";
  const containerClass = isWarning
    ? "bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700/40"
    : "bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700/40";
  const iconColor = isWarning
    ? "text-yellow-600 dark:text-yellow-400"
    : "text-red-600 dark:text-red-400";
  const textColor = isWarning
    ? "text-yellow-800 dark:text-yellow-200"
    : "text-red-800 dark:text-red-200";
  const detailColor = isWarning
    ? "text-yellow-700 dark:text-yellow-300"
    : "text-red-700 dark:text-red-300";

  return (
    <div
      className={`mt-6 sm:mt-8 rounded-card p-4 sm:p-5 animate-fade-in-up ${containerClass}`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        {isWarning ? (
          <svg
            className={`w-5 h-5 flex-shrink-0 mt-0.5 ${iconColor}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        ) : (
          <svg
            className={`w-5 h-5 flex-shrink-0 mt-0.5 ${iconColor}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        )}

        <div className="flex-1 min-w-0">
          {/* Primary message */}
          <p className={`text-sm sm:text-base font-medium ${textColor}`}>
            {message}
          </p>

          {/* Optional detail text */}
          {detail && (
            <p className={`text-sm mt-1 ${detailColor}`}>{detail}</p>
          )}

          {/* Collapsible data source details (AC21) */}
          {dataSources && dataSources.length > 0 && (
            <details
              className="mt-3 cursor-pointer group"
              open={detailsOpen}
              onToggle={(e) =>
                setDetailsOpen((e.target as HTMLDetailsElement).open)
              }
            >
              <summary
                className={`text-sm font-medium list-none flex items-center gap-2 select-none ${detailColor} hover:underline`}
              >
                <svg
                  className="w-4 h-4 transition-transform group-open:rotate-90"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
                Detalhes por fonte de dados
              </summary>

              <div className="mt-2 ml-6 space-y-1.5">
                {dataSources.map((ds) => {
                  const { label, className } = sourceStatusLabel(ds.status);
                  return (
                    <div
                      key={ds.source}
                      className="flex items-center justify-between text-sm py-1"
                    >
                      <span className={textColor}>
                        {sourceDisplayName(ds.source)}
                      </span>
                      <span className="flex items-center gap-3">
                        <span className={`font-medium ${className}`}>
                          {label}
                        </span>
                        {ds.status === "ok" && (
                          <span className="text-xs text-ink-muted tabular-nums">
                            {ds.records.toLocaleString("pt-BR")}{" "}
                            {ds.records === 1 ? "registro" : "registros"}
                          </span>
                        )}
                      </span>
                    </div>
                  );
                })}
              </div>
            </details>
          )}

          {/* Retry button (AC22) */}
          {showRetry && onRetry && (
            <button
              onClick={onRetry}
              disabled={loading}
              className={`mt-4 px-4 py-2 rounded-button text-sm font-medium transition-all flex items-center gap-2 ${
                isWarning
                  ? "bg-yellow-600 hover:bg-yellow-700 text-white disabled:bg-yellow-400"
                  : "bg-red-600 hover:bg-red-700 text-white disabled:bg-red-400"
              } disabled:cursor-not-allowed`}
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-4 w-4"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Tentando...
                </>
              ) : (
                "Tentar novamente"
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default DegradationBanner;
