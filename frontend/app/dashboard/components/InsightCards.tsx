"use client";

import Link from "next/link";
import type { PipelineAlertsData, NewOpportunitiesData } from "./DashboardTypes";

/**
 * DEBT-127 AC1-AC4: Pipeline deadline alerts card.
 * Shows count of pipeline items with deadlines in the next 7 days.
 */
function PipelineAlertsCard({ data }: { data: PipelineAlertsData | null }) {
  if (!data) return null;

  const hasAlerts = data.total > 0;

  return (
    <div
      className={`rounded-card border p-5 ${
        hasAlerts
          ? "bg-amber-50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-800"
          : "bg-[var(--surface-0)] border-[var(--border)]"
      }`}
      data-testid="pipeline-alerts-card"
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
            hasAlerts
              ? "bg-amber-100 dark:bg-amber-900/30"
              : "bg-[var(--surface-1)]"
          }`}
        >
          <svg
            aria-hidden="true"
            className={`w-5 h-5 ${hasAlerts ? "text-amber-600 dark:text-amber-400" : "text-[var(--ink-muted)]"}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-display font-semibold text-[var(--ink)]">
            {hasAlerts
              ? `${data.total} ${data.total === 1 ? "edital vence" : "editais vencem"} esta semana`
              : "Nenhum prazo urgente"}
          </p>
          <p className="text-sm text-[var(--ink-secondary)] mt-1">
            {hasAlerts
              ? "Revise seus prazos no pipeline"
              : "Todos os prazos do seu pipeline estão em dia"}
          </p>
        </div>
      </div>
      {hasAlerts && (
        <Link
          href="/pipeline"
          className="inline-flex items-center gap-1 mt-3 text-sm font-medium text-amber-700 dark:text-amber-400 hover:underline"
          data-testid="pipeline-alerts-cta"
        >
          Ver no pipeline
          <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </Link>
      )}
    </div>
  );
}

/**
 * DEBT-127 AC6-AC9: New opportunities since last search.
 * Shows count from latest search or onboarding prompt.
 */
function NewOpportunitiesCard({ data }: { data: NewOpportunitiesData | null }) {
  if (!data) return null;

  // AC9: No previous search — onboarding prompt
  if (!data.has_previous_search) {
    return (
      <div
        className="rounded-card border border-[var(--border-accent)] bg-[var(--brand-blue-subtle)] p-5"
        data-testid="new-opportunities-card"
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[var(--brand-blue)]/10 flex items-center justify-center">
            <svg
              aria-hidden="true"
              className="w-5 h-5 text-[var(--brand-blue)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-display font-semibold text-[var(--ink)]">
              {`Fa\u00E7a sua primeira busca`}
            </p>
            <p className="text-sm text-[var(--ink-secondary)] mt-1">
              {`Descubra oportunidades de licita\u00E7\u00E3o relevantes para o seu setor`}
            </p>
          </div>
        </div>
        <Link
          href="/buscar"
          className="inline-flex items-center gap-1 mt-3 text-sm font-medium text-[var(--brand-blue)] hover:underline"
          data-testid="new-opportunities-cta"
        >
          Buscar oportunidades
          <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </Link>
      </div>
    );
  }

  // AC6-AC8: Show opportunities count with time context
  const daysLabel =
    data.days_since_last_search === 0
      ? "hoje"
      : data.days_since_last_search === 1
        ? "ontem"
        : `${data.days_since_last_search} dias`;

  return (
    <div
      className="rounded-card border border-[var(--border-accent)] bg-[var(--brand-blue-subtle)] p-5"
      data-testid="new-opportunities-card"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[var(--brand-blue)]/10 flex items-center justify-center">
          <svg
            aria-hidden="true"
            className="w-5 h-5 text-[var(--brand-blue)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-display font-semibold text-[var(--ink)]">
            {`${data.count} oportunidades na sua ${data.label ?? "última busca"}`}
          </p>
          <p className="text-sm text-[var(--ink-secondary)] mt-1">
            {data.days_since_last_search === 0
              ? `Busca realizada ${daysLabel}`
              : `\u00DAltima busca h\u00E1 ${daysLabel} \u2014 novas oportunidades podem ter surgido`}
          </p>
        </div>
      </div>
      <Link
        href="/buscar"
        className="inline-flex items-center gap-1 mt-3 text-sm font-medium text-[var(--brand-blue)] hover:underline"
        data-testid="new-opportunities-cta"
      >
        Buscar novamente
        <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </Link>
    </div>
  );
}

/**
 * DEBT-127 AC10-AC12: Insight cards container.
 * Prominently positioned at top of dashboard, stacks vertically on mobile.
 */
export function InsightCards({
  pipelineAlerts,
  newOpportunities,
}: {
  pipelineAlerts: PipelineAlertsData | null;
  newOpportunities: NewOpportunitiesData | null;
}) {
  // Don't render section if both are null (still loading or failed)
  if (!pipelineAlerts && !newOpportunities) return null;

  return (
    <div
      className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"
      data-testid="insight-cards"
    >
      <PipelineAlertsCard data={pipelineAlerts} />
      <NewOpportunitiesCard data={newOpportunities} />
    </div>
  );
}
