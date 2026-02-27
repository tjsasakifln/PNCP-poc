"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";

// ============================================================================
// Types
// ============================================================================

interface SLOData {
  key: string;
  name: string;
  description: string;
  target: number;
  window_days: number;
  unit: string;
  sli_value: number | null;
  is_met: boolean;
  error_budget_total: number;
  error_budget_consumed_pct: number;
  error_budget_remaining_pct: number;
}

interface AlertData {
  name: string;
  severity: string;
  for_duration: string;
  summary: string;
  firing: boolean;
  value: number | null;
}

interface SLOResponse {
  compliance: "compliant" | "violation" | "no_data";
  slos: Record<string, SLOData>;
  alerts: AlertData[];
  firing_count: number;
  recording_rules: Record<string, string>;
}

// ============================================================================
// Component
// ============================================================================

export default function AdminSLOPage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const [data, setData] = useState<SLOResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchSLOs = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/slo", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.status === 401) {
        setError("Autenticacao necessaria.");
        return;
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Erro ${res.status}`);
      }
      const json = await res.json();
      setData(json);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar SLOs");
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (session?.access_token && isAdmin) {
      fetchSLOs();
    } else if (!authLoading) {
      setLoading(false);
    }
  }, [session?.access_token, isAdmin, authLoading, fetchSLOs]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    if (!session?.access_token || !isAdmin) return;
    const interval = setInterval(fetchSLOs, 60_000);
    return () => clearInterval(interval);
  }, [session?.access_token, isAdmin, fetchSLOs]);

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

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)]">
              SLO Dashboard
            </h1>
            <p className="text-[var(--ink-secondary)]">
              {data ? (
                <span>
                  Status:{" "}
                  <span className={
                    data.compliance === "compliant"
                      ? "text-green-600 dark:text-green-400 font-semibold"
                      : data.compliance === "violation"
                        ? "text-red-600 dark:text-red-400 font-semibold"
                        : "text-[var(--ink-muted)]"
                  }>
                    {data.compliance === "compliant" ? "All SLOs Met" : data.compliance === "violation" ? "SLO Violation" : "No Data"}
                  </span>
                </span>
              ) : "Carregando..."}
              {lastRefresh && (
                <span className="ml-2 text-xs">
                  (atualizado {lastRefresh.toLocaleTimeString("pt-BR")})
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/admin" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              Usuarios
            </Link>
            <Link href="/admin/metrics" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              Metrics
            </Link>
            <Link href="/admin/cache" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              Cache
            </Link>
            <button
              onClick={fetchSLOs}
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

        {loading && !data && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-[var(--brand-navy)] border-t-transparent rounded-full" />
          </div>
        )}

        {data && (
          <>
            {/* AC7: SLO Compliance Gauges */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                SLO Compliance
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(data.slos).map(([key, slo]) => (
                  <SLOGaugeCard key={key} slo={slo} />
                ))}
              </div>
            </div>

            {/* AC8: Error Budget Remaining */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                Error Budget
              </h2>
              <div className="space-y-4">
                {Object.entries(data.slos).map(([key, slo]) => (
                  <ErrorBudgetBar key={key} slo={slo} />
                ))}
              </div>
            </div>

            {/* Alerts */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                Alert Rules
                {data.firing_count > 0 && (
                  <span className="ml-2 px-2 py-0.5 text-sm rounded-full bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
                    {data.firing_count} firing
                  </span>
                )}
              </h2>
              <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[var(--surface-2)] text-left">
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Alert</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Severity</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Duration</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Value</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.alerts.map((alert) => (
                      <tr key={alert.name} className="border-t border-[var(--border)]">
                        <td className="px-4 py-3">
                          <div className="font-medium text-[var(--ink)]">{alert.name}</div>
                          <div className="text-xs text-[var(--ink-muted)]">{alert.summary}</div>
                        </td>
                        <td className="px-4 py-3">
                          <SeverityBadge severity={alert.severity} />
                        </td>
                        <td className="px-4 py-3 text-[var(--ink-secondary)] font-data">{alert.for_duration}</td>
                        <td className="px-4 py-3 font-data text-[var(--ink)]">
                          {alert.value !== null ? formatAlertValue(alert.name, alert.value) : "-"}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                            alert.firing
                              ? "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                              : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                          }`}>
                            {alert.firing ? "FIRING" : "OK"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* AC9: Recording Rules Reference */}
            {data.recording_rules && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
                  Prometheus Recording Rules
                </h2>
                <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4">
                  <div className="space-y-3">
                    {Object.entries(data.recording_rules).map(([name, expr]) => (
                      <div key={name}>
                        <div className="text-sm font-semibold text-[var(--ink)]">{name}</div>
                        <pre className="text-xs text-[var(--ink-muted)] mt-1 overflow-x-auto whitespace-pre-wrap break-all font-data">
                          {expr}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// AC7: SLO Gauge Card
// ============================================================================

function SLOGaugeCard({ slo }: { slo: SLOData }) {
  const value = slo.sli_value;
  const hasData = value !== null;

  // For ratio SLOs, display as percentage
  const displayValue = hasData
    ? slo.unit === "ratio"
      ? `${(value * 100).toFixed(1)}%`
      : `${value.toFixed(1)}s`
    : "N/A";

  const targetDisplay = slo.unit === "ratio"
    ? `${(slo.target * 100).toFixed(0)}%`
    : `<${slo.target}s`;

  // Gauge percentage (0-100)
  let gaugePercent = 0;
  if (hasData) {
    if (slo.unit === "ratio") {
      gaugePercent = value * 100;
    } else {
      // For latency: invert — lower is better
      gaugePercent = Math.max(0, Math.min(100, (1 - value / (slo.target * 2)) * 100));
    }
  }

  // Color based on SLO compliance
  const gaugeColor = !hasData
    ? "text-[var(--ink-muted)]"
    : slo.is_met
      ? "text-green-500 dark:text-green-400"
      : "text-red-500 dark:text-red-400";

  const bgColor = !hasData
    ? "stroke-[var(--surface-2)]"
    : slo.is_met
      ? "stroke-green-500/20"
      : "stroke-red-500/20";

  const fgColor = !hasData
    ? "stroke-[var(--ink-muted)]"
    : slo.is_met
      ? "stroke-green-500"
      : "stroke-red-500";

  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-sm font-semibold text-[var(--ink)]">{slo.name}</div>
          <div className="text-xs text-[var(--ink-muted)]">{slo.window_days}d window</div>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
          !hasData
            ? "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
            : slo.is_met
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
              : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
        }`}>
          {!hasData ? "NO DATA" : slo.is_met ? "MET" : "VIOLATED"}
        </span>
      </div>

      {/* Circular Gauge */}
      <div className="flex items-center justify-center my-4">
        <div className="relative w-24 h-24">
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
            {/* Background circle */}
            <circle
              cx="18" cy="18" r="14"
              fill="none"
              strokeWidth="3"
              className={bgColor}
            />
            {/* Progress arc */}
            <circle
              cx="18" cy="18" r="14"
              fill="none"
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray={`${gaugePercent * 0.88} 88`}
              className={fgColor}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-lg font-bold ${gaugeColor}`}>
              {displayValue}
            </span>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-[var(--ink-muted)]">
        Target: {targetDisplay}
      </div>
    </div>
  );
}

// ============================================================================
// AC8: Error Budget Bar
// ============================================================================

function ErrorBudgetBar({ slo }: { slo: SLOData }) {
  const consumed = slo.error_budget_consumed_pct;
  const remaining = slo.error_budget_remaining_pct;

  const barColor =
    consumed <= 50
      ? "bg-green-500"
      : consumed <= 80
        ? "bg-amber-500"
        : "bg-red-500";

  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-[var(--ink)]">{slo.name}</span>
        <span className="text-sm font-data text-[var(--ink-secondary)]">
          {remaining.toFixed(1)}% remaining
        </span>
      </div>
      <div className="w-full h-3 bg-[var(--surface-2)] rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(100, consumed)}%` }}
        />
      </div>
      <div className="flex justify-between mt-1 text-xs text-[var(--ink-muted)]">
        <span>Budget: {(slo.error_budget_total * 100).toFixed(1)}%</span>
        <span>Consumed: {consumed.toFixed(1)}%</span>
      </div>
    </div>
  );
}

// ============================================================================
// Helpers
// ============================================================================

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
    warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
    info: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${colors[severity] || "bg-gray-100 text-gray-800"}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function formatAlertValue(alertName: string, value: number): string {
  if (alertName === "SearchSuccessLow" || alertName === "SSEDropRate" || alertName === "ErrorBudgetBurn") {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (alertName === "SearchLatencyHigh") {
    return `${value.toFixed(1)}s`;
  }
  return String(value);
}
