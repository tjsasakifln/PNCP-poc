"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../components/AuthProvider";
import Link from "next/link";
import { toast } from "sonner";

interface CacheMetrics {
  hit_rate_24h: number;
  miss_rate_24h: number;
  stale_served_24h: number;
  fresh_served_24h: number;
  total_entries: number;
  priority_distribution: { hot: number; warm: number; cold: number };
  age_distribution: Record<string, number>;
  degraded_keys: number;
  avg_fetch_duration_ms: number;
  top_keys: Array<{
    params_hash: string;
    access_count: number;
    priority: string;
    age_hours: number;
  }>;
}

interface CacheEntry {
  params_hash: string;
  user_id: string;
  search_params: Record<string, unknown>;
  results_count: number;
  sources: string[];
  fetched_at: string;
  created_at: string;
  priority: string;
  access_count: number;
  last_accessed_at: string | null;
  fail_streak: number;
  degraded_until: string | null;
  coverage: Record<string, unknown> | null;
  fetch_duration_ms: number | null;
  age_hours: number;
  cache_status: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  hot: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  warm: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  cold: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
};

const STATUS_COLORS: Record<string, string> = {
  fresh: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  stale: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  expired: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
};

export default function AdminCachePage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const [metrics, setMetrics] = useState<CacheMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inspecting, setInspecting] = useState<string | null>(null);
  const [inspectedEntry, setInspectedEntry] = useState<CacheEntry | null>(null);
  const [showDeleteAll, setShowDeleteAll] = useState(false);
  const [invalidating, setInvalidating] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/admin/cache/metrics", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar métricas");
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (session?.access_token && isAdmin) {
      fetchMetrics();
    } else if (!authLoading) {
      setLoading(false);
    }
  }, [session?.access_token, isAdmin, authLoading, fetchMetrics]);

  const handleInspect = async (hash: string) => {
    if (!session?.access_token) return;
    setInspecting(hash);
    try {
      const res = await fetch(`/api/admin/cache/${hash}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const data = await res.json();
      setInspectedEntry(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao inspecionar");
    } finally {
      setInspecting(null);
    }
  };

  const handleInvalidate = async (hash: string) => {
    if (!session?.access_token) return;
    setInvalidating(hash);
    try {
      const res = await fetch(`/api/admin/cache/${hash}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const data = await res.json();
      toast.success(`Invalidado em: ${data.deleted_levels?.join(", ")}`);
      fetchMetrics();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao invalidar");
    } finally {
      setInvalidating(null);
    }
  };

  const handleInvalidateAll = async () => {
    if (!session?.access_token) return;
    setShowDeleteAll(false);
    try {
      const res = await fetch("/api/admin/cache", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "X-Confirm": "delete-all",
        },
      });
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const data = await res.json();
      toast.success(
        `Cache limpo: ${data.deleted_counts?.supabase || 0} Supabase, ${data.deleted_counts?.redis || 0} Redis, ${data.deleted_counts?.local || 0} local`
      );
      fetchMetrics();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao limpar cache");
    }
  };

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
        <Link href="/login" className="text-[var(--brand-blue)]">Login necessário</Link>
      </div>
    );
  }

  if (!isAdmin && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center max-w-md px-4">
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">Acesso Restrito</h1>
          <p className="text-[var(--ink-secondary)] mb-6">
            Esta página é exclusiva para administradores.
          </p>
          <Link href="/buscar" className="inline-block px-6 py-2 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors">
            Voltar
          </Link>
        </div>
      </div>
    );
  }

  const formatPct = (v: number) => `${(v * 100).toFixed(1)}%`;
  const formatAge = (h: number) =>
    h < 1 ? `${Math.round(h * 60)}min` : `${h.toFixed(1)}h`;

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)]">
              Admin - Cache Dashboard
            </h1>
            <p className="text-[var(--ink-secondary)]">
              Observabilidade e controle do cache de buscas
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/admin"
              className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
            >
              Usuários
            </Link>
            <button
              onClick={fetchMetrics}
              disabled={loading}
              className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm hover:bg-[var(--brand-blue)] disabled:opacity-50"
            >
              {loading ? "Atualizando..." : "Atualizar"}
            </button>
            <button
              onClick={() => setShowDeleteAll(true)}
              className="px-4 py-2 bg-red-600 text-white rounded-button text-sm hover:bg-red-700"
            >
              Invalidar Tudo
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-[var(--error-subtle)] border border-[var(--error)] rounded-card text-[var(--error)]">
            {error}
          </div>
        )}

        {/* Metrics Cards */}
        {metrics && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <MetricCard label="Hit Rate (24h)" value={formatPct(metrics.hit_rate_24h)} />
              <MetricCard label="Total Entries" value={String(metrics.total_entries)} />
              <MetricCard label="Degraded Keys" value={String(metrics.degraded_keys)} accent={metrics.degraded_keys > 0 ? "error" : undefined} />
              <MetricCard label="Avg Fetch" value={`${metrics.avg_fetch_duration_ms}ms`} />
              <MetricCard label="Fresh Served (24h)" value={String(metrics.fresh_served_24h)} />
              <MetricCard label="Stale Served (24h)" value={String(metrics.stale_served_24h)} />
              <MetricCard label="Miss Rate (24h)" value={formatPct(metrics.miss_rate_24h)} />
              <MetricCard
                label="Hot / Warm / Cold"
                value={`${metrics.priority_distribution.hot} / ${metrics.priority_distribution.warm} / ${metrics.priority_distribution.cold}`}
              />
            </div>

            {/* Age Distribution */}
            <div className="mb-8 bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-6">
              <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Age Distribution</h2>
              <div className="flex gap-4">
                {Object.entries(metrics.age_distribution).map(([bucket, count]) => (
                  <div key={bucket} className="flex-1 text-center">
                    <div className="text-2xl font-bold text-[var(--ink)]">{count}</div>
                    <div className="text-sm text-[var(--ink-secondary)]">{bucket}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Keys Table */}
            <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card overflow-hidden mb-8">
              <div className="px-6 py-4 border-b border-[var(--border)]">
                <h2 className="text-lg font-semibold text-[var(--ink)]">
                  Top Cache Keys ({metrics.top_keys.length})
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[var(--surface-2)] text-left">
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Hash</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Priority</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Age</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Accesses</th>
                      <th className="px-4 py-3 font-medium text-[var(--ink-secondary)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.top_keys.map((key) => (
                      <tr key={key.params_hash} className="border-t border-[var(--border)] hover:bg-[var(--surface-2)]">
                        <td className="px-4 py-3 font-mono text-xs text-[var(--ink)]">
                          {key.params_hash.slice(0, 12)}...
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[key.priority] || ""}`}>
                            {key.priority}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-[var(--ink-secondary)]">
                          {formatAge(key.age_hours)}
                        </td>
                        <td className="px-4 py-3 text-[var(--ink)]">{key.access_count}</td>
                        <td className="px-4 py-3">
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleInspect(key.params_hash)}
                              disabled={inspecting === key.params_hash}
                              className="text-xs px-2 py-1 border border-[var(--border)] rounded hover:bg-[var(--surface-2)] text-[var(--ink-secondary)]"
                            >
                              {inspecting === key.params_hash ? "..." : "Inspecionar"}
                            </button>
                            <button
                              onClick={() => handleInvalidate(key.params_hash)}
                              disabled={invalidating === key.params_hash}
                              className="text-xs px-2 py-1 border border-red-300 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600"
                            >
                              {invalidating === key.params_hash ? "..." : "Invalidar"}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {metrics.top_keys.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-[var(--ink-secondary)]">
                          Nenhuma entrada no cache
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {loading && !metrics && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-[var(--brand-navy)] border-t-transparent rounded-full" />
          </div>
        )}

        {/* Inspection Modal */}
        {inspectedEntry && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-[var(--surface-1)] rounded-card max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-[var(--ink)]">
                  Cache Entry: {inspectedEntry.params_hash.slice(0, 12)}...
                </h3>
                <button
                  onClick={() => setInspectedEntry(null)}
                  className="text-[var(--ink-secondary)] hover:text-[var(--ink)] text-xl"
                >
                  &times;
                </button>
              </div>
              <div className="space-y-3 text-sm">
                <DetailRow label="Status">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[inspectedEntry.cache_status] || ""}`}>
                    {inspectedEntry.cache_status}
                  </span>
                </DetailRow>
                <DetailRow label="Priority">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[inspectedEntry.priority] || ""}`}>
                    {inspectedEntry.priority}
                  </span>
                </DetailRow>
                <DetailRow label="Age">{formatAge(inspectedEntry.age_hours)}</DetailRow>
                <DetailRow label="Results">{inspectedEntry.results_count}</DetailRow>
                <DetailRow label="Sources">{inspectedEntry.sources?.join(", ") || "—"}</DetailRow>
                <DetailRow label="Access Count">{inspectedEntry.access_count}</DetailRow>
                <DetailRow label="Fail Streak">{inspectedEntry.fail_streak}</DetailRow>
                <DetailRow label="Degraded Until">{inspectedEntry.degraded_until || "—"}</DetailRow>
                <DetailRow label="Fetch Duration">{inspectedEntry.fetch_duration_ms ? `${inspectedEntry.fetch_duration_ms}ms` : "—"}</DetailRow>
                <DetailRow label="Fetched At">{inspectedEntry.fetched_at || "—"}</DetailRow>
                <DetailRow label="Last Accessed">{inspectedEntry.last_accessed_at || "—"}</DetailRow>
                <DetailRow label="User ID">
                  <span className="font-mono text-xs">{inspectedEntry.user_id}</span>
                </DetailRow>
                {inspectedEntry.search_params && (
                  <div>
                    <div className="font-medium text-[var(--ink-secondary)] mb-1">Search Params</div>
                    <pre className="bg-[var(--surface-2)] p-3 rounded text-xs overflow-x-auto text-[var(--ink)]">
                      {JSON.stringify(inspectedEntry.search_params, null, 2)}
                    </pre>
                  </div>
                )}
                {inspectedEntry.coverage && (
                  <div>
                    <div className="font-medium text-[var(--ink-secondary)] mb-1">Coverage</div>
                    <pre className="bg-[var(--surface-2)] p-3 rounded text-xs overflow-x-auto text-[var(--ink)]">
                      {JSON.stringify(inspectedEntry.coverage, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => {
                    handleInvalidate(inspectedEntry.params_hash);
                    setInspectedEntry(null);
                  }}
                  className="px-4 py-2 bg-red-600 text-white rounded-button text-sm hover:bg-red-700"
                >
                  Invalidar
                </button>
                <button
                  onClick={() => setInspectedEntry(null)}
                  className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-2)] text-[var(--ink)]"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete All Confirmation */}
        {showDeleteAll && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-[var(--surface-1)] rounded-card max-w-md w-full p-6 shadow-xl">
              <h3 className="text-lg font-semibold text-[var(--ink)] mb-2">
                Invalidar Todo o Cache
              </h3>
              <p className="text-[var(--ink-secondary)] mb-6">
                Esta ação removerá <strong>todas</strong> as entradas de cache em Supabase,
                Redis e arquivos locais. As próximas buscas serão mais lentas até
                o cache ser reconstruído.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteAll(false)}
                  className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-2)] text-[var(--ink)]"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleInvalidateAll}
                  className="px-4 py-2 bg-red-600 text-white rounded-button text-sm hover:bg-red-700"
                >
                  Confirmar Invalidação Total
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: "error";
}) {
  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-4">
      <div className="text-sm text-[var(--ink-secondary)] mb-1">{label}</div>
      <div
        className={`text-2xl font-bold ${
          accent === "error" ? "text-[var(--error)]" : "text-[var(--ink)]"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function DetailRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 text-[var(--ink-secondary)] shrink-0">{label}</span>
      <span className="text-[var(--ink)]">{children}</span>
    </div>
  );
}
