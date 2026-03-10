"use client";

import { useState, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useBackendStatusContext } from "../components/BackendStatusIndicator";
import { useFetchWithBackoff } from "../../hooks/useFetchWithBackoff";
import { useProfileCompleteness } from "../../hooks/useProfileCompleteness";
import { PageHeader } from "../../components/PageHeader";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import { TrialUpsellCTA } from "../../components/billing/TrialUpsellCTA";
import { usePlan } from "../../hooks/usePlan";
import { useIsMobile } from "../../hooks/useIsMobile";
import { formatCurrencyBR } from "../../lib/format-currency";
import { Download } from "lucide-react";

import { DashboardStatCards } from "./components/DashboardStatCards";
import { DashboardTimeSeriesChart } from "./components/DashboardTimeSeriesChart";
import { DashboardDimensionsWidget } from "./components/DashboardDimensionsWidget";
import { DashboardQuickLinks } from "./components/DashboardQuickLinks";
import {
  DashboardProfileHeaderControls,
  DashboardProfileSection,
} from "./components/DashboardProfileSection";
import {
  DashboardFullPageError,
  DashboardRetryingState,
  DashboardLoadingSkeleton,
  DashboardNotAuthenticated,
  DashboardEmptyState,
  DashboardStaleBanner,
} from "./components/DashboardErrorStates";
import { useDashboardDerivedData } from "./components/useDashboardDerivedData";
import type { DashboardData, Period } from "./components/DashboardTypes";
import { PageErrorBoundary } from "../../components/PageErrorBoundary";

const LOADING_TIMEOUT_MS = 10_000;

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit", month: "long", year: "numeric",
  });
}

export default function DashboardPage() {
  const { session, loading: authLoading } = useAuth();
  const { trackEvent } = useAnalytics();
  const { status: backendStatus } = useBackendStatusContext();
  const { planInfo } = usePlan();
  const isMobile = useIsMobile();

  const [period, setPeriod] = useState<Period>("week");

  // STORY-260: Profile completeness (FE-007: SWR)
  // Local override allows ProfileCompletionPrompt to show immediate feedback;
  // SWR revalidates on next render cycle.
  const { completenessPct: swrProfilePct } = useProfileCompleteness();
  const [profilePctOverride, setProfilePctOverride] = useState<number | null>(null);
  const profilePct = profilePctOverride ?? swrProfilePct;

  const fetchAnalytics = useCallback(
    async (endpoint: string, params?: Record<string, string>, signal?: AbortSignal) => {
      if (!session?.access_token) return null;
      const searchParams = new URLSearchParams(params);
      searchParams.set("endpoint", endpoint);
      const res = await fetch(`/api/analytics?${searchParams}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        signal,
      });
      if (!res.ok) throw new Error("Erro ao carregar dados");
      return res.json();
    },
    [session?.access_token]
  );

  // CRIT-018 AC1-AC6: Fetch function consumed by useFetchWithBackoff
  // AC4/AC5: Use Promise.allSettled so individual sections can fail independently
  const fetchDashboard = useCallback(
    async (signal: AbortSignal): Promise<DashboardData> => {
      const results = await Promise.allSettled([
        fetchAnalytics("summary", undefined, signal),
        fetchAnalytics("searches-over-time", { period, range_days: "90" }, signal),
        fetchAnalytics("top-dimensions", { limit: "7" }, signal),
      ]);
      trackEvent("dashboard_viewed", { period });
      return {
        summary: results[0].status === "fulfilled" ? results[0].value : null,
        timeSeries: results[1].status === "fulfilled" ? (results[1].value?.data || []) : [],
        dimensions: results[2].status === "fulfilled" ? results[2].value : null,
        summaryError: results[0].status === "rejected",
        timeSeriesError: results[1].status === "rejected",
        dimensionsError: results[2].status === "rejected",
      };
    },
    [period, fetchAnalytics, trackEvent]
  );

  const {
    data,
    loading,
    error,
    retryCount,
    hasExhaustedRetries,
    manualRetry,
  } = useFetchWithBackoff<DashboardData>(fetchDashboard, {
    enabled: !authLoading && !!session && backendStatus !== "offline",
    maxRetries: 3,
    initialDelayMs: 2000,
    maxDelayMs: 30000,
    timeoutMs: LOADING_TIMEOUT_MS,
  });

  // AC4/AC5: Per-section error flags (always from personal data)
  const summaryError = data?.summaryError ?? false;
  const timeSeriesError = data?.timeSeriesError ?? false;
  const dimensionsError = data?.dimensionsError ?? false;

  const summary = data?.summary ?? null;
  const timeSeries = data?.timeSeries ?? [];
  const dimensions = data?.dimensions ?? null;

  const { ufPieData, sectorChartData, handleExportCSV } = useDashboardDerivedData(
    summary,
    dimensions
  );

  // ── Auth guard ──────────────────────────────────────────────────────────────

  if (authLoading) return <AuthLoadingScreen />;
  if (!session) return <DashboardNotAuthenticated />;

  // ── CRIT-018 AC8 / CRIT-031: Error states ──────────────────────────────────

  const allSectionsFailed = summaryError && timeSeriesError && dimensionsError;

  if (error && hasExhaustedRetries && !data) {
    return <DashboardFullPageError onRetry={manualRetry} />;
  }
  if (data && allSectionsFailed) {
    return <DashboardFullPageError onRetry={manualRetry} />;
  }
  if (error && !hasExhaustedRetries && !data) {
    return <DashboardRetryingState retryCount={retryCount} />;
  }

  // ── Loading skeleton ────────────────────────────────────────────────────────

  if (loading && !data) return <DashboardLoadingSkeleton />;

  // ── Empty state ─────────────────────────────────────────────────────────────

  if (summary && summary.total_searches === 0) {
    return (
      <div className="min-h-screen bg-[var(--canvas)]">
        <PageHeader title="Dashboard" />
        <div className="max-w-6xl mx-auto py-8 px-4">
          <DashboardEmptyState />
        </div>
      </div>
    );
  }

  // ── Dashboard content ───────────────────────────────────────────────────────

  return (
    <PageErrorBoundary pageName="dashboard">
    <div className="min-h-screen bg-[var(--canvas)]">
      {error && hasExhaustedRetries && data && (
        <DashboardStaleBanner onRetry={manualRetry} />
      )}

      <PageHeader
        title="Dashboard"
        extraControls={
          <>
            <DashboardProfileHeaderControls profilePct={profilePct} />
            <button
              onClick={handleExportCSV}
              className="hidden sm:flex px-3 py-1.5 text-sm border border-[var(--border)] rounded-button
                         text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] transition-colors items-center gap-1.5"
            >
              <Download aria-hidden="true" className="w-4 h-4" strokeWidth={2} />
              CSV
            </button>
          </>
        }
      />

      <div className="max-w-6xl mx-auto py-8 px-4">
        {summary && (
          <p className="text-sm text-[var(--ink-muted)] mb-6">
            Membro desde {formatDate(summary.member_since)}
          </p>
        )}

        <DashboardProfileSection
          session={session}
          profilePct={profilePct}
          onProfileUpdated={setProfilePctOverride}
        />

        <DashboardStatCards
          summary={summary}
          summaryError={summaryError}
          onRetry={manualRetry}
        />

        {/* STORY-312 AC4: Dashboard CTA for trial users with >= 3 searches */}
        {summary && summary.total_searches >= 3 && (
          <div className="mb-8">
            <TrialUpsellCTA
              variant="dashboard"
              planId={planInfo?.plan_id}
              subscriptionStatus={planInfo?.subscription_status}
              contextData={{
                valor: formatCurrencyBR(summary.total_value_discovered).replace("R$ ", ""),
              }}
            />
          </div>
        )}

        <DashboardTimeSeriesChart
          timeSeries={timeSeries}
          timeSeriesError={timeSeriesError}
          period={period}
          setPeriod={setPeriod}
          isMobile={isMobile}
          onRetry={manualRetry}
        />

        <DashboardDimensionsWidget
          dimensions={dimensions}
          dimensionsError={dimensionsError}
          ufPieData={ufPieData}
          sectorChartData={sectorChartData}
          isMobile={isMobile}
          onRetry={manualRetry}
        />

        <DashboardQuickLinks />
      </div>
    </div>
    </PageErrorBoundary>
  );
}
