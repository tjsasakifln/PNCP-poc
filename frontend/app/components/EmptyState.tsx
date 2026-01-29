"use client";

import type { FilterStats } from "../types";

interface EmptyStateProps {
  onAdjustSearch?: () => void;
  rawCount?: number;
  stateCount?: number;
  filterStats?: FilterStats | null;
  sectorName?: string;
}

export function EmptyState({
  onAdjustSearch,
  rawCount = 0,
  stateCount = 0,
  filterStats,
  sectorName = "uniformes",
}: EmptyStateProps) {
  const handleAdjust = () => {
    if (onAdjustSearch) {
      onAdjustSearch();
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  // Build rejection breakdown for display
  const rejectionBreakdown: { label: string; count: number; tip: string }[] = [];
  if (filterStats) {
    if (filterStats.rejeitadas_keyword > 0) {
      rejectionBreakdown.push({
        label: "Sem palavras-chave do setor",
        count: filterStats.rejeitadas_keyword,
        tip: "Tente outro setor que melhor descreva o que procura",
      });
    }
    if (filterStats.rejeitadas_valor > 0) {
      rejectionBreakdown.push({
        label: "Fora da faixa de valor (R$ 10k - R$ 10M)",
        count: filterStats.rejeitadas_valor,
        tip: "Licitações com valores muito baixos ou altos são excluídas",
      });
    }
    if (filterStats.rejeitadas_uf > 0) {
      rejectionBreakdown.push({
        label: "Estado não selecionado",
        count: filterStats.rejeitadas_uf,
        tip: "Selecione mais estados para ampliar resultados",
      });
    }
  }

  return (
    <div className="mt-8 p-8 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700 text-center">
      {/* Icon */}
      <div className="w-20 h-20 mx-auto mb-6 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
        <svg className="w-10 h-10 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold font-display text-gray-800 dark:text-gray-200 mb-2">
        Nenhuma licitação de {sectorName.toLowerCase()} encontrada
      </h3>

      {/* Context with filter breakdown */}
      {rawCount > 0 && rejectionBreakdown.length > 0 ? (
        <div className="mb-6">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Encontramos {rawCount.toLocaleString("pt-BR")} licitações no PNCP, mas nenhuma passou nos filtros:
          </p>
          <div className="text-left max-w-md mx-auto space-y-2">
            {rejectionBreakdown.map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                <span className="inline-flex items-center justify-center min-w-[2.5rem] h-7 rounded-full bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 text-sm font-bold tabular-nums">
                  {item.count}
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{item.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.tip}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : rawCount > 0 ? (
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Encontramos {rawCount.toLocaleString("pt-BR")} licitações no PNCP, mas nenhuma corresponde ao setor de {sectorName.toLowerCase()}.
        </p>
      ) : (
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Não encontramos licitações publicadas no PNCP para o período e estados selecionados.
        </p>
      )}

      {/* Suggestions */}
      <div className="text-left max-w-sm mx-auto mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
        <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
          <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Sugestões para encontrar resultados:
        </p>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-0.5">•</span>
            <span><strong>Amplie o período</strong> — Tente buscar nos últimos 14 ou 30 dias</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-0.5">•</span>
            <span><strong>Selecione mais estados</strong> — Adicione estados vizinhos ou use &quot;Selecionar todos&quot;</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-600 dark:text-green-400 mt-0.5">•</span>
            <span><strong>Troque o setor</strong> — Setores como &quot;Alimentos&quot; e &quot;Limpeza&quot; têm mais licitações</span>
          </li>
        </ul>
      </div>

      {/* Stats */}
      {stateCount > 0 && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">
          Pesquisa realizada em {stateCount} estado{stateCount > 1 ? "s" : ""} usando 5 modalidades de contratação
        </p>
      )}

      {/* Action Button */}
      <button
        onClick={handleAdjust}
        className="px-6 py-3 bg-emerald-700 text-white rounded-md font-semibold hover:bg-emerald-800 active:bg-emerald-900 transition-colors"
      >
        Ajustar critérios de busca
      </button>
    </div>
  );
}

export default EmptyState;
