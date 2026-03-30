"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";

interface DashboardMetrics {
  search: {
    total: number;
    active: number;
    avg_duration_s: number;
  };
  cache: {
    hits: number;
    misses: number;
    hit_rate: number;
  };
  errors: {
    api_total: number;
    search_total: number;
    sse_total: number;
    rate_limit_total: number;
    by_source: Array<{ labels: Record<string, string>; value: number }>;
  };
  llm: {
    total_calls: number;
    avg_duration_s: number;
    total_tokens: number;
  };
  circuit_breaker: {
    pncp: string;
    portal_compras: string;
    compras_gov: string;
  };
  fetch_durations: Record<string, number>;
  filter_decisions: Array<{ labels: Record<string, string>; value: number }>;
  cta_conversion: Array<{ variant: string; shown: number; clicked: number; dismissed: number; ctr: number }>;
}

interface MetricsResponse {
  raw_available: boolean;
  metrics_count: number;
  dashboard: DashboardMetrics;
}

const CB_COLORS: Record<string, string> = {
  HEALTHY: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  DEGRADED: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
};

export default function AdminMetricsPage() {
  const { session, loading: authLoading, isAdmin, isAdminLoading } = useAuth();
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchMetrics = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/metrics", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.status === 401) {
        setError("Autenticacao necessaria.");
        return;
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Erro ${res.status}`);
      }
      const json = await res.json();
      setData(json);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar metricas");
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (session?.access_token && isAdmin) {
      fetchMetrics();
    } else if (!authLoading && !isAdminLoading) {
      setLoading(false);
    }
  }, [session?.access_token, isAdmin, isAdminLoading, authLoading, fetchMetrics]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!session?.access_token || !isAdmin) return;
    const interval = setInterval(fetchMetrics, 30_000);
    return () => clearInterval(interval);
  }, [session?.access_token, isAdmin, fetchMetrics]);

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
        <Link href="/login" className="text-[var(--brand-blue)]">Login necessario</Link>
      </div>
    );
  }

  if (!isAdmin && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center max-w-md px-4">
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">Acesso Restrito</h1>
          <p className="text-[var(--ink-secondary)] mb-6">
            Esta pagina e exclusiva para administradores.
          </p>
          <Link href="/buscar" className="inline-block px-6 py-2 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors">
            Voltar
          </Link>
        </div>
      </div>
    );
  }

  const d = data?.dashboard;

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)]">
              Admin - Prometheus Metrics
            </h1>
            <p className="text-[var(--ink-secondary)]">
              {data
                ? `${data.metrics_count} metricas coletadas`
                : "Carregando metricas..."}
              {lastRefresh && (
                <span className="ml-2 text-xs">
                  (atualizado {lastRefresh.toLocaleTimeString("pt-BR")})
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/admin"
              className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
            >
              Usuarios
            </Link>
            <Link
              href="/admin/cache"
              className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
            >
              Cache
            </Link>
            <Link
              href="/admin/slo"
              className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
            >
              SLOs
            </Link>
            <button
              onClick={fetchMetrics}
              disabled={loading}
              className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm hover:bg-[var(--brand-blue)] disabled:opacity-50"
            >
              {loading ? "Atualizando..." : "Atualizar"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-[var(--error-subtle)] border border-[var(--error)] rounded-card text-[var(--error)]">
            {error}
          </div>
        )}

        {loading && !d && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-[var(--brand-navy)] border-t-transparent rounded-full" />
          </div>
        )}

        {d && (
          <>
            {/* Circuit Breaker Status */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                Circuit Breaker Status
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <CircuitBreakerCard source="PNCP" state={d.circuit_breaker.pncp} />
                <CircuitBreakerCard source="Portal de Compras" state={d.circuit_breaker.portal_compras} />
                <CircuitBreakerCard source="ComprasGov" state={d.circuit_breaker.compras_gov} />
              </div>
            </div>

            {/* Search Metrics */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                Search Pipeline
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard label="Total Searches" value={String(d.search.total)} />
                <MetricCard label="Active Searches" value={String(d.search.active)} accent={d.search.active > 5 ? "warning" : undefined} />
                <MetricCard label="Avg Duration" value={`${d.search.avg_duration_s}s`} accent={d.search.avg_duration_s > 60 ? "error" : undefined} />
                <MetricCard label="Cache Hit Rate" value={`${d.cache.hit_rate}%`} accent={d.cache.hit_rate < 30 ? "warning" : undefined} />
              </div>
            </div>

            {/* Cache Metrics */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                Cache
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Cache Hits" value={formatNumber(d.cache.hits)} />
                <MetricCard label="Cache Misses" value={formatNumber(d.cache.misses)} />
                <MetricCard label="Hit Rate" value={`${d.cache.hit_rate}%`} />
              </div>
            </div>

            {/* Error Metrics */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                Errors
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard label="API Errors" value={String(d.errors.api_total)} accent={d.errors.api_total > 0 ? "error" : undefined} />
                <MetricCard label="Search Errors" value={String(d.errors.search_total)} accent={d.errors.search_total > 0 ? "error" : undefined} />
                <MetricCard label="SSE Errors" value={String(d.errors.sse_total)} accent={d.errors.sse_total > 0 ? "warning" : undefined} />
                <MetricCard label="Rate Limited" value={String(d.errors.rate_limit_total)} accent={d.errors.rate_limit_total > 0 ? "warning" : undefined} />
              </div>

              {/* Errors by Source */}
              {d.errors.by_source.length > 0 && (
                <div className="mt-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4">
                  <h3 className="text-sm font-semibold text-[var(--ink-secondary)] mb-3">
                    API Errors by Source
                  </h3>
                  <div className="space-y-2">
                    {d.errors.by_source.map((item, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-[var(--ink-secondary)]">
                          {item.labels.source || "unknown"}
                          {item.labels.error_type && (
                            <span className="ml-1 text-xs opacity-70">({item.labels.error_type})</span>
                          )}
                        </span>
                        <span className="font-data text-[var(--ink)]">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* LLM Metrics */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                LLM (GPT-4.1-nano)
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="Total Calls" value={formatNumber(d.llm.total_calls)} />
                <MetricCard label="Avg Latency" value={`${d.llm.avg_duration_s}s`} />
                <MetricCard label="Total Tokens" value={formatNumber(d.llm.total_tokens)} />
              </div>
            </div>

            {/* Fetch Durations by Source */}
            {Object.keys(d.fetch_durations).length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                  Avg Fetch Duration by Source
                </h2>
                <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4">
                  <div className="space-y-3">
                    {Object.entries(d.fetch_durations)
                      .sort(([, a], [, b]) => b - a)
                      .map(([source, avgSec]) => (
                        <div key={source} className="flex items-center gap-3">
                          <span className="w-40 text-sm text-[var(--ink-secondary)] shrink-0">
                            {source}
                          </span>
                          <div className="flex-1 h-4 bg-[var(--surface-2)] rounded overflow-hidden">
                            <div
                              className="h-full bg-[var(--brand-navy)] rounded transition-all"
                              style={{
                                width: `${Math.min(100, (avgSec / 120) * 100)}%`,
                              }}
                            />
                          </div>
                          <span className="w-16 text-right text-sm font-data text-[var(--ink)]">
                            {avgSec.toFixed(1)}s
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}

            {/* Filter Decisions */}
            {d.filter_decisions.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                  Filter Decisions
                </h2>
                <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-[var(--surface-2)] text-left">
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Stage</th>
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Decision</th>
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)] text-right">Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {d.filter_decisions.map((item, i) => (
                        <tr key={i} className="border-t border-[var(--border)]">
                          <td className="px-4 py-2 text-[var(--ink)]">{item.labels.stage || "-"}</td>
                          <td className="px-4 py-2">
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                item.labels.decision === "pass"
                                  ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                                  : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                              }`}
                            >
                              {item.labels.decision || "-"}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-right font-data text-[var(--ink)]">{item.value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* STORY-312 AC11: CTA Conversion Metrics */}
            {d.cta_conversion && d.cta_conversion.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                  CTA Conversion (Trial Upsell)
                </h2>
                <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-[var(--surface-2)] text-left">
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Variant</th>
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)] text-right">Shown</th>
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)] text-right">Clicked</th>
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)] text-right">Dismissed</th>
                        <th className="px-4 py-3 font-medium text-[var(--ink-secondary)] text-right">CTR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {d.cta_conversion.map((row, i) => (
                        <tr key={row.variant} className="border-t border-[var(--border)]">
                          <td className="px-4 py-2 text-[var(--ink)]">
                            <span className="font-medium">{row.variant}</span>
                            {i === 0 && (
                              <span className="ml-2 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                                Top
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2 text-right font-data text-[var(--ink)]">{row.shown}</td>
                          <td className="px-4 py-2 text-right font-data text-[var(--ink)]">{row.clicked}</td>
                          <td className="px-4 py-2 text-right font-data text-[var(--ink-secondary)]">{row.dismissed}</td>
                          <td className="px-4 py-2 text-right">
                            <span
                              className={`font-data font-semibold ${
                                row.ctr >= 10
                                  ? "text-green-600 dark:text-green-400"
                                  : row.ctr >= 5
                                    ? "text-amber-600 dark:text-amber-400"
                                    : "text-[var(--ink-secondary)]"
                              }`}
                            >
                              {row.ctr}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ---------- Helper Components ---------- */

function MetricCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: "error" | "warning";
}) {
  const colorClass =
    accent === "error"
      ? "text-[var(--error)]"
      : accent === "warning"
        ? "text-amber-600 dark:text-amber-400"
        : "text-[var(--ink)]";

  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4">
      <div className="text-sm text-[var(--ink-secondary)] mb-1">{label}</div>
      <div className={`text-2xl font-bold ${colorClass}`}>{value}</div>
    </div>
  );
}

function CircuitBreakerCard({ source, state }: { source: string; state: string }) {
  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4 flex items-center justify-between">
      <div>
        <div className="text-sm text-[var(--ink-secondary)]">Circuit Breaker</div>
        <div className="text-lg font-semibold text-[var(--ink)]">{source}</div>
      </div>
      <span
        className={`px-3 py-1 rounded-full text-sm font-semibold ${
          CB_COLORS[state] || "bg-gray-100 text-gray-800"
        }`}
      >
        {state}
      </span>
    </div>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}
