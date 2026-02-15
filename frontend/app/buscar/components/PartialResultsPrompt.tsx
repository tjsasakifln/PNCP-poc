"use client";

import React from "react";

// ============================================================================
// INTERFACES
// ============================================================================

export interface PartialResultsPromptProps {
  totalFound: number;
  succeededCount: number;
  pendingCount: number;
  elapsedSeconds: number;
  onViewPartial: () => void;
  onWaitComplete: () => void;
  dismissed: boolean;
}

export interface PartialResultsBannerProps {
  visibleCount: number;
  totalCount: number;
  searching: boolean;
}

export interface FailedUfsBannerProps {
  successCount: number;
  failedUfs: string[];
  onRetryFailed: () => void;
  loading: boolean;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatElapsedTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// ============================================================================
// AC5: PARTIAL RESULTS PROMPT
// ============================================================================

export function PartialResultsPrompt({
  totalFound,
  succeededCount,
  pendingCount,
  elapsedSeconds,
  onViewPartial,
  onWaitComplete,
  dismissed,
}: PartialResultsPromptProps): React.ReactElement | null {
  if (dismissed) {
    return null;
  }

  return (
    <div className="animate-fade-in-up rounded-card bg-surface-0 dark:bg-surface-0 border-2 border-amber-500 dark:border-amber-600 p-6 shadow-lg">
      {/* Icon and Message */}
      <div className="flex items-start gap-4 mb-4">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
          <svg
            className="w-6 h-6 text-amber-600 dark:text-amber-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <div className="flex-1">
          <h3 className="text-ink dark:text-ink font-semibold text-lg mb-2">
            Resultados parciais disponíveis
          </h3>
          <p className="text-ink-secondary dark:text-ink-secondary text-sm mb-3">
            Encontramos{" "}
            <strong className="text-ink dark:text-ink font-semibold">
              {totalFound} {totalFound === 1 ? "oportunidade" : "oportunidades"}
            </strong>{" "}
            em{" "}
            <strong className="text-ink dark:text-ink font-semibold">
              {succeededCount} {succeededCount === 1 ? "estado" : "estados"}
            </strong>
            . Ainda consultando{" "}
            <strong className="text-ink dark:text-ink font-semibold">
              {pendingCount} {pendingCount === 1 ? "estado" : "estados"}
            </strong>
            ...
          </p>

          {/* Timer */}
          <div className="flex items-center gap-2 text-ink-secondary dark:text-ink-secondary text-sm mb-4">
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>Consultando há {formatElapsedTime(elapsedSeconds)}</span>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={onViewPartial}
              className="px-5 py-2.5 bg-amber-600 hover:bg-amber-700 dark:bg-amber-600 dark:hover:bg-amber-700 text-white font-medium rounded-lg transition-colors duration-200 shadow-sm hover:shadow-md"
            >
              Ver resultados parciais
            </button>
            <button
              onClick={onWaitComplete}
              className="px-5 py-2.5 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-ink dark:text-ink border border-gray-300 dark:border-gray-600 font-medium rounded-lg transition-colors duration-200"
            >
              Aguardar busca completa
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// AC6: PARTIAL RESULTS BANNER (mini-banner above results)
// ============================================================================

export function PartialResultsBanner({
  visibleCount,
  totalCount,
  searching,
}: PartialResultsBannerProps): React.ReactElement {
  return (
    <div className="animate-fade-in-up rounded-card bg-blue-50 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-700 px-4 py-3 mb-4">
      <div className="flex items-center gap-3">
        {/* Info Icon */}
        <div className="flex-shrink-0 w-5 h-5 text-blue-600 dark:text-blue-400">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        {/* Message */}
        <p className="text-sm text-blue-900 dark:text-blue-100">
          Mostrando{" "}
          <strong className="font-semibold">
            {visibleCount} de {totalCount} estados
          </strong>
          .{" "}
          {searching && (
            <span className="inline-flex items-center gap-1.5">
              Busca em andamento
              <span className="inline-flex gap-0.5">
                <span className="w-1 h-1 bg-blue-600 dark:bg-blue-400 rounded-full animate-pulse" />
                <span className="w-1 h-1 bg-blue-600 dark:bg-blue-400 rounded-full animate-pulse animation-delay-200" />
                <span className="w-1 h-1 bg-blue-600 dark:bg-blue-400 rounded-full animate-pulse animation-delay-400" />
              </span>
            </span>
          )}
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// AC7: FAILED UFS BANNER (blue info style, not error red)
// ============================================================================

export function FailedUfsBanner({
  successCount,
  failedUfs,
  onRetryFailed,
  loading,
}: FailedUfsBannerProps): React.ReactElement | null {
  // Don't show if all states failed (that's SourcesUnavailable territory)
  if (successCount === 0) {
    return null;
  }

  // Don't show if no failed UFs
  if (failedUfs.length === 0) {
    return null;
  }

  return (
    <div className="animate-fade-in-up rounded-card bg-blue-50 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-700 p-4 mb-6">
      <div className="flex items-start gap-3">
        {/* Info Icon */}
        <div className="flex-shrink-0 w-6 h-6 mt-0.5 text-blue-600 dark:text-blue-400">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <div className="flex-1">
          {/* Message */}
          <p className="text-sm text-blue-900 dark:text-blue-100 mb-3">
            Resultados de{" "}
            <strong className="font-semibold">
              {successCount} {successCount === 1 ? "estado" : "estados"}
            </strong>
            . Alguns estados ficaram temporariamente indisponíveis. Você pode
            tentar novamente para consultar todos.
          </p>

          {/* Retry Button */}
          <button
            onClick={onRetryFailed}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors duration-200 shadow-sm hover:shadow-md"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Consultando...
              </span>
            ) : (
              "Consultar estados restantes"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
