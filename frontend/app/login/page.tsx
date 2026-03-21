"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics } from "../../hooks/useAnalytics";
import Link from "next/link";
import InstitutionalSidebar from "../components/InstitutionalSidebar";
import { toast } from "sonner";
import { translateAuthError } from "../../lib/error-messages";
import { Button } from "../../components/ui/button";
import dynamic from "next/dynamic";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, loginPasswordSchema, type LoginFormData } from "../../lib/schemas/forms";

import { LoginForm } from "./components/LoginForm";

// STORY-317: Lazy load to avoid supabase import at module level (breaks tests)
const TotpVerificationScreen = dynamic(
  () => import("../../components/auth/TotpVerificationScreen").then(mod => ({ default: mod.TotpVerificationScreen })),
  { ssr: false }
);

// Map error codes to user-friendly messages
const ERROR_MESSAGES: Record<string, string> = {
  auth_failed: "Falha na autenticação. Tente novamente.",
  session_expired: "Sua sessão expirou. Faça login novamente.",
  login_required: "Faça login para acessar esta página.",
  unexpected_error: "Erro inesperado. Tente novamente.",
  access_denied: "Acesso negado. Verifique suas credenciais.",
  invalid_request: "Requisição inválida. Tente novamente.",
};

const INFO_REASONS = new Set(["login_required"]);

// AC17: Categorize login errors for analytics
function categorizeLoginError(rawMessage: string): string {
  const lower = rawMessage.toLowerCase();
  if (lower.includes("invalid login credentials")) return "wrong_creds";
  if (lower.includes("error sending magic link email")) return "not_registered";
  if (lower.includes("rate limit")) return "rate_limited";
  if (lower.includes("fetch failed") || lower.includes("networkerror") || lower.includes("network error")) return "network";
  return "unknown";
}

function LoginLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
      <div className="text-center" role="status">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)] mx-auto mb-4"></div>
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginLoading />}>
      <LoginContent />
    </Suspense>
  );
}

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signInWithEmail, signInWithMagicLink, signInWithGoogle, session, loading: authLoading } = useAuth();
  const { trackEvent, identifyUser } = useAnalytics();

  const [mode, setMode] = useState<"password" | "magic">("password");
  const activeSchema = mode === "password" ? loginPasswordSchema : loginSchema;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const form = useForm<LoginFormData>({
    resolver: zodResolver(activeSchema) as any,
    mode: "onBlur",
    reValidateMode: "onChange",
    defaultValues: { email: "", password: "" },
  });

  const email = form.watch("email");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [magicSent, setMagicSent] = useState(false);
  const [showMfaVerification, setShowMfaVerification] = useState(false);

  // Check for error/reason params from OAuth callback or middleware redirect
  useEffect(() => {
    const errorParam = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");
    const reasonParam = searchParams.get("reason");

    if (errorParam) {
      const message = ERROR_MESSAGES[errorParam] || errorDescription || "Erro ao fazer login";
      setError(message);
      toast.error(message);
    } else if (reasonParam) {
      const message = ERROR_MESSAGES[reasonParam];
      if (message) {
        if (INFO_REASONS.has(reasonParam)) { toast.info(message); }
        else { setError(message); toast.error(message); }
      }
    }

    if (errorParam || reasonParam) {
      const url = new URL(window.location.href);
      url.searchParams.delete("error");
      url.searchParams.delete("error_description");
      url.searchParams.delete("reason");
      window.history.replaceState({}, "", url.pathname);
    }
  }, [searchParams]);

  // Handle already authenticated users + MFA check
  useEffect(() => {
    if (!authLoading && session) {
      identifyUser(session.user.id, { plan_type: 'unknown', signup_date: session.user.created_at });

      (async () => {
        try {
          const { supabase: sb } = await import("../../lib/supabase");
          const { data: aalData } = await sb.auth.mfa.getAuthenticatorAssuranceLevel();
          if (aalData && aalData.nextLevel === "aal2" && aalData.currentLevel === "aal1") {
            setShowMfaVerification(true);
            return;
          }
        } catch { /* MFA check failed */ }

        const redirectTo = searchParams.get("redirect") || "/buscar";
        toast.info("Você já está autenticado!");
        setTimeout(() => { router.push(redirectTo); }, 1500);
      })();
    }
  }, [authLoading, session, router, searchParams]);

  const onFormSubmit = async (data: LoginFormData) => {
    setError(null);
    setSuccess(false);
    trackEvent('login_attempted', { method: mode === "magic" ? "magic_link" : "email" });
    setLoading(true);

    try {
      if (mode === "magic") {
        await signInWithMagicLink(data.email);
        setMagicSent(true);
        trackEvent('login_completed', { method: "magic_link" });
        toast.success("Link mágico enviado! Verifique seu email.");
      } else {
        await signInWithEmail(data.email, data.password);
        try {
          const { supabase: sb } = await import("../../lib/supabase");
          const { data: aalData } = await sb.auth.mfa.getAuthenticatorAssuranceLevel();
          if (aalData && aalData.nextLevel === "aal2" && aalData.currentLevel === "aal1") {
            trackEvent('login_completed', { method: "email", mfa_required: true });
            setShowMfaVerification(true);
            setLoading(false);
            return;
          }
        } catch { /* MFA check failed */ }
        setSuccess(true);
        trackEvent('login_completed', { method: "email" });
        toast.success("Login realizado com sucesso!");
      }
    } catch (err: unknown) {
      const rawMessage = err instanceof Error ? err.message : "Erro ao fazer login";
      const translatedMessage = translateAuthError(rawMessage);
      trackEvent('login_failed', { method: mode === "magic" ? "magic_link" : "email", error_category: categorizeLoginError(rawMessage) });
      setError(translatedMessage);
      toast.error(translatedMessage);
    } finally {
      setLoading(false);
    }
  };

  // UX-359 AC3/AC5: Auto-scroll to form via URL param
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('scroll') === 'form' || params.get('source')?.includes('cta')) {
      setTimeout(() => {
        document.getElementById('login-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    }
  }, []);

  // STORY-317 AC13: Show MFA verification screen
  if (showMfaVerification) {
    const redirectTo = searchParams.get("redirect") || "/buscar";
    return (
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]"><div role="status" className="w-8 h-8 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" /></div>}>
        <TotpVerificationScreen
          onVerified={() => { toast.success("Verificação MFA bem-sucedida!"); router.push(redirectTo); }}
          onCancel={async () => { const { supabase: sb } = await import("../../lib/supabase"); await sb.auth.signOut(); setShowMfaVerification(false); }}
          redirectTo={redirectTo}
        />
      </Suspense>
    );
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center" role="status">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)] mx-auto mb-4"></div>
          <p className="text-[var(--ink-secondary)]">Verificando autenticação...</p>
        </div>
      </div>
    );
  }

  if (session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)] p-4">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg text-center">
          <div className="text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-[var(--ink)] mb-2">Você já está logado</h2>
          <p className="text-[var(--ink-secondary)] mb-6">Sua sessão está ativa como <strong>{session.user.email}</strong></p>
          <Button variant="primary" size="lg" className="w-full mb-3" onClick={() => router.push("/buscar")}>Ir para o painel</Button>
          <Link href="/conta" className="block w-full py-2 text-sm text-[var(--ink-muted)] hover:text-[var(--brand-blue)] transition-colors">Gerenciar conta</Link>
        </div>
      </div>
    );
  }

  if (magicSent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg text-center">
          <div className="text-4xl mb-4">&#9993;</div>
          <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">Verifique seu email</h2>
          <p className="text-[var(--ink-secondary)]">Enviamos um link de acesso para <strong>{email}</strong>. Clique no link para entrar.</p>
          <p className="text-xs text-[var(--ink-muted)] mt-3">O link expira em 1 hora. Verifique também a pasta de spam.</p>
          <div className="mt-6 space-y-3">
            <button onClick={() => setMagicSent(false)} className="w-full py-2 text-sm text-[var(--brand-blue)] hover:underline">Tentar novamente</button>
            <Link href="/planos" className="block w-full py-2 text-sm text-[var(--ink-muted)] hover:text-[var(--ink)] transition-colors">← Voltar</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <InstitutionalSidebar variant="login" className="w-full md:w-1/2" scrollTargetId="login-form" />

      <div id="login-form" className="w-full md:w-1/2 flex items-center justify-center bg-[var(--canvas)] p-4 py-4 md:py-8 scroll-mt-4">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg">
          <h1 className="text-2xl font-display font-bold text-center text-[var(--ink)] mb-2">Acesse suas análises</h1>
          <p className="text-center text-[var(--ink-secondary)] mb-8">Entre para acessar suas análises de viabilidade</p>

          <LoginForm
            form={form}
            mode={mode}
            onModeChange={setMode}
            loading={loading}
            error={error}
            success={success}
            onSubmit={onFormSubmit}
            onGoogleSignIn={() => signInWithGoogle()}
          />
        </div>
      </div>
    </div>
  );
}
