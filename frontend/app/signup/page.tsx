"use client";

import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics, getStoredUTMParams } from "../../hooks/useAnalytics";
import { translateAuthError } from "../../lib/error-messages";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import InstitutionalSidebar from "../components/InstitutionalSidebar";
import { safeSetItem, safeGetItem } from "../../lib/storage";
import { signupSchema, type SignupFormData } from "../../lib/schemas/forms";

import { SignupSuccess } from "./components/SignupSuccess";
import { SignupOAuth } from "./components/SignupOAuth";
import { SignupForm } from "./components/SignupForm";

// STORY-323: Partner name type
type PartnerInfo = { name: string; slug: string } | null;

export default function SignupPage() {
  const { signUpWithEmail, signInWithGoogle } = useAuth();
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

  const onSubmit = async (data: SignupFormData) => {
    setError(null);

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

          <SignupOAuth onGoogleSignup={() => signInWithGoogle()} />

          <SignupForm
            form={form}
            loading={loading}
            error={error}
            onSubmit={onSubmit}
            isFormValid={isFormValid}
          />
        </div>
      </div>
    </div>
  );
}
