"use client";

import { useState } from "react";
import { PLAN_CONFIGS } from "../../../lib/plans";
import { toast } from "sonner";

const PLAN_OPTIONS = Object.keys(PLAN_CONFIGS);

const getAdminPlanDisplayName = (planId: string): string => {
  const config = PLAN_CONFIGS[planId];
  if (!config) return planId;
  return config.price
    ? `${config.displayNamePt} (${config.price})`
    : config.displayNamePt;
};

interface AdminCreateUserProps {
  session: { access_token: string } | null;
  onCreated: () => void;
  onCancel: () => void;
}

export function AdminCreateUser({ session, onCreated, onCancel }: AdminCreateUserProps) {
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newName, setNewName] = useState("");
  const [newCompany, setNewCompany] = useState("");
  const [newPlan, setNewPlan] = useState("free_trial");
  const [creating, setCreating] = useState(false);

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
      onCreated();
      onCancel();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erro ao criar usuário");
    } finally {
      setCreating(false);
    }
  };

  return (
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
  );
}
