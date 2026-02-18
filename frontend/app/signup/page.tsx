"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics, getStoredUTMParams } from "../../hooks/useAnalytics";
import { getUserFriendlyError } from "../../lib/error-messages";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import InstitutionalSidebar from "../components/InstitutionalSidebar";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech";

// Helper constants and functions removed - no longer needed for simplified form

export default function SignupPage() {
  const { signUpWithEmail, signInWithGoogle } = useAuth();
  const { trackEvent } = useAnalytics();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [fullName, setFullName] = useState("");
  const [emailTouched, setEmailTouched] = useState(false);
  const [formTouched, setFormTouched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // GTM-FIX-009: Confirmation screen state
  const [countdown, setCountdown] = useState(60);
  const [isResending, setIsResending] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);

  // GTM-FIX-009 AC2: Countdown timer (starts at 60s on success)
  useEffect(() => {
    if (!success || countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [success, countdown]);

  // GTM-FIX-009 AC7/AC9: Poll for confirmation every 5s
  useEffect(() => {
    if (!success || isConfirmed) return;
    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `/api/auth/status?email=${encodeURIComponent(email)}`
        );
        const data = await response.json();
        if (data.confirmed) {
          setIsConfirmed(true);
          clearInterval(interval);
          toast.success("Email confirmado! Redirecionando...");
          setTimeout(() => router.push("/onboarding"), 1500);
        }
      } catch {
        // Silently retry on next interval
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [success, isConfirmed, email, router]);

  // GTM-FIX-009 AC3/AC5: Resend handler
  const handleResend = async () => {
    if (countdown > 0 || isResending) return;
    setIsResending(true);
    try {
      const response = await fetch("/api/auth/resend-confirmation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (response.ok) {
        toast.success("Email reenviado! Verifique sua caixa de entrada.");
        setCountdown(60); // AC5: Reset countdown
      } else {
        const data = await response.json();
        toast.error(data.detail || data.message || "Erro ao reenviar.");
      }
    } catch {
      toast.error("Erro ao reenviar email. Tente novamente.");
    } finally {
      setIsResending(false);
    }
  };


  // STORY-226 AC17: Enforce password policy (8+ chars, 1 uppercase, 1 digit)
  const passwordMeetsPolicy =
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /\d/.test(password);

  // GTM-FIX-037 AC1: Email validation
  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const showEmailError = emailTouched && email.trim() !== "" && !isEmailValid;

  const isFormValid =
    fullName.trim() !== "" &&
    email.trim() !== "" &&
    isEmailValid &&
    passwordMeetsPolicy;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!passwordMeetsPolicy) {
      setError("A senha deve ter pelo menos 8 caracteres, 1 letra maiúscula e 1 número");
      return;
    }

    // AC13: Track signup attempt (after validation, before async work)
    trackEvent('signup_attempted', { method: "email" });

    setLoading(true);

    try {
      await signUpWithEmail(email, password, fullName);
      setSuccess(true);
      // AC14 + AC26: Track signup_completed with UTM params
      trackEvent('signup_completed', {
        method: "email",
        ...getStoredUTMParams(),
      });
      // AC9: identifyUser skipped here — user must confirm email first.
      // Identity will be linked on first login (AC7).
    } catch (err: unknown) {
      setError(getUserFriendlyError(err));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg text-center">
          {/* AC10: Confirmed transition */}
          {isConfirmed ? (
            <>
              <div className="text-4xl mb-4" data-testid="confirmed-icon">&#10003;</div>
              <h2 className="text-xl font-semibold text-green-600 mb-2">
                Email confirmado!
              </h2>
              <p className="text-[var(--ink-secondary)]">Redirecionando...</p>
            </>
          ) : (
            <>
              {/* AC1: Mail icon */}
              <div className="text-4xl mb-4" data-testid="mail-icon">&#9993;</div>

              <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">
                Confirme seu email
              </h2>

              <p className="text-[var(--ink-secondary)] mb-4">
                Enviamos um link de confirmação para:
                <br />
                <strong>{email}</strong>
              </p>

              {/* AC7: Polling indicator */}
              <p className="text-sm text-[var(--brand-blue)] mb-4" data-testid="polling-indicator">
                Aguardando confirmação...
              </p>

              {/* AC1/AC2: Resend button with countdown */}
              <button
                onClick={handleResend}
                disabled={countdown > 0 || isResending}
                data-testid="resend-button"
                className="w-full py-3 bg-[var(--brand-blue)] text-white rounded-button
                           font-semibold disabled:bg-gray-300 disabled:text-gray-500
                           disabled:cursor-not-allowed hover:opacity-90 transition-colors"
              >
                {isResending
                  ? "Reenviando..."
                  : countdown > 0
                    ? `Reenviar em ${countdown}s`
                    : "Reenviar email"}
              </button>

              {/* AC11: Spam helper section */}
              <div className="mt-6 p-4 bg-[var(--surface-1)] rounded-input text-left">
                <h3 className="font-semibold text-sm mb-2 text-[var(--ink)]">
                  Não recebeu o email?
                </h3>
                <ul className="text-sm space-y-1 text-[var(--ink-secondary)]">
                  <li>• Verifique sua caixa de spam/lixo eletrônico</li>
                  <li>• Aguarde até 5 minutos</li>
                  <li>• Confirme se o email está correto</li>
                </ul>
                {/* AC12: Change email link */}
                <button
                  onClick={() => {
                    setSuccess(false);
                    setCountdown(60);
                  }}
                  data-testid="change-email-link"
                  className="text-[var(--brand-blue)] text-sm mt-2 underline hover:opacity-80"
                >
                  Alterar email
                </button>
              </div>

              <Link
                href="/login"
                className="mt-4 inline-block text-sm text-[var(--ink-muted)] hover:underline"
              >
                Ir para login
              </Link>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Left: Institutional Sidebar */}
      <InstitutionalSidebar variant="signup" className="w-full md:w-1/2" />

      {/* Right: Signup Form */}
      <div className="w-full md:w-1/2 flex items-center justify-center bg-[var(--canvas)] p-4 py-8">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg">
          <h1 className="text-2xl font-display font-bold text-center text-[var(--ink)] mb-2">
            Criar conta
          </h1>
          <p className="text-center text-[var(--ink-secondary)] mb-4">
            Experimente o SmartLic completo por 7 dias
          </p>
          <div className="mb-6 p-3 bg-[var(--surface-1)] rounded-input text-xs text-[var(--ink-secondary)] space-y-1">
            <p className="font-medium text-[var(--ink)]">Teste grátis por 7 dias:</p>
            <ul className="space-y-0.5">
              <li>&#10003; 3 análises completas</li>
              <li>&#10003; Acesso a todos os recursos</li>
              <li>&#10003; Sem cartão de crédito</li>
            </ul>
          </div>

        {error && (
          <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">
            {error}
          </div>
        )}

        {/* Google OAuth */}
        <button
          onClick={() => signInWithGoogle()}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 mb-4
                     border border-[var(--border)] rounded-button bg-[var(--surface-0)]
                     text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
        >
          <svg
              role="img"
              aria-label="Ícone" width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Cadastrar com Google
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-xs text-[var(--ink-muted)]">OU</span>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div>
            <label htmlFor="fullName" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Nome completo
            </label>
            <input
              id="fullName"
              type="text"
              required
              value={fullName}
              onChange={(e) => { setFullName(e.target.value); setFormTouched(true); }}
              className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]"
              placeholder="Seu nome"
            />
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => { setEmail(e.target.value); setFormTouched(true); }}
              onBlur={() => setEmailTouched(true)}
              className={`w-full px-4 py-3 rounded-input border
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]
                         ${showEmailError ? 'border-[var(--error)]' : 'border-[var(--border)]'}`}
              placeholder="seu@email.com"
            />
            {showEmailError && (
              <p className="mt-1 text-xs text-[var(--error)]" data-testid="email-error">
                Digite um email válido
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Senha
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => { setPassword(e.target.value); setFormTouched(true); }}
                className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)]
                           bg-[var(--surface-0)] text-[var(--ink)]
                           focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                           focus:ring-[var(--brand-blue-subtle)]"
                placeholder="Min. 8 caracteres, 1 maiúscula, 1 número"
                minLength={8}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                           hover:text-[var(--ink)] transition-colors"
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
              >
                {showPassword ? (
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
            {/* STORY-226 AC17: Password policy feedback */}
            {password && !passwordMeetsPolicy && (
              <ul className="mt-1 text-xs space-y-0.5">
                <li className={password.length >= 8 ? "text-green-600" : "text-[var(--error)]"}>
                  {password.length >= 8 ? "\u2713" : "\u2717"} Mínimo 8 caracteres
                </li>
                <li className={/[A-Z]/.test(password) ? "text-green-600" : "text-[var(--error)]"}>
                  {/[A-Z]/.test(password) ? "\u2713" : "\u2717"} Pelo menos 1 letra maiúscula
                </li>
                <li className={/\d/.test(password) ? "text-green-600" : "text-[var(--error)]"}>
                  {/\d/.test(password) ? "\u2713" : "\u2717"} Pelo menos 1 número
                </li>
              </ul>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !isFormValid}
            className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button
                       font-semibold hover:bg-[var(--brand-blue)] transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Criando conta..." : "Criar conta"}
          </button>
          {!isFormValid && formTouched && !loading && (
            <p className="mt-2 text-xs text-center text-[var(--ink-muted)]" data-testid="form-hint">
              Preencha todos os campos corretamente para continuar.
            </p>
          )}
        </form>

        <p className="mt-6 text-center text-sm text-[var(--ink-secondary)]">
          Já tem conta?{" "}
          <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
            Fazer login
          </Link>
        </p>
        </div>
      </div>
    </div>
  );
}
