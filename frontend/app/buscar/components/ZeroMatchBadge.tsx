"use client";

import type { ZeroMatchProgress } from "../../../hooks/useSearchSSE";

interface ZeroMatchBadgeProps {
  progress: ZeroMatchProgress | null;
}

/**
 * CRIT-059 AC5: Badge showing async zero-match classification progress.
 * Displays "Analisando mais X oportunidades com IA..." while job runs,
 * then shows result count when complete.
 */
export function ZeroMatchBadge({ progress }: ZeroMatchBadgeProps) {
  if (!progress) return null;

  if (progress.status === 'started') {
    return (
      <div className="px-4 py-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg flex items-center gap-2">
        <svg className="animate-spin h-4 w-4 text-indigo-600 dark:text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-sm text-indigo-800 dark:text-indigo-300">
          Analisando mais {progress.willClassify} oportunidades com IA...
        </span>
      </div>
    );
  }

  if (progress.status === 'classifying') {
    const pct = progress.willClassify > 0
      ? Math.round((progress.classified / progress.willClassify) * 100)
      : 0;
    return (
      <div className="px-4 py-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg">
        <div className="flex items-center gap-2 mb-1">
          <svg className="animate-spin h-4 w-4 text-indigo-600 dark:text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-sm text-indigo-800 dark:text-indigo-300">
            Classificação IA: {progress.classified}/{progress.willClassify}
            {progress.approved > 0 && ` — ${progress.approved} aprovadas`}
          </span>
        </div>
        <div className="w-full bg-indigo-200 dark:bg-indigo-800 rounded-full h-1.5">
          <div
            className="bg-indigo-600 dark:bg-indigo-400 h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    );
  }

  if (progress.status === 'ready' && progress.approved > 0) {
    return (
      <div className="px-4 py-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
        <svg className="h-4 w-4 text-green-600 dark:text-green-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <span className="text-sm text-green-800 dark:text-green-300">
          IA encontrou +{progress.approved} oportunidades adicionais
        </span>
      </div>
    );
  }

  if (progress.status === 'error') {
    return (
      <div className="px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg flex items-center gap-2">
        <span className="text-sm text-amber-800 dark:text-amber-300">
          Classificação IA parcialmente indisponível
        </span>
      </div>
    );
  }

  return null;
}
