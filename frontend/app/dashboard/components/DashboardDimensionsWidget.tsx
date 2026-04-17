"use client";

import dynamic from "next/dynamic";
import { ErrorStateWithRetry } from "../../../components/ErrorStateWithRetry";
import { formatCurrencyBR } from "../../../lib/format-currency";
import type { TopDimensions, DimensionItem } from "./DashboardTypes";

// DEBT-012: References CSS vars defined in globals.css (--chart-1 … --chart-10)
const CHART_COLORS = [
  "var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)",
  "var(--chart-6)", "var(--chart-7)", "var(--chart-8)", "var(--chart-9)", "var(--chart-10)",
];

const formatCurrency = formatCurrencyBR;

const ChartSkeleton = () => (
  <div className="h-64 bg-[var(--surface-1)] rounded-card animate-pulse" />
);

const UfPieChart = dynamic(
  () => import("../DashboardCharts").then((mod) => mod.UfPieChart),
  { ssr: false, loading: ChartSkeleton }
);
const SectorBarChart = dynamic(
  () => import("../DashboardCharts").then((mod) => mod.SectorBarChart),
  { ssr: false, loading: ChartSkeleton }
);

export function DashboardDimensionsWidget({
  dimensions,
  dimensionsError,
  ufPieData,
  sectorChartData,
  isMobile,
  onRetry,
}: {
  dimensions: TopDimensions | null;
  dimensionsError: boolean;
  ufPieData: { name: string; value: number; fill: string }[];
  sectorChartData: (DimensionItem & { name: string })[];
  isMobile: boolean;
  onRetry: () => void;
}) {
  if (dimensionsError) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div
          className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6"
          data-testid="dimensions-error"
        >
          <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
            Estados mais analisados
          </h2>
          <ErrorStateWithRetry
            message={`Dados indisponíveis.`}
            onRetry={onRetry}
            compact
          />
        </div>
        <div
          className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6"
          data-testid="dimensions-error"
        >
          <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
            Setores mais analisados
          </h2>
          <ErrorStateWithRetry
            message={`Dados indisponíveis.`}
            onRetry={onRetry}
            compact
          />
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {/* Top UFs */}
      <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6">
        <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
          Estados mais analisados
        </h2>
        {dimensions && dimensions.top_ufs.length > 0 ? (
          <div className="flex gap-6">
            <div className="flex-1">
              <UfPieChart data={ufPieData} />
            </div>
            <div className="flex-1 space-y-2">
              {dimensions.top_ufs.map((uf, i) => (
                <div key={uf.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: backgroundColor is computed from chart color palette by index */}
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                    />
                    <span className="text-sm text-[var(--ink)]">
                      {uf.name}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-data font-semibold text-[var(--ink)]">
                      {uf.count}
                    </span>
                    <span className="text-xs text-[var(--ink-muted)] ml-2">
                      {formatCurrency(uf.value)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-[var(--ink-muted)] text-sm">Sem dados ainda</p>
        )}
      </div>

      {/* Top Sectors */}
      <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6">
        <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
          Setores mais analisados
        </h2>
        {sectorChartData.length > 0 ? (
          <SectorBarChart data={sectorChartData} isMobile={isMobile} />
        ) : (
          <p className="text-[var(--ink-muted)] text-sm">Sem dados ainda</p>
        )}
      </div>
    </div>
  );
}
