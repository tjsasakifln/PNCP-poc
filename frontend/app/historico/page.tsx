"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAnalytics } from "../../hooks/useAnalytics";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "Smart PNCP";

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

  // Handle re-run search navigation
  const handleRerunSearch = useCallback((searchSession: SearchSession) => {
    // Track analytics event
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
    });

    // Build URL params for the search page
    const params = new URLSearchParams();
    params.set('ufs', searchSession.ufs.join(','));
    params.set('data_inicial', searchSession.data_inicial);
    params.set('data_final', searchSession.data_final);

    // Set sector or custom terms
    if (searchSession.custom_keywords && searchSession.custom_keywords.length > 0) {
      params.set('mode', 'termos');
      params.set('termos', searchSession.custom_keywords.join(' '));
    } else if (searchSession.sectors.length > 0) {
      params.set('mode', 'setor');
      params.set('setor', searchSession.sectors[0]);
    }

    router.push(`/?${params.toString()}`);
  }, [router, trackEvent]);

  useEffect(() => {
    if (authLoading || !session) return;
    fetchSessions();
  }, [session, authLoading, page]);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "/api";
      const res = await fetch(
        `${backendUrl}/sessions?limit=${limit}&offset=${page * limit}`,
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
            href="/"
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
            <Link href="/" className="text-[var(--brand-blue)] hover:underline">
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
                      {s.resumo_executivo && (
                        <p className="text-sm text-[var(--ink-secondary)] mt-2 line-clamp-2">
                          {s.resumo_executivo}
                        </p>
                      )}
                    </div>
                    <div className="text-right ml-4 shrink-0">
                      <p className="text-lg font-data font-semibold text-[var(--ink)]">
                        {s.total_filtered}
                      </p>
                      <p className="text-xs text-[var(--ink-muted)]">resultados</p>
                      <p className="text-sm font-data text-[var(--success)] mt-1">
                        {formatCurrency(s.valor_total)}
                      </p>
                      <button
                        onClick={() => handleRerunSearch(s)}
                        className="mt-3 px-3 py-1.5 text-xs font-medium text-[var(--brand-blue)]
                                   border border-[var(--brand-blue)] rounded-button
                                   hover:bg-[var(--brand-blue-subtle)] transition-colors
                                   flex items-center gap-1.5"
                        title="Repetir esta busca com os mesmos parâmetros"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Repetir busca
                      </button>
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
