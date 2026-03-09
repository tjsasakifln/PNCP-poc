"use client";

import { useState, useEffect, useCallback } from "react";
import { useUser } from "../../../contexts/UserContext";
import { toast } from "sonner";
import Link from "next/link";
import { completenessCount, TOTAL_PROFILE_FIELDS, type ProfileContext } from "../profile-utils";
import { ATESTADOS_CATALOG, PORTE_OPTIONS, EXPERIENCIA_OPTIONS, ALL_UFS } from "../conta-constants";
import { ProfileField, SelectField, NumberField } from "../conta-fields";

/** DEBT-011 FE-001: /conta/perfil — Profile editing + Licitante profile. */
export default function PerfilPage() {
  const { user, session, authLoading } = useUser();

  // Profile de Licitante state
  const [profileCtx, setProfileCtx] = useState<ProfileContext | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileEdit, setProfileEdit] = useState(false);
  const [editUfs, setEditUfs] = useState<string[]>([]);
  const [editPorte, setEditPorte] = useState("");
  const [editExperiencia, setEditExperiencia] = useState("");
  const [editValorMin, setEditValorMin] = useState("");
  const [editValorMax, setEditValorMax] = useState("");
  const [editFuncionários, setEditFuncionários] = useState("");
  const [editFaturamento, setEditFaturamento] = useState("");
  const [editAtestados, setEditAtestados] = useState<string[]>([]);

  const fetchProfileCtx = useCallback(async () => {
    if (!session?.access_token) return;
    setProfileLoading(true);
    try {
      const res = await fetch("/api/profile-context", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProfileCtx(data.context_data ?? {});
      }
    } catch {
      // silent
    } finally {
      setProfileLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    fetchProfileCtx();
  }, [fetchProfileCtx]);

  const startEdit = () => {
    if (!profileCtx) return;
    setEditUfs(profileCtx.ufs_atuacao ?? []);
    setEditPorte(profileCtx.porte_empresa ?? "");
    setEditExperiencia(profileCtx.experiencia_licitacoes ?? "");
    setEditValorMin(profileCtx.faixa_valor_min != null ? String(profileCtx.faixa_valor_min) : "");
    setEditValorMax(profileCtx.faixa_valor_max != null ? String(profileCtx.faixa_valor_max) : "");
    setEditFuncionários(profileCtx.capacidade_funcionarios != null ? String(profileCtx.capacidade_funcionarios) : "");
    setEditFaturamento(profileCtx.faturamento_anual != null ? String(profileCtx.faturamento_anual) : "");
    setEditAtestados(profileCtx.atestados ?? []);
    setProfileEdit(true);
  };

  const handleSaveProfile = async () => {
    if (!session?.access_token) return;
    setProfileSaving(true);
    try {
      const payload: ProfileContext = {
        ...(profileCtx ?? {}),
        ufs_atuacao: editUfs.length ? editUfs : undefined,
        porte_empresa: editPorte || undefined,
        experiencia_licitacoes: editExperiencia || undefined,
        faixa_valor_min: editValorMin ? Number(editValorMin) : null,
        faixa_valor_max: editValorMax ? Number(editValorMax) : null,
        capacidade_funcionarios: editFuncionários ? Number(editFuncionários) : null,
        faturamento_anual: editFaturamento ? Number(editFaturamento) : null,
        atestados: editAtestados.length ? editAtestados : undefined,
      };
      const res = await fetch("/api/profile-context", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setProfileCtx(data.context_data ?? payload);
        setProfileEdit(false);
        toast.success("Perfil de licitante atualizado!");
      } else {
        toast.error("Erro ao salvar perfil. Tente novamente.");
      }
    } catch {
      toast.error("Erro ao salvar perfil. Tente novamente.");
    } finally {
      setProfileSaving(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    );
  }

  if (!user || !session) {
    return (
      <div className="text-center py-12">
        <p className="text-[var(--ink-secondary)] mb-4">Faça login para acessar sua conta</p>
        <Link href="/login" className="text-[var(--brand-blue)] hover:underline">Ir para login</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Profile info */}
      <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
        <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Dados do perfil</h2>
        <div className="space-y-3">
          <div>
            <span className="text-sm text-[var(--ink-muted)]">Email</span>
            <p className="text-[var(--ink)]">{user.email}</p>
          </div>
          <div>
            <span className="text-sm text-[var(--ink-muted)]">Nome</span>
            <p className="text-[var(--ink)]">
              {user.user_metadata?.full_name || user.user_metadata?.name || "-"}
            </p>
          </div>
        </div>
      </div>

      {/* Perfil de Licitante */}
      <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card" data-testid="profile-licitante-section">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-[var(--ink)]">Perfil de Licitante</h2>
            {profileCtx !== null && (
              <p className="text-xs text-[var(--ink-muted)] mt-0.5">
                {completenessCount(profileCtx)}/{TOTAL_PROFILE_FIELDS} campos preenchidos
                {completenessCount(profileCtx) === TOTAL_PROFILE_FIELDS && (
                  <span className="ml-2 text-emerald-600 dark:text-emerald-400 font-medium">Completo!</span>
                )}
              </p>
            )}
          </div>
          {!profileEdit && !profileLoading && (
            <button
              onClick={startEdit}
              className="text-sm text-[var(--brand-blue)] hover:underline font-medium"
              data-testid="edit-profile-btn"
            >
              Editar
            </button>
          )}
        </div>

        {/* Progress bar */}
        {profileCtx !== null && (() => {
          const filled = completenessCount(profileCtx);
          const pct = Math.floor((filled / TOTAL_PROFILE_FIELDS) * 100);
          const barColor = pct <= 33 ? "bg-red-500" : pct <= 66 ? "bg-yellow-500" : "bg-green-500";
          return (
            <div className="mb-4" data-testid="profile-progress-bar">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-[var(--ink-muted)]">{filled}/{TOTAL_PROFILE_FIELDS} campos</span>
                <span className={`text-xs font-medium ${pct <= 33 ? "text-red-600 dark:text-red-400" : pct <= 66 ? "text-yellow-600 dark:text-yellow-400" : "text-green-600 dark:text-green-400"}`}>{pct}%</span>
              </div>
              <div className="w-full h-2 bg-[var(--surface-1)] rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${barColor}`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })()}

        {/* Guidance banner */}
        {profileCtx !== null && completenessCount(profileCtx) < TOTAL_PROFILE_FIELDS && !profileEdit && (
          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start gap-3" data-testid="profile-guidance-banner">
            <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-300">
                Perfil completo melhora a precisão da análise de viabilidade em até 40%
              </p>
              <button
                onClick={startEdit}
                className="mt-2 text-sm font-semibold text-blue-700 dark:text-blue-400 hover:underline"
                data-testid="fill-now-btn"
              >
                Preencher agora →
              </button>
            </div>
          </div>
        )}

        {profileLoading && (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 bg-[var(--surface-1)] rounded" />
            ))}
          </div>
        )}

        {!profileLoading && !profileEdit && profileCtx !== null && (
          <div className="space-y-3">
            <ProfileField label="Estados de atuação" value={profileCtx.ufs_atuacao?.length ? profileCtx.ufs_atuacao.join(", ") : null} />
            <ProfileField label="Porte da empresa" value={PORTE_OPTIONS.find((o) => o.value === profileCtx.porte_empresa)?.label ?? profileCtx.porte_empresa} />
            <ProfileField label="Experiência" value={EXPERIENCIA_OPTIONS.find((o) => o.value === profileCtx.experiencia_licitacoes)?.label ?? profileCtx.experiencia_licitacoes} />
            <ProfileField label="Faixa de valor" value={profileCtx.faixa_valor_min != null && profileCtx.faixa_valor_max != null ? `R$ ${Number(profileCtx.faixa_valor_min).toLocaleString("pt-BR")} – R$ ${Number(profileCtx.faixa_valor_max).toLocaleString("pt-BR")}` : null} />
            <ProfileField label="Funcionários" value={profileCtx.capacidade_funcionarios != null ? String(profileCtx.capacidade_funcionarios) : null} />
            <ProfileField label="Faturamento anual" value={profileCtx.faturamento_anual != null ? `R$ ${Number(profileCtx.faturamento_anual).toLocaleString("pt-BR")}` : null} />
            <ProfileField label="Atestados" value={profileCtx.atestados?.length ? profileCtx.atestados.map((id) => ATESTADOS_CATALOG.find((a) => a.id === id)?.label ?? id).join(", ") : null} />
          </div>
        )}

        {/* Edit form */}
        {!profileLoading && profileEdit && (
          <div className="space-y-5">
            {/* UFs */}
            <div>
              <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">Estados de atuação</label>
              <div className="flex flex-wrap gap-1.5">
                {ALL_UFS.map((uf) => (
                  <button
                    key={uf}
                    type="button"
                    onClick={() => setEditUfs((prev) => prev.includes(uf) ? prev.filter((u) => u !== uf) : [...prev, uf])}
                    className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                      editUfs.includes(uf)
                        ? "border-[var(--brand-blue)] bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)] font-medium"
                        : "border-[var(--border)] text-[var(--ink-secondary)] hover:border-[var(--border-strong)]"
                    }`}
                  >
                    {uf}
                  </button>
                ))}
              </div>
            </div>

            <SelectField label="Porte da empresa" value={editPorte} onChange={setEditPorte} options={PORTE_OPTIONS} />
            <SelectField label="Experiência com licitações" value={editExperiencia} onChange={setEditExperiencia} options={EXPERIENCIA_OPTIONS} />

            {/* Value range */}
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="Valor mínimo (R$)" value={editValorMin} onChange={setEditValorMin} placeholder="Ex: 50000" />
              <NumberField label="Valor máximo (R$)" value={editValorMax} onChange={setEditValorMax} placeholder="Ex: 5000000" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <NumberField label="Funcionários" value={editFuncionários} onChange={setEditFuncionários} placeholder="Ex: 15" />
              <NumberField label="Faturamento anual (R$)" value={editFaturamento} onChange={setEditFaturamento} placeholder="Ex: 500000" />
            </div>

            {/* Certifications */}
            <div>
              <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">Atestados e certificações</label>
              <div className="space-y-1.5">
                {ATESTADOS_CATALOG.map((cert) => (
                  <button
                    key={cert.id}
                    type="button"
                    onClick={() => setEditAtestados((prev) => prev.includes(cert.id) ? prev.filter((id) => id !== cert.id) : [...prev, cert.id])}
                    className={`w-full text-left px-3 py-2 rounded-input border text-sm transition-colors ${
                      editAtestados.includes(cert.id)
                        ? "border-[var(--brand-blue)] bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)]"
                        : "border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:bg-[var(--surface-1)]"
                    }`}
                  >
                    {cert.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleSaveProfile}
                disabled={profileSaving}
                className="flex-1 py-2.5 bg-[var(--brand-navy)] text-white rounded-button font-semibold text-sm hover:bg-[var(--brand-blue)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                data-testid="save-profile-btn"
              >
                {profileSaving ? "Salvando..." : "Salvar perfil"}
              </button>
              <button
                onClick={() => setProfileEdit(false)}
                disabled={profileSaving}
                className="px-4 py-2.5 border border-[var(--border)] rounded-button text-sm text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
