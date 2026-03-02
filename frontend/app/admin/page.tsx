"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PLAN_CONFIGS } from "../../lib/plans";
import { toast } from "sonner";

interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  company: string | null;
  plan_type: string;
  created_at: string;
  user_subscriptions: Array<{
    id: string;
    plan_id: string;
    credits_remaining: number | null;
    expires_at: string | null;
    is_active: boolean;
  }>;
}

// Plan IDs for dropdowns (from centralized config)
const PLAN_OPTIONS = Object.keys(PLAN_CONFIGS);

// Helper to get formatted display name for admin dropdowns (includes price)
const getAdminPlanDisplayName = (planId: string): string => {
  const config = PLAN_CONFIGS[planId];
  if (!config) return planId;
  return config.price
    ? `${config.displayNamePt} (${config.price})`
    : config.displayNamePt;
};

export default function AdminPage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;

  // Create user form
  const [showCreate, setShowCreate] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newName, setNewName] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [newPlan, setNewPlan] = useState("free_trial");
  const [creating, setCreating] = useState(false);

  // Credit editing state
  const [editingCreditsUserId, setEditingCreditsUserId] = useState<string | null>(null);
  const [editCreditsValue, setEditCreditsValue] = useState<string>("");
  const [savingCredits, setSavingCredits] = useState(false);

  // STORY-352 AC5: Uptime widget state
  const [uptimePct30d, setUptimePct30d] = useState<number | null>(null);

  // STORY-350 AC6: Source health state
  const [sourceHealth, setSourceHealth] = useState<Record<string, {
    status: string;
    latency_ms?: number;
    last_check?: string;
  }>>({});
  const [sourceHealthLoading, setSourceHealthLoading] = useState(false);

  // STORY-314: Reconciliation widget state
  const [reconHistory, setReconHistory] = useState<Array<{
    id: string;
    run_at: string;
    total_checked: number;
    divergences_found: number;
    auto_fixed: number;
    manual_review: number;
    duration_ms: number;
  }>>([]);
  const [reconLoading, setReconLoading] = useState(false);
  const [reconTriggering, setReconTriggering] = useState(false);

  const fetchUsers = useCallback(async () => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
      if (search) params.set("search", search);
      const res = await fetch(`/api/admin/users?${params}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.status === 403) {
        setError("Acesso negado. Você não é administrador.");
        return;
      }
      if (!res.ok) throw new Error("Erro ao carregar usuários");
      const data = await res.json();
      setUsers(data.users);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [session, page, search]);

  const fetchSourceHealth = useCallback(async () => {
    setSourceHealthLoading(true);
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        if (data.sources) setSourceHealth(data.sources);
        if (data.uptime_pct_30d !== undefined) setUptimePct30d(data.uptime_pct_30d);
      }
    } catch {
      // Non-critical — widget is informational
    } finally {
      setSourceHealthLoading(false);
    }
  }, []);

  const fetchReconHistory = useCallback(async () => {
    if (!session) return;
    setReconLoading(true);
    try {
      const res = await fetch("/api/admin/reconciliation/history?limit=5", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setReconHistory(data.runs || []);
      }
    } catch {
      // Non-critical — widget is informational
    } finally {
      setReconLoading(false);
    }
  }, [session]);

  const handleTriggerReconciliation = async () => {
    if (!session) return;
    setReconTriggering(true);
    try {
      const res = await fetch("/api/admin/reconciliation/trigger", {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        toast.success("Reconciliacao executada com sucesso");
        fetchReconHistory();
      } else if (res.status === 409) {
        toast.error("Reconciliacao ja em execucao");
      } else {
        toast.error("Erro ao executar reconciliacao");
      }
    } catch {
      toast.error("Erro de conexao");
    } finally {
      setReconTriggering(false);
    }
  };

  useEffect(() => {
    if (!authLoading && session) {
      fetchUsers();
      fetchReconHistory();
      fetchSourceHealth();
    }
  }, [authLoading, session, fetchUsers, fetchReconHistory, fetchSourceHealth]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session) return;
    setCreating(true);
    try {
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          email: newEmail,
          password: newPassword,
          full_name: newName || undefined,
          company: newCompany || undefined,
          plan_id: newPlan,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao criar usuário");
      }
      setShowCreate(false);
      setNewEmail("");
      setNewPassword("");
      setNewName("");
      setNewCompany("");
      setNewPlan("free_trial");
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao criar usuário");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (userId: string, email: string) => {
    if (!session) return;
    if (!confirm(`Excluir usuário ${email}? Esta ação não pode ser desfeita.`)) return;

    try {
      const res = await fetch(`/api/admin/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao excluir");
      }
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao excluir usuário");
    }
  };

  const handleAssignPlan = async (userId: string, planId: string) => {
    if (!session) return;
    try {
      const res = await fetch(`/api/admin/users/${userId}/assign-plan?plan_id=${planId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error("Erro ao atribuir plano");
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao atribuir plano");
    }
  };

  const handleStartEditCredits = (userId: string, currentCredits: number | null | undefined) => {
    setEditingCreditsUserId(userId);
    setEditCreditsValue(currentCredits !== null && currentCredits !== undefined ? String(currentCredits) : "0");
  };

  const handleCancelEditCredits = () => {
    setEditingCreditsUserId(null);
    setEditCreditsValue("");
  };

  const handleSaveCredits = async (userId: string) => {
    if (!session) return;

    const credits = parseInt(editCreditsValue, 10);
    if (isNaN(credits) || credits < 0) {
      toast.error("Valor de créditos inválido. Deve ser um número >= 0.");
      return;
    }

    setSavingCredits(true);
    try {
      const res = await fetch(`/api/admin/users/${userId}/credits`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ credits }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao atualizar creditos");
      }

      setEditingCreditsUserId(null);
      setEditCreditsValue("");
      fetchUsers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao atualizar créditos");
    } finally {
      setSavingCredits(false);
    }
  };

  if (authLoading) return <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]"><p className="text-[var(--ink-secondary)]">Carregando...</p></div>;
  if (!session) return <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]"><Link href="/login" className="text-[var(--brand-blue)]">Login necessário</Link></div>;

  // Show 403 for non-admin users
  if (!isAdmin && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center max-w-md px-4">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--error-subtle)] flex items-center justify-center">
            <svg
              role="img"
              aria-label="Aviso" className="w-8 h-8 text-[var(--error)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-2">Acesso Restrito</h1>
          <p className="text-[var(--ink-secondary)] mb-6">
            Esta página é exclusiva para administradores do sistema. Se você acredita que deveria ter acesso, entre em contato com o suporte.
          </p>
          <Link
            href="/buscar"
            className="inline-block px-6 py-2 bg-[var(--brand-navy)] text-white rounded-button
                       hover:bg-[var(--brand-blue)] transition-colors"
          >
            Voltar para início
          </Link>
        </div>
      </div>
    );
  }

  const formatDate = (iso: string) => new Date(iso).toLocaleDateString("pt-BR");

  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-display font-bold text-[var(--ink)]">Admin - Usuários</h1>
            <p className="text-[var(--ink-secondary)]">{total} usuário{total !== 1 ? "s" : ""}</p>
          </div>
          <div className="flex gap-3">
            <Link href="/admin/cache" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              Cache
            </Link>
            <Link href="/admin/metrics" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              Metrics
            </Link>
            <Link href="/admin/slo" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]">
              SLOs
            </Link>
            <Link href="/mensagens" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)]">
              Mensagens
            </Link>
            <Link href="/buscar" className="px-4 py-2 border border-[var(--border)] rounded-button text-sm hover:bg-[var(--surface-1)]">
              Voltar
            </Link>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm hover:bg-[var(--brand-blue)]"
            >
              {showCreate ? "Cancelar" : "Novo usuário"}
            </button>
          </div>
        </div>

        {/* STORY-352 AC5: Uptime Widget */}
        <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-[var(--ink)]">Uptime (30 dias)</h2>
            <Link href="/status" className="text-sm text-[var(--brand-blue)] hover:underline">
              Status Page
            </Link>
          </div>
          <div className="mt-4 flex items-center gap-4">
            <div className={`text-4xl font-bold ${
              uptimePct30d === null ? "text-[var(--ink-muted)]" :
              uptimePct30d >= 99 ? "text-green-600" :
              uptimePct30d >= 95 ? "text-yellow-600" : "text-red-600"
            }`}>
              {uptimePct30d !== null ? `${uptimePct30d}%` : "—"}
            </div>
            <div className="text-sm text-[var(--ink-secondary)]">
              {uptimePct30d !== null && uptimePct30d >= 99
                ? "Alta disponibilidade"
                : uptimePct30d !== null && uptimePct30d >= 95
                  ? "Disponibilidade aceitavel"
                  : uptimePct30d !== null
                    ? "Abaixo do esperado"
                    : "Carregando..."}
            </div>
          </div>
        </div>

        {/* STORY-350 AC6: Fontes ativas card */}
        <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--ink)]">Fontes ativas</h2>
            <button
              onClick={fetchSourceHealth}
              disabled={sourceHealthLoading}
              className="text-xs px-3 py-1 border border-[var(--border)] rounded-button hover:bg-[var(--surface-1)] disabled:opacity-50 text-[var(--ink-secondary)]"
            >
              {sourceHealthLoading ? "Atualizando..." : "Atualizar"}
            </button>
          </div>
          {sourceHealthLoading && Object.keys(sourceHealth).length === 0 ? (
            <div className="h-12 bg-[var(--surface-1)] rounded animate-pulse" />
          ) : Object.keys(sourceHealth).length === 0 ? (
            <p className="text-sm text-[var(--ink-muted)]">Status indisponivel</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {Object.entries(sourceHealth).map(([code, info]) => {
                const statusLabel =
                  info.status === "healthy" ? "UP" : info.status === "degraded" ? "DEGRADED" : "DOWN";
                const statusColor =
                  info.status === "healthy"
                    ? "text-green-600 bg-green-50"
                    : info.status === "degraded"
                      ? "text-yellow-600 bg-yellow-50"
                      : "text-red-600 bg-red-50";
                const dotColor =
                  info.status === "healthy"
                    ? "bg-green-500"
                    : info.status === "degraded"
                      ? "bg-yellow-500"
                      : "bg-red-500";
                const sourceName =
                  code === "pncp" ? "PNCP" : code === "portal" ? "PCP v2" : code === "comprasgov" ? "ComprasGov" : code;

                return (
                  <div
                    key={code}
                    className="flex items-center gap-3 p-4 rounded-card border border-[var(--border)] bg-[var(--surface-1)]"
                  >
                    <span className={`w-3 h-3 rounded-full ${dotColor} flex-shrink-0`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--ink)]">{sourceName}</p>
                      {info.latency_ms !== undefined && (
                        <p className="text-xs text-[var(--ink-muted)]">{info.latency_ms}ms</p>
                      )}
                    </div>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${statusColor}`}>
                      {statusLabel}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* STORY-314 AC12: Reconciliation Widget */}
        <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--ink)]">Reconciliacao Stripe</h2>
            <button
              onClick={handleTriggerReconciliation}
              disabled={reconTriggering}
              className="px-4 py-2 text-sm bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] disabled:opacity-50"
            >
              {reconTriggering ? "Executando..." : "Executar agora"}
            </button>
          </div>

          {reconLoading ? (
            <div className="h-12 bg-[var(--surface-1)] rounded animate-pulse" />
          ) : reconHistory.length === 0 ? (
            <p className="text-sm text-[var(--ink-muted)]">Nenhuma execucao registrada</p>
          ) : (
            <div className="space-y-2">
              {reconHistory.map((run) => {
                const statusColor =
                  run.divergences_found === 0
                    ? "text-green-600"
                    : run.divergences_found < 5
                      ? "text-yellow-600"
                      : "text-red-600";
                const statusDot =
                  run.divergences_found === 0
                    ? "bg-green-500"
                    : run.divergences_found < 5
                      ? "bg-yellow-500"
                      : "bg-red-500";

                return (
                  <div
                    key={run.id}
                    className="flex items-center gap-4 text-sm py-2 px-3 rounded bg-[var(--surface-1)]"
                  >
                    <span className={`w-2 h-2 rounded-full ${statusDot}`} />
                    <span className="text-[var(--ink-muted)] w-36">
                      {new Date(run.run_at).toLocaleString("pt-BR")}
                    </span>
                    <span className="text-[var(--ink-secondary)]">
                      {run.total_checked} verificados
                    </span>
                    <span className={statusColor}>
                      {run.divergences_found} divergencia{run.divergences_found !== 1 ? "s" : ""}
                    </span>
                    <span className="text-[var(--ink-secondary)]">
                      {run.auto_fixed} corrigidas
                    </span>
                    {run.manual_review > 0 && (
                      <span className="text-yellow-600">
                        {run.manual_review} manual
                      </span>
                    )}
                    <span className="text-[var(--ink-muted)] ml-auto">
                      {run.duration_ms}ms
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {error && (
          <div className="mb-6 p-4 bg-[var(--error-subtle)] text-[var(--error)] rounded-card">{error}</div>
        )}

        {/* Create user form */}
        {showCreate && (
          <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
            <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Criar usuário</h2>
            <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-[var(--ink-secondary)] mb-1">Email *</label>
                <input type="email" required value={newEmail} onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]" />
              </div>
              <div>
                <label className="block text-sm text-[var(--ink-secondary)] mb-1">Senha *</label>
                <input type="password" required minLength={6} value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]" />
              </div>
              <div>
                <label className="block text-sm text-[var(--ink-secondary)] mb-1">Nome</label>
                <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]" />
              </div>
              <div>
                <label className="block text-sm text-[var(--ink-secondary)] mb-1">Empresa</label>
                <input type="text" value={newCompany} onChange={(e) => setNewCompany(e.target.value)}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]" />
              </div>
              <div>
                <label className="block text-sm text-[var(--ink-secondary)] mb-1">Plano</label>
                <select value={newPlan} onChange={(e) => setNewPlan(e.target.value)}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)]">
                  {PLAN_OPTIONS.map((p) => <option key={p} value={p}>{getAdminPlanDisplayName(p)}</option>)}
                </select>
              </div>
              <div className="flex items-end">
                <button type="submit" disabled={creating}
                  className="px-6 py-2 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] disabled:opacity-50">
                  {creating ? "Criando..." : "Criar"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Buscar por email, nome ou empresa..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            onKeyDown={(e) => e.key === "Enter" && fetchUsers()}
            className="w-full max-w-md px-4 py-2 rounded-input border border-[var(--border)]
                       bg-[var(--surface-0)] text-[var(--ink)]"
          />
        </div>

        {/* Users table */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-[var(--surface-1)] rounded-card animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-3 px-4 text-[var(--ink-secondary)] font-medium">Email</th>
                  <th className="text-left py-3 px-4 text-[var(--ink-secondary)] font-medium">Nome</th>
                  <th className="text-left py-3 px-4 text-[var(--ink-secondary)] font-medium">Empresa</th>
                  <th className="text-left py-3 px-4 text-[var(--ink-secondary)] font-medium">Plano</th>
                  <th className="text-left py-3 px-4 text-[var(--ink-secondary)] font-medium">Créditos</th>
                  <th className="text-left py-3 px-4 text-[var(--ink-secondary)] font-medium">Criado</th>
                  <th className="text-right py-3 px-4 text-[var(--ink-secondary)] font-medium">Ações</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const activeSub = u.user_subscriptions?.find((s) => s.is_active);
                  return (
                    <tr key={u.id} className="border-b border-[var(--border)] hover:bg-[var(--surface-1)]">
                      <td className="py-3 px-4 text-[var(--ink)]">{u.email}</td>
                      <td className="py-3 px-4 text-[var(--ink-secondary)]">{u.full_name || "-"}</td>
                      <td className="py-3 px-4 text-[var(--ink-secondary)]">{u.company || "-"}</td>
                      <td className="py-3 px-4">
                        <select
                          value={activeSub?.plan_id || u.plan_type}
                          onChange={(e) => handleAssignPlan(u.id, e.target.value)}
                          className="text-xs px-2 py-1 rounded border border-[var(--border)] bg-[var(--surface-0)]"
                        >
                          {PLAN_OPTIONS.map((p) => <option key={p} value={p}>{getAdminPlanDisplayName(p)}</option>)}
                        </select>
                      </td>
                      <td className="py-3 px-4 font-data text-[var(--ink)]">
                        {editingCreditsUserId === u.id ? (
                          <div className="flex items-center gap-1">
                            <input
                              type="number"
                              min="0"
                              value={editCreditsValue}
                              onChange={(e) => setEditCreditsValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") handleSaveCredits(u.id);
                                if (e.key === "Escape") handleCancelEditCredits();
                              }}
                              className="w-20 px-2 py-1 text-xs rounded border border-[var(--border)] bg-[var(--surface-0)]"
                              disabled={savingCredits}
                              autoFocus
                            />
                            <button
                              onClick={() => handleSaveCredits(u.id)}
                              disabled={savingCredits}
                              className="text-xs px-2 py-1 bg-[var(--brand-navy)] text-white rounded hover:bg-[var(--brand-blue)] disabled:opacity-50"
                              title="Salvar"
                            >
                              {savingCredits ? "..." : "OK"}
                            </button>
                            <button
                              onClick={handleCancelEditCredits}
                              disabled={savingCredits}
                              className="text-xs px-1 py-1 text-[var(--ink-muted)] hover:text-[var(--ink)]"
                              title="Cancelar"
                            >
                              X
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => handleStartEditCredits(u.id, activeSub?.credits_remaining)}
                            className="hover:bg-[var(--surface-1)] px-2 py-1 rounded cursor-pointer transition-colors"
                            title="Clique para editar creditos"
                          >
                            {activeSub?.credits_remaining !== null && activeSub?.credits_remaining !== undefined
                              ? activeSub.credits_remaining
                              : "\u221E"}
                          </button>
                        )}
                      </td>
                      <td className="py-3 px-4 text-[var(--ink-muted)]">{formatDate(u.created_at)}</td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleDelete(u.id, u.email)}
                          className="text-xs text-[var(--error)] hover:underline"
                        >
                          Excluir
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {Math.ceil(total / limit) > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
              className="px-3 py-1 text-sm border border-[var(--border)] rounded-button disabled:opacity-30">
              Anterior
            </button>
            <span className="text-sm text-[var(--ink-secondary)]">{page + 1} de {Math.ceil(total / limit)}</span>
            <button onClick={() => setPage(page + 1)} disabled={page >= Math.ceil(total / limit) - 1}
              className="px-3 py-1 text-sm border border-[var(--border)] rounded-button disabled:opacity-30">
              Próximo
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
