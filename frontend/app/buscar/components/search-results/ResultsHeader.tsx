"use client";

import type { BuscaResult } from "../../../types";
import type { FilterSummary } from "../../../../hooks/useSearchSSE";

interface ResultsHeaderProps {
  result: BuscaResult;
  rawCount: number;
  isProfileComplete?: boolean;
  filterSummary?: FilterSummary | null;
}

/**
 * TD-007 AC4: Results header — total count, filter stats, LLM source badges, sector info.
 * Displays the "X oportunidades selecionadas de Y analisadas" header with
 * personalized analysis badge and confidence distribution.
 */
export function ResultsHeader({
  result,
  rawCount,
  isProfileComplete = true,
  filterSummary,
}: ResultsHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-strong" aria-live="polite" aria-atomic="true">
      <div>
        <div className="flex items-center gap-2 flex-wrap">
          <h2 className="text-lg font-semibold text-ink" data-testid="results-header">
            {result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'oportunidade selecionada' : 'oportunidades selecionadas'}{rawCount > 0 ? ` de ${rawCount.toLocaleString("pt-BR")} analisadas` : ''}
          </h2>
          {/* STORY-260 AC17: "Análise personalizada" badge when profile is complete */}
          {isProfileComplete && result.resumo.total_oportunidades > 0 && (
            <div
              className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 text-xs rounded-full"
              title="Resultados otimizados para o perfil da sua empresa"
              data-testid="personalized-analysis-badge"
            >
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              {`Análise personalizada`}
            </div>
          )}
        </div>
        {filterSummary && filterSummary.totalRaw > 0 && (
          <p className="text-sm text-ink-secondary mt-0.5" data-testid="filter-context-line">
            Analisamos {filterSummary.totalRaw.toLocaleString("pt-BR")} oportunidades e selecionamos {result.resumo.total_oportunidades} {result.resumo.total_oportunidades === 1 ? 'compatível' : 'compatíveis'} com seu perfil
            {/* C-02 AC9: Confidence distribution counts */}
            {(() => {
              const counts = { high: 0, medium: 0, low: 0 };
              let hasAny = false;
              result.licitacoes.forEach(l => {
                if (l.confidence === "high") { counts.high++; hasAny = true; }
                else if (l.confidence === "medium") { counts.medium++; hasAny = true; }
                else if (l.confidence === "low") { counts.low++; hasAny = true; }
              });
              if (!hasAny) return null;
              const parts: string[] = [];
              if (counts.high > 0) parts.push(`${counts.high} alta`);
              if (counts.medium > 0) parts.push(`${counts.medium} média`);
              if (counts.low > 0) parts.push(`${counts.low} baixa`);
              return <span className="text-ink-muted"> ({parts.join(", ")})</span>;
            })()}
          </p>
        )}
      </div>
    </div>
  );
}
