"use client";

interface EmptyStateProps {
  /** Callback when user wants to adjust search */
  onAdjustSearch?: () => void;
  /** Number of raw results before filtering (for context) */
  rawCount?: number;
  /** Number of states searched */
  stateCount?: number;
}

/**
 * Empty state component for when search returns no results
 *
 * Provides:
 * - Clear visual indication of empty results
 * - Helpful suggestions for getting results
 * - Context about what was searched
 * - Call to action to adjust search
 */
export function EmptyState({
  onAdjustSearch,
  rawCount = 0,
  stateCount = 0,
}: EmptyStateProps) {
  const handleAdjust = () => {
    if (onAdjustSearch) {
      onAdjustSearch();
    } else {
      // Scroll to top of page
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <div className="mt-8 p-8 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
      {/* Icon */}
      <div className="w-20 h-20 mx-auto mb-6 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
        <svg
          className="w-10 h-10 text-gray-400 dark:text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold font-display text-gray-800 dark:text-gray-200 mb-2">
        Nenhuma licitacao de uniformes encontrada
      </h3>

      {/* Context */}
      {rawCount > 0 && (
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Encontramos {rawCount.toLocaleString("pt-BR")} licitacoes no PNCP, mas nenhuma passou nos
          filtros de uniformes.
        </p>
      )}

      {rawCount === 0 && (
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Nao encontramos licitacoes publicadas no PNCP para o periodo e estados selecionados.
        </p>
      )}

      {/* Suggestions */}
      <div className="text-left max-w-sm mx-auto mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
        <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
          <svg
            className="w-4 h-4 text-green-600 dark:text-green-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
          Sugestoes para encontrar resultados:
        </p>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-0.5">•</span>
            <span>
              <strong>Amplie o periodo</strong> — Tente buscar nos ultimos 14 ou 30 dias
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-0.5">•</span>
            <span>
              <strong>Selecione mais estados</strong> — Adicione estados vizinhos ou use
              &quot;Selecionar todos&quot;
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-0.5">•</span>
            <span>
              <strong>Verifique as datas</strong> — Certifique-se de que o periodo inclui dias uteis
            </span>
          </li>
        </ul>
      </div>

      {/* Stats (if available) */}
      {stateCount > 0 && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">
          Pesquisa realizada em {stateCount} estado{stateCount > 1 ? "s" : ""} usando 5 modalidades
          de contratacao
        </p>
      )}

      {/* Action Button */}
      <button
        onClick={handleAdjust}
        className="px-6 py-3 bg-emerald-700 text-white rounded-md font-semibold hover:bg-emerald-800 active:bg-emerald-900 transition-colors"
      >
        Ajustar criterios de busca
      </button>
    </div>
  );
}

export default EmptyState;
