"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics, getStoredUTMParams } from "../../hooks/useAnalytics";
import { translateAuthError } from "../../lib/error-messages";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import InstitutionalSidebar from "../components/InstitutionalSidebar";
import { APP_NAME } from "../../lib/config";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/Input";
import { Label } from "../../components/ui/Label";
import { safeSetItem } from "../../lib/storage";
import { signupSchema, type SignupFormData, getPasswordStrength } from "../../lib/schemas/forms";

// STORY-258: Email type result
type EmailCheckResult = {
  is_disposable: boolean;
  is_corporate: boolean;
} | null;

// STORY-258: Phone check result
type PhoneCheckResult = {
  already_registered: boolean;
} | null;

// STORY-323: Partner name type
type PartnerInfo = { name: string; slug: string } | null;

export default function SignupPage() {
  const { signUpWithEmail, signInWithGoogle } = useAuth();
  const { trackEvent } = useAnalytics();
  const router = useRouter();

  // react-hook-form with zod resolver (FE-028)
  const {
    register,
    handleSubmit: rhfHandleSubmit,
    watch,
    formState: { errors, isDirty },
    setError: setFieldError,
    clearErrors,
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    mode: "onBlur",
    defaultValues: {
      fullName: "",
      email: "",
      phone: "",
      password: "",
      confirmPassword: "",
    },
  });

  const fullName = watch("fullName");
  const password = watch("password");
  const confirmPassword = watch("confirmPassword");
  const email = watch("email");
  const phone = watch("phone") || "";

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // STORY-323 AC16: Partner tracking
  const [partnerInfo, setPartnerInfo] = useState<PartnerInfo>(null);

  // STORY-258: Email validation state
  const [emailCheckLoading, setEmailCheckLoading] = useState(false);
  const [emailCheckResult, setEmailCheckResult] = useState<EmailCheckResult>(null);
  const [emailCheckError, setEmailCheckError] = useState<string | null>(null);

  // STORY-258: Phone validation state
  const [phoneCheckLoading, setPhoneCheckLoading] = useState(false);
  const [phoneCheckResult, setPhoneCheckResult] = useState<PhoneCheckResult>(null);
  const [phoneCheckError, setPhoneCheckError] = useState<string | null>(null);
  const phoneDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // GTM-FIX-009: Confirmation screen state
  const [countdown, setCountdown] = useState(60);
  const [isResending, setIsResending] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);

  // Password strength
  const passwordStrength = getPasswordStrength(password);
  const passwordMeetsPolicy =
    password.length >= 8 && /[A-Z]/.test(password) && /\d/.test(password);
  const confirmPasswordMatch = confirmPassword !== "" && confirmPassword === password;

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


  // STORY-258: Email check on blur
  const handleEmailBlur = useCallback(async () => {
    const trimmed = email.trim();
    const basicValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);
    if (!basicValid || !trimmed) return;

    setEmailCheckLoading(true);
    setEmailCheckError(null);
    setEmailCheckResult(null);
    try {
      const res = await fetch(
        `/api/auth/check-email?email=${encodeURIComponent(trimmed)}`
      );
      if (res.ok) {
        const data = await res.json();
        setEmailCheckResult(data);
        if (data.is_disposable) {
          setEmailCheckError(
            "Emails descartáveis não são aceitos. Use um email corporativo ou permanente."
          );
        }
      }
    } catch {
      // silent — do not block signup on check failure
    } finally {
      setEmailCheckLoading(false);
    }
  }, [email]);

  // STORY-258: Phone check with 300ms debounce on blur
  const handlePhoneBlur = useCallback(() => {
    const trimmed = phone.trim();
    if (!trimmed) return;

    if (phoneDebounceRef.current) clearTimeout(phoneDebounceRef.current);
    phoneDebounceRef.current = setTimeout(async () => {
      setPhoneCheckLoading(true);
      setPhoneCheckError(null);
      setPhoneCheckResult(null);
      try {
        const res = await fetch(
          `/api/auth/check-phone?phone=${encodeURIComponent(trimmed)}`
        );
        if (res.ok) {
          const data = await res.json();
          setPhoneCheckResult(data);
          if (data.already_registered) {
            setPhoneCheckError(
              "Este telefone já está associado a uma conta. Tente fazer login."
            );
          }
        }
      } catch {
        // silent
      } finally {
        setPhoneCheckLoading(false);
      }
    }, 300);
  }, [phone]);

  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isFormValid =
    fullName.trim() !== "" &&
    email.trim() !== "" &&
    isEmailValid &&
    passwordMeetsPolicy &&
    confirmPassword === password &&
    confirmPassword !== "" &&
    !emailCheckError &&
    !phoneCheckError;

  const onSubmit = async (data: SignupFormData) => {
    setError(null);

    if (emailCheckError || phoneCheckError) return;

    // AC13: Track signup attempt (after validation, before async work)
    trackEvent('signup_attempted', { method: "email" });

    setLoading(true);

    try {
      await signUpWithEmail(data.email, data.password, data.fullName);
      setSuccess(true);
      // AC14 + AC26: Track signup_completed with UTM params
      trackEvent('signup_completed', {
        method: "email",
        ...getStoredUTMParams(),
      });
      // AC9: identifyUser skipped here — user must confirm email first.
      // Identity will be linked on first login (AC7).
    } catch (err: unknown) {
      const rawMessage = err instanceof Error ? err.message : "Erro ao criar conta";
      setError(translateAuthError(rawMessage));
    } finally {
      setLoading(false);
    }
  };

  // STORY-323 AC16: Detect ?partner=slug and persist to cookie/localStorage
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const partnerSlug = params.get("partner");
    if (partnerSlug) {
      // Persist partner slug for checkout flow
      safeSetItem("smartlic_partner", partnerSlug);
      document.cookie = `smartlic_partner=${partnerSlug};path=/;max-age=${7 * 24 * 60 * 60}`;
      // Fetch partner name for badge display
      setPartnerInfo({ name: partnerSlug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()), slug: partnerSlug });
    } else {
      // Check if already stored from previous visit
      const stored = localStorage.getItem("smartlic_partner");
      if (stored) {
        setPartnerInfo({ name: stored.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()), slug: stored });
      }
    }
  }, []);

  // UX-359 AC3: Auto-scroll to form via URL param
  const formRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('scroll') === 'form' || params.get('source')?.includes('cta')) {
      setTimeout(() => {
        formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    }
  }, []);

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-canvas">
        <div className="w-full max-w-md p-8 bg-surface-0 rounded-card shadow-lg text-center">
          {/* AC10: Confirmed transition */}
          {isConfirmed ? (
            <>
              <div className="text-4xl mb-4" data-testid="confirmed-icon">&#10003;</div>
              <h2 className="text-xl font-semibold text-green-600 mb-2">
                Email confirmado!
              </h2>
              <p className="text-ink-secondary">Redirecionando...</p>
            </>
          ) : (
            <>
              {/* AC1: Mail icon */}
              <div className="text-4xl mb-4" data-testid="mail-icon">&#9993;</div>

              <h2 className="text-xl font-semibold text-ink mb-2">
                Confirme seu email
              </h2>

              <p className="text-ink-secondary mb-4">
                Enviamos um link de confirmação para:
                <br />
                <strong>{email}</strong>
              </p>

              {/* AC7: Polling indicator */}
              <p className="text-sm text-brand-blue mb-4" data-testid="polling-indicator">
                Aguardando confirmação...
              </p>

              {/* AC1/AC2: Resend button with countdown */}
              <button
                onClick={handleResend}
                disabled={countdown > 0 || isResending}
                data-testid="resend-button"
                className="w-full py-3 bg-brand-blue text-white rounded-button
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
              <div className="mt-6 p-4 bg-surface-1 rounded-input text-left">
                <h3 className="font-semibold text-sm mb-2 text-ink">
                  Não recebeu o email?
                </h3>
                <ul className="text-sm space-y-1 text-ink-secondary">
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
                  className="text-brand-blue text-sm mt-2 underline hover:opacity-80"
                >
                  Alterar email
                </button>
              </div>

              <Link
                href="/login"
                className="mt-4 inline-block text-sm text-ink-muted hover:underline"
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
      <InstitutionalSidebar variant="signup" className="w-full md:w-1/2" scrollTargetId="signup-form" />

      {/* Right: Signup Form */}
      <div id="signup-form" ref={formRef} className="w-full md:w-1/2 flex items-center justify-center bg-canvas p-4 py-4 md:py-8 scroll-mt-4">
        <div className="w-full max-w-md p-8 bg-surface-0 rounded-card shadow-lg">
          <h1 className="text-2xl font-display font-bold text-center text-ink mb-2">
            Criar conta
          </h1>
          <p className="text-center text-ink-secondary mb-4">
            Veja quais licitações valem a pena para sua empresa — em 2 minutos
          </p>

          {/* STORY-323 AC16: Partner referral badge */}
          {partnerInfo && (
            <div data-testid="partner-badge" className="mb-4 p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-input text-center">
              <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                Indicado por <strong>{partnerInfo.name}</strong>
              </p>
              <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-0.5">
                Desconto exclusivo aplicado automaticamente
              </p>
            </div>
          )}
          <div className="mb-6 p-3 bg-surface-1 rounded-input text-xs text-ink-secondary space-y-1">
            <p className="font-medium text-ink">Acesso imediato:</p>
            <ul className="space-y-0.5">
              <li>&#10003; Análise de compatibilidade com seu perfil</li>
              <li>&#10003; Editais filtrados por setor e região</li>
              <li>&#10003; Sem cartão de crédito</li>
            </ul>
          </div>

        {error && (
          <div className="mb-4 p-3 bg-error-subtle text-error rounded-input text-sm">
            {error}
          </div>
        )}

        {/* Google OAuth */}
        <button
          onClick={() => signInWithGoogle()}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 mb-4
                     border rounded-button bg-surface-0
                     text-ink hover:bg-surface-1 transition-colors"
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
          <span className="text-xs text-ink-muted">OU</span>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        <form onSubmit={rhfHandleSubmit(onSubmit)} className="space-y-4">
          {/* Full Name — SAB-007 AC1 */}
          <div>
            <Label htmlFor="fullName" required>
              Nome completo
            </Label>
            <Input
              id="fullName"
              type="text"
              inputSize="lg"
              placeholder="Seu nome"
              required
              error={errors.fullName?.message}
              errorTestId="name-error"
              {...register("fullName")}
            />
          </div>

          {/* Email */}
          <div>
            <Label htmlFor="email" required>
              Email
            </Label>
            <div className="relative">
              <Input
                id="email"
                type="email"
                inputSize="lg"
                placeholder="seu@email.com"
                required
                state={errors.email || emailCheckError ? "error" : undefined}
                {...register("email", {
                  onChange: () => {
                    setEmailCheckResult(null);
                    setEmailCheckError(null);
                  },
                  onBlur: handleEmailBlur,
                })}
              />
              {/* STORY-258: Loading spinner */}
              {emailCheckLoading && (
                <div className="absolute right-3 top-3">
                  <svg className="animate-spin h-4 w-4 text-ink-muted" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                </div>
              )}
            </div>
            {/* SAB-007 AC2: Format error */}
            {errors.email && !emailCheckError && (
              <p className="mt-1 text-xs text-error" data-testid="email-error">
                {errors.email.message}
              </p>
            )}
            {/* STORY-258: Disposable email error */}
            {emailCheckError && (
              <p className="mt-1 text-xs text-error" data-testid="email-disposable-error">
                {emailCheckError}
              </p>
            )}
            {/* STORY-258: Email type badge */}
            {emailCheckResult && !emailCheckError && (
              <span
                className={`inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                  emailCheckResult.is_corporate
                    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                    : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                }`}
                data-testid="email-type-badge"
              >
                <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  {emailCheckResult.is_corporate ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  )}
                </svg>
                {emailCheckResult.is_corporate ? "Email corporativo" : "Email pessoal"}
              </span>
            )}
          </div>

          {/* Phone (STORY-258) */}
          <div>
            <Label htmlFor="phone">
              Telefone <span className="text-ink-muted font-normal">(opcional)</span>
            </Label>
            <Input
              id="phone"
              type="tel"
              inputSize="lg"
              placeholder="+55 11 91234-5678"
              error={phoneCheckError || undefined}
              errorTestId="phone-error"
              {...register("phone", {
                onChange: () => {
                  setPhoneCheckResult(null);
                  setPhoneCheckError(null);
                },
                onBlur: handlePhoneBlur,
              })}
            />
            {phoneCheckLoading && (
              <p className="mt-1 text-xs text-ink-muted">Verificando...</p>
            )}
            {phoneCheckResult && !phoneCheckError && (
              <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400" data-testid="phone-ok">
                Telefone disponível
              </p>
            )}
          </div>

          {/* Password — SAB-007 AC3 */}
          <div>
            <Label htmlFor="password" required>
              Senha
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                inputSize="lg"
                className="pr-12"
                placeholder="Min. 8 caracteres, 1 maiúscula, 1 número"
                required
                minLength={8}
                error={errors.password?.message}
                {...register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 p-1 text-ink-muted
                           hover:text-ink transition-colors"
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
            {/* SAB-007 AC3: Password strength bar */}
            {password && (
              <div className="mt-2" data-testid="password-strength">
                <div className="flex gap-1 mb-1">
                  <div className={`h-1.5 flex-1 rounded-full transition-colors ${
                    passwordStrength.score >= 1 ? (
                      passwordStrength.level === "fraca" ? "bg-red-500" :
                      passwordStrength.level === "média" ? "bg-yellow-500" : "bg-green-500"
                    ) : "bg-gray-200 dark:bg-gray-700"
                  }`} />
                  <div className={`h-1.5 flex-1 rounded-full transition-colors ${
                    passwordStrength.score >= 2 ? (
                      passwordStrength.level === "média" ? "bg-yellow-500" : "bg-green-500"
                    ) : "bg-gray-200 dark:bg-gray-700"
                  }`} />
                  <div className={`h-1.5 flex-1 rounded-full transition-colors ${
                    passwordStrength.score >= 3 ? "bg-green-500" : "bg-gray-200 dark:bg-gray-700"
                  }`} />
                </div>
                <p className={`text-xs ${
                  passwordStrength.level === "fraca" ? "text-red-500" :
                  passwordStrength.level === "média" ? "text-yellow-600 dark:text-yellow-400" :
                  "text-green-600"
                }`} data-testid="password-strength-label">
                  Senha {passwordStrength.level}
                </p>
              </div>
            )}
            {/* Password policy requirements */}
            {password && !passwordMeetsPolicy && (
              <ul className="mt-1 text-xs space-y-0.5">
                <li className={password.length >= 8 ? "text-green-600" : "text-error"}>
                  {password.length >= 8 ? "\u2713" : "\u2717"} Mínimo 8 caracteres
                </li>
                <li className={/[A-Z]/.test(password) ? "text-green-600" : "text-error"}>
                  {/[A-Z]/.test(password) ? "\u2713" : "\u2717"} Pelo menos 1 letra maiúscula
                </li>
                <li className={/\d/.test(password) ? "text-green-600" : "text-error"}>
                  {/\d/.test(password) ? "\u2713" : "\u2717"} Pelo menos 1 número
                </li>
              </ul>
            )}
          </div>

          {/* Confirm Password — SAB-007 AC4 */}
          <div>
            <Label htmlFor="confirmPassword" required>
              Confirmar senha
            </Label>
            <Input
              id="confirmPassword"
              type="password"
              inputSize="lg"
              placeholder="Repita sua senha"
              required
              state={confirmPasswordMatch ? "success" : undefined}
              error={errors.confirmPassword?.message}
              errorTestId="confirm-password-error"
              {...register("confirmPassword")}
            />
            {confirmPasswordMatch && !errors.confirmPassword && (
              <p className="mt-1 text-xs text-green-600" data-testid="confirm-password-match">
                &#10003; Senhas coincidem
              </p>
            )}
          </div>

          {/* SAB-007 AC5/AC6/AC7: Submit button with tooltip, transition, spinner */}
          <div className="relative group">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className={`w-full transition-all duration-300 ease-in-out font-semibold
                         ${isFormValid
                           ? "shadow-md hover:shadow-lg"
                           : "!bg-gray-300 dark:!bg-gray-700 !text-gray-500 dark:!text-gray-400 cursor-not-allowed"
                         }`}
              disabled={loading || !isFormValid}
              loading={loading}
            >
              {loading ? "Criando conta..." : "Criar conta"}
            </Button>
            {/* AC5: Tooltip when disabled */}
            {!isFormValid && !loading && (
              <div
                className="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1.5
                           bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900
                           text-xs rounded-md whitespace-nowrap
                           opacity-0 group-hover:opacity-100 transition-opacity
                           pointer-events-none z-10"
                role="tooltip"
                data-testid="submit-tooltip"
              >
                Preencha todos os campos
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-100" />
              </div>
            )}
          </div>
          {!isFormValid && isDirty && !loading && (
            <p className="mt-2 text-xs text-center text-ink-muted" data-testid="form-hint">
              Preencha todos os campos corretamente para continuar.
            </p>
          )}
        </form>

        <p className="mt-6 text-center text-sm text-ink-secondary">
          Já tem conta?{" "}
          <Link href="/login" className="text-brand-blue hover:underline">
            Fazer login
          </Link>
        </p>
        </div>
      </div>
    </div>
  );
}
