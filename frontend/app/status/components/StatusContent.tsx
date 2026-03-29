"use client";

import { useState, useEffect, useCallback } from "react";
import UptimeChart from "./UptimeChart";
import IncidentList from "./IncidentList";

interface SourceStatus {
  status: string;
  latency_ms: number | null;
  error?: string;
  last_check?: string;
}

interface StatusData {
  status: string;
  sources: Record<string, SourceStatus>;
  components: Record<string, string>;
  uptime_pct_24h: number;
  uptime_pct_7d: number;
  uptime_pct_30d: number;
  last_incident: string | null;
  timestamp: string;
}

interface Incident {
  id: string;
  started_at: string;
  resolved_at: string | null;
  status: "ongoing" | "resolved";
  affected_sources: string[];
  description: string;
}

interface DayData {
  date: string;
  uptime_pct: number;
  checks: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
}

const SOURCE_LABELS: Record<string, string> = {
  pncp: "PNCP (Portal Nacional)",
  portal: "Portal de Compras Públicas",
  comprasgov: "ComprasGov",
};

const COMPONENT_LABELS: Record<string, string> = {
  redis: "Cache (Redis)",
  supabase: "Banco de Dados",
  arq_worker: "Processamento em Background",
};

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; bg: string; label: string }> = {
    healthy: { color: "text-green-700 dark:text-green-400", bg: "bg-green-100 dark:bg-green-900/30", label: "Operacional" },
    degraded: { color: "text-yellow-700 dark:text-yellow-400", bg: "bg-yellow-100 dark:bg-yellow-900/30", label: "Degradado" },
    unhealthy: { color: "text-red-700 dark:text-red-400", bg: "bg-red-100 dark:bg-red-900/30", label: "Indisponível" },
    unknown: { color: "text-gray-700 dark:text-gray-400", bg: "bg-gray-100 dark:bg-gray-900/30", label: "Desconhecido" },
    up: { color: "text-green-700 dark:text-green-400", bg: "bg-green-100 dark:bg-green-900/30", label: "Operacional" },
    down: { color: "text-red-700 dark:text-red-400", bg: "bg-red-100 dark:bg-red-900/30", label: "Indisponível" },
  };
  const c = config[status] || config.unknown;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${c.color} ${c.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        status === "healthy" || status === "up" ? "bg-green-500" :
        status === "degraded" ? "bg-yellow-500" :
        status === "unhealthy" || status === "down" ? "bg-red-500" : "bg-gray-500"
      }`} />
      {c.label}
    </span>
  );
}

function OverallStatusBanner({ status }: { status: string }) {
  const config: Record<string, { bg: string; icon: string; text: string }> = {
    healthy: { bg: "bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800", icon: "text-green-600", text: "Todos os sistemas operacionais" },
    degraded: { bg: "bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800", icon: "text-yellow-600", text: "Alguns sistemas com performance reduzida" },
    unhealthy: { bg: "bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800", icon: "text-red-600", text: "Estamos investigando problemas no sistema" },
  };
  const c = config[status] || config.healthy;

  return (
    <div className={`rounded-xl border p-6 mb-8 ${c.bg}`}>
      <div className="flex items-center gap-3">
        <div className={`text-3xl ${c.icon}`}>
          {status === "healthy" ? "✓" : status === "degraded" ? "⚠" : "✕"}
        </div>
        <div>
          <h2 className="text-xl font-bold text-ink">{c.text}</h2>
          <p className="text-sm text-ink-secondary mt-0.5">
            Última verificação: {new Date().toLocaleString("pt-BR")}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * StatusContent — client component responsible for fetching and rendering
 * live system status data with auto-refresh every 60 seconds.
 * Exported separately so the page shell (header) can be a Server Component.
 */
export default function StatusContent() {
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [uptimeHistory, setUptimeHistory] = useState<DayData[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const [statusRes, incidentsRes, historyRes] = await Promise.allSettled([
        fetch("/api/status"),
        fetch("/api/status?path=incidents"),
        fetch("/api/status?path=uptime-history"),
      ]);

      if (statusRes.status === "fulfilled" && statusRes.value.ok) {
        setStatusData(await statusRes.value.json());
      }
      if (incidentsRes.status === "fulfilled" && incidentsRes.value.ok) {
        const data = await incidentsRes.value.json();
        setIncidents(data.incidents || []);
      }
      if (historyRes.status === "fulfilled" && historyRes.value.ok) {
        const data = await historyRes.value.json();
        setUptimeHistory(data.history || []);
      }
    } catch {
      // Silently fail — page shows stale data
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch + auto-refresh every 60s (AC14)
  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 60_000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const overallStatus = statusData?.status || "unknown";

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <>
      {/* Overall status banner */}
      <OverallStatusBanner status={overallStatus} />

      {/* Data Sources */}
      <section className="mb-8">
        <h3 className="text-lg font-semibold text-ink mb-4">Fontes de Dados</h3>
        <div className="space-y-2">
          {(!statusData?.sources || Object.keys(statusData.sources).length === 0) && (
            <p className="text-sm text-muted-foreground">Informação de fontes indisponível no momento.</p>
          )}
          {statusData?.sources && Object.entries(statusData.sources).map(([key, source]) => (
            <div key={key} className="flex items-center justify-between p-3 bg-surface-1 rounded-lg border border-border">
              <span className="text-sm font-medium text-ink">
                {SOURCE_LABELS[key] || key}
              </span>
              <div className="flex items-center gap-3">
                {source.latency_ms !== null && (
                  <span className="text-xs text-ink-muted">{source.latency_ms}ms</span>
                )}
                <StatusBadge status={source.status} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Components */}
      <section className="mb-8">
        <h3 className="text-lg font-semibold text-ink mb-4">Componentes</h3>
        <div className="space-y-2">
          {statusData?.components && Object.entries(statusData.components).map(([key, status]) => (
            <div key={key} className="flex items-center justify-between p-3 bg-surface-1 rounded-lg border border-border">
              <span className="text-sm font-medium text-ink">
                {COMPONENT_LABELS[key] || key}
              </span>
              <StatusBadge status={status} />
            </div>
          ))}
        </div>
      </section>

      {/* Uptime */}
      <section className="mb-8">
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: "24 horas", value: statusData?.uptime_pct_24h },
            { label: "7 dias", value: statusData?.uptime_pct_7d },
            { label: "30 dias", value: statusData?.uptime_pct_30d },
          ].map(({ label, value }) => (
            <div key={label} className="text-center p-4 bg-surface-1 rounded-lg border border-border">
              <div className="text-2xl font-bold text-ink">
                {value !== undefined ? `${value}%` : "—"}
              </div>
              <div className="text-xs text-ink-secondary mt-1">{label}</div>
            </div>
          ))}
        </div>

        {/* Uptime chart (AC12) */}
        <div className="p-4 bg-surface-1 rounded-lg border border-border">
          <UptimeChart history={uptimeHistory} />
        </div>
      </section>

      {/* Incidents (AC13) */}
      <section className="mb-8">
        <div className="p-4 bg-surface-1 rounded-lg border border-border">
          <IncidentList incidents={incidents} />
        </div>
      </section>

      {/* Auto-refresh indicator */}
      <div className="text-center text-xs text-ink-muted pb-8">
        Atualização automática a cada 60 segundos
      </div>
    </>
  );
}
