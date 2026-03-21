"use client";

import { useState } from "react";
import { PLAN_CONFIGS } from "../../../lib/plans";
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

const PLAN_OPTIONS = Object.keys(PLAN_CONFIGS);

const getAdminPlanDisplayName = (planId: string): string => {
  const config = PLAN_CONFIGS[planId];
  if (!config) return planId;
  return config.price
    ? `${config.displayNamePt} (${config.price})`
    : config.displayNamePt;
};

interface AdminUserTableProps {
  users: UserProfile[];
  total: number;
  loading: boolean;
  error: string | null;
  search: string;
  page: number;
  limit: number;
  session: { access_token: string } | null;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onRefresh: () => void;
}

export function AdminUserTable({
  users,
  total,
  loading,
  error,
  search,
  page,
  limit,
  session,
  onSearchChange,
  onPageChange,
  onRefresh,
}: AdminUserTableProps) {
  // Credit editing state
  const [editingCreditsUserId, setEditingCreditsUserId] = useState<string | null>(null);
  const [editCreditsValue, setEditCreditsValue] = useState<string>("");
  const [savingCredits, setSavingCredits] = useState(false);

  const handleAssignPlan = async (userId: string, planId: string) => {
    if (!session) return;
    try {
      const res = await fetch(`/api/admin/users/${userId}/assign-plan?plan_id=${planId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) throw new Error("Erro ao atribuir plano");
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao atribuir plano");
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
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao excluir usuário");
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
        throw new Error(err.detail || "Erro ao atualizar créditos");
      }

      setEditingCreditsUserId(null);
      setEditCreditsValue("");
      onRefresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao atualizar créditos");
    } finally {
      setSavingCredits(false);
    }
  };

  const formatDate = (iso: string) => new Date(iso).toLocaleDateString("pt-BR");

  return (
    <>
      {error && (
        <div className="mb-6 p-4 bg-[var(--error-subtle)] text-[var(--error)] rounded-card">{error}</div>
      )}

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Buscar por email, nome ou empresa..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onRefresh()}
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
                          title="Clique para editar créditos"
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
          <button onClick={() => onPageChange(Math.max(0, page - 1))} disabled={page === 0}
            className="px-3 py-1 text-sm border border-[var(--border)] rounded-button disabled:opacity-30">
            Anterior
          </button>
          <span className="text-sm text-[var(--ink-secondary)]">{page + 1} de {Math.ceil(total / limit)}</span>
          <button onClick={() => onPageChange(page + 1)} disabled={page >= Math.ceil(total / limit) - 1}
            className="px-3 py-1 text-sm border border-[var(--border)] rounded-button disabled:opacity-30">
            Próximo
          </button>
        </div>
      )}
    </>
  );
}
