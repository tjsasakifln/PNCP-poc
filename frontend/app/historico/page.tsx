"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAnalytics } from "../../hooks/useAnalytics";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech";

// CRIT-002 AC18: SearchSessionStatus type
type SearchSessionStatus = 'created' | 'processing' | 'completed' | 'failed' | 'timed_out' | 'cancelled';

interface SearchSession {
  id: string;
  sectors: string[];
  ufs: string[];
  data_inicial: string;
  data_final: string;
  custom_keywords: string[] | null;
  total_raw: number;
  total_filtered: number;
  valor_total: number;
  resumo_executivo: string | null;
  created_at: string;
  // CRIT-002 AC18: Lifecycle fields
  status: SearchSessionStatus;
  error_message: string | null;
  error_code: string | null;
  duration_ms: number | null;
  pipeline_stage: string | null;
  started_at: string;
  response_state: string | null;
}

// CRIT-002 AC20: Status badge configuration
const STATUS_CONFIG: Record<SearchSessionStatus, {
  label: string;
  bgClass: string;
  textClass: string;
  icon: string;
}> = {
  completed: {
    label: "Concluida",
    bgClass: "bg-emerald-100 dark:bg-emerald-900/30",
    textClass: "text-emerald-700 dark:text-emerald-400",
    icon: "check",
  },
  failed: {
    label: "Falhou",
    bgClass: "bg-red-100 dark:bg-red-900/30",
    textClass: "text-red-700 dark:text-red-400",
    icon: "x",
  },
  timed_out: {
    label: "Timeout",
    bgClass: "bg-orange-100 dark:bg-orange-900/30",
    textClass: "text-orange-700 dark:text-orange-400",
    icon: "clock",
  },
  processing: {
    label: "Processando...",
    bgClass: "bg-blue-100 dark:bg-blue-900/30",
    textClass: "text-blue-700 dark:text-blue-400",
    icon: "spinner",
  },
  cancelled: {
    label: "Cancelada",
    bgClass: "bg-gray-100 dark:bg-gray-800",
    textClass: "text-gray-500 dark:text-gray-400",
    icon: "minus",
  },
  created: {
    label: "Iniciada",
    bgClass: "bg-gray-100 dark:bg-gray-800",
    textClass: "text-gray-500 dark:text-gray-400",
    icon: "dot",
  },
};

function StatusBadge({ status }: { status: SearchSessionStatus }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.completed;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded ${config.bgClass} ${config.textClass}`}
      data-testid={`status-badge-${status}`}
    >
      {config.icon === "check" && (
        <svg aria-hidden="true" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )}
      {config.icon === "x" && (
        <svg aria-hidden="true" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      )}
      {config.icon === "clock" && (
        <svg aria-hidden="true" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )}
      {config.icon === "spinner" && (
        <svg aria-hidden="true" className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {config.label}
    </span>
  );
}

export default function HistoricoPage() {
  const { session, loading: authLoading } = useAuth();
  const router = useRouter();
  const { trackEvent } = useAnalytics();
  const [sessions, setSessions] = useState<SearchSession[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const limit = 20;

  // Handle re-run search navigation (AC17: "Tentar novamente" for failed/timed_out)
  const handleRerunSearch = useCallback((searchSession: SearchSession) => {
    trackEvent('search_rerun', {
      session_id: searchSession.id,
      sectors: searchSession.sectors,
      ufs: searchSession.ufs,
      date_range: {
        inicial: searchSession.data_inicial,
        final: searchSession.data_final,
      },
      has_custom_keywords: Boolean(searchSession.custom_keywords?.length),
      original_results: searchSession.total_filtered,
      original_status: searchSession.status,
    });

    const params = new URLSearchParams();
    params.set('ufs', searchSession.ufs.join(','));
    params.set('data_inicial', searchSession.data_inicial);
    params.set('data_final', searchSession.data_final);

    if (searchSession.custom_keywords && searchSession.custom_keywords.length > 0) {
      params.set('mode', 'termos');
      params.set('termos', searchSession.custom_keywords.join(' '));
    } else if (searchSession.sectors.length > 0) {
      params.set('mode', 'setor');
      params.set('setor', searchSession.sectors[0]);
    }

    router.push(`/buscar?${params.toString()}`);
  }, [router, trackEvent]);

  useEffect(() => {
    if (authLoading || !session) return;
    fetchSessions();
  }, [session, authLoading, page]);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/sessions?limit=${limit}&offset=${page * limit}`,
        { headers: { Authorization: `Bearer ${session!.access_token}` } }
      );
      if (!res.ok) throw new Error("Erro ao carregar histórico");
      const data = await res.json();
      setSessions(data.sessions);
      setTotal(data.total);
    } catch {
      setSessions([]);
    } finally {
      setLoading(false);
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
        <div className="text-center">
          <p className="text-[var(--ink-secondary)] mb-4">Faça login para ver seu histórico</p>
          <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
            Ir para login
          </Link>
        </div>
      </div>
    );
  }

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val);

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });

  const isRetryable = (status: SearchSessionStatus) =>
    status === "failed" || status === "timed_out";

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)]">
              Histórico de Buscas
            </h1>
            <p className="text-[var(--ink-secondary)]">{total} busca{total !== 1 ? "s" : ""} realizada{total !== 1 ? "s" : ""}</p>
          </div>
          <Link
            href="/buscar"
            className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button
                       hover:bg-[var(--brand-blue)] transition-colors text-sm"
          >
            Nova busca
          </Link>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-28 bg-[var(--surface-1)] rounded-card animate-pulse" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-[var(--ink-muted)] text-lg mb-4">Nenhuma busca realizada ainda</p>
            <Link href="/buscar" className="text-[var(--brand-blue)] hover:underline">
              Fazer primeira busca
            </Link>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className="p-5 bg-[var(--surface-0)] border border-[var(--border)] rounded-card
                             hover:border-[var(--border-strong)] transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-data px-2 py-0.5 bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)] rounded">
                          {s.sectors.join(", ")}
                        </span>
                        {/* CRIT-002 AC20: Status badge */}
                        <StatusBadge status={s.status || "completed"} />
                        <span className="text-xs text-[var(--ink-muted)]">
                          {formatDate(s.created_at)}
                        </span>
                      </div>
                      <p className="text-sm text-[var(--ink)] mb-1">
                        <span className="font-medium">{s.ufs.join(", ")}</span>
                        {" "}| {s.data_inicial} a {s.data_final}
                      </p>
                      {s.custom_keywords && s.custom_keywords.length > 0 && (
                        <p className="text-xs text-[var(--ink-muted)]">
                          Termos: {s.custom_keywords.join(", ")}
                        </p>
                      )}
                      {/* AC17: Show error message for failed/timed_out sessions */}
                      {s.error_message && isRetryable(s.status) && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1 line-clamp-2">
                          {s.error_message.slice(0, 100)}
                        </p>
                      )}
                      {s.resumo_executivo && s.status === "completed" && (
                        <p className="text-sm text-[var(--ink-secondary)] mt-2 line-clamp-2">
                          {s.resumo_executivo}
                        </p>
                      )}
                    </div>
                    <div className="text-right ml-4 shrink-0">
                      {s.status === "completed" && (
                        <>
                          <p className="text-lg font-data font-semibold text-[var(--ink)]">
                            {s.total_filtered}
                          </p>
                          <p className="text-xs text-[var(--ink-muted)]">resultados</p>
                          <p className="text-sm font-data text-[var(--success)] mt-1">
                            {formatCurrency(s.valor_total)}
                          </p>
                        </>
                      )}
                      {s.duration_ms != null && (
                        <p className="text-xs text-[var(--ink-muted)] mt-1">
                          {(s.duration_ms / 1000).toFixed(1)}s
                        </p>
                      )}
                      {/* AC17: "Tentar novamente" for failed/timed_out, "Repetir busca" for completed */}
                      {isRetryable(s.status) ? (
                        <button
                          onClick={() => handleRerunSearch(s)}
                          data-testid="retry-button"
                          className="mt-3 px-3 py-1.5 text-xs font-medium text-red-600 dark:text-red-400
                                     border border-red-300 dark:border-red-700 rounded-button
                                     hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors
                                     flex items-center gap-1.5"
                          title="Tentar novamente com os mesmos parâmetros"
                        >
                          <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Tentar novamente
                        </button>
                      ) : s.status === "completed" ? (
                        <button
                          onClick={() => handleRerunSearch(s)}
                          className="mt-3 px-3 py-1.5 text-xs font-medium text-[var(--brand-blue)]
                                     border border-[var(--brand-blue)] rounded-button
                                     hover:bg-[var(--brand-blue-subtle)] transition-colors
                                     flex items-center gap-1.5"
                          title="Repetir esta busca com os mesmos parâmetros"
                        >
                          <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Repetir busca
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-3 py-1 text-sm border border-[var(--border)] rounded-button
                             disabled:opacity-30 hover:bg-[var(--surface-1)]"
                >
                  Anterior
                </button>
                <span className="text-sm text-[var(--ink-secondary)]">
                  {page + 1} de {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="px-3 py-1 text-sm border border-[var(--border)] rounded-button
                             disabled:opacity-30 hover:bg-[var(--surface-1)]"
                >
                  Próximo
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
