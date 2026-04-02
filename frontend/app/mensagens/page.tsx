"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../components/AuthProvider";
import { PageHeader } from "../../components/PageHeader";
import { ErrorStateWithRetry } from "../../components/ErrorStateWithRetry";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import { ComingSoonPage } from "../../components/ComingSoonPage";
import { isFeatureGated } from "../../lib/feature-gates";
import { getUserFriendlyError } from "../../lib/error-messages";
import { useConversations } from "../../hooks/useConversations";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type {
  ConversationSummary,
  ConversationDetail,
  ConversationCategory,
} from "../types";

const CATEGORY_LABELS: Record<string, string> = {
  suporte: "Suporte",
  sugestao: "Sugestão",
  funcionalidade: "Funcionalidade",
  bug: "Bug",
  outro: "Outro",
};

const STATUS_LABELS: Record<string, string> = {
  aberto: "Aberto",
  respondido: "Respondido",
  resolvido: "Resolvido",
};

const STATUS_COLORS: Record<string, string> = {
  aberto: "bg-[var(--warning)] text-white",
  respondido: "bg-[var(--brand-blue)] text-white",
  resolvido: "bg-[var(--success)] text-white",
};

// DEBT-FE-018: Status icons alongside color to avoid color-only conveying meaning
const STATUS_ICONS: Record<string, React.ReactElement> = {
  aberto: (
    <svg aria-hidden="true" className="w-2.5 h-2.5 inline-block mr-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  respondido: (
    <svg aria-hidden="true" className="w-2.5 h-2.5 inline-block mr-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  ),
  resolvido: (
    <svg aria-hidden="true" className="w-2.5 h-2.5 inline-block mr-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

const STATUS_FILTER_TABS: Array<{ value: string; label: string }> = [
  { value: "", label: "Todos" },
  { value: "aberto", label: "Aberto" },
  { value: "respondido", label: "Respondido" },
  { value: "resolvido", label: "Resolvido" },
];

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "agora";
  if (mins < 60) return `${mins}min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d`;
  return new Date(dateStr).toLocaleDateString("pt-BR");
}

// DEBT-FE-012: Show ComingSoonPage when feature is gated
const MENSAGENS_GATED = isFeatureGated("mensagens");

export default function MensagensPage() {
  if (MENSAGENS_GATED) {
    return (
      <>
        <PageHeader title="Suporte" />
        <ComingSoonPage
          title="Central de Mensagens"
          description="Comunique-se diretamente com a equipe SmartLic. Envie duvidas, sugestoes ou reporte problemas e acompanhe suas conversas em um so lugar."
        />
      </>
    );
  }

  return <MensagensPageInner />;
}

function MensagensPageInner() {
  const { session, user, loading: authLoading, isAdmin } = useAuth();
  const router = useRouter();

  // State
  const [selectedConv, setSelectedConv] = useState<ConversationDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [loadingThread, setLoadingThread] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // SWR-based conversations list (FE-007)
  const {
    conversations,
    isLoading: loading,
    error: conversationsError,
    mutate: mutateConversations,
  } = useConversations({ statusFilter });
  const fetchError = !!conversationsError;

  // New conversation form
  const [showNew, setShowNew] = useState(false);
  const [newCategory, setNewCategory] = useState<ConversationCategory>("suporte");
  const [newSubject, setNewSubject] = useState("");
  const [newBody, setNewBody] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Reply
  const [replyBody, setReplyBody] = useState("");
  const [replying, setReplying] = useState(false);

  // Mobile: show thread view
  const [mobileShowThread, setMobileShowThread] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const authHeader = session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : undefined;

  // Redirect if not logged in
  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [authLoading, user, router]);


  // Fetch single conversation thread
  const fetchThread = useCallback(
    async (id: string) => {
      if (!authHeader) return;
      setLoadingThread(true);
      try {
        const res = await fetch(`/api/messages/conversations/${id}`, {
          headers: { ...authHeader, "Content-Type": "application/json" },
        });
        if (!res.ok) throw new Error("Erro ao carregar conversa");
        const data: ConversationDetail = await res.json();
        setSelectedConv(data);
        setMobileShowThread(true);
      } catch {
        setError("Erro ao carregar conversa");
      } finally {
        setLoadingThread(false);
      }
    },
    [authHeader],
  );

  // Scroll to bottom of messages when thread loads or new message arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [selectedConv?.messages]);

  // Create conversation
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authHeader || !newSubject.trim() || !newBody.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch("/api/messages/conversations", {
        method: "POST",
        headers: { ...authHeader, "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: newSubject.trim(),
          category: newCategory,
          body: newBody.trim(),
        }),
      });
      if (!res.ok) throw new Error("Erro ao criar conversa");
      const data = await res.json();
      setNewSubject("");
      setNewBody("");
      setShowNew(false);
      await mutateConversations();
      // Open the newly created conversation
      fetchThread(data.id);
    } catch {
      setError("Erro ao criar conversa");
    } finally {
      setSubmitting(false);
    }
  };

  // Reply
  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authHeader || !selectedConv || !replyBody.trim()) return;
    setReplying(true);
    try {
      const res = await fetch(
        `/api/messages/conversations/${selectedConv.id}/reply`,
        {
          method: "POST",
          headers: { ...authHeader, "Content-Type": "application/json" },
          body: JSON.stringify({ body: replyBody.trim() }),
        },
      );
      if (!res.ok) throw new Error("Erro ao enviar resposta");
      setReplyBody("");
      await fetchThread(selectedConv.id);
      mutateConversations(); // refresh list for status change
    } catch {
      setError("Erro ao enviar resposta");
    } finally {
      setReplying(false);
    }
  };

  // Mark resolved (admin)
  const handleResolve = async () => {
    if (!authHeader || !selectedConv) return;
    try {
      const res = await fetch(
        `/api/messages/conversations/${selectedConv.id}/status`,
        {
          method: "PATCH",
          headers: { ...authHeader, "Content-Type": "application/json" },
          body: JSON.stringify({ status: "resolvido" }),
        },
      );
      if (!res.ok) throw new Error("Erro ao atualizar status");
      await fetchThread(selectedConv.id);
      mutateConversations(); // refresh list for status change
    } catch {
      setError("Erro ao atualizar status");
    }
  };

  // GTM-POLISH-001 AC1-AC3: Unified auth loading
  if (authLoading) {
    return <AuthLoadingScreen />;
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="w-8 h-8 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--canvas)] flex flex-col">
      <PageHeader title="Suporte" />

      {/* Main layout: two-panel */}
      <div className="flex-1 flex max-w-6xl mx-auto w-full">
        {/* Left panel — conversation list */}
        <div
          className={`w-full md:w-[360px] md:min-w-[320px] border-r border-[var(--border)] bg-[var(--surface-0)] flex flex-col ${
            mobileShowThread ? "hidden md:flex" : "flex"
          }`}
        >
          {/* New + filter */}
          <div className="p-4 border-b border-[var(--border)] space-y-3">
            <button
              onClick={() => setShowNew(!showNew)}
              className="w-full px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm font-medium hover:bg-[var(--brand-blue)] transition-colors"
            >
              {showNew ? "Cancelar" : "Nova mensagem"}
            </button>

            {/* Status filter tabs */}
            <div className="flex gap-1 overflow-x-auto">
              {STATUS_FILTER_TABS.map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => setStatusFilter(tab.value)}
                  className={`px-3 py-1 text-xs rounded-full whitespace-nowrap transition-colors ${
                    statusFilter === tab.value
                      ? "bg-[var(--brand-navy)] text-white"
                      : "bg-[var(--surface-1)] text-[var(--ink-secondary)] hover:bg-[var(--surface-2)]"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* New conversation form */}
          {showNew && (
            <form onSubmit={handleCreate} className="p-4 border-b border-[var(--border)] bg-[var(--surface-1)] space-y-3">
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value as ConversationCategory)}
                className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm"
              >
                {(Object.entries(CATEGORY_LABELS) as Array<[ConversationCategory, string]>).map(
                  ([val, label]) => (
                    <option key={val} value={val}>
                      {label}
                    </option>
                  ),
                )}
              </select>
              <input
                type="text"
                placeholder="Assunto"
                value={newSubject}
                onChange={(e) => setNewSubject(e.target.value)}
                maxLength={200}
                required
                className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm"
              />
              <textarea
                placeholder="Sua mensagem..."
                value={newBody}
                onChange={(e) => setNewBody(e.target.value)}
                maxLength={5000}
                required
                rows={3}
                className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm resize-none"
              />
              <button
                type="submit"
                disabled={submitting || !newSubject.trim() || !newBody.trim()}
                className="w-full px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm font-medium hover:bg-[var(--brand-blue)] disabled:opacity-50 transition-colors"
              >
                {submitting ? "Enviando..." : "Enviar"}
              </button>
            </form>
          )}

          {/* Error */}
          {error && (
            <div className="p-3 m-3 bg-[var(--error-subtle)] text-[var(--error)] text-sm rounded-card">
              {error}
              <button onClick={() => setError(null)} className="ml-2 underline text-xs">
                fechar
              </button>
            </div>
          )}

          {/* Conversation list */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              /* GTM-POLISH-001 AC7: Skeleton rows in conversation list */
              <div className="space-y-0" data-testid="mensagens-skeleton">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="px-4 py-3 border-b border-[var(--border)]">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="h-4 w-3/4 bg-[var(--surface-1)] rounded animate-pulse mb-2" style={{ animationDelay: `${i * 100}ms` }} />
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-16 bg-[var(--surface-1)] rounded animate-pulse" />
                          <div className="h-3 w-14 bg-[var(--surface-1)] rounded animate-pulse" />
                        </div>
                      </div>
                      <div className="h-3 w-8 bg-[var(--surface-1)] rounded animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : fetchError ? (
              <ErrorStateWithRetry
                message="Nao foi possivel carregar suas conversas."
                onRetry={() => { mutateConversations(); }}
                compact
              />
            ) : conversations.length === 0 ? (
              /* GTM-POLISH-001 AC9: Enhanced empty state with icon + description + action hint */
              <div className="p-8 text-center" data-testid="mensagens-empty-state">
                <div className="mx-auto mb-4 w-14 h-14 flex items-center justify-center rounded-full bg-[var(--brand-blue-subtle)]">
                  <svg
                    role="img"
                    aria-label="Nenhuma conversa"
                    className="w-7 h-7 text-[var(--brand-blue)]"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                  </svg>
                </div>
                <h3 className="text-base font-semibold text-[var(--ink)] mb-2">
                  Nenhuma conversa ainda
                </h3>
                <p className="text-sm text-[var(--ink-secondary)] mb-4 max-w-xs mx-auto">
                  Envie uma mensagem para nossa equipe de suporte. Respondemos em poucas horas.
                </p>
                <button
                  onClick={() => setShowNew(true)}
                  className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm font-medium hover:bg-[var(--brand-blue)] transition-colors"
                >
                  Iniciar conversa
                </button>
              </div>
            ) : (
              conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => fetchThread(c.id)}
                  className={`w-full text-left px-4 py-3 border-b border-[var(--border)] hover:bg-[var(--surface-1)] transition-colors ${
                    selectedConv?.id === c.id ? "bg-[var(--surface-1)]" : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {c.unread_count > 0 && (
                          <span className="w-2 h-2 rounded-full bg-[var(--brand-blue)] flex-shrink-0" />
                        )}
                        <span className="text-sm font-medium text-[var(--ink)] truncate">
                          {c.subject}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-2)] text-[var(--ink-secondary)]">
                          {CATEGORY_LABELS[c.category] || c.category}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded inline-flex items-center ${STATUS_COLORS[c.status] || ""}`}>
                          {STATUS_ICONS[c.status]}
                          <span aria-hidden="true">{STATUS_LABELS[c.status] || c.status}</span>
                          <span className="sr-only">{STATUS_LABELS[c.status] || c.status}</span>
                        </span>
                      </div>
                      {isAdmin && c.user_email && (
                        <p className="text-[11px] text-[var(--ink-muted)] mt-0.5 truncate">
                          {c.user_email}
                        </p>
                      )}
                    </div>
                    <span className="text-[11px] text-[var(--ink-muted)] whitespace-nowrap flex-shrink-0">
                      {timeAgo(c.last_message_at)}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right panel — thread view */}
        <div
          className={`flex-1 flex flex-col bg-[var(--canvas)] ${
            mobileShowThread ? "flex" : "hidden md:flex"
          }`}
        >
          {/* ISSUE-062: Mobile back button — visible only when thread is open on mobile */}
          {mobileShowThread && (
            <div className="lg:hidden flex items-center gap-2 px-4 py-2 border-b border-[var(--border)] bg-[var(--surface-0)]">
              <button
                onClick={() => setMobileShowThread(false)}
                className="flex items-center gap-1.5 text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
                aria-label="Voltar para conversas"
              >
                <svg className="w-4 h-4" aria-hidden="true" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
                </svg>
                Conversas
              </button>
            </div>
          )}
          {!selectedConv ? (
            <div className="flex-1 flex items-center justify-center text-[var(--ink-muted)] text-sm">
              Selecione uma conversa para visualizar
            </div>
          ) : loadingThread ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              {/* Thread header */}
              <div className="p-4 border-b border-[var(--border)] bg-[var(--surface-0)]">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-[var(--ink)]">
                      {selectedConv.subject}
                    </h2>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 rounded bg-[var(--surface-2)] text-[var(--ink-secondary)]">
                        {CATEGORY_LABELS[selectedConv.category] || selectedConv.category}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded inline-flex items-center ${
                          STATUS_COLORS[selectedConv.status] || ""
                        }`}
                      >
                        {STATUS_ICONS[selectedConv.status]}
                        <span aria-hidden="true">{STATUS_LABELS[selectedConv.status] || selectedConv.status}</span>
                        <span className="sr-only">{STATUS_LABELS[selectedConv.status] || selectedConv.status}</span>
                      </span>
                      <span className="text-xs text-[var(--ink-muted)]">
                        {new Date(selectedConv.created_at).toLocaleDateString("pt-BR")}
                      </span>
                    </div>
                    {isAdmin && selectedConv.user_email && (
                      <p className="text-xs text-[var(--ink-muted)] mt-1">
                        De: {selectedConv.user_email}
                      </p>
                    )}
                  </div>
                  {isAdmin && selectedConv.status !== "resolvido" && (
                    <button
                      onClick={handleResolve}
                      className="px-3 py-1.5 text-xs bg-[var(--success)] text-white rounded-button hover:opacity-90 transition-opacity whitespace-nowrap"
                    >
                      Marcar como resolvido
                    </button>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {selectedConv.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.is_admin_reply ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2.5 ${
                        msg.is_admin_reply
                          ? "bg-[var(--brand-blue-subtle)] text-[var(--ink)]"
                          : "bg-[var(--surface-0)] border border-[var(--border)] text-[var(--ink)]"
                      }`}
                    >
                      {msg.sender_email && (
                        <p className="text-[11px] font-medium text-[var(--ink-muted)] mb-1">
                          {msg.is_admin_reply ? "Equipe SmartLic" : msg.sender_email}
                        </p>
                      )}
                      <p className="text-sm whitespace-pre-wrap break-words">{msg.body}</p>
                      <p className="text-[10px] text-[var(--ink-muted)] mt-1 text-right">
                        {new Date(msg.created_at).toLocaleString("pt-BR", {
                          day: "2-digit",
                          month: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Reply form */}
              {selectedConv.status !== "resolvido" && (
                <form
                  onSubmit={handleReply}
                  className="p-4 border-t border-[var(--border)] bg-[var(--surface-0)] flex gap-2"
                >
                  <textarea
                    placeholder="Escreva sua resposta..."
                    value={replyBody}
                    onChange={(e) => setReplyBody(e.target.value)}
                    maxLength={5000}
                    rows={2}
                    className="flex-1 px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm resize-none"
                  />
                  <button
                    type="submit"
                    disabled={replying || !replyBody.trim()}
                    className="self-end px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm font-medium hover:bg-[var(--brand-blue)] disabled:opacity-50 transition-colors"
                  >
                    {replying ? "..." : "Enviar"}
                  </button>
                </form>
              )}

              {selectedConv.status === "resolvido" && (
                <div className="p-4 border-t border-[var(--border)] bg-[var(--surface-1)] text-center text-sm text-[var(--ink-muted)]">
                  Esta conversa foi marcada como resolvida.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
