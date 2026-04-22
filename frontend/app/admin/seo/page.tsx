"use client";

import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";
import { useAdminSWR } from "../../../hooks/useAdminSWR";
import GSCSummarySection from "./_components/GSCSummarySection";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";

interface SEOMetricRow {
  date: string;
  impressions: number;
  clicks: number;
  ctr: number;
  avg_position: number;
  pages_indexed: number;
  top_queries: Array<{ query: string; clicks: number; impressions: number; position: number }>;
  top_pages: Array<{ page: string; clicks: number; impressions: number; position: number }>;
}

interface SEOMetricsResponse {
  metrics: SEOMetricRow[];
  total: number;
  latest_date: string | null;
}

export default function AdminSEOPage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const { data, error, isLoading } = useAdminSWR<SEOMetricsResponse>(
    isAdmin ? "/api/admin/seo-metrics?days=90" : null
  );

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-blue" />
      </div>
    );
  }

  if (!session || !isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-ink-muted">Acesso restrito a administradores.</p>
      </div>
    );
  }

  const metrics = data?.metrics ?? [];
  const hasData = metrics.length > 0;

  // Chart data (chronological order)
  const chartData = [...metrics].reverse().map((m) => ({
    date: m.date.slice(5), // MM-DD
    impressions: m.impressions,
    clicks: m.clicks,
    ctr: Math.round(m.ctr * 10000) / 100, // 0.0342 → 3.42
    position: m.avg_position,
  }));

  // KPIs from last 7 days
  const last7 = metrics.slice(0, 7);
  const totalImpressions7d = last7.reduce((s, m) => s + m.impressions, 0);
  const totalClicks7d = last7.reduce((s, m) => s + m.clicks, 0);
  const avgCtr7d = last7.length > 0 ? last7.reduce((s, m) => s + m.ctr, 0) / last7.length : 0;
  const avgPosition7d = last7.length > 0 ? last7.reduce((s, m) => s + m.avg_position, 0) / last7.length : 0;

  // Top queries from latest snapshot
  const latestQueries = metrics[0]?.top_queries ?? [];
  const latestPages = metrics[0]?.top_pages ?? [];

  return (
    <div className="min-h-screen bg-surface-0 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-ink-primary">SEO Dashboard</h1>
            <p className="text-sm text-ink-muted mt-1">
              {data?.latest_date
                ? `Último dado: ${data.latest_date}`
                : "Aguardando dados do Google Search Console"}
            </p>
          </div>
          <Link
            href="/admin"
            className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
          >
            ← Admin
          </Link>
        </div>

        {!hasData ? (
          /* Empty state */
          <div className="rounded-xl border border-[var(--border)] p-12 text-center">
            <div className="text-4xl mb-4">📊</div>
            <h2 className="text-lg font-semibold text-ink-primary mb-2">
              Nenhum dado SEO disponível
            </h2>
            <div className="text-sm text-ink-secondary max-w-md mx-auto space-y-2">
              <p>Para ativar o monitoramento SEO:</p>
              <ol className="text-left list-decimal list-inside space-y-1">
                <li>Configure <code className="text-xs bg-surface-1 px-1 rounded">GOOGLE_SERVICE_ACCOUNT_KEY</code> no ambiente do backend</li>
                <li>Adicione o service account como usuário no Google Search Console</li>
                <li>O cron job semanal coletará dados automaticamente</li>
              </ol>
            </div>
          </div>
        ) : (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <KPICard label="Impressões (7d)" value={totalImpressions7d.toLocaleString("pt-BR")} />
              <KPICard label="Cliques (7d)" value={totalClicks7d.toLocaleString("pt-BR")} />
              <KPICard label="CTR médio (7d)" value={`${(avgCtr7d * 100).toFixed(2)}%`} />
              <KPICard label="Posição média (7d)" value={avgPosition7d.toFixed(1)} />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Impressions + Clicks */}
              <div className="rounded-xl border border-[var(--border)] p-4">
                <h3 className="font-semibold text-ink-primary mb-4">Impressões e Cliques</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="date" fontSize={12} stroke="var(--ink-muted)" />
                    <YAxis fontSize={12} stroke="var(--ink-muted)" />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="impressions" name="Impressões" stroke="#3b82f6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="clicks" name="Cliques" stroke="#10b981" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Average Position */}
              <div className="rounded-xl border border-[var(--border)] p-4">
                <h3 className="font-semibold text-ink-primary mb-4">Posição Média</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="date" fontSize={12} stroke="var(--ink-muted)" />
                    <YAxis reversed fontSize={12} stroke="var(--ink-muted)" />
                    <Tooltip />
                    <Line type="monotone" dataKey="position" name="Posição" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Queries + Top Pages */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Queries */}
              <div className="rounded-xl border border-[var(--border)] p-4">
                <h3 className="font-semibold text-ink-primary mb-4">Top Queries</h3>
                {latestQueries.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-ink-muted border-b border-[var(--border)]">
                          <th className="pb-2 font-medium">Query</th>
                          <th className="pb-2 font-medium text-right">Cliques</th>
                          <th className="pb-2 font-medium text-right">Impressões</th>
                          <th className="pb-2 font-medium text-right">Posição</th>
                        </tr>
                      </thead>
                      <tbody>
                        {latestQueries.map((q, i) => (
                          <tr key={i} className="border-b border-[var(--border)] last:border-0">
                            <td className="py-2 text-ink-primary truncate max-w-[200px]">{q.query}</td>
                            <td className="py-2 text-right text-ink-secondary">{q.clicks}</td>
                            <td className="py-2 text-right text-ink-secondary">{q.impressions}</td>
                            <td className="py-2 text-right text-ink-secondary">{q.position}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-ink-muted">Sem dados de queries.</p>
                )}
              </div>

              {/* Top Pages */}
              <div className="rounded-xl border border-[var(--border)] p-4">
                <h3 className="font-semibold text-ink-primary mb-4">Top Páginas</h3>
                {latestPages.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-ink-muted border-b border-[var(--border)]">
                          <th className="pb-2 font-medium">Página</th>
                          <th className="pb-2 font-medium text-right">Cliques</th>
                          <th className="pb-2 font-medium text-right">Impressões</th>
                        </tr>
                      </thead>
                      <tbody>
                        {latestPages.map((p, i) => (
                          <tr key={i} className="border-b border-[var(--border)] last:border-0">
                            <td className="py-2 text-ink-primary truncate max-w-[250px]">
                              {p.page.replace("https://smartlic.tech", "")}
                            </td>
                            <td className="py-2 text-right text-ink-secondary">{p.clicks}</td>
                            <td className="py-2 text-right text-ink-secondary">{p.impressions}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-ink-muted">Sem dados de páginas.</p>
                )}
              </div>
            </div>
          </>
        )}

        {/* STORY-SEO-005: GSC query-level analytics (always rendered — graceful empty state inside) */}
        <GSCSummarySection />
      </div>
    </div>
  );
}

function KPICard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] p-4">
      <p className="text-xs text-ink-muted mb-1">{label}</p>
      <p className="text-2xl font-bold text-ink-primary">{value}</p>
    </div>
  );
}
