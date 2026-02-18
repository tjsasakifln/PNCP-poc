"use client";

// ---------------------------------------------------------------------------
// UX-303 AC5: Enhanced cache banner with fresh/stale distinction + cache level
// Built on STORY-257B AC8 foundation
// ---------------------------------------------------------------------------

/** Human-readable source name mapping */
const SOURCE_DISPLAY_NAMES: Record<string, string> = {
  PNCP: "PNCP",
  PORTAL_COMPRAS: "Portal de Compras Públicas",
  COMPRAS_GOV: "ComprasGov",
  pncp: "PNCP",
  portal_compras: "Portal de Compras Públicas",
  compras_gov: "ComprasGov",
};

export type CacheStatusType = "fresh" | "stale";

export interface CacheBannerProps {
  /** ISO timestamp of when cache was created */
  cachedAt: string;
  /** Refresh handler to fetch fresh data */
  onRefresh: () => void;
  /** Whether a refresh is currently in progress */
  refreshing: boolean;
  /** Source codes that contributed to cached data */
  cachedSources?: string[];
  /** Cache freshness status — green for fresh, amber for stale */
  cacheStatus?: CacheStatusType;
  /** Cache level that served the data */
  cacheLevel?: string;
}

/**
 * Format an ISO date as a human-readable relative time in Portuguese.
 * Examples: "há 30 minutos", "há 2 horas", "há 1 dia"
 */
function formatRelativeTime(isoDate: string): string {
  const now = new Date();
  const past = new Date(isoDate);
  const diffMs = now.getTime() - past.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  const rtf = new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" });

  if (diffDays > 0) {
    return rtf.format(-diffDays, "day");
  } else if (diffHours > 0) {
    return rtf.format(-diffHours, "hour");
  } else if (diffMinutes > 0) {
    return rtf.format(-diffMinutes, "minute");
  } else {
    return "há poucos segundos";
  }
}

export function CacheBanner({
  cachedAt,
  onRefresh,
  refreshing,
  cachedSources,
  cacheStatus,
  cacheLevel,
}: CacheBannerProps) {
  const relativeTime = formatRelativeTime(cachedAt);
  const sourceNames = cachedSources?.length
    ? cachedSources.map((s) => SOURCE_DISPLAY_NAMES[s] || s).join(" + ")
    : null;

  // AC5: Green for fresh, amber for stale (default to stale for backward compat)
  const isFresh = cacheStatus === "fresh";
  const bgColor = isFresh
    ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700/40"
    : "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-700/40";
  const textColor = isFresh
    ? "text-green-800 dark:text-green-200"
    : "text-amber-800 dark:text-amber-200";
  const iconColor = isFresh
    ? "text-green-600 dark:text-green-400"
    : "text-amber-600 dark:text-amber-400";
  const buttonColor = isFresh
    ? "bg-green-600 hover:bg-green-700 disabled:bg-green-400"
    : "bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400";

  return (
    <div
      className={`mt-6 sm:mt-8 rounded-card p-4 sm:p-5 border animate-fade-in-up ${bgColor}`}
      role="alert"
      aria-live="polite"
      data-testid="cache-banner"
      data-cache-status={cacheStatus || "stale"}
    >
      <div className="flex items-start gap-3">
        {/* Icon: checkmark for fresh, warning for stale */}
        {isFresh ? (
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
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
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
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        )}

        <div className="flex-1 min-w-0">
          {/* Primary message with relative time */}
          <p className={`text-sm sm:text-base font-medium ${textColor}`}>
            {isFresh ? (
              <>
                Resultados de <strong>{relativeTime}</strong>
                {sourceNames && <> ({sourceNames})</>}
                . Cache atualizado.
              </>
            ) : sourceNames ? (
              <>
                Resultados de <strong>{relativeTime}</strong>
                {sourceNames && <> ({sourceNames})</>}
                . Dados podem estar desatualizados.
              </>
            ) : (
              <>
                Nossas fontes estão temporariamente lentas. Mostrando resultados de{" "}
                <strong>{relativeTime}</strong>. Dados podem estar desatualizados.
              </>
            )}
          </p>

          {/* Refresh button — only show for stale */}
          {!isFresh && (
            <button
              onClick={onRefresh}
              disabled={refreshing}
              className={`mt-3 px-4 py-2 rounded-button text-sm font-medium transition-all flex items-center gap-2 text-white disabled:cursor-not-allowed ${buttonColor}`}
            >
              {refreshing ? (
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
                  Atualizando...
                </>
              ) : (
                "Tentar atualizar"
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default CacheBanner;
