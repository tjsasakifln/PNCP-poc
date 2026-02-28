"use client";

import { useState, useEffect } from "react";
import { supabase } from "../../lib/supabase";

interface MfaSetupWizardProps {
  userEmail: string;
  onComplete: () => void;
  onCancel: () => void;
}

type Step = "qr" | "verify" | "recovery" | "confirm";

export function MfaSetupWizard({ userEmail, onComplete, onCancel }: MfaSetupWizardProps) {
  const [step, setStep] = useState<Step>("qr");
  const [factorId, setFactorId] = useState("");
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [verifyCode, setVerifyCode] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [codesConfirmed, setCodesConfirmed] = useState(false);

  // AC10 Step 1: Enroll TOTP factor
  useEffect(() => {
    (async () => {
      try {
        const { data, error: enrollError } = await supabase.auth.mfa.enroll({
          factorType: "totp",
          friendlyName: "SmartLic TOTP",
        });

        if (enrollError) {
          setError(enrollError.message);
          return;
        }

        if (data) {
          setFactorId(data.id);
          // AC11: QR code includes issuer "SmartLic" and user email
          setQrCode(data.totp.qr_code);
          setSecret(data.totp.secret);
        }
      } catch (err) {
        setError("Erro ao gerar QR code. Tente novamente.");
      }
    })();
  }, []);

  // AC10 Step 3: Verify TOTP code
  const handleVerify = async () => {
    if (verifyCode.length !== 6) return;

    setError("");
    setLoading(true);

    try {
      const { data: challengeData, error: challengeError } = await supabase.auth.mfa.challenge({
        factorId,
      });

      if (challengeError) {
        setError(challengeError.message);
        setLoading(false);
        return;
      }

      const { error: verifyError } = await supabase.auth.mfa.verify({
        factorId,
        challengeId: challengeData.id,
        code: verifyCode,
      });

      if (verifyError) {
        setError("Código inválido. Verifique e tente novamente.");
        setVerifyCode("");
        setLoading(false);
        return;
      }

      // AC10 Step 4: Generate recovery codes via backend
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        try {
          const res = await fetch("/api/mfa?endpoint=recovery-codes", {
            method: "POST",
            headers: { Authorization: `Bearer ${session.access_token}` },
          });
          if (res.ok) {
            const codesData = await res.json();
            setRecoveryCodes(codesData.codes || []);
          }
        } catch {
          // Recovery codes generation failed — continue anyway
        }
      }

      setStep("recovery");
    } catch {
      setError("Erro na verificação. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  // Auto-submit when 6 digits entered
  useEffect(() => {
    if (verifyCode.length === 6 && step === "verify") {
      handleVerify();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [verifyCode]);

  const handleCopyRecoveryCodes = () => {
    navigator.clipboard.writeText(recoveryCodes.join("\n"));
  };

  return (
    <div className="max-w-md mx-auto">
      {/* Progress indicator */}
      <div className="flex items-center gap-2 mb-6">
        {(["qr", "verify", "recovery", "confirm"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === s
                  ? "bg-[var(--brand-navy)] text-white"
                  : (["qr", "verify", "recovery", "confirm"] as Step[]).indexOf(step) > i
                  ? "bg-[var(--success)] text-white"
                  : "bg-[var(--surface-1)] text-[var(--ink-muted)]"
              }`}
            >
              {i + 1}
            </div>
            {i < 3 && <div className="w-8 h-px bg-[var(--border)]" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-[var(--error-subtle)] border border-[var(--error)]/20 rounded-input text-sm text-[var(--error)]" role="alert">
          {error}
        </div>
      )}

      {/* Step 1-2: QR Code */}
      {step === "qr" && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-[var(--ink)]">
            Escaneie o QR Code
          </h3>
          <p className="text-sm text-[var(--ink-secondary)]">
            Abra seu app autenticador (Google Authenticator, Authy, 1Password ou Microsoft Authenticator)
            e escaneie o código abaixo.
          </p>

          {qrCode ? (
            <div className="flex justify-center p-4 bg-white rounded-lg">
              {/* AC11: QR code with issuer SmartLic + email label */}
              <img src={qrCode} alt="QR Code para configuração TOTP" className="w-48 h-48" />
            </div>
          ) : (
            <div className="flex justify-center p-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)]" />
            </div>
          )}

          {/* AC10 Step 2: Manual key */}
          <div className="space-y-2">
            <button
              onClick={() => setShowSecret(!showSecret)}
              className="text-sm text-[var(--brand-blue)] hover:underline"
            >
              {showSecret ? "Ocultar chave manual" : "Não consegue escanear? Use a chave manual"}
            </button>
            {showSecret && (
              <div className="p-3 bg-[var(--surface-1)] rounded-input font-mono text-sm break-all select-all">
                {secret}
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="flex-1 py-2 border border-[var(--border)] rounded-button text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
            >
              Cancelar
            </button>
            <button
              onClick={() => setStep("verify")}
              disabled={!qrCode}
              className="flex-1 py-2 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] disabled:opacity-50"
            >
              Próximo
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Verify code */}
      {step === "verify" && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-[var(--ink)]">
            Verificar código
          </h3>
          <p className="text-sm text-[var(--ink-secondary)]">
            Digite o código de 6 dígitos exibido no seu app autenticador.
          </p>

          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            autoFocus
            value={verifyCode}
            onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
            className="w-full px-4 py-4 text-center text-2xl font-mono tracking-[0.5em] rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
            placeholder="000000"
          />

          <div className="flex gap-3">
            <button
              onClick={() => { setStep("qr"); setVerifyCode(""); setError(""); }}
              className="flex-1 py-2 border border-[var(--border)] rounded-button text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
            >
              Voltar
            </button>
            <button
              onClick={handleVerify}
              disabled={verifyCode.length !== 6 || loading}
              className="flex-1 py-2 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] disabled:opacity-50"
            >
              {loading ? "Verificando..." : "Verificar"}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Recovery codes */}
      {step === "recovery" && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-[var(--ink)]">
            Códigos de recuperação
          </h3>
          <div className="p-3 bg-[var(--warning-subtle)] border border-[var(--warning)]/20 rounded-input text-sm text-[var(--warning)]">
            Salve estes códigos em local seguro. Se perder acesso ao seu autenticador, use um destes códigos para entrar. Cada código só pode ser usado uma vez.
          </div>

          <div className="grid grid-cols-2 gap-2 p-4 bg-[var(--surface-1)] rounded-lg font-mono text-sm">
            {recoveryCodes.map((code, i) => (
              <div key={i} className="px-2 py-1 text-center select-all">
                {code}
              </div>
            ))}
          </div>

          <button
            onClick={handleCopyRecoveryCodes}
            className="w-full py-2 border border-[var(--border)] rounded-button text-sm text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
          >
            Copiar códigos
          </button>

          <button
            onClick={() => setStep("confirm")}
            className="w-full py-2 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)]"
          >
            Próximo
          </button>
        </div>
      )}

      {/* Step 5: Confirm */}
      {step === "confirm" && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-[var(--ink)]">
            Confirmar configuração
          </h3>
          <p className="text-sm text-[var(--ink-secondary)]">
            Confirme que salvou seus códigos de recuperação antes de finalizar.
          </p>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={codesConfirmed}
              onChange={(e) => setCodesConfirmed(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-[var(--border)] text-[var(--brand-blue)] focus:ring-[var(--brand-blue)]"
            />
            <span className="text-sm text-[var(--ink)]">
              Salvei meus códigos de recuperação em local seguro
            </span>
          </label>

          <div className="flex gap-3">
            <button
              onClick={() => setStep("recovery")}
              className="flex-1 py-2 border border-[var(--border)] rounded-button text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
            >
              Voltar
            </button>
            <button
              onClick={onComplete}
              disabled={!codesConfirmed}
              className="flex-1 py-2 bg-[var(--success)] text-white rounded-button font-semibold hover:opacity-90 disabled:opacity-50"
            >
              Concluir
            </button>
          </div>
        </div>
      )}

      {/* AC12: Supported apps note */}
      {(step === "qr" || step === "verify") && (
        <p className="mt-4 text-xs text-center text-[var(--ink-muted)]">
          Compatível com Google Authenticator, Authy, 1Password e Microsoft Authenticator
        </p>
      )}
    </div>
  );
}
