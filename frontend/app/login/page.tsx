"use client";

import { useState } from "react";
import { useAuth } from "../components/AuthProvider";
import Link from "next/link";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "Smart PNCP";

export default function LoginPage() {
  const { signInWithEmail, signInWithMagicLink, signInWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [mode, setMode] = useState<"password" | "magic">("password");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [magicSent, setMagicSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "magic") {
        await signInWithMagicLink(email);
        setMagicSent(true);
      } else {
        await signInWithEmail(email, password);
        window.location.href = "/";
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erro ao fazer login";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

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
    <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
      <div className="w-full max-w-md p-8 bg-[var(--surface-0)] rounded-card shadow-lg">
        <h1 className="text-2xl font-display font-bold text-center text-[var(--ink)] mb-2">
          {APP_NAME}
        </h1>
        <p className="text-center text-[var(--ink-secondary)] mb-8">
          Entre para acessar suas buscas
        </p>

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
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Entrar com Google
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-xs text-[var(--ink-muted)]">OU</span>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        {/* Mode toggle */}
        <div className="flex mb-4 bg-[var(--surface-1)] rounded-button p-1">
          <button
            onClick={() => setMode("password")}
            className={`flex-1 py-2 text-sm rounded-button transition-colors ${
              mode === "password"
                ? "bg-[var(--surface-0)] text-[var(--ink)] shadow-sm"
                : "text-[var(--ink-muted)]"
            }`}
          >
            Email + Senha
          </button>
          <button
            onClick={() => setMode("magic")}
            className={`flex-1 py-2 text-sm rounded-button transition-colors ${
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
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[var(--brand-navy)] text-white rounded-button
                       font-semibold hover:bg-[var(--brand-blue)] transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Entrando..." : mode === "magic" ? "Enviar link" : "Entrar"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-[var(--ink-secondary)]">
          Nao tem conta?{" "}
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
  );
}
