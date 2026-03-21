"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "../components/AuthProvider";
import { useAnalytics } from "../../hooks/useAnalytics";
import Link from "next/link";
import InstitutionalSidebar from "../components/InstitutionalSidebar";
import { toast } from "sonner";
import { translateAuthError } from "../../lib/error-messages";
import { APP_NAME } from "../../lib/config";
import { Button } from "../../components/ui/button";
import dynamic from "next/dynamic";

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

// Reason codes that are informational (not errors)
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

// Loading fallback for Suspense
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

// Main page wrapper with Suspense boundary (required for useSearchParams in Next.js 15+)
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

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [mode, setMode] = useState<"password" | "magic">("password");
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
      // AC3: Display context-appropriate message per reason code
      const message = ERROR_MESSAGES[reasonParam];
      if (message) {
        if (INFO_REASONS.has(reasonParam)) {
          toast.info(message);
        } else {
          setError(message);
          toast.error(message);
        }
      }
    }

    // Clear params from URL without redirect
    if (errorParam || reasonParam) {
      const url = new URL(window.location.href);
      url.searchParams.delete("error");
      url.searchParams.delete("error_description");
      url.searchParams.delete("reason");
      window.history.replaceState({}, "", url.pathname);
    }
  }, [searchParams]);

  // Handle already authenticated users
  // AC7: Link user identity after login
  // STORY-317 AC13: Check if MFA verification is needed after login
  useEffect(() => {
    if (!authLoading && session) {
      // AC7: Link user identity after login
      identifyUser(session.user.id, {
        plan_type: 'unknown',
        signup_date: session.user.created_at,
      });

      // STORY-317 AC13: Check MFA status before redirect
      (async () => {
        try {
          const { supabase: sb } = await import("../../lib/supabase");
          const { data: aalData } = await sb.auth.mfa.getAuthenticatorAssuranceLevel();
          if (aalData && aalData.nextLevel === "aal2" && aalData.currentLevel === "aal1") {
            // User has MFA enrolled but hasn't verified this session
            setShowMfaVerification(true);
            return;
          }
        } catch {
          // MFA check failed — proceed normally
        }

        const redirectTo = searchParams.get("redirect") || "/buscar";
        toast.info("Você já está autenticado!");
        setTimeout(() => {
          router.push(redirectTo);
        }, 1500);
      })();
    }
  }, [authLoading, session, router, searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    // AC15: Track login attempt before any async work
    trackEvent('login_attempted', {
      method: mode === "magic" ? "magic_link" : "email",
    });

    setLoading(true);

    try {
      if (mode === "magic") {
        await signInWithMagicLink(email);
        setMagicSent(true);
        // AC16: Track login_completed for magic link
        trackEvent('login_completed', { method: "magic_link" });
        toast.success("Link mágico enviado! Verifique seu email.");
      } else {
        await signInWithEmail(email, password);

        // STORY-317 AC13: Check if MFA is needed after password login
        try {
          const { supabase: sb } = await import("../../lib/supabase");
          const { data: aalData } = await sb.auth.mfa.getAuthenticatorAssuranceLevel();
          if (aalData && aalData.nextLevel === "aal2" && aalData.currentLevel === "aal1") {
            trackEvent('login_completed', { method: "email", mfa_required: true });
            setShowMfaVerification(true);
            setLoading(false);
            return;
          }
        } catch {
          // MFA check failed — proceed normally
        }

        setSuccess(true);
        // AC16: Track login_completed for email
        trackEvent('login_completed', { method: "email" });
        toast.success("Login realizado com sucesso!");
        // Don't redirect here - the useEffect above will handle it
        // when the session state updates
      }
    } catch (err: unknown) {
      const rawMessage = err instanceof Error ? err.message : "Erro ao fazer login";
      const translatedMessage = translateAuthError(rawMessage);
      // AC17: Track login_failed with error categorization
      trackEvent('login_failed', {
        method: mode === "magic" ? "magic_link" : "email",
        error_category: categorizeLoginError(rawMessage),
      });
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
          onVerified={() => {
            toast.success("Verificação MFA bem-sucedida!");
            router.push(redirectTo);
          }}
          onCancel={async () => {
            const { supabase: sb } = await import("../../lib/supabase");
            await sb.auth.signOut();
            setShowMfaVerification(false);
          }}
          redirectTo={redirectTo}
        />
      </Suspense>
    );
  }

  // Show loading while checking initial auth state
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

  // Show "already logged in" screen if authenticated (mobile-friendly, no scrolling)
  if (session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)] p-4">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg text-center">
          <div className="text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-[var(--ink)] mb-2">Você já está logado</h2>
          <p className="text-[var(--ink-secondary)] mb-6">
            Sua sessão está ativa como <strong>{session.user.email}</strong>
          </p>
          <Button
            variant="primary"
            size="lg"
            className="w-full mb-3"
            onClick={() => router.push("/buscar")}
          >
            Ir para o painel
          </Button>
          <Link
            href="/conta"
            className="block w-full py-2 text-sm text-[var(--ink-muted)] hover:text-[var(--brand-blue)] transition-colors"
          >
            Gerenciar conta
          </Link>
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
          <p className="text-[var(--ink-secondary)]">
            Enviamos um link de acesso para <strong>{email}</strong>.
            Clique no link para entrar.
          </p>
          <p className="text-xs text-[var(--ink-muted)] mt-3">
            O link expira em 1 hora. Verifique também a pasta de spam.
          </p>
          <div className="mt-6 space-y-3">
            <button
              onClick={() => setMagicSent(false)}
              className="w-full py-2 text-sm text-[var(--brand-blue)] hover:underline"
            >
              Tentar novamente
            </button>
            <Link
              href="/planos"
              className="block w-full py-2 text-sm text-[var(--ink-muted)] hover:text-[var(--ink)] transition-colors"
            >
              ← Voltar
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Left: Institutional Sidebar */}
      <InstitutionalSidebar variant="login" className="w-full md:w-1/2" scrollTargetId="login-form" />

      {/* Right: Login Form */}
      <div id="login-form" className="w-full md:w-1/2 flex items-center justify-center bg-[var(--canvas)] p-4 py-4 md:py-8 scroll-mt-4">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg">
          <h1 className="text-2xl font-display font-bold text-center text-[var(--ink)] mb-2">
            Acesse suas análises
          </h1>
          <p className="text-center text-[var(--ink-secondary)] mb-8">
            Entre para acessar suas análises de viabilidade
          </p>

        {success && (
          <div className="mb-4 p-3 bg-[var(--success-subtle)] border border-[var(--success)]/20 rounded-input text-sm flex items-center gap-2" role="status">
            <svg className="w-5 h-5 text-[var(--success)] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-[var(--success)]">Login realizado! Redirecionando...</span>
          </div>
        )}

        {error && (
          <div id="login-error" className="mb-4 p-3 bg-[var(--error-subtle)] border border-[var(--error)]/20 rounded-input text-sm flex items-start gap-2" role="alert">
            <svg className="w-5 h-5 text-[var(--error)] flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-[var(--error)]">{error}</span>
          </div>
        )}

        {/* SAB-012 AC10: Google OAuth as primary CTA — full-width, prominent */}
        <button
          onClick={() => signInWithGoogle()}
          disabled={loading}
          data-testid="google-oauth-button"
          className="w-full flex items-center justify-center gap-3 px-4 py-3.5 mb-6
                     border-2 border-[var(--ink)] rounded-button bg-white
                     text-[var(--ink)] hover:bg-gray-50 transition-all shadow-md
                     disabled:opacity-50 disabled:cursor-not-allowed
                     font-semibold text-base"
        >
          <svg
              role="img"
              aria-label="Ícone Google" width="20" height="20" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Entrar com Google
        </button>

        {/* SAB-012 AC11: Divider with "ou continue com email" */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-xs text-[var(--ink-muted)] whitespace-nowrap">ou continue com email</span>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        {/* SAB-012 AC12: Email/senha + Magic Link as secondary options */}
        <div className="flex mb-4 bg-[var(--surface-1)] rounded-button p-1">
          <button
            onClick={() => setMode("password")}
            className={`flex-1 py-1.5 text-xs rounded-button transition-colors ${
              mode === "password"
                ? "bg-[var(--surface-0)] text-[var(--ink)] shadow-sm"
                : "text-[var(--ink-muted)]"
            }`}
          >
            Email + Senha
          </button>
          <button
            onClick={() => setMode("magic")}
            className={`flex-1 py-1.5 text-xs rounded-button transition-colors ${
              mode === "magic"
                ? "bg-[var(--surface-0)] text-[var(--ink)] shadow-sm"
                : "text-[var(--ink-muted)]"
            }`}
          >
            Magic Link
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={!!error}
              aria-describedby={error ? "login-error" : undefined}
              className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                         bg-[var(--surface-0)] text-[var(--ink)]
                         focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                         focus:ring-[var(--brand-blue-subtle)]"
              placeholder="seu@email.com"
            />
          </div>

          {mode === "password" && (
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
                  onChange={(e) => setPassword(e.target.value)}
                  aria-invalid={!!error}
                  aria-describedby={error ? "login-error" : undefined}
                  className="w-full px-4 py-3 pr-12 rounded-input border border-[var(--border)]
                             bg-[var(--surface-0)] text-[var(--ink)]
                             focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                             focus:ring-[var(--brand-blue-subtle)]"
                  placeholder="Sua senha"
                  minLength={6}
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
              <div className="mt-1 text-right">
                <Link
                  href="/recuperar-senha"
                  className="text-sm text-[var(--brand-blue)] hover:underline"
                >
                  Esqueci minha senha
                </Link>
              </div>
            </div>
          )}

          {/* SAB-012 AC12: Secondary submit — less prominent than Google OAuth */}
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={loading}
            loading={loading}
          >
            {loading ? "Entrando..." : mode === "magic" ? "Enviar link" : "Entrar"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--ink-secondary)]">
          Não tem conta?{" "}
          <Link href="/signup" className="text-[var(--brand-blue)] hover:underline">
            Criar conta
          </Link>
        </p>

        <div className="mt-4 pt-4 border-t border-[var(--border)] text-center">
          <Link
            href="/planos"
            className="text-sm text-[var(--ink-muted)] hover:text-[var(--brand-blue)] transition-colors"
          >
            ← Ver planos disponíveis
          </Link>
        </div>
        </div>
      </div>
    </div>
  );
}
