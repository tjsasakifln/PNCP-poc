"use client";

import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface TrialMetrics {
  active_trials: number;
  conversion_rate_30d: number;
  converted_count: number;
  total_started: number;
  risk_distribution: { critical: number; at_risk: number; healthy: number };
  email_funnel: Array<{
    email_type: string;
    sent: number;
    opened: number;
    clicked: number;
  }>;
}

interface AtRiskUser {
  user_id: string;
  email: string;
  full_name: string;
  company: string;
  trial_day: number;
  searches_count: number;
  risk_category: string;
}

interface Props {
  metrics: TrialMetrics | null;
  atRiskUsers: AtRiskUser[];
  loading: boolean;
}

const RISK_COLORS: Record<string, string> = {
  critical: "#ef4444",
  at_risk: "#f59e0b",
  healthy: "#22c55e",
};

const RISK_LABELS: Record<string, string> = {
  critical: "Critico",
  at_risk: "Em risco",
  healthy: "Saudavel",
};

export function AdminTrialMetrics({ metrics, atRiskUsers, loading }: Props) {
  if (loading) {
    return (
      <div className="mb-8 bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6 animate-pulse">
        <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-4" />
        <div className="h-32 bg-gray-100 dark:bg-gray-800 rounded" />
      </div>
    );
  }

  if (!metrics) return null;

  const riskDist = metrics.risk_distribution || { critical: 0, at_risk: 0, healthy: 0 };
  const riskData = Object.entries(riskDist)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name: RISK_LABELS[key] ?? key,
      value,
      color: RISK_COLORS[key] ?? "#6b7280",
    }));

  return (
    <div className="mb-8 bg-[var(--surface-0)] border border-[var(--border)] rounded-card p-6">
      <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">
        Trial Conversion
      </h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 dark:bg-blue-950/30 rounded-card p-4 text-center">
          <p className="text-2xl font-bold text-blue-600">
            {metrics.active_trials}
          </p>
          <p className="text-xs text-blue-500 mt-1">Trials ativos</p>
        </div>
        <div className="bg-green-50 dark:bg-green-950/30 rounded-card p-4 text-center">
          <p className="text-2xl font-bold text-green-600">
            {metrics.conversion_rate_30d}%
          </p>
          <p className="text-xs text-green-500 mt-1">Conversao 30d</p>
        </div>
        <div className="bg-red-50 dark:bg-red-950/30 rounded-card p-4 text-center">
          <p className="text-2xl font-bold text-red-600">
            {riskDist.critical + riskDist.at_risk}
          </p>
          <p className="text-xs text-red-500 mt-1">Em risco</p>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Risk Distribution Pie */}
        {riskData.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-[var(--ink-secondary)] mb-2">
              Distribuicao de Risco
            </h3>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={riskData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  label
                >
                  {riskData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Email Funnel Bar */}
        {(metrics.email_funnel || []).length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-[var(--ink-secondary)] mb-2">
              Funil de Emails
            </h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={metrics.email_funnel}>
                <XAxis dataKey="email_type" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="sent" fill="#93c5fd" name="Enviados" />
                <Bar dataKey="opened" fill="#3b82f6" name="Abertos" />
                <Bar dataKey="clicked" fill="#1d4ed8" name="Clicados" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* At-Risk Users Table */}
      {atRiskUsers.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-[var(--ink-secondary)] mb-2">
            Usuarios em Risco ({atRiskUsers.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-2 px-2 text-xs font-medium text-[var(--ink-secondary)]">
                    Email
                  </th>
                  <th className="text-left py-2 px-2 text-xs font-medium text-[var(--ink-secondary)]">
                    Empresa
                  </th>
                  <th className="text-center py-2 px-2 text-xs font-medium text-[var(--ink-secondary)]">
                    Dia
                  </th>
                  <th className="text-center py-2 px-2 text-xs font-medium text-[var(--ink-secondary)]">
                    Buscas
                  </th>
                  <th className="text-center py-2 px-2 text-xs font-medium text-[var(--ink-secondary)]">
                    Risco
                  </th>
                </tr>
              </thead>
              <tbody>
                {atRiskUsers.map((u) => (
                  <tr
                    key={u.user_id}
                    className="border-b border-[var(--border)] hover:bg-[var(--surface-1)]"
                  >
                    <td className="py-2 px-2 text-xs truncate max-w-[200px]">
                      {u.email}
                    </td>
                    <td className="py-2 px-2 text-xs truncate max-w-[150px]">
                      {u.company || "-"}
                    </td>
                    <td className="py-2 px-2 text-xs text-center">
                      {u.trial_day}
                    </td>
                    <td className="py-2 px-2 text-xs text-center">
                      {u.searches_count}
                    </td>
                    <td className="py-2 px-2 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          u.risk_category === "critical"
                            ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                            : u.risk_category === "at_risk"
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                              : "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                        }`}
                      >
                        {RISK_LABELS[u.risk_category] ?? u.risk_category}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
