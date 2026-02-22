"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics } from "../../hooks/useAnalytics";
import { PageHeader } from "../../components/PageHeader";
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

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech";

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

const CHART_COLORS = [
  "#116dff", "#0d5ad4", "#0a1e3f", "#3b8bff", "#6aa7ff",
  "#16a34a", "#ca8a04", "#dc2626", "#8b5cf6", "#ec4899",
];

// ============================================================================
// Helpers
// ============================================================================

function formatCurrency(val: number): string {
  if (val >= 1_000_000) return `R$ ${(val / 1_000_000).toFixed(1)}M`;
  if (val >= 1_000) return `R$ ${(val / 1_000).toFixed(0)}k`;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val);
}

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
}: {
  icon: string;
  label: string;
  value: string;
  subtitle?: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`p-5 rounded-card border transition-colors ${
        accent
          ? "bg-[var(--brand-blue-subtle)] border-[var(--border-accent)]"
          : "bg-[var(--surface-0)] border-[var(--border)]"
      }`}
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
              aria-label="Ícone" width="100" height="100" viewBox="0 0 100 100">
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
        {used} de {total === -1 ? "ilimitado" : total} buscas
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

export default function DashboardPage() {
  const { session, user, loading: authLoading } = useAuth();
  const { trackEvent } = useAnalytics();

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>([]);
  const [dimensions, setDimensions] = useState<TopDimensions | null>(null);
  const [period, setPeriod] = useState<Period>("week");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch helper
  const fetchAnalytics = useCallback(
    async (endpoint: string, params?: Record<string, string>) => {
      if (!session?.access_token) return null;

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      const searchParams = new URLSearchParams(params);

      let url: string;
      if (backendUrl) {
        url = `${backendUrl}/v1/analytics/${endpoint}${searchParams.toString() ? `?${searchParams}` : ""}`;
      } else {
        searchParams.set("endpoint", endpoint);
        url = `/api/analytics?${searchParams}`;
      }

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error(`Erro ao carregar ${endpoint}`);
      return res.json();
    },
    [session?.access_token]
  );

  // Load all data
  useEffect(() => {
    if (authLoading || !session) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [summaryData, timeData, dimData] = await Promise.all([
          fetchAnalytics("summary"),
          fetchAnalytics("searches-over-time", { period, range_days: "90" }),
          fetchAnalytics("top-dimensions", { limit: "7" }),
        ]);
        setSummary(summaryData);
        setTimeSeries(timeData?.data || []);
        setDimensions(dimData);
        trackEvent("dashboard_viewed", { period });
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Erro ao carregar dashboard");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [authLoading, session, period, fetchAnalytics, trackEvent]);

  // Reload time series when period changes
  useEffect(() => {
    if (!session || authLoading || loading) return;

    fetchAnalytics("searches-over-time", { period, range_days: "90" })
      .then((data) => {
        if (data) setTimeSeries(data.data || []);
      })
      .catch(() => {});
  }, [period]);

  // CSV export
  const handleExportCSV = useCallback(() => {
    if (!summary || !dimensions) return;

    const rows = [
      ["Metrica", "Valor"],
      ["Total de Buscas", String(summary.total_searches)],
      ["Total de Downloads", String(summary.total_downloads)],
      ["Oportunidades Encontradas", String(summary.total_opportunities)],
      ["Valor Total Descoberto", String(summary.total_value_discovered)],
      ["Horas Economizadas", String(summary.estimated_hours_saved)],
      ["Taxa de Sucesso", `${summary.success_rate}%`],
      [""],
      ["Top UFs", "Buscas", "Valor"],
      ...dimensions.top_ufs.map((u) => [u.name, String(u.count), String(u.value)]),
      [""],
      ["Top Setores", "Buscas", "Valor"],
      ...dimensions.top_sectors.map((s) => [s.name, String(s.count), String(s.value)]),
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
      dimensions?.top_ufs.map((u, i) => ({
        name: UF_NAMES[u.name] || u.name,
        value: u.count,
        fill: CHART_COLORS[i % CHART_COLORS.length],
      })) || [],
    [dimensions]
  );

  // ──────────────────────────────────────────────────────────────────────────
  // Auth guard
  // ──────────────────────────────────────────────────────────────────────────

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center">
          <p className="text-[var(--ink-secondary)] mb-4">Faça login para acessar o dashboard</p>
          <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
            Ir para login
          </Link>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Loading state
  // ──────────────────────────────────────────────────────────────────────────

  if (loading) {
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
  // Error state
  // ──────────────────────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
        <div className="max-w-6xl mx-auto text-center py-16">
          <p className="text-[var(--error)] text-lg mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Empty state
  // ──────────────────────────────────────────────────────────────────────────

  if (summary && summary.total_searches === 0) {
    return (
      <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">Meu Dashboard</h1>
          <div className="text-center py-20">
            <span className="text-5xl mb-6 block">📊</span>
            <h2 className="text-xl font-display font-semibold text-[var(--ink)] mb-3">
              Seu dashboard está vazio
            </h2>
            <p className="text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
              Faça sua primeira busca para começar a ver estatísticas sobre oportunidades
              descobertas e valor identificado.
            </p>
            <Link
              href="/buscar"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                         rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
            >
              <svg
              role="img"
              aria-label="Pesquisar" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Fazer primeira busca
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
      <PageHeader
        title="Dashboard"
        extraControls={
          <>
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
        {/* Subtitle */}
        {summary && (
          <p className="text-sm text-[var(--ink-muted)] mb-6">
            Membro desde {formatDate(summary.member_since)}
          </p>
        )}

        {/* Stat Cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
            <StatCard
              icon="🔍"
              label="Buscas realizadas"
              value={formatNumber(summary.total_searches)}
            />
            <StatCard
              icon="📋"
              label="Oportunidades encontradas"
              value={formatNumber(summary.total_opportunities)}
              subtitle={`~${summary.avg_results_per_search} por busca`}
            />
            <StatCard
              icon="💰"
              label="Valor total descoberto"
              value={formatCurrency(summary.total_value_discovered)}
              accent
            />
            <StatCard
              icon="⏱️"
              label="Horas economizadas"
              value={`${formatNumber(summary.estimated_hours_saved)}h`}
              subtitle="vs busca manual em portais"
            />
            <StatCard
              icon="✅"
              label="Taxa de sucesso"
              value={`${summary.success_rate}%`}
              subtitle={`${summary.total_downloads} com resultados`}
            />
          </div>
        )}

        {/* Time Series Chart */}
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
                  {p === "day" ? "Dia" : p === "week" ? "Semana" : "Mês"}
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
                  name="Buscas"
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
              Sem dados para o período selecionado
            </div>
          )}
        </div>

        {/* Top Dimensions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Top UFs */}
          <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6">
            <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
              Estados mais buscados
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
              Setores mais buscados
            </h2>
            {dimensions && dimensions.top_sectors.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={dimensions.top_sectors}
                  layout="vertical"
                  margin={{ left: 10, right: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                  <XAxis type="number" tick={{ fill: "var(--ink-muted)", fontSize: 11 }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={120}
                    tick={{ fill: "var(--ink-secondary)", fontSize: 11 }}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="count" fill="#116dff" radius={[0, 4, 4, 0]} name="Buscas" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-[var(--ink-muted)] text-sm">Sem dados ainda</p>
            )}
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6">
          <h2 className="text-lg font-display font-semibold text-[var(--ink)] mb-4">
            Acesso rápido
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Link
              href="/buscar"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">🔍</span>
              <span className="text-sm text-[var(--ink)]">Nova Busca</span>
            </Link>
            <Link
              href="/historico"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">📜</span>
              <span className="text-sm text-[var(--ink)]">Histórico</span>
            </Link>
            <Link
              href="/conta"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">⚙️</span>
              <span className="text-sm text-[var(--ink)]">Minha Conta</span>
            </Link>
            <Link
              href="/planos"
              className="flex items-center gap-3 p-3 rounded-card border border-[var(--border)]
                         hover:border-[var(--border-strong)] hover:bg-[var(--surface-1)] transition-colors"
            >
              <span className="text-xl">💎</span>
              <span className="text-sm text-[var(--ink)]">Planos</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
