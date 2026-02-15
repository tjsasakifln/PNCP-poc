"use client";

import { useState, useEffect } from "react";

// ---------------------------------------------------------------------------
// STORY-257B AC10: Fallback when all sources failed and no cache is available
// ---------------------------------------------------------------------------

interface SourcesUnavailableProps {
  /** Retry handler to fetch fresh data */
  onRetry: () => void;
  /** Handler to load last saved search */
  onLoadLastSearch: () => void;
  /** Whether the user has a last saved search available */
  hasLastSearch: boolean;
  /** Whether a retry is currently in progress */
  retrying: boolean;
}

export function SourcesUnavailable({
  onRetry,
  onLoadLastSearch,
  hasLastSearch,
  retrying,
}: SourcesUnavailableProps) {
  const [cooldown, setCooldown] = useState(30);

  useEffect(() => {
    if (cooldown <= 0 || retrying) return;

    const timer = setInterval(() => {
      setCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown, retrying]);

  const handleRetry = () => {
    if (cooldown > 0 || retrying) return;
    setCooldown(30); // Reset cooldown
    onRetry();
  };

  const retryDisabled = cooldown > 0 || retrying;

  return (
    <div className="mt-8 flex flex-col items-center justify-center p-8 sm:p-12 bg-surface-0 dark:bg-surface-1 rounded-card border border-border animate-fade-in-up">
      {/* Friendly refresh icon (circular arrow) */}
      <svg
        className="w-16 h-16 text-ink-muted mb-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        />
      </svg>

      {/* Title */}
      <h2 className="text-xl sm:text-2xl font-display font-semibold text-ink text-center mb-3">
        Nossas fontes de dados governamentais estão temporariamente
        indisponíveis
      </h2>

      {/* Subtitle */}
      <p className="text-base text-ink-secondary text-center max-w-md mb-8">
        Isso geralmente se resolve em poucos minutos. Seus resultados anteriores
        continuam acessíveis.
      </p>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Retry button with cooldown timer */}
        <button
          onClick={handleRetry}
          disabled={retryDisabled}
          className="px-5 py-2.5 rounded-button text-sm font-medium transition-all flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {retrying ? (
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
          ) : cooldown > 0 ? (
            `Tentar novamente (0:${cooldown.toString().padStart(2, "0")})`
          ) : (
            "Tentar novamente"
          )}
        </button>

        {/* Load last search button */}
        <button
          onClick={onLoadLastSearch}
          disabled={!hasLastSearch || retrying}
          className="px-5 py-2.5 rounded-button text-sm font-medium transition-all border border-border bg-transparent hover:bg-surface-1 text-ink disabled:text-ink-muted disabled:cursor-not-allowed relative group"
          title={
            !hasLastSearch ? "Nenhuma busca anterior encontrada" : undefined
          }
        >
          Ver última busca salva
          {!hasLastSearch && (
            <span className="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1.5 text-xs bg-gray-900 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
              Nenhuma busca anterior encontrada
            </span>
          )}
        </button>
      </div>
    </div>
  );
}

export default SourcesUnavailable;
