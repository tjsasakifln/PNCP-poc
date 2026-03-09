"use client";

import { useState, useEffect, useCallback } from "react";
import { useUser } from "../../../contexts/UserContext";
import { supabase } from "../../../lib/supabase";
import { MfaSetupWizard } from "../../../components/auth/MfaSetupWizard";
import { getUserFriendlyError } from "../../../lib/error-messages";
import { Button } from "../../../components/ui/button";
import { toast } from "sonner";

/**
 * DEBT-011 FE-001: /conta/seguranca — Password change + MFA management.
 */

interface MfaFactor {
  id: string;
  type: string;
  friendly_name: string;
  verified: boolean;
}

export default function SegurancaPage() {
  const { user, session, authLoading, isAdmin, signOut } = useUser();
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [factors, setFactors] = useState<MfaFactor[]>([]);
  const [showSetup, setShowSetup] = useState(false);
  const [showDisable, setShowDisable] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [disableLoading, setDisableLoading] = useState(false);
  const [disableError, setDisableError] = useState("");
  const [loading, setLoading] = useState(true);

  // Password state
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdError, setPwdError] = useState<string | null>(null);
  const [pwdSuccess, setPwdSuccess] = useState(false);

  const fetchMfaStatus = useCallback(async () => {
    try {
      const { data } = await supabase.auth.mfa.listFactors();
      const verifiedFactors = data?.totp?.filter(
        (f: { status: string }) => f.status === "verified"
      ) || [];
      setMfaEnabled(verifiedFactors.length > 0);
      setFactors(
        verifiedFactors.map((f: { id: string; factor_type: string; friendly_name?: string; status: string }) => ({
          id: f.id,
          type: f.factor_type || "totp",
          friendly_name: f.friendly_name || "Autenticador",
          verified: f.status === "verified",
        }))
      );
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading) fetchMfaStatus();
  }, [authLoading, fetchMfaStatus]);

  const handleDisable = async () => {
    if (isAdmin) { setDisableError("Admin/Master não pode desativar MFA."); return; }
    if (disableCode.length !== 6) return;
    setDisableLoading(true);
    setDisableError("");
    try {
      const factor = factors[0];
      if (!factor) return;
      const { error: verifyError } = await supabase.auth.mfa.challengeAndVerify({ factorId: factor.id, code: disableCode });
      if (verifyError) { setDisableError("Código inválido. Verifique e tente novamente."); setDisableCode(""); setDisableLoading(false); return; }
      const { error: unenrollError } = await supabase.auth.mfa.unenroll({ factorId: factor.id });
      if (unenrollError) { setDisableError(unenrollError.message); setDisableLoading(false); return; }
      await supabase.auth.refreshSession();
      setShowDisable(false);
      setDisableCode("");
      toast.success("MFA desativado com sucesso.");
      fetchMfaStatus();
    } catch {
      setDisableError("Erro ao desativar MFA.");
    } finally {
      setDisableLoading(false);
    }
  };

  const handleSetupComplete = () => { setShowSetup(false); toast.success("MFA configurado com sucesso!"); fetchMfaStatus(); };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdError(null);
    setPwdSuccess(false);
    if (newPassword.length < 6) { setPwdError("Senha deve ter no mínimo 6 caracteres"); return; }
    if (newPassword !== confirmPassword) { setPwdError("As senhas não coincidem"); return; }
    setPwdLoading(true);
    try {
      const res = await fetch("/api/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session!.access_token}` },
        body: JSON.stringify({ new_password: newPassword }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Erro ao alterar senha");
      }
      setPwdSuccess(true);
      setNewPassword("");
      setConfirmPassword("");
      setShowNewPassword(false);
      setShowConfirmPassword(false);
      setTimeout(async () => { await signOut(); }, 2000);
    } catch (err) {
      setPwdError(getUserFriendlyError(err));
    } finally {
      setPwdLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)]" />
      </div>
    );
  }

  if (!user) {
    return <div className="flex items-center justify-center py-12"><p className="text-[var(--ink-secondary)]">Faça login para acessar esta página.</p></div>;
  }

  return (
    <div className="space-y-6">
      {/* Password change */}
      <div className="p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
        <h2 className="text-lg font-semibold text-[var(--ink)] mb-4">Alterar senha</h2>

        {pwdError && <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">{pwdError}</div>}
        {pwdSuccess && <div className="mb-4 p-3 bg-[var(--success-subtle)] text-[var(--success)] rounded-input text-sm">Senha alterada com sucesso! Redirecionando para login...</div>}

        <div className="mb-4 p-3 bg-[var(--warning-subtle)] text-[var(--warning)] rounded-input text-sm flex items-start gap-2">
          <svg role="img" aria-label="Aviso" className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Ao alterar sua senha, você será desconectado e precisará fazer login novamente.</span>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4">
          <PasswordField id="newPassword" label="Nova senha" value={newPassword} onChange={setNewPassword} show={showNewPassword} onToggle={() => setShowNewPassword(!showNewPassword)} placeholder="Minimo 6 caracteres" />
          <PasswordField id="confirmPassword" label="Confirmar nova senha" value={confirmPassword} onChange={setConfirmPassword} show={showConfirmPassword} onToggle={() => setShowConfirmPassword(!showConfirmPassword)} placeholder="Repita a nova senha" />
          <Button type="submit" disabled={pwdLoading} loading={pwdLoading} variant="primary" size="lg" className="w-full">
            {pwdLoading ? "Alterando..." : "Alterar senha"}
          </Button>
        </form>
      </div>

      {/* MFA */}
      {showSetup && (
        <div className="p-6 bg-[var(--surface-0)] rounded-card border border-[var(--border)]">
          <MfaSetupWizard userEmail={user.email || ""} onComplete={handleSetupComplete} onCancel={() => setShowSetup(false)} />
        </div>
      )}

      {!showSetup && (
        <div className="p-6 bg-[var(--surface-0)] rounded-card border border-[var(--border)]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--ink)]">Autenticação em dois fatores (MFA)</h2>
            {mfaEnabled ? (
              <span className="px-3 py-1 bg-[var(--success-subtle)] text-[var(--success)] text-sm font-medium rounded-full">MFA Ativo</span>
            ) : (
              <span className="px-3 py-1 bg-[var(--surface-1)] text-[var(--ink-muted)] text-sm font-medium rounded-full">Inativo</span>
            )}
          </div>

          <p className="text-sm text-[var(--ink-secondary)] mb-6">
            {mfaEnabled
              ? "Sua conta está protegida com autenticação em dois fatores."
              : "Adicione uma camada extra de segurança à sua conta."}
          </p>

          {mfaEnabled && factors.length > 0 && (
            <div className="mb-6 p-4 bg-[var(--surface-1)] rounded-lg">
              <h3 className="text-sm font-medium text-[var(--ink)] mb-2">Fatores configurados</h3>
              {factors.map((f) => (
                <div key={f.id} className="flex items-center gap-3 text-sm text-[var(--ink-secondary)]">
                  <svg className="w-4 h-4 text-[var(--success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>{f.friendly_name || "Autenticador TOTP"}</span>
                </div>
              ))}
            </div>
          )}

          {!mfaEnabled ? (
            <button onClick={() => setShowSetup(true)} className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors">
              Ativar autenticação em dois fatores
            </button>
          ) : (
            <div className="space-y-3">
              <button
                onClick={async () => {
                  if (!session?.access_token) return;
                  try {
                    const res = await fetch("/api/mfa?endpoint=regenerate-recovery", { method: "POST", headers: { Authorization: `Bearer ${session.access_token}` } });
                    if (res.ok) { const data = await res.json(); navigator.clipboard.writeText(data.codes.join("\n")); toast.success("Novos códigos gerados e copiados!"); }
                    else { const err = await res.json(); toast.error(err.error || "Erro ao regenerar códigos."); }
                  } catch { toast.error("Erro ao regenerar códigos de recuperação."); }
                }}
                className="w-full py-2 border border-[var(--border)] rounded-button text-sm text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
              >
                Regenerar códigos de recuperação
              </button>

              {isAdmin ? (
                <p className="text-xs text-center text-[var(--ink-muted)]">Contas admin/master não podem desativar MFA.</p>
              ) : (
                <>
                  {!showDisable ? (
                    <button onClick={() => setShowDisable(true)} className="w-full py-2 text-sm text-[var(--error)] hover:underline">Desativar MFA</button>
                  ) : (
                    <div className="p-4 bg-[var(--error-subtle)] rounded-lg space-y-3">
                      <p className="text-sm text-[var(--error)] font-medium">Tem certeza? Sua conta ficará menos segura.</p>
                      <p className="text-xs text-[var(--ink-secondary)]">Digite seu codigo TOTP atual para confirmar a desativação.</p>
                      {disableError && <p className="text-sm text-[var(--error)]">{disableError}</p>}
                      <input type="text" inputMode="numeric" pattern="[0-9]*" maxLength={6} autoFocus value={disableCode} onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ""))} className="w-full px-4 py-2 text-center font-mono rounded-input border border-[var(--border)] bg-[var(--surface-0)]" placeholder="000000" />
                      <div className="flex gap-3">
                        <button onClick={() => { setShowDisable(false); setDisableCode(""); setDisableError(""); }} className="flex-1 py-2 border border-[var(--border)] rounded-button text-sm">Cancelar</button>
                        <button onClick={handleDisable} disabled={disableCode.length !== 6 || disableLoading} className="flex-1 py-2 bg-[var(--error)] text-white rounded-button text-sm font-semibold disabled:opacity-50">
                          {disableLoading ? "Desativando..." : "Confirmar desativação"}
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PasswordField({ id, label, value, onChange, show, onToggle, placeholder }: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  show: boolean;
  onToggle: () => void;
  placeholder: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">{label}</label>
      <div className="relative">
        <input
          id={id}
          type={show ? "text" : "password"}
          required
          minLength={6}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
          placeholder={placeholder}
        />
        <button type="button" onClick={onToggle} className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)] hover:text-[var(--ink)] transition-colors" aria-label={show ? "Ocultar senha" : "Mostrar senha"}>
          <svg role="img" aria-label="Icone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {show ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            ) : (
              <>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </>
            )}
          </svg>
        </button>
      </div>
    </div>
  );
}
