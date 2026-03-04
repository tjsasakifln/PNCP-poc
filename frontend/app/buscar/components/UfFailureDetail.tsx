"use client";

export interface UfFailureDetailProps {
  /** Brazilian state abbreviation (e.g., "SP", "RJ") */
  uf: string;
  /** Reason for the failure */
  reason: "timeout" | "rate_limit" | "offline" | "error";
  /** Data source name (e.g., "PNCP", "PCP", "ComprasGov") */
  source: string;
  /** Optional retry callback — shows retry button when provided */
  onRetry?: () => void;
}

/**
 * STAB-005 AC5: Per-UF failure message with contextual explanation and optional retry.
 */
export function UfFailureDetail({ uf, reason, source, onRetry }: UfFailureDetailProps) {
  const { message, icon } = getFailureConfig(uf, reason, source);

  return (
    <div
      className="flex items-center gap-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800"
      data-testid={`uf-failure-${uf}`}
      role="alert"
    >
      {/* Failure icon */}
      <div className="flex-shrink-0 text-red-500 dark:text-red-400">
        {icon}
      </div>

      {/* Message */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-red-800 dark:text-red-200">
          <span className="font-semibold">{uf}:</span> {message}
        </p>
      </div>

      {/* Retry button (optional) */}
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-md bg-red-100 dark:bg-red-800/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-800/50 transition-colors"
          data-testid={`uf-retry-${uf}`}
        >
          Tentar novamente
        </button>
      )}
    </div>
  );
}

interface FailureConfig {
  message: string;
  icon: React.ReactNode;
}

function getFailureConfig(uf: string, reason: string, source: string): FailureConfig {
  const iconSize = "w-5 h-5";

  switch (reason) {
    case "timeout":
      return {
        message: `${source} não respondeu para ${uf} (tempo esgotado)`,
        icon: (
          <svg className={iconSize} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
    case "rate_limit":
      return {
        message: `Taxa limite atingida para ${uf}`,
        icon: (
          <svg className={iconSize} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        ),
      };
    case "offline":
      return {
        message: `Fonte ${source} indisponível para ${uf}`,
        icon: (
          <svg className={iconSize} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m-2.829-2.829a5 5 0 000-7.07m-4.243 9.9a9 9 0 01-4.95-4.95M3 3l18 18" />
          </svg>
        ),
      };
    case "error":
    default:
      return {
        message: `Erro ao consultar ${uf}`,
        icon: (
          <svg className={iconSize} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ),
      };
  }
}
