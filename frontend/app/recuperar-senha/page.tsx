"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../components/AuthProvider";
import { supabase } from "../../lib/supabase";
import Link from "next/link";
import InstitutionalSidebar from "../components/InstitutionalSidebar";

export default function RecuperarSenhaPage() {
  const router = useRouter();
  const { session, loading: authLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  // AC9: Redirect authenticated users to /buscar
  useEffect(() => {
    if (!authLoading && session) {
      router.push("/buscar");
    }
  }, [authLoading, session, router]);

  // Cooldown timer (60s rate limit UX)
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      setLoading(true);

      try {
        const canonicalUrl =
          process.env.NEXT_PUBLIC_CANONICAL_URL || window.location.origin;

        // AC5: Call Supabase resetPasswordForEmail
        const { error: resetError } =
          await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${canonicalUrl}/redefinir-senha`,
          });

        if (resetError) throw resetError;

        // AC6: Show success state
        setSent(true);
        setCooldown(60);
      } catch (err: unknown) {
        // AC7: Show user-friendly error
        const errObj = err as { message?: string };
        const message = errObj?.message || "Erro ao enviar email";
        if (message.toLowerCase().includes("rate limit")) {
          setError(
            "Muitas tentativas. Aguarde alguns minutos antes de tentar novamente."
          );
        } else if (
          message.toLowerCase().includes("fetch") ||
          message.toLowerCase().includes("network")
        ) {
          setError("Erro de conexão. Verifique sua internet e tente novamente.");
        } else {
          setError(message);
        }
      } finally {
        setLoading(false);
      }
    },
    [email]
  );

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)] mx-auto mb-4"></div>
          <p className="text-[var(--ink-secondary)]">Carregando...</p>
        </div>
      </div>
    );
  }

  // AC6: Success state after email sent
  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)] p-4">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg text-center">
          <div className="text-4xl mb-4">&#9993;</div>
          <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">
            Verifique seu email
          </h2>
          <p className="text-[var(--ink-secondary)]">
            Link de recuperação enviado para <strong>{email}</strong>. Verifique
            sua caixa de entrada.
          </p>
          <p className="text-xs text-[var(--ink-muted)] mt-3">
            O link expira em 1 hora. Verifique também a pasta de spam.
          </p>
          <div className="mt-6 space-y-3">
            <button
              onClick={() => {
                setSent(false);
                setEmail("");
              }}
              disabled={cooldown > 0}
              className="w-full py-2 text-sm text-[var(--brand-blue)] hover:underline
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cooldown > 0
                ? `Reenviar em ${cooldown}s`
                : "Enviar novamente"}
            </button>
            {/* AC8: Back to login link */}
            <Link
              href="/login"
              className="block w-full py-2 text-sm text-[var(--ink-muted)] hover:text-[var(--ink)] transition-colors"
            >
              ← Voltar ao login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Left: Institutional Sidebar */}
      <InstitutionalSidebar variant="login" className="w-full md:w-1/2" />

      {/* Right: Reset Form */}
      <div className="w-full md:w-1/2 flex items-center justify-center bg-[var(--canvas)] p-4">
        <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg">
          <h1 className="text-2xl font-display font-bold text-center text-[var(--ink)] mb-2">
            Recuperar senha
          </h1>
          <p className="text-center text-[var(--ink-secondary)] mb-8">
            Informe seu email para receber o link de recuperação
          </p>

          {error && (
            <div
              className="mb-4 p-3 bg-[var(--error-subtle)] border border-[var(--error)]/20 rounded-input text-sm flex items-start gap-2"
              role="alert"
            >
              <svg
                className="w-5 h-5 text-[var(--error)] flex-shrink-0 mt-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <span className="text-[var(--error)]">{error}</span>
            </div>
          )}

          {/* AC4: Email input + submit button */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="reset-email"
                className="block text-sm font-medium text-[var(--ink-secondary)] mb-1"
              >
                Email
              </label>
              <input
                id="reset-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-input border border-[var(--border)]
                           bg-[var(--surface-0)] text-[var(--ink)]
                           focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                           focus:ring-[var(--brand-blue-subtle)]"
                placeholder="seu@email.com"
              />
            </div>

            <button
              type="submit"
              disabled={loading || cooldown > 0}
              className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button
                         font-semibold hover:bg-[var(--brand-blue)] transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Enviando...
                </>
              ) : cooldown > 0 ? (
                `Aguarde ${cooldown}s`
              ) : (
                "Enviar link de recuperação"
              )}
            </button>
          </form>

          {/* AC8: Back to login */}
          <p className="mt-6 text-center text-sm text-[var(--ink-secondary)]">
            Lembrou sua senha?{" "}
            <Link
              href="/login"
              className="text-[var(--brand-blue)] hover:underline"
            >
              Voltar ao login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
