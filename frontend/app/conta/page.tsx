"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../components/AuthProvider";
import { usePlan } from "../../hooks/usePlan";
import { PageHeader } from "../../components/PageHeader";
import { getUserFriendlyError } from "../../lib/error-messages";
import { getPlanDisplayName } from "../../lib/plans";
import Link from "next/link";
import { toast } from "sonner";
import { CancelSubscriptionModal } from "../../components/account/CancelSubscriptionModal";

// ─── Certifications catalog (mirrors backend ATESTADOS_DISPONIVEIS) ───────────
const ATESTADOS_CATALOG: Array<{ id: string; label: string }> = [
  { id: "crea", label: "CREA (Engenharia)" },
  { id: "crf", label: "CRF (Farmácia)" },
  { id: "inmetro", label: "INMETRO" },
  { id: "iso_9001", label: "ISO 9001 (Qualidade)" },
  { id: "iso_14001", label: "ISO 14001 (Ambiental)" },
  { id: "pgr_pcmso", label: "PGR/PCMSO (Segurança do Trabalho)" },
  { id: "alvara_sanitario", label: "Alvará Sanitário" },
  { id: "registro_anvisa", label: "Registro ANVISA" },
  { id: "habilitacao_antt", label: "Habilitação ANTT" },
  { id: "registro_cfq", label: "Registro CRQ (Química)" },
  { id: "licenca_ambiental", label: "Licença Ambiental" },
  { id: "crt", label: "CRT (Técnico)" },
];

const PORTE_OPTIONS = [
  { value: "mei", label: "MEI — Microempreendedor Individual" },
  { value: "me", label: "ME — Microempresa" },
  { value: "epp", label: "EPP — Empresa de Pequeno Porte" },
  { value: "medio", label: "Médio Porte" },
  { value: "grande", label: "Grande Empresa" },
];

const EXPERIENCIA_OPTIONS = [
  { value: "iniciante", label: "Iniciante — nunca participei" },
  { value: "basico", label: "Básico — já participei de algumas" },
  { value: "intermediario", label: "Intermediário — participo regularmente" },
  { value: "avancado", label: "Avançado — processo sistematizado" },
];

const ALL_UFS = [
  "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
  "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
  "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
];

import { completenessCount, TOTAL_PROFILE_FIELDS, type ProfileContext } from "./profile-utils";

export default function ContaPage() {
  const { user, session, loading: authLoading, signOut } = useAuth();
  const { planInfo, error: planError, isFromCache, cachedAt, refresh: refreshPlan } = usePlan();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Account deletion state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleted, setDeleted] = useState(false);

  // Data export state
  const [exporting, setExporting] = useState(false);

  // Subscription cancellation state
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancellingEndsAt, setCancellingEndsAt] = useState<string | null>(null);

  // STORY-278: Alert Preferences state
  const [alertEnabled, setAlertEnabled] = useState(true);
  const [alertFrequency, setAlertFrequency] = useState("daily");
  const [alertLoading, setAlertLoading] = useState(false);
  const [alertSaving, setAlertSaving] = useState(false);
  // STORY-315 AC17: Digest mode (consolidated vs individual)
  const [digestMode, setDigestMode] = useState<"individual" | "consolidated">("individual");
  // STORY-315 AC14: User's alerts list
  const [userAlerts, setUserAlerts] = useState<Array<{ id: string; name: string; active: boolean; filters: Record<string, unknown> }>>([]);
  const [userAlertsLoading, setUserAlertsLoading] = useState(false);

  // SAB-010 AC10-AC11: Section refs for anchor navigation
  const perfilRef = useRef<HTMLDivElement>(null);
  const segurancaRef = useRef<HTMLDivElement>(null);
  const senhaRef = useRef<HTMLDivElement>(null);
  const acessoRef = useRef<HTMLDivElement>(null);
  const licitanteRef = useRef<HTMLDivElement>(null);
  const alertasRef = useRef<HTMLDivElement>(null);
  const lgpdRef = useRef<HTMLDivElement>(null);
  const [activeSection, setActiveSection] = useState("perfil");

  // STORY-260: Profile de Licitante state
  const [profileCtx, setProfileCtx] = useState<ProfileContext | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileEdit, setProfileEdit] = useState(false);
  // Editable form state (populated when editing starts)
  const [editUfs, setEditUfs] = useState<string[]>([]);
  const [editPorte, setEditPorte] = useState("");
  const [editExperiencia, setEditExperiencia] = useState("");
  const [editValorMin, setEditValorMin] = useState("");
  const [editValorMax, setEditValorMax] = useState("");
  const [editFuncionarios, setEditFuncionarios] = useState("");
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

  // STORY-278: Fetch alert preferences
  const fetchAlertPrefs = useCallback(async () => {
    if (!session?.access_token) return;
    setAlertLoading(true);
    try {
      const res = await fetch("/api/alert-preferences", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAlertEnabled(data.enabled ?? true);
        setAlertFrequency(data.frequency ?? "daily");
      }
    } catch {
      // silent — defaults are fine
    } finally {
      setAlertLoading(false);
    }
  }, [session?.access_token]);

  // STORY-315 AC14: Fetch user alerts list
  const fetchUserAlerts = useCallback(async () => {
    if (!session?.access_token) return;
    setUserAlertsLoading(true);
    try {
      const res = await fetch("/api/alerts", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : data.alerts || [];
        setUserAlerts(list);
      }
    } catch {
      // silent — non-critical
    } finally {
      setUserAlertsLoading(false);
    }
  }, [session?.access_token]);

  const handleSaveAlertPrefs = useCallback(async (enabled: boolean, frequency: string) => {
    if (!session?.access_token) return;
    setAlertSaving(true);
    try {
      const res = await fetch("/api/alert-preferences", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ enabled, frequency }),
      });
      if (res.ok) {
        const data = await res.json();
        setAlertEnabled(data.enabled);
        setAlertFrequency(data.frequency);
        toast.success("Preferências de alerta atualizadas");
      } else {
        toast.error("Erro ao salvar preferências");
      }
    } catch {
      toast.error("Erro de conexão");
    } finally {
      setAlertSaving(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    fetchProfileCtx();
    fetchAlertPrefs();
    fetchUserAlerts();
  }, [fetchProfileCtx, fetchAlertPrefs, fetchUserAlerts]);

  // SAB-010 AC11: Smooth scroll to section
  const scrollToSection = useCallback((key: string) => {
    const refs: Record<string, React.RefObject<HTMLDivElement | null>> = {
      perfil: perfilRef, seguranca: segurancaRef, senha: senhaRef,
      acesso: acessoRef, licitante: licitanteRef, alertas: alertasRef, lgpd: lgpdRef,
    };
    refs[key]?.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    setActiveSection(key);
  }, []);

  // SAB-010 AC10: Track active section via IntersectionObserver
  useEffect(() => {
    const entries: Array<{ key: string; ref: React.RefObject<HTMLDivElement | null> }> = [
      { key: "perfil", ref: perfilRef }, { key: "seguranca", ref: segurancaRef },
      { key: "senha", ref: senhaRef }, { key: "acesso", ref: acessoRef },
      { key: "licitante", ref: licitanteRef }, { key: "alertas", ref: alertasRef },
      { key: "lgpd", ref: lgpdRef },
    ];
    const observers: IntersectionObserver[] = [];
    entries.forEach(({ key, ref }) => {
      const el = ref.current;
      if (!el) return;
      const observer = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActiveSection(key); },
        { rootMargin: "-80px 0px -60% 0px", threshold: 0 }
      );
      observer.observe(el);
      observers.push(observer);
    });
    return () => observers.forEach((o) => o.disconnect());
  }, [profileCtx]);

  // SAB-010 AC2: "Preencher agora" — enters edit mode and scrolls to licitante section
  const handleFillNow = () => {
    startEdit();
    setTimeout(() => {
      licitanteRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  };

  const startEdit = () => {
    if (!profileCtx) return;
    setEditUfs(profileCtx.ufs_atuacao ?? []);
    setEditPorte(profileCtx.porte_empresa ?? "");
    setEditExperiencia(profileCtx.experiencia_licitacoes ?? "");
    setEditValorMin(profileCtx.faixa_valor_min != null ? String(profileCtx.faixa_valor_min) : "");
    setEditValorMax(profileCtx.faixa_valor_max != null ? String(profileCtx.faixa_valor_max) : "");
    setEditFuncionarios(profileCtx.capacidade_funcionarios != null ? String(profileCtx.capacidade_funcionarios) : "");
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
        capacidade_funcionarios: editFuncionarios ? Number(editFuncionarios) : null,
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
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    );
  }

  if (!user || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center">
          <p className="text-[var(--ink-secondary)] mb-4">Faça login para acessar sua conta</p>
          <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
            Ir para login
          </Link>
        </div>
      </div>
    );
  }

  // Show deletion confirmation page
  if (deleted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[var(--success-subtle)] flex items-center justify-center">
            <svg role="img" aria-label="Sucesso" className="w-8 h-8 text-[var(--success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-display font-bold text-[var(--ink)] mb-3">
            Conta excluída
          </h1>
          <p className="text-[var(--ink-secondary)] mb-6">
            Sua conta e todos os dados associados foram excluídos permanentemente.
            Você será redirecionado para a página inicial.
          </p>
        </div>
      </div>
    );
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (newPassword.length < 6) {
      setError("Senha deve ter no mínimo 6 caracteres");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("As senhas não coincidem");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ new_password: newPassword }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao alterar senha");
      }

      setSuccess(true);
      setNewPassword("");
      setConfirmPassword("");
      setShowNewPassword(false);
      setShowConfirmPassword(false);

      // Logout apos 2 segundos para o usuario ver a mensagem de sucesso
      setTimeout(async () => {
        await signOut();
      }, 2000);
    } catch (err) {
      setError(getUserFriendlyError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      const res = await fetch("/api/me", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || data.message || "Erro ao excluir conta");
      }

      setShowDeleteModal(false);
      setDeleted(true);

      // Redirect to home after 3 seconds
      setTimeout(async () => {
        await signOut();
      }, 3000);
    } catch (err) {
      setDeleteError(getUserFriendlyError(err));
    } finally {
      setDeleting(false);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const res = await fetch("/api/me/export", {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!res.ok) {
        throw new Error("Erro ao exportar dados");
      }

      // Extract filename from Content-Disposition header or build default
      const disposition = res.headers.get("Content-Disposition");
      let filename = `smartlic_dados_${user.id.slice(0, 8)}_${new Date().toISOString().slice(0, 10)}.json`;
      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/);
        if (match) filename = match[1];
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(getUserFriendlyError(err));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      <PageHeader title="Minha Conta" />

      {/* SAB-010 AC10: Sticky anchor navigation */}
      <nav className="sticky top-0 z-20 bg-[var(--canvas)] border-b border-[var(--border)]" data-testid="section-nav">
        <div className="max-w-lg mx-auto px-4 flex gap-1 overflow-x-auto py-2 scrollbar-hide" role="tablist">
          {[
            { key: "perfil", label: "Perfil" },
            { key: "seguranca", label: "Segurança" },
            { key: "senha", label: "Senha" },
            { key: "acesso", label: "Acesso" },
            { key: "licitante", label: "Licitante" },
            { key: "alertas", label: "Alertas" },
            { key: "lgpd", label: "LGPD" },
          ].map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeSection === tab.key}
              onClick={() => scrollToSection(tab.key)}
              className={`px-3 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                activeSection === tab.key
                  ? "bg-[var(--brand-navy)] text-white"
                  : "text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      <div className="max-w-lg mx-auto py-8 px-4">

        {/* Profile info */}
        <div ref={perfilRef} className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6 scroll-mt-14">
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

        {/* STORY-317 AC9: Security section with MFA link */}
        <div ref={segurancaRef} className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6 scroll-mt-14">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[var(--ink)]">Segurança</h2>
              <p className="text-sm text-[var(--ink-secondary)] mt-1">
                Gerencie a autenticação em dois fatores (MFA) e outras configurações de segurança.
              </p>
            </div>
            <Link
              href="/conta/seguranca"
              className="px-4 py-2 bg-[var(--brand-navy)] text-white rounded-button text-sm font-semibold hover:bg-[var(--brand-blue)] transition-colors"
            >
              Configurar MFA
            </Link>
          </div>
        </div>

        {/* Change password */}
        <div ref={senhaRef} className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6 scroll-mt-14">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Alterar senha</h2>

          {error && (
            <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-[var(--success-subtle)] text-[var(--success)] rounded-input text-sm">
              Senha alterada com sucesso! Redirecionando para login...
            </div>
          )}

          {/* Aviso sobre logout */}
          <div className="mb-4 p-3 bg-[var(--warning-subtle,#fef3cd)] text-[var(--warning,#856404)] rounded-input text-sm flex items-start gap-2">
            <svg
              role="img"
              aria-label="Aviso" className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Ao alterar sua senha, você será desconectado e precisará fazer login novamente.</span>
          </div>

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
                Nova senha
              </label>
              <div className="relative">
                <input
                  id="newPassword"
                  type={showNewPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)]
                             bg-[var(--surface-0)] text-[var(--ink)]
                             focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                             focus:ring-[var(--brand-blue-subtle)]"
                  placeholder="Mínimo 6 caracteres"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                             hover:text-[var(--ink)] transition-colors"
                  aria-label={showNewPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showNewPassword ? (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
                Confirmar nova senha
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)]
                             bg-[var(--surface-0)] text-[var(--ink)]
                             focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                             focus:ring-[var(--brand-blue-subtle)]"
                  placeholder="Repita a nova senha"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                             hover:text-[var(--ink)] transition-colors"
                  aria-label={showConfirmPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showConfirmPassword ? (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg
              role="img"
              aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button
                         font-semibold hover:bg-[var(--brand-blue)] transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Alterando..." : "Alterar senha"}
            </button>
          </form>
        </div>

        {/* Plan Status Section (AC9-AC13) */}
        <div ref={acessoRef} className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6 scroll-mt-14" data-testid="plan-section">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Seu Acesso ao SmartLic</h2>

          {/* GTM-UX-004 AC2: Show "Verificado ha X min" when using cached data */}
          {isFromCache && cachedAt && (
            <div className="mb-4 p-3 bg-[var(--warning-subtle,#fef3cd)] rounded-input text-sm text-[var(--warning,#856404)] flex items-center gap-2" data-testid="plan-cache-notice">
              <svg aria-hidden="true" className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Verificado há {Math.max(1, Math.round((Date.now() - cachedAt) / 60000))} min
            </div>
          )}

          {/* GTM-UX-004 AC3: Error state when backend fails and no cache */}
          {planError && !planInfo && (
            <div className="text-center py-4" data-testid="plan-error">
              <p className="text-[var(--ink-secondary)] mb-3">
                Não foi possível verificar seu plano.
              </p>
              <button
                onClick={refreshPlan}
                className="px-4 py-2 rounded-button bg-[var(--brand-navy)] text-white text-sm font-medium hover:bg-[var(--brand-blue)] transition-colors"
              >
                Tentar novamente
              </button>
            </div>
          )}

          {planInfo ? (
            <div className="space-y-4">
              {/* Status badge */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-[var(--ink-muted)]">Status:</span>
                {planInfo.plan_id === "free_trial" ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-400">
                    Período de avaliação
                  </span>
                ) : planInfo.subscription_status === "active" ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400">
                    Ativo
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                    Expirado
                  </span>
                )}
              </div>

              {/* Trial-specific info (AC10) */}
              {planInfo.plan_id === "free_trial" && planInfo.trial_expires_at && (() => {
                const daysLeft = Math.max(0, Math.ceil((new Date(planInfo.trial_expires_at!).getTime() - Date.now()) / 86400000));
                const totalTrialDays = 7;
                const used = planInfo.quota_used ?? 0;
                const total = planInfo.capabilities.max_requests_per_month ?? 3;
                const usagePct = total > 0 ? Math.min(Math.round((used / total) * 100), 100) : 0;

                return (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--ink-secondary)]">Dias restantes</span>
                      <span className="font-medium text-[var(--ink)]">{daysLeft} de {totalTrialDays}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--ink-secondary)]">Análises usadas</span>
                      <span className="font-medium text-[var(--ink)]">{used} de {total}</span>
                    </div>
                    <div className="w-full h-2 bg-[var(--surface-1)] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${usagePct}%`,
                          backgroundColor: usagePct > 80 ? "var(--error,#dc2626)" : "var(--brand-blue)",
                        }}
                      />
                    </div>
                    <p className="text-xs text-[var(--ink-muted)] text-right">{usagePct}% utilizado</p>
                  </div>
                );
              })()}

              {/* Subscriber info (AC11) */}
              {planInfo.plan_id !== "free_trial" && planInfo.subscription_status === "active" && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--ink-secondary)]">Acesso</span>
                    <span className="font-medium text-[var(--ink)]">{getPlanDisplayName(planInfo.plan_id, planInfo.plan_name)}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--ink-secondary)]">Análises este mês</span>
                    <span className="font-medium text-[var(--ink)]">
                      {planInfo.quota_used} de {planInfo.capabilities.max_requests_per_month === -1 ? "ilimitado" : planInfo.capabilities.max_requests_per_month}
                    </span>
                  </div>
                  {planInfo.quota_reset_date && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--ink-secondary)]">Próxima renovação</span>
                      <span className="font-medium text-[var(--ink)]">
                        {new Date(planInfo.quota_reset_date).toLocaleDateString("pt-BR", { day: "2-digit", month: "long" })}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Cancelling notice */}
              {cancellingEndsAt && (
                <div className="flex items-center gap-3 p-3 bg-[var(--warning-subtle,#fef3cd)] rounded-input">
                  <svg aria-hidden="true" className="w-5 h-5 text-[var(--warning,#856404)] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-[var(--warning,#856404)]">
                      Ativo até {new Date(cancellingEndsAt).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })}
                    </p>
                    <p className="text-xs text-[var(--ink-muted)] mt-0.5">
                      Você mantém acesso completo até esta data.
                    </p>
                  </div>
                </div>
              )}

              {/* CTA: primary = Subscribe (trial) or Manage (subscriber) — AC12 */}
              <div className="pt-2 space-y-3">
                {planInfo.plan_id === "free_trial" ? (
                  <Link
                    href="/planos"
                    className="w-full py-3 px-4 rounded-button bg-[var(--brand-navy)] text-white
                               hover:bg-[var(--brand-blue)] transition-colors
                               flex items-center justify-center gap-2 font-medium"
                    data-testid="plan-cta-primary"
                  >
                    Assinar SmartLic Pro
                    <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </Link>
                ) : planInfo.subscription_status === "active" && !cancellingEndsAt ? (
                  <Link
                    href="/planos"
                    className="w-full py-3 px-4 rounded-button border border-[var(--brand-blue)] text-[var(--brand-blue)]
                               bg-transparent hover:bg-[var(--brand-blue-subtle)] transition-colors
                               flex items-center justify-center gap-2 font-medium text-sm"
                    data-testid="plan-cta-primary"
                  >
                    Gerenciar acesso
                  </Link>
                ) : planInfo.subscription_status !== "active" ? (
                  <Link
                    href="/planos"
                    className="w-full py-3 px-4 rounded-button bg-[var(--brand-navy)] text-white
                               hover:bg-[var(--brand-blue)] transition-colors
                               flex items-center justify-center gap-2 font-medium"
                    data-testid="plan-cta-primary"
                  >
                    Reativar SmartLic Pro
                    <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </Link>
                ) : null}

                {/* Cancel — secondary/discreet (AC13) */}
                {planInfo.subscription_status === "active" && !cancellingEndsAt && planInfo.plan_id !== "free_trial" && (
                  <button
                    onClick={() => setShowCancelModal(true)}
                    className="w-full text-center text-xs text-[var(--ink-muted)] hover:text-[var(--error,#dc2626)]
                               transition-colors py-2"
                    data-testid="cancel-link"
                  >
                    Cancelar acesso
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="animate-pulse space-y-3">
              <div className="h-4 w-32 bg-[var(--surface-1)] rounded" />
              <div className="h-4 w-48 bg-[var(--surface-1)] rounded" />
              <div className="h-10 w-full bg-[var(--surface-1)] rounded-button" />
            </div>
          )}
        </div>

        {/* STORY-260: Perfil de Licitante section */}
        <div ref={licitanteRef} className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6 scroll-mt-14" data-testid="profile-licitante-section">
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

          {/* SAB-010 AC3: Color-coded progress bar */}
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

          {/* SAB-010 AC1: Motivational banner + AC2: Fill now button */}
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
                  onClick={handleFillNow}
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
              {/* UFs */}
              <div className="flex items-start justify-between">
                <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">Estados de atuação</span>
                <span className="text-sm text-[var(--ink)] text-right">
                  {profileCtx.ufs_atuacao?.length
                    ? profileCtx.ufs_atuacao.join(", ")
                    : <span className="text-[var(--ink-muted)] italic">Não informado</span>}
                </span>
              </div>
              {/* Porte */}
              <div className="flex items-start justify-between">
                <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">Porte da empresa</span>
                <span className="text-sm text-[var(--ink)] text-right">
                  {PORTE_OPTIONS.find((o) => o.value === profileCtx.porte_empresa)?.label
                    ?? (profileCtx.porte_empresa || <span className="text-[var(--ink-muted)] italic">Não informado</span>)}
                </span>
              </div>
              {/* Experiência */}
              <div className="flex items-start justify-between">
                <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">Experiência</span>
                <span className="text-sm text-[var(--ink)] text-right">
                  {EXPERIENCIA_OPTIONS.find((o) => o.value === profileCtx.experiencia_licitacoes)?.label
                    ?? (profileCtx.experiencia_licitacoes || <span className="text-[var(--ink-muted)] italic">Não informado</span>)}
                </span>
              </div>
              {/* Faixa de valor */}
              <div className="flex items-start justify-between">
                <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">Faixa de valor</span>
                <span className="text-sm text-[var(--ink)] text-right">
                  {profileCtx.faixa_valor_min != null && profileCtx.faixa_valor_max != null
                    ? `R$ ${Number(profileCtx.faixa_valor_min).toLocaleString("pt-BR")} – R$ ${Number(profileCtx.faixa_valor_max).toLocaleString("pt-BR")}`
                    : <span className="text-[var(--ink-muted)] italic">Não informado</span>}
                </span>
              </div>
              {/* Capacidade */}
              <div className="flex items-start justify-between">
                <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">Funcionários</span>
                <span className="text-sm text-[var(--ink)] text-right">
                  {profileCtx.capacidade_funcionarios != null
                    ? profileCtx.capacidade_funcionarios
                    : <span className="text-[var(--ink-muted)] italic">Não informado</span>}
                </span>
              </div>
              {/* Faturamento */}
              <div className="flex items-start justify-between">
                <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">Faturamento anual</span>
                <span className="text-sm text-[var(--ink)] text-right">
                  {profileCtx.faturamento_anual != null
                    ? `R$ ${Number(profileCtx.faturamento_anual).toLocaleString("pt-BR")}`
                    : <span className="text-[var(--ink-muted)] italic">Não informado</span>}
                </span>
              </div>
              {/* Atestados */}
              <div className="flex items-start justify-between">
                <span className="text-sm text-[var(--ink-muted)] w-36 flex-shrink-0">Atestados</span>
                <span className="text-sm text-[var(--ink)] text-right">
                  {profileCtx.atestados?.length
                    ? profileCtx.atestados
                        .map((id) => ATESTADOS_CATALOG.find((a) => a.id === id)?.label ?? id)
                        .join(", ")
                    : <span className="text-[var(--ink-muted)] italic">Não informado</span>}
                </span>
              </div>
            </div>
          )}

          {!profileLoading && profileEdit && (
            <div className="space-y-5">
              {/* UFs multi-select */}
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">Estados de atuação</label>
                <div className="flex flex-wrap gap-1.5">
                  {ALL_UFS.map((uf) => (
                    <button
                      key={uf}
                      type="button"
                      onClick={() =>
                        setEditUfs((prev) =>
                          prev.includes(uf) ? prev.filter((u) => u !== uf) : [...prev, uf]
                        )
                      }
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

              {/* Porte select */}
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Porte da empresa</label>
                <select
                  value={editPorte}
                  onChange={(e) => setEditPorte(e.target.value)}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
                >
                  <option value="">Selecione...</option>
                  {PORTE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              {/* Experiência select */}
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Experiência com licitações</label>
                <select
                  value={editExperiencia}
                  onChange={(e) => setEditExperiencia(e.target.value)}
                  className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
                >
                  <option value="">Selecione...</option>
                  {EXPERIENCIA_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              {/* Faixa de valor */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Valor mínimo (R$)</label>
                  <input
                    type="number"
                    min={0}
                    value={editValorMin}
                    onChange={(e) => setEditValorMin(e.target.value)}
                    placeholder="Ex: 50000"
                    className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Valor máximo (R$)</label>
                  <input
                    type="number"
                    min={0}
                    value={editValorMax}
                    onChange={(e) => setEditValorMax(e.target.value)}
                    placeholder="Ex: 5000000"
                    className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
                  />
                </div>
              </div>

              {/* Funcionários + Faturamento */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Funcionários</label>
                  <input
                    type="number"
                    min={0}
                    value={editFuncionarios}
                    onChange={(e) => setEditFuncionarios(e.target.value)}
                    placeholder="Ex: 15"
                    className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">Faturamento anual (R$)</label>
                  <input
                    type="number"
                    min={0}
                    value={editFaturamento}
                    onChange={(e) => setEditFaturamento(e.target.value)}
                    placeholder="Ex: 500000"
                    className="w-full px-3 py-2 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] text-sm focus:border-[var(--brand-blue)] focus:outline-none"
                  />
                </div>
              </div>

              {/* Atestados multi-select */}
              <div>
                <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">Atestados e certificações</label>
                <div className="space-y-1.5">
                  {ATESTADOS_CATALOG.map((cert) => (
                    <button
                      key={cert.id}
                      type="button"
                      onClick={() =>
                        setEditAtestados((prev) =>
                          prev.includes(cert.id)
                            ? prev.filter((id) => id !== cert.id)
                            : [...prev, cert.id]
                        )
                      }
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

        {/* STORY-278: Alert Preferences section */}
        <div ref={alertasRef} className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6 scroll-mt-14" data-testid="alert-preferences-section">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Alertas por Email</h2>
          <p className="text-sm text-[var(--ink-secondary)] mb-4">
            Receba oportunidades de licitação filtradas para seu perfil diretamente no seu email.
          </p>

          {alertLoading ? (
            <div className="h-16 bg-[var(--surface-1)] rounded animate-pulse" />
          ) : (
            <div className="space-y-4">
              {/* Toggle on/off */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--ink)]">Receber alerta por email</span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={alertEnabled}
                  disabled={alertSaving}
                  data-testid="alert-toggle"
                  onClick={() => {
                    const newEnabled = !alertEnabled;
                    setAlertEnabled(newEnabled);
                    handleSaveAlertPrefs(newEnabled, alertFrequency);
                  }}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--brand-blue)] ${
                    alertEnabled ? "bg-[var(--brand-navy)]" : "bg-[var(--surface-2)]"
                  } ${alertSaving ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      alertEnabled ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              {/* Frequency selector — only shown when enabled */}
              {alertEnabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">Frequência</label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { value: "daily", label: "Diário" },
                        { value: "twice_weekly", label: "2x por semana" },
                        { value: "weekly", label: "Semanal" },
                      ].map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          disabled={alertSaving}
                          data-testid={`alert-freq-${opt.value}`}
                          onClick={() => {
                            setAlertFrequency(opt.value);
                            handleSaveAlertPrefs(alertEnabled, opt.value);
                          }}
                          className={`px-4 py-2 rounded-button text-sm font-medium transition-colors ${
                            alertFrequency === opt.value
                              ? "bg-[var(--brand-navy)] text-white"
                              : "border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:bg-[var(--surface-1)]"
                          } ${alertSaving ? "opacity-50 cursor-not-allowed" : ""}`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* STORY-315 AC17: Digest mode — consolidated vs individual */}
                  <div>
                    <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-2">
                      Formato do email
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { value: "individual" as const, label: "1 email por alerta" },
                        { value: "consolidated" as const, label: "1 email consolidado" },
                      ].map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          data-testid={`digest-mode-${opt.value}`}
                          onClick={() => setDigestMode(opt.value)}
                          className={`px-4 py-2 rounded-button text-sm font-medium transition-colors ${
                            digestMode === opt.value
                              ? "bg-[var(--brand-navy)] text-white"
                              : "border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] hover:bg-[var(--surface-1)]"
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                    <p className="text-[11px] text-[var(--ink-muted)] mt-1">
                      {digestMode === "consolidated"
                        ? "Você receberá 1 email com todos os alertas reunidos."
                        : "Você receberá 1 email separado para cada alerta."}
                    </p>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* STORY-315 AC14: Meus Alertas section */}
        <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6" data-testid="meus-alertas-section">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--ink)]">Meus Alertas</h2>
            <Link
              href="/alertas"
              className="text-sm font-medium text-[var(--brand-blue)] hover:underline"
            >
              Gerenciar alertas
            </Link>
          </div>

          {userAlertsLoading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="h-12 bg-[var(--surface-1)] rounded animate-pulse" />
              ))}
            </div>
          ) : userAlerts.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-sm text-[var(--ink-muted)] mb-3">
                Você ainda não tem alertas configurados.
              </p>
              <Link
                href="/alertas"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-button text-sm font-medium bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] transition-colors"
                data-testid="create-first-alert-btn"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Criar primeiro alerta
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {userAlerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg border transition-colors ${
                    alert.active
                      ? "border-[var(--brand-blue)]/20 bg-[var(--surface-0)]"
                      : "border-[var(--border)] bg-[var(--surface-1)] opacity-60"
                  }`}
                  data-testid={`conta-alert-${alert.id}`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${alert.active ? "bg-green-500" : "bg-[var(--ink-faint)]"}`} />
                    <span className="text-sm font-medium text-[var(--ink)] truncate">
                      {alert.name}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--ink-muted)] flex-shrink-0 ml-2">
                    {alert.active ? "Ativo" : "Inativo"}
                  </span>
                </div>
              ))}
              {userAlerts.length > 5 && (
                <Link
                  href="/alertas"
                  className="block text-center text-sm text-[var(--brand-blue)] hover:underline py-1"
                >
                  Ver todos os {userAlerts.length} alertas
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Data & Privacy section (LGPD) */}
        <div ref={lgpdRef} className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6 scroll-mt-14">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Dados e Privacidade</h2>
          <p className="text-sm text-[var(--ink-secondary)] mb-4">
            Conforme a LGPD, você pode exportar seus dados ou excluir sua conta a qualquer momento.
          </p>

          <div className="space-y-3">
            {/* Export Data Button */}
            <button
              onClick={handleExportData}
              disabled={exporting}
              className="w-full py-3 px-4 rounded-button border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         hover:bg-[var(--surface-1)] transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2"
            >
              <svg role="img" aria-label="Exportar" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {exporting ? "Exportando..." : "Exportar Meus Dados"}
            </button>

            {/* Delete Account Button */}
            <button
              onClick={() => setShowDeleteModal(true)}
              className="w-full py-3 px-4 rounded-button border border-[var(--error,#dc2626)]
                         text-[var(--error,#dc2626)] bg-transparent
                         hover:bg-[var(--error-subtle,#fef2f2)] transition-colors
                         flex items-center justify-center gap-2"
            >
              <svg role="img" aria-label="Excluir" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Excluir Minha Conta
            </button>
          </div>
        </div>
      </div>

      {/* Cancel Subscription Modal */}
      <CancelSubscriptionModal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        onCancelled={(endsAt) => {
          setShowCancelModal(false);
          setCancellingEndsAt(endsAt);
        }}
        accessToken={session.access_token}
      />

      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div
            role="alertdialog"
            aria-labelledby="delete-title"
            aria-describedby="delete-desc"
            className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-6 max-w-md w-full shadow-xl"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-[var(--error-subtle,#fef2f2)] flex items-center justify-center flex-shrink-0">
                <svg role="img" aria-label="Atenção" className="w-5 h-5 text-[var(--error,#dc2626)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 id="delete-title" className="text-lg font-semibold text-[var(--ink)]">
                Excluir conta permanentemente?
              </h3>
            </div>

            <p id="delete-desc" className="text-sm text-[var(--ink-secondary)] mb-6">
              Todos os seus dados serão excluídos permanentemente: perfil, histórico de buscas,
              assinaturas, mensagens. Esta ação <strong>não pode ser desfeita</strong>.
            </p>

            {deleteError && (
              <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">
                {deleteError}
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteError(null);
                }}
                disabled={deleting}
                className="px-4 py-2 rounded-button border border-[var(--border)]
                           text-[var(--ink)] bg-[var(--surface-0)]
                           hover:bg-[var(--surface-1)] transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="px-4 py-2 rounded-button bg-[var(--error,#dc2626)] text-white
                           hover:opacity-90 transition-opacity
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? "Excluindo..." : "Excluir Permanentemente"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
