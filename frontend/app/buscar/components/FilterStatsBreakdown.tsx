"use client";

import type { FilterStats } from "../../types";

export interface FilterStatsBreakdownProps {
  stats: FilterStats;
}

/**
 * STAB-005 AC3: Visual funnel showing how filters progressively reduced results.
 * Uses horizontal CSS bars with color coding per filter stage.
 */
export function FilterStatsBreakdown({ stats }: FilterStatsBreakdownProps) {
  // Calculate total items that entered the filter pipeline
  const totalFound =
    (stats.rejeitadas_uf ?? 0) +
    (stats.rejeitadas_valor ?? 0) +
    (stats.rejeitadas_keyword ?? 0) +
    (stats.rejeitadas_min_match ?? 0) +
    (stats.rejeitadas_prazo ?? 0) +
    (stats.rejeitadas_outros ?? 0);

  // If no rejections recorded, nothing to show
  if (totalFound === 0) return null;

  // Build funnel stages in order of filter application
  const stages: { label: string; removed: number; color: string; bgColor: string }[] = [
    {
      label: "UF (estado)",
      removed: stats.rejeitadas_uf ?? 0,
      color: "bg-red-500 dark:bg-red-600",
      bgColor: "text-red-700 dark:text-red-400",
    },
    {
      label: "Faixa de valor",
      removed: stats.rejeitadas_valor ?? 0,
      color: "bg-orange-500 dark:bg-orange-600",
      bgColor: "text-orange-700 dark:text-orange-400",
    },
    {
      label: "Palavras-chave",
      removed: stats.rejeitadas_keyword ?? 0,
      color: "bg-amber-500 dark:bg-amber-600",
      bgColor: "text-amber-700 dark:text-amber-400",
    },
    {
      label: "Correspondencia minima",
      removed: stats.rejeitadas_min_match ?? 0,
      color: "bg-yellow-500 dark:bg-yellow-600",
      bgColor: "text-yellow-700 dark:text-yellow-400",
    },
    {
      label: "Prazo/status",
      removed: stats.rejeitadas_prazo ?? 0,
      color: "bg-purple-500 dark:bg-purple-600",
      bgColor: "text-purple-700 dark:text-purple-400",
    },
    {
      label: "Outros",
      removed: stats.rejeitadas_outros ?? 0,
      color: "bg-gray-500 dark:bg-gray-600",
      bgColor: "text-gray-700 dark:text-gray-400",
    },
  ];

  // Only show stages that actually removed items
  const activeStages = stages.filter((s) => s.removed > 0);

  if (activeStages.length === 0) return null;

  return (
    <div
      className="mt-4 p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg"
      data-testid="filter-stats-breakdown"
    >
      <h4 className="text-sm font-semibold text-[var(--ink)] mb-3">
        Detalhamento dos filtros
      </h4>

      <p className="text-xs text-[var(--ink-secondary)] mb-4">
        {totalFound} {totalFound === 1 ? "licitação removida" : "licitações removidas"} pelos filtros:
      </p>

      <div className="space-y-3">
        {activeStages.map((stage) => {
          const pct = totalFound > 0 ? Math.round((stage.removed / totalFound) * 100) : 0;
          return (
            <div key={stage.label} data-testid={`filter-stage-${stage.label}`}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className={`font-medium ${stage.bgColor}`}>{stage.label}</span>
                <span className="text-[var(--ink-secondary)] tabular-nums">
                  {stage.removed} ({pct}%)
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-[var(--surface-2)] overflow-hidden">
                {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width is a computed percentage from filter stage results */}
                <div
                  className={`h-full rounded-full ${stage.color} transition-all duration-500`}
                  style={{ width: `${Math.max(pct, 2)}%` }}
                  role="progressbar"
                  aria-valuenow={pct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${stage.label}: ${stage.removed} removidas`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
