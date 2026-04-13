"use client";

/**
 * STORY-295 AC10: Per-source status indicators for progressive results.
 *
 * Shows visual status for each data source during search:
 * - Pending (gray): Not started yet
 * - Fetching (blue spinner): In progress
 * - Success (green check): Completed with results
 * - Partial (yellow): Timed out but returned some results
 * - Error (red X): Failed completely
 * - Timeout (orange clock): Timed out with no results
 */

import type { SourceStatus, SourceStatusType } from "../../../hooks/useSearchSSE";

const SOURCE_LABELS: Record<string, string> = {
  PNCP: "PNCP",
  PORTAL_COMPRAS: "Portal de Compras",
  COMPRAS_GOV: "ComprasGov",
  LICITAJA: "LicitaJá",
};

function sanitizeErrorForDisplay(error: string | undefined): string {
  if (!error) return "";
  const lower = error.toLowerCase();
  if (
    lower.includes("401") ||
    lower.includes("authentication") ||
    lower.includes("auth") ||
    lower.includes("api_key") ||
    lower.includes("api key")
  ) {
    return "indisponível";
  }
  if (lower.includes("403") || lower.includes("forbidden")) return "indisponível";
  if (lower.includes("429") || lower.includes("rate limit")) return "sobrecarregado";
  if (lower.includes("timeout")) return "não respondeu a tempo";
  return "erro temporário";
}

function getStatusIcon(status: SourceStatusType): string {
  switch (status) {
    case "success":
      return "\u2713"; // ✓
    case "fetching":
    case "pending":
      return "\u231B"; // ⏳
    case "error":
      return "\u2717"; // ✗
    case "timeout":
      return "\u23F1"; // ⏱
    case "partial":
      return "\u26A0"; // ⚠
    default:
      return "\u2022"; // •
  }
}

function getStatusColor(status: SourceStatusType): string {
  switch (status) {
    case "success":
      return "text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800";
    case "fetching":
      return "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800";
    case "pending":
      return "text-[var(--ink-secondary)] bg-[var(--surface-1)] border-[var(--border)]";
    case "error":
      return "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800";
    case "timeout":
      return "text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800";
    case "partial":
      return "text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800";
    default:
      return "text-[var(--ink-secondary)] bg-[var(--surface-1)] border-[var(--border)]";
  }
}

function getStatusLabel(status: SourceStatusType): string {
  switch (status) {
    case "success":
      return "Concluída";
    case "fetching":
      return "Analisando...";
    case "pending":
      return "Aguardando";
    case "error":
      return "Falhou";
    case "timeout":
      return "Timeout";
    case "partial":
      return "Parcial";
    default:
      return status;
  }
}

interface SourceStatusGridProps {
  sourceStatuses: Map<string, SourceStatus>;
  className?: string;
}

export default function SourceStatusGrid({
  sourceStatuses,
  className = "",
}: SourceStatusGridProps) {
  if (sourceStatuses.size === 0) return null;

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {Array.from(sourceStatuses.entries()).map(([source, info]) => (
        <div
          key={source}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium ${getStatusColor(info.status)}`}
          title={
            info.error
              ? `${getStatusLabel(info.status)}: ${sanitizeErrorForDisplay(info.error)}`
              : `${getStatusLabel(info.status)} — ${info.recordCount} resultados em ${(info.durationMs / 1000).toFixed(1)}s`
          }
        >
          <span
            className={info.status === "fetching" ? "animate-pulse" : ""}
          >
            {getStatusIcon(info.status)}
          </span>
          <span>{SOURCE_LABELS[source] || source}</span>
          {info.recordCount > 0 && (
            <span className="opacity-70">({info.recordCount})</span>
          )}
        </div>
      ))}
    </div>
  );
}
