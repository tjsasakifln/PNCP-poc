"use client";

import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics, getAcquisitionProperties } from "../../hooks/useAnalytics";
import { translateAuthError } from "../../lib/error-messages";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";
import InstitutionalSidebar from "../components/InstitutionalSidebar";
import { buttonVariants } from "../../components/ui/button";
import { safeSetItem, safeGetItem } from "../../lib/storage";
import { signupSchema, type SignupFormData } from "../../lib/schemas/forms";

import { SignupSuccess } from "./components/SignupSuccess";
import { SignupOAuth } from "./components/SignupOAuth";
import { SignupForm } from "./components/SignupForm";
import CardCollect from "./components/CardCollect";
import { computeRolloutBranch, readRolloutPctFromEnv, type RolloutBranch } from "./hooks/useRolloutBranch";

// STORY-323: Partner name type
type PartnerInfo = { name: string; slug: string } | null;

export default function SignupPage() {
  const { signUpWithEmail, signInWithGoogle, session: authSession, loading: authLoading } = useAuth();
  const { trackEvent } = useAnalytics();
  const router = useRouter();

  // react-hook-form with zod resolver (FE-028)
  const form = useForm<SignupFormData>({
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

  const fullName = form.watch("fullName");
  const password = form.watch("password");
  const confirmPassword = form.watch("confirmPassword");
  const email = form.watch("email");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // CONV-003b: 2-step state machine. Step 1 = email/password form.
  // Step 2 = Stripe PaymentElement (only when rollout branch == "card").
  const [step, setStep] = useState<1 | 2>(1);
  const [rolloutBranch, setRolloutBranch] = useState<RolloutBranch | null>(null);
  const [pendingFormData, setPendingFormData] = useState<SignupFormData | null>(null);

  // ISSUE-068: Redirect already-authenticated users (consistent with /login)
  useEffect(() => {
    if (!authLoading && authSession) {
      toast.info("Você já está autenticado!", { id: "already-auth" });
      setTimeout(() => { router.push("/buscar"); }, 1500);
    }
  }, [authLoading, authSession, router]);

  // STORY-323 AC16: Partner tracking
  const [partnerInfo, setPartnerInfo] = useState<PartnerInfo>(null);

  // GTM-FIX-009: Confirmation screen state
  const [countdown, setCountdown] = useState(60);
  const [isResending, setIsResending] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);

  const passwordMeetsPolicy =
    password.length >= 8 && /[A-Z]/.test(password) && /\d/.test(password);
  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isFormValid =
    fullName.trim() !== "" &&
    email.trim() !== "" &&
    isEmailValid &&
    passwordMeetsPolicy &&
    confirmPassword === password &&
    confirmPassword !== "";

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

  // CONV-003b: legacy path (Supabase direct). Invoked on rollout=legacy or when
  // the card branch is disabled (PCT=0).
  const runLegacySignup = async (data: SignupFormData) => {
    await signUpWithEmail(data.email, data.password, data.fullName);
    setSuccess(true);
    trackEvent('signup_completed', {
      method: "email",
      rollout_branch: "legacy",
      ...getAcquisitionProperties(),
    });
  };

  // CONV-003b: card path (backend /v1/auth/signup). Creates Stripe Customer +
  // Subscription with 14-day trial. Called from onCardReady in step 2.
  const runCardSignup = async (data: SignupFormData, paymentMethodId: string) => {
    const res = await fetch("/api/auth/signup-trial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: data.email,
        password: data.password,
        full_name: data.fullName,
        stripe_payment_method_id: paymentMethodId,
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail ?? `signup-trial falhou (${res.status})`);
    }
    setSuccess(true);
    trackEvent('signup_completed', {
      method: "email",
      rollout_branch: "card",
      ...getAcquisitionProperties(),
    });
    // CONV-003c AC4: capture instrumented funnel event. CNAE is collected
    // later in onboarding, not at signup — pass only the fields available
    // at this point so downstream Mixpanel breakdowns stay honest.
    trackEvent('trial_card_captured', {
      method: "email",
    });
  };

  const onSubmit = async (data: SignupFormData) => {
    setError(null);

    // AC13: Track signup attempt (after validation, before async work)
    trackEvent('signup_attempted', { method: "email" });

    // CONV-003b: compute rollout branch BEFORE the expensive paths.
    // SHA-256 is fast (<1ms) and determines whether to show step 2.
    const pct = readRolloutPctFromEnv();
    const branch = await computeRolloutBranch(data.email, pct);
    setRolloutBranch(branch);

    if (branch === "card") {
      // Defer the actual network call until the card is collected in step 2.
      setPendingFormData(data);
      setStep(2);
      return;
    }

    // Legacy path — keep original UX untouched.
    setLoading(true);
    try {
      await runLegacySignup(data);
    } catch (err: unknown) {
      const rawMessage = err instanceof Error ? err.message : "Erro ao criar conta";
      setError(translateAuthError(rawMessage));
    } finally {
      setLoading(false);
    }
  };

  const onCardReady = async (paymentMethodId: string) => {
    if (!pendingFormData) return;
    setError(null);
    setLoading(true);
    try {
      await runCardSignup(pendingFormData, paymentMethodId);
    } catch (err: unknown) {
      const rawMessage = err instanceof Error ? err.message : "Erro ao criar conta";
      setError(translateAuthError(rawMessage));
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  const onBackToStep1 = () => {
    setStep(1);
    setPendingFormData(null);
    setError(null);
  };

  // SEO-PLAYBOOK Frente 2: persist ?ref=CODE for referral program
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const refCode = params.get("ref");
    if (refCode && /^[A-Z0-9]{8}$/i.test(refCode)) {
      safeSetItem("referral_code", refCode.toUpperCase());
    }
  }, []);

  // SEO-PLAYBOOK Frente 2: once the user is authenticated AND a referral_code
  // is in localStorage, call /api/referral/redeem to register the conversion.
  // Never blocks signup flow — failures are silently logged.
  useEffect(() => {
    if (!authSession?.access_token || !authSession.user?.id) return;
    const code = safeGetItem("referral_code");
    if (!code) return;

    (async () => {
      try {
        const res = await fetch("/api/referral/redeem", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authSession.access_token}`,
          },
          body: JSON.stringify({
            code,
            referred_user_id: authSession.user.id,
          }),
        });
        if (!res.ok) {
          console.warn("[signup] referral redeem non-ok", res.status);
        } else {
          // Playbook §7.4 viral loop instrumentation — confirms the
          // referee actually completed signup attributed to a code.
          trackEvent("referral_signed_up", {
            code,
            referred_user_id: authSession.user.id,
          });
        }
      } catch (e) {
        console.warn("[signup] referral redeem failed", e);
      } finally {
        try {
          localStorage.removeItem("referral_code");
        } catch {
          /* ignore */
        }
      }
    })();
  }, [authSession]);

  // STORY-323 AC16: Detect ?partner=slug and persist to cookie/localStorage
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const partnerSlug = params.get("partner");
    if (partnerSlug) {
      safeSetItem("smartlic_partner", partnerSlug);
      document.cookie = `smartlic_partner=${partnerSlug};path=/;max-age=${7 * 24 * 60 * 60}`;
      setPartnerInfo({ name: partnerSlug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()), slug: partnerSlug });
    } else {
      const stored = safeGetItem("smartlic_partner");
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
      <SignupSuccess
        email={email}
        isConfirmed={isConfirmed}
        countdown={countdown}
        isResending={isResending}
        onResend={handleResend}
        onChangeEmail={() => {
          setSuccess(false);
          setCountdown(60);
        }}
      />
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

          {/* Already-authenticated fallback: visible CTA (complements silent redirect in useEffect) */}
          {!authLoading && authSession && (
            <div className="mb-4 p-3 bg-brand-blue-subtle rounded-input text-center" data-testid="already-auth-banner">
              <p className="text-sm text-ink mb-2">Você já tem uma conta ativa.</p>
              <Link
                href="/buscar"
                className={buttonVariants({ variant: "primary", size: "sm" })}
              >
                Ir para Buscar
              </Link>
            </div>
          )}

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
          {/* Zero-churn P2 §9: Security/LGPD badges for B2G audience */}
          <div className="mb-6 flex items-center justify-center gap-3 text-[10px] text-ink-muted">
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              Dados criptografados
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              LGPD
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
              Fontes oficiais
            </span>
          </div>

          {step === 1 && (
            <>
              <SignupOAuth onGoogleSignup={() => signInWithGoogle()} />

              <SignupForm
                form={form}
                loading={loading}
                error={error}
                onSubmit={onSubmit}
                isFormValid={isFormValid}
              />
            </>
          )}

          {step === 2 && rolloutBranch === "card" && (
            <div data-testid="signup-step-2-card">
              <h2 className="text-lg font-semibold text-ink mb-2">
                Adicione um cartão para começar seu trial
              </h2>
              <p className="text-sm text-ink-secondary mb-4">
                14 dias grátis. Cobrança automática em {new Date(Date.now() + 14 * 86400e3).toLocaleDateString("pt-BR")}
              </p>
              {error && (
                <div
                  role="alert"
                  className="mb-3 p-2 text-sm text-red-700 bg-red-50 rounded"
                  data-testid="signup-step-2-error"
                >
                  {error}
                </div>
              )}
              <CardCollect
                onCardReady={onCardReady}
                onBack={onBackToStep1}
                loading={loading}
                submitLabel="Começar trial de 14 dias"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
