"use client";

import useSWR from "swr";
import Link from "next/link";
import { useAuth } from "../../components/AuthProvider";
import { usePlan } from "../../../hooks/usePlan";

/**
 * STORY-443: Trial Value Dashboard Card
 *
 * Expanded card shown at the top of the dashboard for active free_trial users.
 * Displays accumulated value, opportunities, searches, and trial day progress.
 * Only visible for non-expired free_trial users.
 */

interface TrialValueData {
  total_value: number;
  total_opportunities: number;
  searches_used: number;
  trial_expires_at: string;
}

const TRIAL_DURATION_DAYS = 14;

const formatCompact = (val: number): string => {
  if (val >= 1_000_000) return `R$ ${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `R$ ${(val / 1_000).toFixed(0)}K`;
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(val);
};

function getTrialDay(trialExpiresAt: string): number {
  const expiresMs = new Date(trialExpiresAt).getTime();
  const startMs = expiresMs - TRIAL_DURATION_DAYS * 86_400_000;
  const elapsed = Date.now() - startMs;
  return Math.min(TRIAL_DURATION_DAYS, Math.max(1, Math.ceil(elapsed / 86_400_000)));
}

function getProgressColor(day: number): string {
  if (day <= 7) return "bg-emerald-500";
  if (day <= 11) return "bg-amber-400";
  return "bg-red-500";
}

function getProgressBarTrack(day: number): string {
  if (day <= 7) return "bg-emerald-100 dark:bg-emerald-900/30";
  if (day <= 11) return "bg-amber-100 dark:bg-amber-900/30";
  return "bg-red-100 dark:bg-red-900/30";
}

function SkeletonCard() {
  return (
    <div
      className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-6 animate-pulse"
      data-testid="trial-value-card-skeleton"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="h-5 w-48 bg-[var(--border)] rounded" />
        <div className="h-4 w-24 bg-[var(--border)] rounded" />
      </div>
      <div className="h-3 w-full bg-[var(--border)] rounded-full mb-6" />
      <div className="flex gap-6">
        <div className="h-8 w-32 bg-[var(--border)] rounded" />
        <div className="h-8 w-24 bg-[var(--border)] rounded" />
        <div className="h-8 w-20 bg-[var(--border)] rounded" />
      </div>
    </div>
  );
}

export function TrialValueCard() {
  const { session } = useAuth();
  const { planInfo } = usePlan();

  const isTrial = planInfo?.plan_id === "free_trial";
  const isExpired = planInfo?.trial_expires_at
    ? new Date(planInfo.trial_expires_at).getTime() < Date.now()
    : false;

  const shouldFetch = isTrial && !isExpired && !!session?.access_token;

  const { data, isLoading } = useSWR<TrialValueData>(
    shouldFetch ? "/api/analytics?endpoint=trial-value" : null,
    async (url: string) => {
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${session!.access_token}` },
      });
      if (!res.ok) throw new Error("fetch_failed");
      return res.json();
    },
    {
      revalidateOnFocus: false,
      dedupingInterval: 300_000, // 5 min
      errorRetryCount: 1,
    }
  );

  // AC5: Don't render for paid users or expired trials
  if (!isTrial || isExpired) return null;

  // AC6: Skeleton during fetch
  if (isLoading) return <SkeletonCard />;

  // Don't render if no data or backend error, or if data is missing required fields
  if (!data || data.total_opportunities == null || data.total_value == null) return null;

  const trialDay = data.trial_expires_at
    ? getTrialDay(data.trial_expires_at)
    : (planInfo?.trial_expires_at ? getTrialDay(planInfo.trial_expires_at) : 1);

  const progressPct = Math.min(100, (trialDay / TRIAL_DURATION_DAYS) * 100);
  const progressColor = getProgressColor(trialDay);
  const trackColor = getProgressBarTrack(trialDay);

  return (
    <div
      className="rounded-2xl border border-emerald-200/60 dark:border-emerald-800/40 bg-gradient-to-br from-emerald-50 to-blue-50 dark:from-emerald-900/20 dark:to-blue-900/20 p-6 mb-6"
      data-testid="trial-value-card"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h2 className="text-base font-semibold text-[var(--ink-primary)]">
          Você está no trial gratuito
        </h2>
        <span className="text-sm text-[var(--ink-secondary)] font-medium">
          Dia {trialDay} de {TRIAL_DURATION_DAYS}
        </span>
      </div>

      {/* AC4: Progress bar */}
      <div
        className={`w-full h-2.5 rounded-full mb-6 ${trackColor}`}
        role="progressbar"
        aria-valuenow={trialDay}
        aria-valuemin={1}
        aria-valuemax={TRIAL_DURATION_DAYS}
        aria-label={`Dia ${trialDay} de ${TRIAL_DURATION_DAYS} do trial`}
      >
        {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width is computed from trial day progress percentage */}
        <div
          className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
          style={{ width: `${progressPct}%` }}
          data-testid="trial-progress-bar"
        />
      </div>

      {/* Metrics row */}
      <div className="flex flex-wrap gap-6 mb-6">
        <div>
          <div
            className="text-xl font-bold text-emerald-700 dark:text-emerald-300"
            data-testid="trial-total-value"
          >
            {formatCompact(data.total_value)}
          </div>
          <div className="text-xs text-[var(--ink-muted)] mt-0.5">analisados</div>
        </div>

        <div className="border-l border-[var(--border)] pl-6">
          <div
            className="text-xl font-bold text-[var(--ink-primary)]"
            data-testid="trial-total-opportunities"
          >
            {data.total_opportunities.toLocaleString("pt-BR")}
          </div>
          <div className="text-xs text-[var(--ink-muted)] mt-0.5">oportunidades</div>
        </div>

        <div className="border-l border-[var(--border)] pl-6">
          <div
            className="text-xl font-bold text-[var(--ink-primary)]"
            data-testid="trial-searches-used"
          >
            {data.searches_used}
          </div>
          <div className="text-xs text-[var(--ink-muted)] mt-0.5">buscas</div>
        </div>
      </div>

      {/* AC3: CTA */}
      <Link
        href="/planos"
        className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-button bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-colors"
        data-testid="trial-cta-link"
      >
        Continue analisando com SmartLic Pro
        <span aria-hidden="true">→</span>
      </Link>
    </div>
  );
}
