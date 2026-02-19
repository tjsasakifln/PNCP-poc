"use client";

import type { UfStatusDetailItem } from "../../types";

export interface CoverageBarProps {
  coveragePct: number;
  ufsStatusDetail: UfStatusDetailItem[];
}

export function CoverageBar({ coveragePct, ufsStatusDetail }: CoverageBarProps) {
  const okCount = ufsStatusDetail.filter(u => u.status === "ok").length;
  const totalCount = ufsStatusDetail.length;

  return (
    <div>
      <div className="flex gap-0.5 h-2 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800">
        {ufsStatusDetail.map((uf) => (
          <div
            key={uf.uf}
            className={`flex-1 relative group ${
              uf.status === "ok"
                ? "bg-green-500 dark:bg-green-400"
                : "bg-gray-300 dark:bg-gray-600"
            }`}
            title={
              uf.status === "ok"
                ? `${uf.uf}: OK (${uf.results_count} resultados)`
                : `${uf.uf}: ${uf.status === "timeout" ? "Timeout" : uf.status === "error" ? "Erro" : "Ignorado"}`
            }
            role="img"
            aria-label={`${uf.uf}: ${uf.status === "ok" ? `OK, ${uf.results_count} resultados` : uf.status}`}
          />
        ))}
      </div>

      <p className="text-xs text-ink-secondary mt-1.5">
        <span className="font-semibold">{coveragePct}% de cobertura</span>
        <span className="mx-1">—</span>
        {okCount} de {totalCount} estados processados
      </p>
    </div>
  );
}
