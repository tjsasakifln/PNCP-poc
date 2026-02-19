"use client";

import { useState, useRef, useEffect } from "react";
import type { CoverageMetadata } from "../../types";

export interface CoverageBarProps {
  coverageMetadata: CoverageMetadata;
  /** Whether CacheBanner is already visible (to avoid info duplication) */
  cacheBannerVisible?: boolean;
}

function getBarColor(pct: number): { bar: string; text: string; bg: string } {
  if (pct >= 100) return {
    bar: "bg-green-500 dark:bg-green-400",
    text: "text-green-700 dark:text-green-300",
    bg: "bg-green-50 dark:bg-green-950",
  };
  if (pct >= 70) return {
    bar: "bg-amber-500 dark:bg-amber-400",
    text: "text-amber-700 dark:text-amber-300",
    bg: "bg-amber-50 dark:bg-amber-950",
  };
  return {
    bar: "bg-red-500 dark:bg-red-400",
    text: "text-red-700 dark:text-red-300",
    bg: "bg-red-50 dark:bg-red-950",
  };
}

export function CoverageBar({ coverageMetadata, cacheBannerVisible }: CoverageBarProps) {
  const [expanded, setExpanded] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const { ufs_requested, ufs_processed, ufs_failed, coverage_pct } = coverageMetadata;
  const colors = getBarColor(coverage_pct);

  // Close on outside click
  useEffect(() => {
    if (!expanded) return;
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node) &&
          buttonRef.current && !buttonRef.current.contains(e.target as Node)) {
        setExpanded(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setExpanded(false);
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [expanded]);

  const ariaLabel = `Cobertura da busca: ${ufs_processed.length} de ${ufs_requested.length} estados processados, ${Math.round(coverage_pct)} por cento`;

  return (
    <div className="relative" data-testid="coverage-bar">
      {/* Clickable/tappable bar area */}
      <button
        ref={buttonRef}
        onClick={() => setExpanded(!expanded)}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setExpanded(!expanded); } }}
        className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue rounded-lg p-3"
        aria-expanded={expanded}
        aria-controls="uf-breakdown-panel"
      >
        {/* Progress bar */}
        <div
          role="progressbar"
          aria-valuenow={Math.round(coverage_pct)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={ariaLabel}
          className="h-2.5 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700"
        >
          <div
            className={`h-full rounded-full transition-all duration-500 ${colors.bar}`}
            style={{ width: `${Math.min(coverage_pct, 100)}%` }}
          />
        </div>

        {/* Text label */}
        <div className="flex items-center justify-between mt-2">
          <p className={`text-sm font-medium ${colors.text}`}>
            Cobertura: {ufs_processed.length} de {ufs_requested.length} UFs ({coverage_pct.toFixed(1)}%)
          </p>
          {ufs_failed.length > 0 && (
            <span className="text-xs text-ink-secondary flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              Detalhes
            </span>
          )}
        </div>
      </button>

      {/* AC6: UF Breakdown Panel */}
      {expanded && (
        <div
          id="uf-breakdown-panel"
          ref={panelRef}
          className="mt-1 p-4 bg-surface border border-border rounded-card shadow-lg animate-fade-in-up sm:absolute sm:left-0 sm:right-0 sm:z-20"
          role="region"
          aria-label="Detalhes de cobertura por estado"
        >
          {/* Processed UFs */}
          {ufs_processed.length > 0 && (
            <div className="mb-3">
              <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1.5 flex items-center gap-1">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Processadas ({ufs_processed.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {ufs_processed.map((uf) => (
                  <span
                    key={uf}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {uf}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Failed UFs */}
          {ufs_failed.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-red-700 dark:text-red-400 mb-1.5 flex items-center gap-1">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Falharam ({ufs_failed.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {ufs_failed.map((uf) => (
                  <span
                    key={uf}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    {uf} (timeout)
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
