"use client";

interface PartialTimeoutBannerProps {
  succeededUfs: string[];
  failedUfs: string[];
  onRetryFailed: () => void;
  searchId?: string | null;
}

/**
 * CRIT-006 AC22-24: Banner shown when search times out but partial UFs succeeded.
 * Shows completed vs pending UFs and offers retry for failed ones.
 */
export function PartialTimeoutBanner({
  succeededUfs,
  failedUfs,
  onRetryFailed,
  searchId,
}: PartialTimeoutBannerProps) {
  if (succeededUfs.length === 0 && failedUfs.length === 0) return null;

  return (
    <div
      className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 rounded-card"
      role="alert"
      data-testid="partial-timeout-banner"
    >
      <div className="flex items-start gap-3">
        <svg className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">
            Busca incompleta — tempo limite excedido
          </p>
          <div className="mt-2 text-sm text-amber-700 dark:text-amber-300">
            {succeededUfs.length > 0 && (
              <p>
                Estados concluidos ({succeededUfs.length}): {succeededUfs.join(", ")}
              </p>
            )}
            {failedUfs.length > 0 && (
              <p className="mt-1">
                Estados pendentes ({failedUfs.length}): {failedUfs.join(", ")}
              </p>
            )}
          </div>
          {failedUfs.length > 0 && (
            <button
              onClick={onRetryFailed}
              className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-amber-100 text-amber-800 hover:bg-amber-200 dark:bg-amber-800/40 dark:text-amber-200 dark:hover:bg-amber-800/60 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Buscar estados restantes
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
