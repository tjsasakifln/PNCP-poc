"use client";

import { useState, useEffect, useRef } from "react";

// ---------------------------------------------------------------------------
// GTM-UX-001: Unified DataQualityBanner
// Replaces 6-8 individual banners (CacheBanner, DegradationBanner,
// TruncationWarningBanner, OperationalStateBanner, PartialTimeoutBanner,
// RefreshBanner, SourcesUnavailable, FreshnessIndicator) with a single,
// priority-driven banner. Maximum 1 banner visible at a time (AC3).
// ---------------------------------------------------------------------------

// ============================================================================
// Types
// ============================================================================

export type BannerSeverity = "error" | "warning" | "info";

export interface DataQualityBannerProps {
  // UF coverage
  totalUfs: number;
  succeededUfs: number;
  failedUfs: string[];

  // Cache state
  isCached: boolean;
  cachedAt?: string | null;
  cacheStatus?: "fresh" | "stale";

  // Truncation
  isTruncated: boolean;

  // Sources
  sourcesTotal: number;
  sourcesAvailable: number;
  sourceNames?: string[];

  // Degradation / response state
  responseState?: "live" | "cached" | "degraded" | "empty_failure";
  coveragePct?: number;

  // Actions
  onRefresh: () => void;
  onRetry: () => void;
  loading: boolean;
}

// ============================================================================
// Helpers
// ============================================================================

/** Human-readable relative time in Portuguese (pt-BR). */
function formatRelativeTime(isoDate: string): string {
  const now = new Date();
  const past = new Date(isoDate);
  const diffMs = now.getTime() - past.getTime();
  const diffHours = Math.floor(diffMs / 3600000);
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffHours >= 24) return `${Math.floor(diffHours / 24)}d atrás`;
  if (diffHours > 0) return `${diffHours}h atrás`;
  if (diffMinutes > 0) return `${diffMinutes}min atrás`;
  return "agora";
}

/** Determine banner severity from the worst condition (AC4 priority). */
function deriveSeverity(props: DataQualityBannerProps): BannerSeverity {
  // Priority 1 — error (red): total failure
  if (props.responseState === "empty_failure" || props.succeededUfs === 0) {
    return "error";
  }

  // Priority 2 — warning (amber): partial failures, stale cache, or truncation
  if (
    props.failedUfs.length > 0 ||
    (props.isCached && props.cacheStatus === "stale") ||
    props.isTruncated
  ) {
    return "warning";
  }

  // Priority 3 — info (blue): default / everything OK / fresh cache
  return "info";
}

/** Check whether there is anything noteworthy to report. */
function hasAnythingToReport(props: DataQualityBannerProps): boolean {
  if (props.failedUfs.length > 0) return true;
  if (props.isCached) return true;
  if (props.isTruncated) return true;
  if (props.sourcesAvailable < props.sourcesTotal) return true;
  if (
    props.responseState === "degraded" ||
    props.responseState === "empty_failure"
  ) {
    return true;
  }
  if (props.coveragePct !== undefined && props.coveragePct < 100) return true;
  return false;
}

// ============================================================================
// Severity-based style configuration (AC14)
// ============================================================================

interface SeverityStyles {
  border: string;
  bg: string;
  text: string;
  badgeBg: string;
  badgeText: string;
  buttonBg: string;
  iconPath: string;
}

const severityConfig: Record<BannerSeverity, SeverityStyles> = {
  error: {
    border: "border-red-300/40 dark:border-red-700/30",
    bg: "bg-red-50/70 dark:bg-red-950/70",
    text: "text-red-800 dark:text-red-200",
    badgeBg: "bg-red-100/80 dark:bg-red-900/40",
    badgeText: "text-red-700 dark:text-red-300",
    buttonBg:
      "bg-red-600 hover:bg-red-700 focus-visible:ring-red-500 text-white disabled:bg-red-400",
    iconPath:
      "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
  },
  warning: {
    border: "border-amber-300/40 dark:border-amber-700/30",
    bg: "bg-amber-50/70 dark:bg-amber-950/70",
    text: "text-amber-800 dark:text-amber-200",
    badgeBg: "bg-amber-100/80 dark:bg-amber-900/40",
    badgeText: "text-amber-700 dark:text-amber-300",
    buttonBg:
      "bg-amber-600 hover:bg-amber-700 focus-visible:ring-amber-500 text-white disabled:bg-amber-400",
    iconPath:
      "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
  },
  info: {
    border: "border-blue-300/40 dark:border-blue-700/30",
    bg: "bg-blue-50/70 dark:bg-blue-950/70",
    text: "text-blue-800 dark:text-blue-200",
    badgeBg: "bg-blue-100/80 dark:bg-blue-900/40",
    badgeText: "text-blue-700 dark:text-blue-300",
    buttonBg:
      "bg-blue-600 hover:bg-blue-700 focus-visible:ring-blue-500 text-white disabled:bg-blue-400",
    iconPath:
      "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  },
};

// ============================================================================
// Spinner sub-component
// ============================================================================

function Spinner() {
  return (
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
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function DataQualityBanner(props: DataQualityBannerProps) {
  const {
    totalUfs,
    succeededUfs,
    failedUfs,
    isCached,
    cachedAt,
    cacheStatus,
    isTruncated,
    sourcesTotal,
    sourcesAvailable,
    sourceNames,
    onRefresh,
    onRetry,
    loading,
  } = props;

  // AC: Return null if there is nothing to report
  if (!hasAnythingToReport(props)) {
    return null;
  }

  const severity = deriveSeverity(props);
  const config = severityConfig[severity];

  // ---- Build pipe-separated message segments (AC2) ----
  const segments: string[] = [];

  // UFs: only if not all succeeded
  if (succeededUfs < totalUfs) {
    segments.push(`Resultados de ${succeededUfs}/${totalUfs} estados`);
  }

  // Cache: relative time or live
  if (isCached && cachedAt) {
    const relTime = formatRelativeTime(cachedAt);
    segments.push(relTime === "agora" ? "Dados em tempo real" : `Cache de ${relTime}`);
  }

  // Timeouts: only if > 0
  if (failedUfs.length > 0) {
    segments.push(
      `${failedUfs.length} ${failedUfs.length === 1 ? "timeout" : "timeouts"}`
    );
  }

  // Sources: only if not all available
  if (sourcesAvailable < sourcesTotal) {
    segments.push(`${sourcesAvailable}/${sourcesTotal} fontes`);
  }

  // Truncation
  if (isTruncated) {
    segments.push("Resultados truncados");
  }

  const message = segments.join(" | ");

  // ---- Action button (AC8) ----
  const isError = severity === "error" || failedUfs.length > 0;
  const isStale = cacheStatus === "stale";

  let actionLabel: string | null = null;
  let actionHandler: (() => void) | null = null;

  if (isError) {
    actionLabel = "Tentar novamente";
    actionHandler = onRetry;
  } else if (isStale) {
    actionLabel = "Atualizar";
    actionHandler = onRefresh;
  }

  return (
    <div
      data-testid="data-quality-banner"
      role="status"
      aria-live="polite"
      className={[
        // AC13: Glass morphism
        "backdrop-blur-md bg-white/70 dark:bg-gray-900/70",
        "border border-white/20 dark:border-gray-700/30 shadow-lg",
        // Severity-specific color tint overlay
        config.bg,
        config.border,
        // Layout
        "rounded-card p-3 sm:p-4 mt-4 animate-fade-in-up",
      ].join(" ")}
    >
      <div className="flex items-start gap-3">
        {/* Severity icon */}
        <svg
          className={`w-5 h-5 flex-shrink-0 mt-0.5 ${config.text}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d={config.iconPath}
          />
        </svg>

        <div className="flex-1 min-w-0">
          {/* Primary message (AC2) */}
          {message && (
            <p
              className={`text-sm sm:text-base font-medium ${config.text} leading-snug`}
            >
              {message}
            </p>
          )}

          {/* Badges row (AC5-AC7, AC15 mobile horizontal scroll) */}
          <BadgesRow
            totalUfs={totalUfs}
            succeededUfs={succeededUfs}
            failedUfs={failedUfs}
            isCached={isCached}
            cachedAt={cachedAt}
            sourcesTotal={sourcesTotal}
            sourcesAvailable={sourcesAvailable}
            sourceNames={sourceNames}
            config={config}
          />

          {/* Action button (AC8) */}
          {actionLabel && actionHandler && (
            <button
              onClick={actionHandler}
              disabled={loading}
              className={[
                "mt-3 px-4 py-2 rounded-button text-sm font-medium",
                "transition-all flex items-center gap-2",
                "disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
                config.buttonBg,
              ].join(" ")}
            >
              {loading ? (
                <>
                  <Spinner />
                  {isError ? "Tentando..." : "Atualizando..."}
                </>
              ) : (
                actionLabel
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// BadgesRow — inline badges for UFs, freshness, sources (AC5-AC7, AC15)
// ============================================================================

interface BadgesRowProps {
  totalUfs: number;
  succeededUfs: number;
  failedUfs: string[];
  isCached: boolean;
  cachedAt?: string | null;
  sourcesTotal: number;
  sourcesAvailable: number;
  sourceNames?: string[];
  config: SeverityStyles;
}

function BadgesRow({
  totalUfs,
  succeededUfs,
  failedUfs,
  isCached,
  cachedAt,
  sourcesTotal,
  sourcesAvailable,
  sourceNames,
  config,
}: BadgesRowProps) {
  // ---- UFs badge expand state (AC5) ----
  const [ufsExpanded, setUfsExpanded] = useState(false);
  const ufsRef = useRef<HTMLDivElement>(null);

  // ---- Sources tooltip state (AC7) ----
  const [sourcesTooltipOpen, setSourcesTooltipOpen] = useState(false);
  const sourcesRef = useRef<HTMLDivElement>(null);

  // ---- Freshness: keep relative time updated every 60s ----
  const [freshnessLabel, setFreshnessLabel] = useState(() => {
    if (!isCached || !cachedAt) return "Dados em tempo real";
    const rel = formatRelativeTime(cachedAt);
    return rel === "agora" ? "Dados em tempo real" : `Dados de ${rel}`;
  });

  useEffect(() => {
    // Compute initial value
    if (!isCached || !cachedAt) {
      setFreshnessLabel("Dados em tempo real");
      return;
    }
    const compute = () => {
      const rel = formatRelativeTime(cachedAt);
      setFreshnessLabel(rel === "agora" ? "Dados em tempo real" : `Dados de ${rel}`);
    };
    compute();
    const interval = setInterval(compute, 60000);
    return () => clearInterval(interval);
  }, [isCached, cachedAt]);

  // Close popover on outside click / Escape
  useEffect(() => {
    if (!ufsExpanded && !sourcesTooltipOpen) return;

    function handleClick(e: MouseEvent) {
      if (
        ufsExpanded &&
        ufsRef.current &&
        !ufsRef.current.contains(e.target as Node)
      ) {
        setUfsExpanded(false);
      }
      if (
        sourcesTooltipOpen &&
        sourcesRef.current &&
        !sourcesRef.current.contains(e.target as Node)
      ) {
        setSourcesTooltipOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setUfsExpanded(false);
        setSourcesTooltipOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [ufsExpanded, sourcesTooltipOpen]);

  const badgeBase = `inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium cursor-pointer select-none transition-colors ${config.badgeBg} ${config.badgeText}`;

  return (
    // AC15: Mobile horizontal scroll container
    <div
      className="mt-2 flex items-center gap-2 overflow-x-auto flex-nowrap scrollbar-hide pb-1 -mb-1"
      data-testid="badges-row"
    >
      {/* Badge 1: UFs (AC5) */}
      <div className="relative flex-shrink-0" ref={ufsRef}>
        <button
          type="button"
          onClick={() => setUfsExpanded(!ufsExpanded)}
          className={badgeBase}
          aria-expanded={ufsExpanded}
          aria-controls="uf-detail-panel"
          aria-label={`${succeededUfs} de ${totalUfs} estados processados. Clique para detalhes.`}
        >
          {/* Map pin icon */}
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
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          {succeededUfs}/{totalUfs} estados
          {/* Expand chevron */}
          <svg
            className={`w-3 h-3 transition-transform ${ufsExpanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {/* Expandable detail panel showing failed UFs */}
        {ufsExpanded && failedUfs.length > 0 && (
          <div
            id="uf-detail-panel"
            className="absolute left-0 top-full mt-1 z-30 w-64 p-3 rounded-card border border-border bg-surface shadow-xl animate-fade-in-up"
            role="region"
            aria-label="Detalhes de estados com falha"
          >
            <p className="text-xs font-semibold text-red-700 dark:text-red-400 mb-2 flex items-center gap-1">
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              Estados com falha ({failedUfs.length})
            </p>
            <div className="flex flex-wrap gap-1.5">
              {failedUfs.map((uf) => (
                <span
                  key={uf}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
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
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                  {uf} (timeout)
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Badge 2: Freshness (AC6) */}
      <span
        className={`${badgeBase} flex-shrink-0`}
        title={cachedAt ? new Date(cachedAt).toLocaleString("pt-BR") : undefined}
        aria-label={freshnessLabel}
      >
        {/* Clock icon */}
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
        {freshnessLabel}
      </span>

      {/* Badge 3: Sources (AC7) */}
      <div className="relative flex-shrink-0" ref={sourcesRef}>
        <button
          type="button"
          onClick={() => setSourcesTooltipOpen(!sourcesTooltipOpen)}
          className={badgeBase}
          aria-label={`${sourcesAvailable} de ${sourcesTotal} fontes disponíveis`}
        >
          {/* Database icon */}
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
              d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
            />
          </svg>
          {sourcesAvailable}/{sourcesTotal} fontes
        </button>

        {/* Tooltip with source names */}
        {sourcesTooltipOpen && sourceNames && sourceNames.length > 0 && (
          <div
            className="absolute left-0 top-full mt-1 z-30 w-56 p-3 rounded-card border border-border bg-surface shadow-xl animate-fade-in-up"
            role="tooltip"
          >
            <p className="text-xs font-semibold text-ink mb-1.5">
              Fontes de dados:
            </p>
            <ul className="space-y-1">
              {sourceNames.map((name, idx) => (
                <li
                  key={name}
                  className="flex items-center gap-2 text-xs text-ink-secondary"
                >
                  <span
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      idx < sourcesAvailable
                        ? "bg-green-500"
                        : "bg-red-500"
                    }`}
                    aria-hidden="true"
                  />
                  {name}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default DataQualityBanner;
