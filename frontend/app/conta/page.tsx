"use client";

import { useState } from "react";
import { useAuth } from "../components/AuthProvider";
import { usePlan } from "../../hooks/usePlan";
import { PageHeader } from "../../components/PageHeader";
import { getUserFriendlyError } from "../../lib/error-messages";
import { getPlanDisplayName } from "../../lib/plans";
import Link from "next/link";
import { toast } from "sonner";
import { CancelSubscriptionModal } from "../../components/account/CancelSubscriptionModal";

export default function ContaPage() {
  const { user, session, loading: authLoading, signOut } = useAuth();
  const { planInfo } = usePlan();
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
      <div className="max-w-lg mx-auto py-8 px-4">

        {/* Profile info */}
        <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6">
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

        {/* Change password */}
        <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6">
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
            <span>Ao alterar sua senha, voce sera desconectado e precisara fazer login novamente.</span>
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
        <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6" data-testid="plan-section">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Seu Acesso ao SmartLic</h2>

          {planInfo ? (
            <div className="space-y-4">
              {/* Status badge */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-[var(--ink-muted)]">Status:</span>
                {planInfo.plan_id === "free_trial" ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                    Periodo de avaliacao
                  </span>
                ) : planInfo.subscription_status === "active" ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400">
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
                      <span className="text-[var(--ink-secondary)]">Analises usadas</span>
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
                    <span className="text-[var(--ink-secondary)]">Analises este mes</span>
                    <span className="font-medium text-[var(--ink)]">
                      {planInfo.quota_used} de {planInfo.capabilities.max_requests_per_month === -1 ? "ilimitado" : planInfo.capabilities.max_requests_per_month}
                    </span>
                  </div>
                  {planInfo.quota_reset_date && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--ink-secondary)]">Proxima renovacao</span>
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
                      Ativo ate {new Date(cancellingEndsAt).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })}
                    </p>
                    <p className="text-xs text-[var(--ink-muted)] mt-0.5">
                      Voce mantem acesso completo ate esta data.
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

        {/* Data & Privacy section (LGPD) */}
        <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card mb-6">
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
