"use client";

import { CoverageBar } from "./CoverageBar";
import { FreshnessIndicator } from "./FreshnessIndicator";
import { ReliabilityBadge } from "./ReliabilityBadge";
import type { UfStatusDetailItem } from "../../types";

export type OperationalState = "operational" | "partial" | "degraded" | "unavailable";

export interface OperationalStateBannerProps {
  coveragePct: number;
  responseState?: "live" | "cached" | "degraded" | "empty_failure";
  ufsStatusDetail?: UfStatusDetailItem[];
  ultimaAtualizacao?: string | null;
  cachedAt?: string | null;
  cacheStatus?: "fresh" | "stale";
}

function deriveState(
  coveragePct: number,
  responseState?: string,
): OperationalState {
  if (responseState === "empty_failure") return "unavailable";
  if (responseState === "cached") return "degraded";
  if (coveragePct >= 100) return "operational";
  if (coveragePct >= 50) return "partial";
  return "degraded";
}

const stateConfig: Record<OperationalState, {
  bg: string;
  border: string;
  text: string;
  icon: string;
  label: string;
}> = {
  operational: {
    bg: "bg-green-50 dark:bg-green-950",
    border: "border-green-200 dark:border-green-800",
    text: "text-green-700 dark:text-green-300",
    icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
    label: "Cobertura completa",
  },
  partial: {
    bg: "bg-amber-50 dark:bg-amber-950",
    border: "border-amber-200 dark:border-amber-800",
    text: "text-amber-700 dark:text-amber-300",
    icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    label: "Cobertura parcial",
  },
  degraded: {
    bg: "bg-orange-50 dark:bg-orange-950",
    border: "border-orange-200 dark:border-orange-800",
    text: "text-orange-700 dark:text-orange-300",
    icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
    label: "Dados em cache",
  },
  unavailable: {
    bg: "bg-red-50 dark:bg-red-950",
    border: "border-red-200 dark:border-red-800",
    text: "text-red-700 dark:text-red-300",
    icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
    label: "Fontes indisponíveis",
  },
};

export function OperationalStateBanner({
  coveragePct,
  responseState,
  ufsStatusDetail,
  ultimaAtualizacao,
  cachedAt,
  cacheStatus,
}: OperationalStateBannerProps) {
  const state = deriveState(coveragePct, responseState);
  const config = stateConfig[state];

  const timestamp = cachedAt || ultimaAtualizacao;

  return (
    <div
      className={`${config.bg} ${config.border} border rounded-card p-4 animate-fade-in-up`}
      role="status"
      aria-label={config.label}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-2">
          <svg
            className={`w-5 h-5 ${config.text} shrink-0`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={config.icon} />
          </svg>
          <span className={`text-sm font-semibold ${config.text}`}>
            {state === "operational" && "Cobertura completa — todos os estados processados"}
            {state === "partial" && `${coveragePct}% de cobertura`}
            {state === "degraded" && "Dados de cache — atualizando em background"}
            {state === "unavailable" && "Fontes indisponíveis — tente novamente em 5 min"}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {timestamp && <FreshnessIndicator timestamp={timestamp} />}
          <ReliabilityBadge
            coveragePct={coveragePct}
            timestamp={timestamp || undefined}
            responseState={responseState}
            cacheStatus={cacheStatus}
          />
        </div>
      </div>

      {state !== "unavailable" && ufsStatusDetail && ufsStatusDetail.length > 0 && (
        <div className="mt-3 hidden sm:block">
          <CoverageBar
            coveragePct={coveragePct}
            ufsStatusDetail={ufsStatusDetail}
          />
        </div>
      )}

      {state !== "unavailable" && state !== "operational" && ufsStatusDetail && (
        <div className="mt-2 sm:hidden">
          <p className={`text-xs ${config.text}`}>
            {ufsStatusDetail.filter(u => u.status === "ok").length} de {ufsStatusDetail.length} estados processados
          </p>
        </div>
      )}
    </div>
  );
}
