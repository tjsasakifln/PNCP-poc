"use client";

import { useState, useEffect, useCallback } from "react";
import { supabase } from "../../lib/supabase";

interface TotpVerificationScreenProps {
  onVerified: () => void;
  onCancel?: () => void;
  redirectTo?: string;
}

export function TotpVerificationScreen({ onVerified, onCancel, redirectTo }: TotpVerificationScreenProps) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryCode, setRecoveryCode] = useState("");
  const [attemptsLeft, setAttemptsLeft] = useState<number | null>(null);

  // AC13: Verify TOTP code
  const handleVerify = useCallback(async () => {
    if (code.length !== 6) return;

    setError("");
    setLoading(true);

    try {
      const { data: factors } = await supabase.auth.mfa.listFactors();
      const totpFactor = factors?.totp?.[0];

      if (!totpFactor) {
        setError("Nenhum fator TOTP encontrado.");
        setLoading(false);
        return;
      }

      const { error: verifyError } = await supabase.auth.mfa.challengeAndVerify({
        factorId: totpFactor.id,
        code,
      });

      if (verifyError) {
        // AC14: Show error with remaining attempts
        setError("Código inválido. Verifique e tente novamente.");
        setCode("");
        setLoading(false);
        return;
      }

      // AC15: Success — redirect to original destination
      onVerified();
    } catch {
      setError("Erro na verificação. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }, [code, onVerified]);

  // AC13: Auto-submit when 6 digits entered
  useEffect(() => {
    if (code.length === 6 && !loading) {
      handleVerify();
    }
  }, [code, loading, handleVerify]);

  // AC13: Verify recovery code
  const handleRecoveryVerify = async () => {
    if (!recoveryCode.trim()) return;

    setError("");
    setLoading(true);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token) {
        setError("Sessão inválida. Faça login novamente.");
        setLoading(false);
        return;
      }

      const res = await fetch("/api/mfa?endpoint=verify-recovery", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code: recoveryCode }),
      });

      const data = await res.json();

      if (res.status === 429) {
        setError(data.error || "Muitas tentativas. Tente novamente em 1 hora.");
        setLoading(false);
        return;
      }

      if (data.success) {
        onVerified();
      } else {
        setError(data.message || "Código de recuperação inválido.");
        if (data.message?.includes("Tentativas restantes:")) {
          const match = data.message.match(/Tentativas restantes: (\d+)/);
          if (match) setAttemptsLeft(parseInt(match[1], 10));
        }
        setRecoveryCode("");
      }
    } catch {
      setError("Erro ao verificar código de recuperação.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)] p-4">
      <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg">
        <div className="text-center mb-6">
          <div className="w-16 h-16 mx-auto mb-4 bg-[var(--brand-blue-subtle)] rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-[var(--brand-navy)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-[var(--ink)]">
            Verificação em dois fatores
          </h2>
          <p className="text-sm text-[var(--ink-secondary)] mt-1">
            {showRecovery
              ? "Digite um código de recuperação"
              : "Digite o código do seu app autenticador"}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-[var(--error-subtle)] border border-[var(--error)]/20 rounded-input text-sm text-[var(--error)]" role="alert">
            {error}
            {attemptsLeft !== null && attemptsLeft <= 1 && (
              <p className="mt-1 font-semibold">Sua conta será temporariamente bloqueada após a próxima tentativa.</p>
            )}
          </div>
        )}

        {!showRecovery ? (
          <>
            {/* AC13: TOTP code input */}
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              className="w-full px-4 py-4 text-center text-2xl font-mono tracking-[0.5em] rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
              placeholder="000000"
              disabled={loading}
            />

            <button
              onClick={handleVerify}
              disabled={code.length !== 6 || loading}
              className="w-full mt-4 py-3 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Verificando...
                </>
              ) : "Verificar"}
            </button>

            {/* AC13: Recovery code fallback link */}
            <button
              onClick={() => { setShowRecovery(true); setError(""); }}
              className="w-full mt-3 py-2 text-sm text-[var(--brand-blue)] hover:underline"
            >
              Usar código de recuperação
            </button>
          </>
        ) : (
          <>
            {/* Recovery code input */}
            <input
              type="text"
              autoFocus
              value={recoveryCode}
              onChange={(e) => setRecoveryCode(e.target.value)}
              className="w-full px-4 py-3 font-mono rounded-input border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue-subtle)]"
              placeholder="XXXX-XXXX"
              disabled={loading}
            />

            <button
              onClick={handleRecoveryVerify}
              disabled={!recoveryCode.trim() || loading}
              className="w-full mt-4 py-3 bg-[var(--brand-navy)] text-white rounded-button font-semibold hover:bg-[var(--brand-blue)] disabled:opacity-50"
            >
              {loading ? "Verificando..." : "Verificar código"}
            </button>

            <button
              onClick={() => { setShowRecovery(false); setError(""); setRecoveryCode(""); }}
              className="w-full mt-3 py-2 text-sm text-[var(--brand-blue)] hover:underline"
            >
              Usar código do autenticador
            </button>
          </>
        )}

        {onCancel && (
          <button
            onClick={onCancel}
            className="w-full mt-3 py-2 text-sm text-[var(--ink-muted)] hover:text-[var(--ink)] transition-colors"
          >
            Cancelar
          </button>
        )}
      </div>
    </div>
  );
}
