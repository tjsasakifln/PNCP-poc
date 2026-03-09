"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useBackendStatusContext } from "../../components/BackendStatusIndicator";
import { useFetchWithBackoff } from "../../hooks/useFetchWithBackoff";
import { PageHeader } from "../../components/PageHeader";
import { ErrorStateWithRetry } from "../../components/ErrorStateWithRetry";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import ProfileCompletionPrompt from "../../components/ProfileCompletionPrompt";
import ProfileProgressBar from "../../components/ProfileProgressBar";
import ProfileCongratulations from "../../components/ProfileCongratulations";
import Link from "next/link";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { TrialUpsellCTA } from "../../components/billing/TrialUpsellCTA";
import { usePlan } from "../../hooks/usePlan";
import { formatCurrencyBR } from "../../lib/format-currency";
import { APP_NAME } from "../../lib/config";

// UX-406: Feature flag — organizations/teams not yet implemented in backend
const ORGS_ENABLED = process.env.NEXT_PUBLIC_ORGS_ENABLED === "true";

// ============================================================================
// Types
// ============================================================================

interface AnalyticsSummary {
  total_searches: number;
  total_downloads: number;
  total_opportunities: number;
  total_value_discovered: number;
  estimated_hours_saved: number;
  avg_results_per_search: number;
  success_rate: number;
  member_since: string;
}

interface TimeSeriesPoint {
  label: string;
  searches: number;
  opportunities: number;
  value: number;
}

interface DimensionItem {
  name: string;
  count: number;
  value: number;
}

interface TopDimensions {
  top_ufs: DimensionItem[];
  top_sectors: DimensionItem[];
}

type Period = "day" | "week" | "month";

// ============================================================================
// Constants
// ============================================================================

import { UF_NAMES } from "../../lib/constants/uf-names";
import { getSectorDisplayName } from "../../lib/constants/sector-names";

// DEBT-012: References CSS vars defined in globals.css (--chart-1 … --chart-10)
const CHART_COLORS = [
  "var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)",
  "var(--chart-6)", "var(--chart-7)", "var(--chart-8)", "var(--chart-9)", "var(--chart-10)",
];

// ============================================================================
// Helpers
// ============================================================================

// SAB-012 AC5: PT-BR currency formatting with abbreviations (bi/mi)
const formatCurrency = formatCurrencyBR;

function formatNumber(val: number): string {
  return new Intl.NumberFormat("pt-BR").format(val);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit", month: "long", year: "numeric",
  });
}

// ============================================================================
// Stat Card Component
// ============================================================================

function StatCard({
  icon,
  label,
  value,
  subtitle,
  accent = false,
  tooltip,
}: {
  icon: string;
  label: string;
  value: string;
  subtitle?: string;
  accent?: boolean;
  tooltip?: string;
}) {
  return (
    <div
      className={`p-5 rounded-card border transition-colors ${
        accent
          ? "bg-[var(--brand-blue-subtle)] border-[var(--border-accent)]"
          : "bg-[var(--surface-0)] border-[var(--border)]"
      }`}
      title={tooltip}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-2xl font-display font-bold text-[var(--ink)]">{value}</p>
      <p className="text-sm text-[var(--ink-secondary)] mt-1">{label}</p>
      {subtitle && (
        <p className="text-xs text-[var(--ink-muted)] mt-1">{subtitle}</p>
      )}
    </div>
  );
}

// ============================================================================
// Quota Gauge Component
// ============================================================================

function QuotaRing({ used, total }: { used: number; total: number }) {
  const pct = total > 0 ? Math.min((used / total) * 100, 100) : 0;
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (pct / 100) * circumference;
  const color = pct > 90 ? "var(--error)" : pct > 70 ? "var(--warning)" : "var(--brand-blue)";

  return (
    <div className="flex flex-col items-center">
      <svg
              role="img"
              aria-label={"Ícone"} width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="var(--border)" strokeWidth="8" />
        <circle
          cx="50" cy="50" r="40" fill="none"
          stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text x="50" y="46" textAnchor="middle" className="text-lg font-bold" fill="var(--ink)">
          {Math.round(pct)}%
        </text>
        <text x="50" y="62" textAnchor="middle" className="text-[10px]" fill="var(--ink-muted)">
          utilizado
        </text>
      </svg>
      <p className="text-xs text-[var(--ink-secondary)] mt-1">
        {used} de {total === -1 ? "ilimitado" : total} análises
      </p>
    </div>
  );
}

// ============================================================================
// Custom Tooltip for Charts
// ============================================================================

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[var(--surface-elevated)] border border-[var(--border)] rounded-card p-3 shadow-lg text-sm">
      <p className="font-medium text-[var(--ink)] mb-1">{label}</p>
      {payload.map((entry, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-xs">
          {entry.name}: {entry.name === "value" ? formatCurrency(entry.value) : formatNumber(entry.value)}
        </p>
      ))}
    </div>
  );
}

// ============================================================================
// Main Dashboard Page
// ============================================================================

const LOADING_TIMEOUT_MS = 10_000;

// CRIT-018: Dashboard data bundle returned by the fetch hook
// AC4/AC5: Per-section error flags for independent failure handling
interface DashboardData {
  summary: AnalyticsSummary | null;
  timeSeries: TimeSeriesPoint[];
  dimensions: TopDimensions | null;
  summaryError?: boolean;
  timeSeriesError?: boolean;
  dimensionsError?: boolean;
}

export default function DashboardPage() {
  const { session, user, loading: authLoading } = useAuth();
  const { trackEvent } = useAnalytics();
  const { status: backendStatus } = useBackendStatusContext();
  const { planInfo } = usePlan();

  const [period, setPeriod] = useState<Period>("week");
  const [profilePct, setProfilePct] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"personal" | "team">("personal");
  const [userOrg, setUserOrg] = useState<{ id: string; name: string; user_role: string } | null>(null);
  const [teamData, setTeamData] = useState<DashboardData | null>(null);
  const [teamLoading, setTeamLoading] = useState(false);

  // STORY-260: Fetch profile completeness on mount (for header ring + conditional components)
  useEffect(() => {
    if (!session?.access_token) return;
    let cancelled = false;
    fetch("/api/profile-completeness", {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!cancelled && data?.completeness_pct !== undefined) {
          setProfilePct(data.completeness_pct as number);
        }
      })
      .catch(() => {
        // best-effort: don't show profile section if fetch fails
      });
    return () => {
      cancelled = true;
    };
  }, [session?.access_token]);

  // AC19: Fetch org membership — show team toggle only for owners/admins
  // UX-406: Gated by ORGS_ENABLED — backend endpoint doesn't exist yet
  useEffect(() => {
    if (!ORGS_ENABLED || !session?.access_token) return;
    fetch("/api/organizations/me", {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (
          data?.organization &&
          ["owner", "admin"].includes(data.organization.user_role)
        ) {
          setUserOrg(data.organization);
        }
      })
      .catch(() => {});
  }, [session?.access_token]);

  // AC19: Fetch team dashboard data when switching to team view
  // UX-406: Gated by ORGS_ENABLED — backend endpoint doesn't exist yet
  useEffect(() => {
    if (!ORGS_ENABLED || viewMode !== "team" || !userOrg || !session?.access_token) return;
    setTeamLoading(true);
    fetch(`/api/organizations/${userOrg.id}/dashboard`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setTeamData({
            summary: data.summary ?? null,
            timeSeries: data.time_series ?? [],
            dimensions: data.dimensions ?? null,
          });
        }
      })
      .catch(() => {})
      .finally(() => setTeamLoading(false));
  }, [viewMode, userOrg, session?.access_token]);

  // Stable fetch helper — always uses proxy to avoid CORS issues
  const fetchAnalytics = useCallback(
    async (endpoint: string, params?: Record<string, string>, signal?: AbortSignal) => {
      if (!session?.access_token) return null;

      const searchParams = new URLSearchParams(params);
      searchParams.set("endpoint", endpoint);
      const url = `/api/analytics?${searchParams}`;

      const res = await fetch(url, {
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

  // CRIT-018 AC1-AC6: Backoff-managed fetch with backend status integration
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

  // AC19: Active dataset — personal or team view
  const activeData = viewMode === "team" && teamData ? teamData : data;

  const summary = activeData?.summary ?? null;
  const timeSeries = activeData?.timeSeries ?? [];
  const dimensions = activeData?.dimensions ?? null;

  // CSV export
  const handleExportCSV = useCallback(() => {
    if (!summary || !dimensions) return;

    const rows = [
      ["Metrica", "Valor"],
      ["Total de Análises", String(summary.total_searches)],
      ["Total de Downloads", String(summary.total_downloads)],
      ["Oportunidades Encontradas", String(summary.total_opportunities)],
      ["Valor Total Descoberto", String(summary.total_value_discovered)],
      ["Horas Economizadas", String(summary.estimated_hours_saved)],
      ["Taxa de Sucesso", `${summary.success_rate}%`],
      [""],
      ["Top UFs", "Análises", "Valor"],
      ...dimensions.top_ufs.map((u) => [u.name, String(u.count), String(u.value)]),
      [""],
      ["Top Setores", "Análises", "Valor"],
      ...dimensions.top_sectors.map((s) => [getSectorDisplayName(s.name), String(s.count), String(s.value)]),
    ];

    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${APP_NAME.toLowerCase()}-analytics-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    trackEvent("analytics_exported", { format: "csv" });
  }, [summary, dimensions, trackEvent]);

  // Pie chart data for UFs
  const ufPieData = useMemo(
    () =>
      dimensions?.top_ufs?.map((u, i) => ({
        name: UF_NAMES[u.name] || u.name,
        value: u.count,
        fill: CHART_COLORS[i % CHART_COLORS.length],
      })) || [],
    [dimensions]
  );

  // UX-356 AC1-AC2: Map sector slugs to display names
  const sectorChartData = useMemo(
    () =>
      dimensions?.top_sectors?.map((s) => ({
        ...s,
        name: getSectorDisplayName(s.name),
      })) || [],
    [dimensions]
  );

  // ──────────────────────────────────────────────────────────────────────────
  // Auth guard
  // ──────────────────────────────────────────────────────────────────────────

  // GTM-POLISH-001 AC1-AC3: Unified auth loading
  if (authLoading) {
    return <AuthLoadingScreen />;
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center">
          <p className="text-[var(--ink-secondary)] mb-4">{`Faça login para acessar o dashboard`}</p>
          <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
            Ir para login
          </Link>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CRIT-018 AC8: Error state with cloud+X icon + manual retry
  // ──────────────────────────────────────────────────────────────────────────

  // CRIT-031 AC1-AC3: Full-page error state only when ALL sections failed and no data at all
  // AC5: If at least some data loaded (partial success via allSettled), show per-card errors instead
  const allSectionsFailed = summaryError && timeSeriesError && dimensionsError;
  if (error && hasExhaustedRetries && !data) {
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
        <div className="max-w-6xl mx-auto text-center py-16" data-testid="dashboard-empty-state">
          <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--surface-1)]">
            <svg
              aria-hidden="true"
              className="w-8 h-8 text-[var(--ink-muted)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2 15a5 5 0 005 5h9a5 5 0 10-4.5-7.17A4 4 0 002 15z"
              />
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.5 12.5l5 5m0-5l-5 5" />
            </svg>
          </div>
          <p className="text-lg font-display font-semibold text-[var(--ink)] mb-2">
            {`Dados temporariamente indisponíveis`}
          </p>
          <p className="text-sm text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
            Tente novamente em alguns minutos.
          </p>
          <button
            onClick={manualRetry}
            className="px-5 py-2.5 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
            data-testid="dashboard-retry-button"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  // Also show full-page error when data came back but ALL sections failed
  if (data && allSectionsFailed) {
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
        <div className="max-w-6xl mx-auto text-center py-16" data-testid="dashboard-empty-state">
          <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--surface-1)]">
            <svg
              aria-hidden="true"
              className="w-8 h-8 text-[var(--ink-muted)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2 15a5 5 0 005 5h9a5 5 0 10-4.5-7.17A4 4 0 002 15z"
              />
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.5 12.5l5 5m0-5l-5 5" />
            </svg>
          </div>
          <p className="text-lg font-display font-semibold text-[var(--ink)] mb-2">
            {`Dados temporariamente indisponíveis`}
          </p>
          <p className="text-sm text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
            Tente novamente em alguns minutos.
          </p>
          <button
            onClick={manualRetry}
            className="px-5 py-2.5 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
            data-testid="dashboard-retry-button"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  // Transient error during retries (still retrying automatically)
  // Only show full-page retrying state when we have no data at all
  if (error && !hasExhaustedRetries && !data) {
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
        <div className="max-w-6xl mx-auto text-center py-16" data-testid="dashboard-retrying">
          <div className="mx-auto mb-4 w-8 h-8 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-[var(--ink-secondary)]">
            Tentando reconectar... ({retryCount}/3)
          </p>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Loading state (AC9/AC10: skeletons shown only on initial load, max 10s)
  // ──────────────────────────────────────────────────────────────────────────

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="h-8 w-48 bg-[var(--surface-1)] rounded animate-pulse mb-8" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-[var(--surface-1)] rounded-card animate-pulse" />
            ))}
          </div>
          <div className="h-64 bg-[var(--surface-1)] rounded-card animate-pulse mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-48 bg-[var(--surface-1)] rounded-card animate-pulse" />
            <div className="h-48 bg-[var(--surface-1)] rounded-card animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Empty state
  // ──────────────────────────────────────────────────────────────────────────

  if (summary && summary.total_searches === 0) {
    return (
      <div className="min-h-screen bg-[var(--canvas)]">
        <PageHeader title="Dashboard" />
        <div className="max-w-6xl mx-auto py-8 px-4">
          <div className="text-center py-16 px-4" data-testid="empty-state">
            <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--brand-blue-subtle)]">
              <svg aria-hidden="true" className="w-8 h-8 text-[var(--brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <h2 className="text-xl font-display font-semibold text-[var(--ink)] mb-3">
              {`Seu Painel de Inteligência`}
            </h2>
            <p className="text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
              {`Após suas primeiras análises, você verá aqui:`}
            </p>
            <ul className="text-left max-w-sm mx-auto mb-8 space-y-2">
              <li className="flex items-center gap-2 text-sm text-[var(--ink-secondary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-blue)] flex-shrink-0" />
                Resumo de oportunidades encontradas
              </li>
              <li className="flex items-center gap-2 text-sm text-[var(--ink-secondary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-blue)] flex-shrink-0" />
                {`Tendências do seu setor`}
              </li>
              <li className="flex items-center gap-2 text-sm text-[var(--ink-secondary)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-blue)] flex-shrink-0" />
                Valor total de oportunidades analisadas
              </li>
            </ul>
            <Link
              href="/buscar"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                         rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
              data-testid="empty-state-cta"
            >
              Fazer primeira análise

              <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Dashboard content
  // ──────────────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      {/* CRIT-031 AC4: Stale data banner when showing cached data after error */}
      {error && hasExhaustedRetries && data && (
        <div className="max-w-6xl mx-auto px-4 pt-4" data-testid="stale-data-banner">
          <div className="flex items-center justify-between p-3 rounded-card border border-[var(--border)] bg-[var(--surface-1)]">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--warning)] flex-shrink-0" />
              <span className="text-sm text-[var(--ink-secondary)]">
                Dados podem estar desatualizados
              </span>
            </div>
            <button
              onClick={manualRetry}
              className="text-sm font-medium text-[var(--brand-blue)] hover:underline"
              data-testid="stale-data-retry"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      )}

      <PageHeader
        title="Dashboard"
        extraControls={
          <>
            {/* STORY-260: Profile progress ring in header */}
            {profilePct !== null && profilePct < 100 && (
              <ProfileProgressBar
                percentage={profilePct}
                size={40}
                onClickNext={() => {
                  // Scroll to the profile prompt below the header
                  const el = document.querySelector("[data-testid='profile-completion-prompt']");
                  if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
                }}
              />
            )}
            <button
              onClick={handleExportCSV}
              className="hidden sm:flex px-3 py-1.5 text-sm border border-[var(--border)] rounded-button
                         text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] transition-colors items-center gap-1.5"
            >
              <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              CSV
            </button>
          </>
        }
      />
      <div className="max-w-6xl mx-auto py-8 px-4">
        {/* AC19: Team/personal data toggle — shown only to org owners/admins */}
        {/* UX-406: Gated by ORGS_ENABLED feature flag */}
        {ORGS_ENABLED && userOrg && (
          <div className="flex items-center gap-2 mb-4" data-testid="team-toggle">
            <button
              onClick={() => setViewMode("personal")}
              className={`px-3 py-1.5 text-sm rounded-button transition-colors ${
                viewMode === "personal"
                  ? "bg-[var(--brand-blue)] text-white"
                  : "bg-[var(--surface-1)] text-[var(--ink-secondary)]"
              }`}
              data-testid="toggle-personal"
            >
              Meus dados
            </button>
            <button
              onClick={() => setViewMode("team")}
              className={`px-3 py-1.5 text-sm rounded-button transition-colors ${
                viewMode === "team"
                  ? "bg-[var(--brand-blue)] text-white"
                  : "bg-[var(--surface-1)] text-[var(--ink-secondary)]"
              }`}
              data-testid="toggle-team"
            >
              Dados da equipe
            </button>
            {viewMode === "team" && (
              <span className="text-xs text-[var(--ink-muted)] ml-1">{userOrg.name}</span>
            )}
          </div>
        )}

        {/* AC19: Team loading spinner */}
        {ORGS_ENABLED && viewMode === "team" && teamLoading && (
          <div className="flex items-center gap-2 mb-4 text-sm text-[var(--ink-secondary)]" data-testid="team-loading">
            <div className="w-4 h-4 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
            Carregando dados da equipe...
          </div>
        )}

        {/* Subtitle */}
        {summary && viewMode === "personal" && (
          <p className="text-sm text-[var(--ink-muted)] mb-6">
            Membro desde {formatDate(summary.member_since)}
          </p>
        )}
        {ORGS_ENABLED && viewMode === "team" && userOrg && (
          <p className="text-sm text-[var(--ink-muted)] mb-6">
            Dados agregados da equipe — {userOrg.name}
          </p>
        )}

        {/* STORY-260: Profile completion — congratulations when 100%, prompt otherwise */}
        {session && profilePct === 100 && (
          <div className="mb-6">
            <ProfileCongratulations />
          </div>
        )}
        {session && profilePct !== null && profilePct !== 100 && (
          <div className="mb-6">
            {/* AC13: "Completar perfil" link above the prompt */}
            <div className="flex items-center justify-end mb-2">
              <a href="/conta#perfil" className="text-sm text-[var(--brand-blue)] hover:underline">
                Completar perfil →
              </a>
            </div>
            <ProfileCompletionPrompt
              accessToken={session.access_token}
              onProfileUpdated={(pct) => setProfilePct(pct)}
            />
          </div>
        )}

        {/* AC4/AC5: Stat Cards — show per-card error if summary fetch failed */}
        {summaryError ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
            <div className="col-span-full bg-[var(--surface-0)] border border-[var(--border)] rounded-card" data-testid="summary-error">
              <ErrorStateWithRetry
                message={`Dados indisponíveis.`}
                onRetry={manualRetry}
                compact
              />
            </div>
          </div>
        ) : summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
            <StatCard
              icon={"\uD83D\uDD0D"}
              label="Análises realizadas"
              value={formatNumber(summary.total_searches)}
            />
            <StatCard
              icon={"\uD83D\uDCCB"}
              label="Oportunidades encontradas"
              value={formatNumber(summary.total_opportunities)}
              subtitle={`~${summary.avg_results_per_search} por análise`}
            />
            <StatCard
              icon={"\uD83D\uDCB0"}
              label="Valor total descoberto"
              value={formatCurrency(summary.total_value_discovered)}
              accent
            />
            <StatCard
              icon={"\u23F1\uFE0F"}
              label="Horas economizadas"
              value={`${formatNumber(summary.estimated_hours_saved)}h`}
              subtitle="vs análise manual em portais"
              tooltip={`Estimativa: ${formatNumber(summary.total_searches)} análises × 2h por análise manual em portais governamentais`}
            />
            <StatCard
              icon={"\u2705"}
              label="Taxa de sucesso"
              value={`${summary.success_rate}%`}
              subtitle={`${summary.total_downloads} com resultados`}
            />
          </div>
        )}

        {/* STORY-312 AC4: Dashboard CTA for trial users with >= 3 searches */}
        {summary && summary.total_searches >= 3 && (
          <div className="mb-8">
            <TrialUpsellCTA
              variant="dashboard"
              planId={planInfo?.plan_id}
              subscriptionStatus={planInfo?.subscription_status}
              contextData={{
                valor: formatCurrency(summary.total_value_discovered).replace("R$ ", ""),
              }}
            />
          </div>
        )}

        {/* AC4/AC5: Time Series Chart — show per-card error if time series fetch failed */}
        {timeSeriesError ? (
          <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6 mb-8" data-testid="timeseries-error">
            <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
              Buscas ao longo do tempo
            </h2>
            <ErrorStateWithRetry
              message={`Dados indisponíveis.`}
              onRetry={manualRetry}
              compact
            />
          </div>
        ) : (
          <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-display font-semibold text-[var(--ink)]">
                Buscas ao longo do tempo
              </h2>
              <div className="flex bg-[var(--surface-1)] rounded-button p-0.5">
                {(["day", "week", "month"] as Period[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`px-3 py-1 text-xs rounded-button transition-colors ${
                      period === p
                        ? "bg-[var(--brand-blue)] text-white"
                        : "text-[var(--ink-secondary)] hover:text-[var(--ink)]"
                    }`}
                  >
                    {p === "day" ? "Dia" : p === "week" ? "Semana" : `Mês`}
                  </button>
                ))}
              </div>
            </div>

            {timeSeries.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={timeSeries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis
                    dataKey="label"
                    tick={{ fill: "var(--ink-muted)", fontSize: 12 }}
                    axisLine={{ stroke: "var(--border)" }}
                  />
                  <YAxis
                    tick={{ fill: "var(--ink-muted)", fontSize: 12 }}
                    axisLine={{ stroke: "var(--border)" }}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="searches"
                    stroke="#116dff"
                    strokeWidth={2}
                    dot={{ fill: "#116dff", r: 4 }}
                    name="Análises"
                  />
                  <Line
                    type="monotone"
                    dataKey="opportunities"
                    stroke="#16a34a"
                    strokeWidth={2}
                    dot={{ fill: "#16a34a", r: 4 }}
                    name="Oportunidades"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-[var(--ink-muted)]">
                {`Sem dados para o período selecionado`}
              </div>
            )}
          </div>
        )}

        {/* AC4/AC5: Top Dimensions — show per-card error if dimensions fetch failed */}
        {dimensionsError ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6" data-testid="dimensions-error">
              <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
                Estados mais analisados
              </h2>
              <ErrorStateWithRetry
                message={`Dados indisponíveis.`}
                onRetry={manualRetry}
                compact
              />
            </div>
            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6" data-testid="dimensions-error">
              <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
                Setores mais analisados
              </h2>
              <ErrorStateWithRetry
                message={`Dados indisponíveis.`}
                onRetry={manualRetry}
                compact
              />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Top UFs */}
            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6">
              <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
                Estados mais analisados
              </h2>
              {dimensions && dimensions.top_ufs.length > 0 ? (
                <div className="flex gap-6">
                  <div className="flex-1">
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={ufPieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={80}
                          dataKey="value"
                          stroke="none"
                        >
                          {ufPieData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex-1 space-y-2">
                    {dimensions.top_ufs.map((uf, i) => (
                      <div key={uf.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
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
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={sectorChartData}
                    layout="vertical"
                    margin={{ left: 10, right: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                    <XAxis type="number" tick={{ fill: "var(--ink-muted)", fontSize: 11 }} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={160}
                      tick={{ fill: "var(--ink-secondary)", fontSize: 11 }}
                      tickFormatter={(v: string) => v.length > 22 ? v.slice(0, 20) + "\u2026" : v}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="count" fill="#116dff" radius={[0, 4, 4, 0]} name="Análises" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-[var(--ink-muted)] text-sm">Sem dados ainda</p>
              )}
            </div>
          </div>
        )}

        {/* Quick Links */}
        <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6">
          <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
            {`Acesso rápido`}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Link
              href="/buscar"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">{"\uD83D\uDD0D"}</span>
              <span className="text-sm text-[var(--ink)]">Nova Busca</span>
            </Link>
            <Link
              href="/historico"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">{"\uD83D\uDCDC"}</span>
              <span className="text-sm text-[var(--ink)]">{`Histórico`}</span>
            </Link>
            <Link
              href="/conta"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">{"\u2699\uFE0F"}</span>
              <span className="text-sm text-[var(--ink)]">Minha Conta</span>
            </Link>
            <Link
              href="/planos"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">{"\uD83D\uDC8E"}</span>
              <span className="text-sm text-[var(--ink)]">Planos</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
