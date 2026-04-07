"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useShepherdTour, type TourStep } from "../../hooks/useShepherdTour";
import { useBackendStatusContext } from "../components/BackendStatusIndicator";
import { useFetchWithBackoff } from "../../hooks/useFetchWithBackoff";
import { useProfileCompleteness } from "../../hooks/useProfileCompleteness";
import { PageHeader } from "../../components/PageHeader";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import { TrialUpsellCTA } from "../../components/billing/TrialUpsellCTA";
import { TrialValueTracker } from "../../components/billing/TrialValueTracker";
import { TrialExtensionCard } from "../../components/billing/TrialExtensionCard";
import { usePlan } from "../../hooks/usePlan";
import { useIsMobile } from "../../hooks/useIsMobile";
import { formatCurrencyBR } from "../../lib/format-currency";
import { Download } from "lucide-react";

import { DashboardStatCards } from "./components/DashboardStatCards";
import { DashboardTimeSeriesChart } from "./components/DashboardTimeSeriesChart";
import { DashboardDimensionsWidget } from "./components/DashboardDimensionsWidget";
import { DashboardQuickLinks } from "./components/DashboardQuickLinks";
import { InsightCards } from "./components/InsightCards";
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
import type { DashboardData, Period, PipelineAlertsData, NewOpportunitiesData } from "./components/DashboardTypes";
import { PageErrorBoundary } from "../../components/PageErrorBoundary";

const LOADING_TIMEOUT_MS = 10_000;

// P0 zero-churn: Dashboard tour steps (auto-triggered on first visit)
const DASHBOARD_TOUR_STEPS: TourStep[] = [
  {
    id: "dashboard-stats",
    title: "Seu resumo de atividade",
    text: '<span class="tour-step-counter">Passo 1 de 3</span><p>Aqui você vê o total de buscas, oportunidades encontradas e valor acumulado.</p>',
    attachTo: { element: '[data-testid="dashboard-stat-cards"]', on: "bottom" },
    showOn: () => !!document.querySelector('[data-testid="dashboard-stat-cards"]'),
  },
  {
    id: "dashboard-chart",
    title: "Tendência de buscas",
    text: '<span class="tour-step-counter">Passo 2 de 3</span><p>Acompanhe sua atividade ao longo do tempo. Mais buscas = mais oportunidades.</p>',
    attachTo: { element: '[data-testid="timeseries-chart"]', on: "top" },
    showOn: () => !!document.querySelector('[data-testid="timeseries-chart"]'),
  },
  {
    id: "dashboard-dimensions",
    title: "Suas dimensões",
    text: '<span class="tour-step-counter">Passo 3 de 3</span><p>Veja quais setores, estados e faixas de valor você mais pesquisa.</p>',
    attachTo: { element: '[data-testid="dimensions-widget"]', on: "top" },
    showOn: () => !!document.querySelector('[data-testid="dimensions-widget"]'),
  },
];

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

  // P0 zero-churn: Dashboard tour (auto-trigger on first visit)
  const {
    isCompleted: isDashboardTourCompleted,
    startTour: startDashboardTour,
  } = useShepherdTour({
    tourId: "dashboard",
    steps: DASHBOARD_TOUR_STEPS,
    onComplete: (stepsSeen) => trackEvent("onboarding_tour_completed", { tour: "dashboard", steps_seen: stepsSeen }),
    onSkip: (stepsSeen) => trackEvent("onboarding_tour_skipped", { tour: "dashboard", skipped_at_step: stepsSeen }),
  });

  // STORY-260: Profile completeness (FE-007: SWR)
  // Local override allows ProfileCompletionPrompt to show immediate feedback;
  // SWR revalidates on next render cycle.
  const { completenessPct: swrProfilePct } = useProfileCompleteness();
  const [profilePctOverride, setProfilePctOverride] = useState<number | null>(null);
  const profilePct = profilePctOverride ?? swrProfilePct;

  // DEBT-127: Insight cards data
  const [pipelineAlerts, setPipelineAlerts] = useState<PipelineAlertsData | null>(null);
  const [newOpportunities, setNewOpportunities] = useState<NewOpportunitiesData | null>(null);

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

  // DEBT-127: Fetch pipeline alerts
  const fetchPipelineAlerts = useCallback(
    async (signal?: AbortSignal) => {
      if (!session?.access_token) return;
      try {
        const res = await fetch("/api/pipeline?_path=/pipeline/alerts", {
          headers: { Authorization: `Bearer ${session.access_token}` },
          signal,
        });
        if (res.ok) setPipelineAlerts(await res.json());
      } catch {
        // Non-critical — silently fail
      }
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
        // DEBT-127: Fetch insights in parallel (non-blocking)
        fetchAnalytics("new-opportunities", undefined, signal).then((d) => {
          setNewOpportunities(d);
          return d;
        }),
        fetchPipelineAlerts(signal),
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
    [period, fetchAnalytics, fetchPipelineAlerts, trackEvent]
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

  // UX-431: Refetch dashboard data when tab becomes visible (prevents stale "last search")
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === "visible" && session && !authLoading) {
        manualRetry();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, [session, authLoading, manualRetry]);

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

  // P0 zero-churn: Auto-start dashboard tour on first visit
  const dashboardTourStarted = useRef(false);
  useEffect(() => {
    if (!loading && data && !dashboardTourStarted.current && !isDashboardTourCompleted()) {
      dashboardTourStarted.current = true;
      const timer = setTimeout(() => startDashboardTour(), 800);
      return () => clearTimeout(timer);
    }
  }, [loading, data, isDashboardTourCompleted, startDashboardTour]);

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
        {/* P0 zero-churn: Trial value tracker */}
        <div className="mb-6">
          <TrialValueTracker />
        </div>

        {/* Zero-Churn P2 §8.2: Trial extension actions checklist */}
        <TrialExtensionCard />

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

        {/* DEBT-127 AC10: Insight cards prominently positioned before charts */}
        <InsightCards
          pipelineAlerts={pipelineAlerts}
          newOpportunities={newOpportunities}
        />

        <div data-testid="dashboard-stat-cards">
          <DashboardStatCards
            summary={summary}
            summaryError={summaryError}
            onRetry={manualRetry}
          />
        </div>

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

        <div data-testid="timeseries-chart">
          <DashboardTimeSeriesChart
            timeSeries={timeSeries}
            timeSeriesError={timeSeriesError}
            period={period}
            setPeriod={setPeriod}
            isMobile={isMobile}
            onRetry={manualRetry}
          />
        </div>

        <div data-testid="dimensions-widget">
        <DashboardDimensionsWidget
          dimensions={dimensions}
          dimensionsError={dimensionsError}
          ufPieData={ufPieData}
          sectorChartData={sectorChartData}
          isMobile={isMobile}
          onRetry={manualRetry}
        />
        </div>

        <DashboardQuickLinks />
      </div>
    </div>
    </PageErrorBoundary>
  );
}
