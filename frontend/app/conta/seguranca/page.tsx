"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../components/AuthProvider";
import { supabase } from "../../../lib/supabase";
import { MfaSetupWizard } from "../../../components/auth/MfaSetupWizard";
import { PageHeader } from "../../../components/PageHeader";
import { toast } from "sonner";
import Link from "next/link";

interface MfaFactor {
  id: string;
  type: string;
  friendly_name: string;
  verified: boolean;
}

export default function SegurancaPage() {
  const { user, session, loading: authLoading, isAdmin } = useAuth();
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [factors, setFactors] = useState<MfaFactor[]>([]);
  const [showSetup, setShowSetup] = useState(false);
  const [showDisable, setShowDisable] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [disableLoading, setDisableLoading] = useState(false);
  const [disableError, setDisableError] = useState("");
  const [loading, setLoading] = useState(true);

  // Fetch MFA status
  const fetchMfaStatus = useCallback(async () => {
    try {
      const { data } = await supabase.auth.mfa.listFactors();
      const verifiedFactors = data?.totp?.filter(
        (f: { status: string }) => f.status === "verified"
      ) || [];

      setMfaEnabled(verifiedFactors.length > 0);
      setFactors(
        verifiedFactors.map((f: { id: string; factor_type: string; friendly_name: string; status: string }) => ({
          id: f.id,
          type: f.factor_type || "totp",
          friendly_name: f.friendly_name || "Autenticador",
          verified: f.status === "verified",
        }))
      );
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading) fetchMfaStatus();
  }, [authLoading, fetchMfaStatus]);

  // AC18: Disable MFA
  const handleDisable = async () => {
    // AC19: Prevent disable for admin/master
    if (isAdmin) {
      setDisableError("Admin/Master não pode desativar MFA.");
      return;
    }

    if (disableCode.length !== 6) return;
    setDisableLoading(true);
    setDisableError("");

    try {
      const factor = factors[0];
      if (!factor) return;

      // Verify current code first
      const { error: verifyError } = await supabase.auth.mfa.challengeAndVerify({
        factorId: factor.id,
        code: disableCode,
      });

      if (verifyError) {
        setDisableError("Código inválido. Verifique e tente novamente.");
        setDisableCode("");
        setDisableLoading(false);
        return;
      }

      // Unenroll the factor
      const { error: unenrollError } = await supabase.auth.mfa.unenroll({
        factorId: factor.id,
      });

      if (unenrollError) {
        setDisableError(unenrollError.message);
        setDisableLoading(false);
        return;
      }

      // Refresh session to downgrade AAL
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

  const handleSetupComplete = () => {
    setShowSetup(false);
    toast.success("MFA configurado com sucesso!");
    fetchMfaStatus();
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)]" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <p className="text-[var(--ink-secondary)]">Faça login para acessar esta página.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <PageHeader
        title="Segurança"
        subtitle="Gerencie a autenticação em dois fatores da sua conta"
      />

      <div className="mt-2 mb-6">
        <Link href="/conta" className="text-sm text-[var(--brand-blue)] hover:underline">
          &larr; Voltar para Conta
        </Link>
      </div>

      {/* MFA Setup Wizard */}
      {showSetup && (
        <div className="mb-8 p-6 bg-[var(--surface-0)] rounded-card shadow-sm border border-[var(--border)]">
          <MfaSetupWizard
            userEmail={user.email || ""}
            onComplete={handleSetupComplete}
            onCancel={() => setShowSetup(false)}
          />
        </div>
      )}

      {/* MFA Status Card */}
      {!showSetup && (
        <div className="p-6 bg-[var(--surface-0)] rounded-card shadow-sm border border-[var(--border)]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--ink)]">
              Autenticação em dois fatores (MFA)
            </h2>
            {/* AC9: Status badge */}
            {mfaEnabled ? (
              <span className="px-3 py-1 bg-[var(--success-subtle)] text-[var(--success)] text-sm font-medium rounded-full">
                MFA Ativo
              </span>
            ) : (
              <span className="px-3 py-1 bg-[var(--surface-1)] text-[var(--ink-muted)] text-sm font-medium rounded-full">
                Inativo
              </span>
            )}
          </div>

          <p className="text-sm text-[var(--ink-secondary)] mb-6">
            {mfaEnabled
              ? "Sua conta está protegida com autenticação em dois fatores. Além da senha, você precisa fornecer um código do seu app autenticador para fazer login."
              : "Adicione uma camada extra de segurança à sua conta. Após ativar, você precisará de um código do app autenticador além da senha para fazer login."}
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

          {/* AC9: Action buttons */}
          {!mfaEnabled ? (
            <button
              onClick={() => setShowSetup(true)}
              className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] transition-colors"
            >
              Ativar autenticação em dois fatores
            </button>
          ) : (
            <div className="space-y-3">
              {/* Regenerate recovery codes */}
              <button
                onClick={async () => {
                  if (!session?.access_token) return;
                  try {
                    const res = await fetch("/api/mfa?endpoint=regenerate-recovery", {
                      method: "POST",
                      headers: { Authorization: `Bearer ${session.access_token}` },
                    });
                    if (res.ok) {
                      const data = await res.json();
                      // Show codes in a simple alert (could be improved with modal)
                      const codesText = data.codes.join("\n");
                      navigator.clipboard.writeText(codesText);
                      toast.success("Novos códigos gerados e copiados!");
                    } else {
                      const err = await res.json();
                      toast.error(err.error || "Erro ao regenerar códigos.");
                    }
                  } catch {
                    toast.error("Erro ao regenerar códigos de recuperação.");
                  }
                }}
                className="w-full py-2 border border-[var(--border)] rounded-button text-sm text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
              >
                Regenerar códigos de recuperação
              </button>

              {/* AC18-19: Disable MFA */}
              {isAdmin ? (
                <p className="text-xs text-center text-[var(--ink-muted)]">
                  Contas admin/master não podem desativar MFA.
                </p>
              ) : (
                <>
                  {!showDisable ? (
                    <button
                      onClick={() => setShowDisable(true)}
                      className="w-full py-2 text-sm text-[var(--error)] hover:underline"
                    >
                      Desativar MFA
                    </button>
                  ) : (
                    <div className="p-4 bg-[var(--error-subtle)] rounded-lg space-y-3">
                      <p className="text-sm text-[var(--error)] font-medium">
                        Tem certeza? Sua conta ficará menos segura.
                      </p>
                      <p className="text-xs text-[var(--ink-secondary)]">
                        Digite seu código TOTP atual para confirmar a desativação.
                      </p>
                      {disableError && (
                        <p className="text-sm text-[var(--error)]">{disableError}</p>
                      )}
                      <input
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        maxLength={6}
                        autoFocus
                        value={disableCode}
                        onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ""))}
                        className="w-full px-4 py-2 text-center font-mono rounded-input border border-[var(--border)] bg-[var(--surface-0)]"
                        placeholder="000000"
                      />
                      <div className="flex gap-3">
                        <button
                          onClick={() => { setShowDisable(false); setDisableCode(""); setDisableError(""); }}
                          className="flex-1 py-2 border border-[var(--border)] rounded-button text-sm"
                        >
                          Cancelar
                        </button>
                        <button
                          onClick={handleDisable}
                          disabled={disableCode.length !== 6 || disableLoading}
                          className="flex-1 py-2 bg-[var(--error)] text-white rounded-button text-sm font-semibold disabled:opacity-50"
                        >
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
