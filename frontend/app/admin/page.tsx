"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PLAN_CONFIGS } from "../../lib/plans";

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

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  const fetchUsers = useCallback(async () => {
    if (!session || !backendUrl) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
      if (search) params.set("search", search);
      const res = await fetch(`${backendUrl}/admin/users?${params}`, {
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
  }, [session, page, search, backendUrl]);

  useEffect(() => {
    if (!authLoading && session) fetchUsers();
  }, [authLoading, session, fetchUsers]);

  // Show error if backend URL not configured (must be after all hooks)
  if (!backendUrl) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-canvas">
        <div className="text-center p-8">
          <h1 className="text-xl font-bold text-ink mb-2">Configuração Necessária</h1>
          <p className="text-ink-secondary">Backend URL não configurado. Configure NEXT_PUBLIC_BACKEND_URL.</p>
        </div>
      </div>
    );
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session) return;
    setCreating(true);
    try {
      const res = await fetch(`${backendUrl}/admin/users`, {
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
      alert(err instanceof Error ? err.message : "Erro");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (userId: string, email: string) => {
    if (!session) return;
    if (!confirm(`Excluir usuário ${email}? Esta ação não pode ser desfeita.`)) return;

    try {
      const res = await fetch(`${backendUrl}/admin/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao excluir");
      }
      fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro");
    }
  };

  const handleAssignPlan = async (userId: string, planId: string) => {
    if (!session) return;
    try {
      const res = await fetch(`${backendUrl}/admin/users/${userId}/assign-plan?plan_id=${planId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error("Erro ao atribuir plano");
      fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro");
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
      alert("Valor de creditos invalido. Deve ser um numero >= 0.");
      return;
    }

    setSavingCredits(true);
    try {
      const res = await fetch(`${backendUrl}/admin/users/${userId}/credits`, {
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
      alert(err instanceof Error ? err.message : "Erro ao atualizar creditos");
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
