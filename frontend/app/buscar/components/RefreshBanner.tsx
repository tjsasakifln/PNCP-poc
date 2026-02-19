"use client";

/**
 * RefreshBanner — A-04 AC8: "Dados atualizados disponíveis" banner.
 *
 * Shown when the background live fetch completes after a cache-first response.
 * Displays count of new opportunities and a button to refresh.
 */

import type { RefreshAvailableInfo } from "../../../hooks/useSearchProgress";

interface RefreshBannerProps {
  refreshInfo: RefreshAvailableInfo;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export default function RefreshBanner({ refreshInfo, onRefresh, isRefreshing }: RefreshBannerProps) {
  const { newCount, updatedCount, removedCount, totalLive } = refreshInfo;

  // Build description parts
  const parts: string[] = [];
  if (newCount > 0) parts.push(`${newCount} ${newCount === 1 ? 'nova' : 'novas'}`);
  if (updatedCount > 0) parts.push(`${updatedCount} ${updatedCount === 1 ? 'atualizada' : 'atualizadas'}`);
  if (removedCount > 0) parts.push(`${removedCount} ${removedCount === 1 ? 'removida' : 'removidas'}`);

  const summary = parts.length > 0
    ? parts.join(', ')
    : `${totalLive} oportunidades`;

  return (
    <div
      className="flex items-center justify-between gap-3 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 dark:border-blue-800 dark:bg-blue-950/50"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-200">
        <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>
          Dados atualizados disponíveis — {summary}
        </span>
      </div>
      <button
        onClick={onRefresh}
        disabled={isRefreshing}
        className="flex-shrink-0 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
      >
        {isRefreshing ? 'Atualizando...' : 'Atualizar resultados'}
      </button>
    </div>
  );
}
