"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import { PageHeader } from "../../components/PageHeader";
import { EmptyState } from "../../components/EmptyState";
import { ErrorStateWithRetry } from "../../components/ErrorStateWithRetry";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useSessions } from "../../hooks/useSessions";
import { usePlan } from "../../hooks/usePlan";
import { getUserFriendlyError } from "../../lib/error-messages";
import { formatCurrencyBR } from "../../lib/format-currency";
import { APP_NAME } from "../../lib/config";
import { PageErrorBoundary } from "../../components/PageErrorBoundary";
import { toast } from "sonner";

// UX-354 -> UX-356: Shared sector slug -> display name mapping
import { getSectorDisplayName } from "../../lib/constants/sector-names";

// All 27 Brazilian UFs
const ALL_UFS = [
  "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
  "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
  "RO", "RR", "RS", "SC", "SE", "SP", "TO",
];

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
  // Zero-Churn P2 §2.2: Backend-computed flag for grace period downloads
  download_available?: boolean;
}

// CRIT-002 AC20: Status badge configuration
const STATUS_CONFIG: Record<SearchSessionStatus, {
  label: string;
  bgClass: string;
  textClass: string;
  icon: string;
}> = {
  completed: {
    label: "Concluída",
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
    label: "Tempo esgotado",
    bgClass: "bg-orange-100 dark:bg-orange-900/30",
    textClass: "text-orange-700 dark:text-orange-400",
    icon: "clock",
  },
  processing: {
    label: "Em andamento",
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

// UX-351 AC8-AC9: Format UFs for display
function formatUfs(ufs: string[]): string {
  if (!ufs || ufs.length === 0) return "";
  // AC8: All 27 UFs = "Todo o Brasil"
  if (ufs.length >= ALL_UFS.length) return "Todo o Brasil";
  // AC9: Up to 5 shown, rest abbreviated
  if (ufs.length <= 5) return ufs.join(", ");
  const shown = ufs.slice(0, 5).join(", ");
  const remaining = ufs.length - 5;
  return `${shown} + ${remaining} ${remaining === 1 ? "outro" : "outros"}`;
}

// UX-351 AC7: Translate error messages stored in DB to Portuguese
function getLocalizedError(message: string | null): string {
  if (!message) return "";
  return getUserFriendlyError(message);
}

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

const TERMINAL_STATUSES: Set<SearchSessionStatus> = new Set(["completed", "failed", "timed_out", "cancelled"]);

export default function HistoricoPage() {
  const { session, loading: authLoading } = useAuth();
  const router = useRouter();
  const { trackEvent } = useAnalytics();
  const { planInfo } = usePlan();
  const [page, setPage] = useState(0);
  // UX-433: Filter to hide failures — default to showing only completed
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'failed'>('completed');

  // Zero-Churn P2 §2.2: Determine if user's plan/trial has expired
  const isExpired = useMemo(() => {
    if (!planInfo) return false;
    const { subscription_status, trial_expires_at, plan_id } = planInfo;
    // Active paid subscription — not expired
    if (subscription_status === "active" || subscription_status === "trialing") return false;
    // Free trial — check expiry
    if (plan_id === "free_trial" && trial_expires_at) {
      return new Date(trial_expires_at) < new Date();
    }
    // Cancelled / past_due / unpaid without active sub
    if (subscription_status && ["canceled", "past_due", "unpaid", "incomplete_expired"].includes(subscription_status)) {
      return true;
    }
    return false;
  }, [planInfo]);

  // ISSUE-040: Reset page to 0 when filter changes to ensure consistent counts
  const handleStatusFilterChange = useCallback((newFilter: 'all' | 'completed' | 'failed') => {
    setPage(0);
    setStatusFilter(newFilter);
  }, []);

  const limit = 20;

  // TD-008 AC7/AC13: SWR-based sessions with auto-polling for active sessions
  const [pollInterval, setPollInterval] = useState(0);
  const { sessions, total, loading, error: fetchError, errorTimestamp, refresh } = useSessions({
    page,
    limit,
    refreshInterval: pollInterval,
    status: statusFilter,
  });

  // UX-351 AC3-AC5: Poll when sessions are in non-terminal state
  useEffect(() => {
    const hasActive = sessions.some((s: SearchSession) => !TERMINAL_STATUSES.has(s.status));
    setPollInterval(hasActive ? 5000 : 0);
  }, [sessions]);

  // UX-433 + ISSUE-040: Status filter is now server-side via useSessions({ status })
  // Sessions are already filtered by the backend — no client-side filtering needed
  const filteredSessions = sessions;

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

  // Zero-Churn P2 §2.2: Grace period Excel download
  const handleDownload = useCallback(async (searchId: string) => {
    try {
      const res = await fetch(`/api/sessions/${searchId}/download`, {
        headers: session?.access_token
          ? { Authorization: `Bearer ${session.access_token}` }
          : {},
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        toast.error(err?.detail || "Erro ao baixar arquivo");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `smartlic-${searchId.slice(0, 8)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Erro ao baixar arquivo");
    }
  }, [session]);

  // GTM-POLISH-001 AC1-AC3: Unified auth loading
  if (authLoading) {
    return <AuthLoadingScreen />;
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

  // SAB-012 AC6: PT-BR currency formatting with abbreviations
  const formatCurrency = formatCurrencyBR;

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });

  const isRetryable = (status: SearchSessionStatus) =>
    status === "failed" || status === "timed_out";

  const totalPages = Math.ceil(total / limit);

  return (
    <PageErrorBoundary pageName="histórico">
    <div className="min-h-screen bg-[var(--canvas)]">
      <PageHeader
        title="Histórico"
        extraControls={
          <Link
            href="/buscar"
            className="hidden sm:inline-flex px-3 py-1.5 bg-[var(--brand-navy)] text-white rounded-button
                       hover:bg-[var(--brand-blue)] transition-colors text-sm"
          >
            Nova análise
          </Link>
        }
      />
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Zero-Churn P2 §2.2: Expired plan banner — download still available for 30 days */}
        {isExpired && (
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  Seu plano expirou
                </p>
                <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  Seus dados ficam disponiveis para download por 30 dias. Assine para continuar analisando.
                </p>
                <a href="/planos" className="inline-block mt-2 text-xs bg-amber-600 text-white px-4 py-1.5 rounded hover:bg-amber-700 transition-colors">
                  Assinar SmartLic Pro
                </a>
              </div>
            </div>
          </div>
        )}

        <p className="text-[var(--ink-secondary)] mb-2">
          {`${total} ${total !== 1 ? 'análises' : 'análise'} ${statusFilter === 'completed' ? (total !== 1 ? 'concluídas' : 'concluída') : statusFilter === 'failed' ? 'com falha' : (total !== 1 ? 'realizadas' : 'realizada')}`}
        </p>

        {/* UX-433: Status filter */}
        <div className="flex items-center gap-2 mb-4" role="radiogroup" aria-label="Filtrar por status">
          {([
            { value: 'completed' as const, label: 'Concluídas', icon: '\u2713' },
            { value: 'all' as const, label: 'Todas', icon: '\u2630' },
            { value: 'failed' as const, label: 'Com falha', icon: '\u2717' },
          ]).map(opt => (
            <button
              key={opt.value}
              onClick={() => handleStatusFilterChange(opt.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-button border transition-colors ${
                statusFilter === opt.value
                  ? 'bg-[var(--brand-navy)] text-white border-[var(--brand-navy)]'
                  : 'bg-[var(--surface-0)] text-[var(--ink-secondary)] border-[var(--border)] hover:border-[var(--border-strong)]'
              }`}
              role="radio"
              aria-checked={statusFilter === opt.value}
            >
              {opt.icon} {opt.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-28 bg-[var(--surface-1)] rounded-card animate-pulse" />
            ))}
          </div>
        ) : fetchError ? (
          <ErrorStateWithRetry
            message={fetchError}
            timestamp={errorTimestamp ?? undefined}
            onRetry={() => refresh()}
          />
        ) : sessions.length === 0 ? (
          <EmptyState
            icon={
              <svg aria-hidden="true" className="w-8 h-8 text-[var(--brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
              </svg>
            }
            title="Histórico de Análises"
            description="Cada análise que você faz fica salva aqui. Você pode revisitar resultados anteriores sem gastar uma nova análise."
            ctaLabel="Fazer primeira análise"
            ctaHref="/buscar"
          />
        ) : (
          <>
            {filteredSessions.length === 0 && statusFilter !== 'all' && (
              <div className="text-center py-8 text-[var(--ink-secondary)]">
                <p className="text-sm">Nenhuma análise {statusFilter === 'completed' ? 'concluída' : 'com falha'} neste período.</p>
                <button onClick={() => handleStatusFilterChange('all')} className="text-sm text-[var(--brand-blue)] hover:underline mt-2">
                  Ver todas as análises
                </button>
              </div>
            )}
            <div className="space-y-4">
              {filteredSessions.map((s: SearchSession) => (
                <div
                  key={s.id}
                  className="p-5 bg-[var(--surface-0)] border border-[var(--border)] rounded-card
                             hover:border-[var(--border-strong)] transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-data px-2 py-0.5 bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)] rounded" data-testid="sector-display">
                          {s.sectors.map(getSectorDisplayName).join(", ")}
                        </span>
                        {/* CRIT-002 AC20: Status badge */}
                        <StatusBadge status={s.status} />
                        <span className="text-xs text-[var(--ink-muted)]">
                          {formatDate(s.created_at)}
                        </span>
                      </div>
                      <p className="text-sm text-[var(--ink)] mb-1" data-testid="uf-display">
                        <span className="font-medium">{formatUfs(s.ufs)}</span>
                        {" "}| {s.data_inicial} a {s.data_final}
                      </p>
                      {s.custom_keywords && s.custom_keywords.length > 0 && (
                        <p className="text-xs text-[var(--ink-muted)]">
                          Termos: {s.custom_keywords.join(", ")}
                        </p>
                      )}
                      {/* UX-357: Unified error messages \u2014 max 2 variants (failure + timeout) */}
                      {isRetryable(s.status) && (s.error_message || s.status === 'timed_out') && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1 line-clamp-2" data-testid="error-message">
                          {s.status === 'timed_out'
                            ? "A análise excedeu o tempo limite. Recomendamos tentar novamente."
                            : getLocalizedError(s.error_message)}
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
                          {s.valor_total > 0 ? (
                            <p className="text-sm font-data text-[var(--success)] mt-1">
                              {formatCurrency(s.valor_total)}
                            </p>
                          ) : (
                            <p className="text-xs text-[var(--ink-muted)] mt-1">
                              Valor não informado
                            </p>
                          )}
                        </>
                      )}
                      {/* SAB-012 AC1-AC3: Smart duration display */}
                      {s.duration_ms != null && s.duration_ms > 60000 && (
                        <p className="text-xs text-[var(--ink-muted)] mt-1 flex items-center gap-1" data-testid="deep-analysis-label">
                          <svg aria-hidden="true" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                          </svg>
                          Análise profunda
                        </p>
                      )}
                      {s.duration_ms != null && s.duration_ms < 30000 && (
                        <p className="text-xs text-[var(--success)] mt-1 flex items-center gap-1" data-testid="fast-search-badge">
                          <svg aria-hidden="true" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
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
                          title="Repetir esta análise com os mesmos parâmetros"
                        >
                          <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Repetir análise
                        </button>
                      ) : null}
                      {/* Zero-Churn P2 §2.2: Grace period download button */}
                      {s.download_available && (
                        <button
                          onClick={() => handleDownload(s.id)}
                          data-testid="download-excel-button"
                          className="mt-2 text-xs text-[var(--brand-blue)] hover:text-[var(--brand-navy)]
                                     flex items-center gap-1 transition-colors"
                          title="Baixar resultados em Excel"
                        >
                          <svg aria-hidden="true" className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Download Excel
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* STORY-333 AC28-AC32: Pagination with improved contrast and sizing */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 mt-8">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-4 py-2 text-base font-medium border border-[var(--border)] rounded-button
                             disabled:opacity-50 disabled:cursor-not-allowed
                             hover:bg-[var(--surface-1)] transition-colors"
                  aria-label="Página anterior"
                  aria-disabled={page === 0}
                  data-testid="historico-prev"
                >
                  Anterior
                </button>
                <span className="text-sm text-[var(--ink-secondary)] tabular-nums" aria-current="page">
                  {page + 1} de {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="px-4 py-2 text-base font-medium border border-[var(--border)] rounded-button
                             disabled:opacity-50 disabled:cursor-not-allowed
                             hover:bg-[var(--surface-1)] transition-colors"
                  aria-label="Próxima página"
                  aria-disabled={page >= totalPages - 1}
                  data-testid="historico-next"
                >
                  Próximo
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
    </PageErrorBoundary>
  );
}
