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
    <div className="mt-8 p-8 bg-surface-1 rounded-card border text-center animate-fade-in-up">
      {/* Icon */}
      <div className="w-20 h-20 mx-auto mb-6 bg-surface-2 rounded-full flex items-center justify-center">
        <svg className="w-10 h-10 text-ink-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="Nenhum documento encontrado">
          <title>Nenhum documento encontrado</title>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>

      {/* Title (STORY-173 AC3, GTM-FIX-028 AC14) */}
      <h3 className="text-xl font-semibold font-display text-ink mb-2">
        Nenhuma Oportunidade Relevante Encontrada
      </h3>

      {/* GTM-FIX-028 AC14/AC16: LLM zero-match analysis note */}
      {filterStats && (filterStats.llm_zero_match_calls ?? 0) > 0 && (
        <div className="mb-4 px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/40 rounded-card text-sm text-blue-800 dark:text-blue-200 flex items-center gap-2">
          <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span>
            IA analisou {filterStats.llm_zero_match_calls} licitações adicionais e nenhuma é relevante para {sectorName.toLowerCase()} neste período. Tente ampliar sua busca.
          </span>
        </div>
      )}

      {/* Context with filter breakdown (STORY-173 AC3) */}
      {rawCount > 0 && rejectionBreakdown.length > 0 ? (
        <div className="mb-6">
          <p className="text-ink-secondary mb-4">
            Nossos filtros eliminaram {rawCount.toLocaleString("pt-BR")} resultados irrelevantes para entregar apenas o que importa. Tente ajustar os filtros ou escolher outro setor:
          </p>
          <div className="text-left max-w-md mx-auto space-y-2">
            {rejectionBreakdown.map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-surface-0 rounded-card border animate-fade-in-up" style={{ animationDelay: `${i * 80}ms` }}>
                <span className="inline-flex items-center justify-center min-w-[2.5rem] h-7 rounded-full bg-error-subtle text-error text-sm font-bold tabular-nums">
                  {item.count}
                </span>
                <div>
                  <p className="text-sm font-medium text-ink">{item.label}</p>
                  <p className="text-xs text-ink-muted mt-1">{item.tip}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : rawCount > 0 ? (
        <p className="text-ink-secondary mb-4">
          Nossos filtros de precisão eliminaram {rawCount.toLocaleString("pt-BR")} resultados não relevantes para o setor de {sectorName.toLowerCase()}. Ajuste os critérios ou tente outro setor.
        </p>
      ) : (
        <p className="text-ink-secondary mb-4">
          Nenhuma oportunidade encontrada para o período e estados selecionados. Tente ampliar a busca.
        </p>
      )}

      {/* Suggestions */}
      <div className="text-left max-w-sm mx-auto mb-6 p-4 bg-surface-0 rounded-card border">
        <p className="text-sm font-semibold text-ink mb-3 flex items-center gap-2">
          <svg className="w-4 h-4 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Sugestões para encontrar resultados:
        </p>
        <ul className="text-sm text-ink-secondary space-y-2">
          <li className="flex items-start gap-2">
            <span className="text-brand-blue mt-0.5">•</span>
            <span><strong>Amplie o período</strong> — Tente buscar nos últimos 14 ou 30 dias</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-brand-blue mt-0.5">•</span>
            <span><strong>Selecione mais estados</strong> — Adicione estados vizinhos ou use &quot;Selecionar todos&quot;</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-brand-blue mt-0.5">•</span>
            <span><strong>Ajuste os filtros</strong> — Experimente ampliar faixa de valor, período ou modalidades de contratação</span>
          </li>
        </ul>
      </div>

      {/* Stats */}
      {stateCount > 0 && (
        <p className="text-xs text-ink-muted mb-4">
          Pesquisa realizada em {stateCount} estado{stateCount > 1 ? "s" : ""} usando 5 modalidades de contratação
        </p>
      )}

      {/* Action Button */}
      <button
        onClick={handleAdjust}
        className="px-6 py-3 bg-brand-navy text-white rounded-button font-semibold
                   hover:bg-brand-blue-hover active:bg-brand-blue transition-colors"
      >
        Ajustar critérios de busca
      </button>
    </div>
  );
}

export default EmptyState;
