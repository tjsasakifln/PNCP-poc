"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "../../../components/ui/button";
import type { LoginFormData } from "../../../lib/schemas/forms";

interface LoginFormProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  form: any; // UseFormReturn with dynamic schema (loginSchema | loginPasswordSchema)
  mode: "password" | "magic";
  onModeChange: (mode: "password" | "magic") => void;
  loading: boolean;
  error: string | null;
  success: boolean;
  onSubmit: (data: LoginFormData) => void;
  onGoogleSignIn: () => void;
}

export function LoginForm({
  form,
  mode,
  onModeChange,
  loading,
  error,
  success,
  onSubmit,
  onGoogleSignIn,
}: LoginFormProps) {
  const { register, handleSubmit: rhfHandleSubmit, formState: { errors: formErrors } } = form;
  const [showPassword, setShowPassword] = useState(false);

  return (
    <>
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

      {/* SAB-012 AC10: Google OAuth as primary CTA */}
      <button
        onClick={onGoogleSignIn}
        disabled={loading}
        data-testid="google-oauth-button"
        className="w-full flex items-center justify-center gap-3 px-4 py-3.5 mb-6
                   border-2 border-[var(--ink)] rounded-button bg-white
                   text-[var(--ink)] hover:bg-gray-50 transition-all shadow-md
                   disabled:opacity-50 disabled:cursor-not-allowed
                   font-semibold text-base"
      >
        <svg role="img" aria-label="Ícone Google" width="20" height="20" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Entrar com Google
      </button>

      {/* SAB-012 AC11: Divider */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-1 h-px bg-[var(--border)]" />
        <span className="text-xs text-[var(--ink-muted)] whitespace-nowrap">ou continue com email</span>
        <div className="flex-1 h-px bg-[var(--border)]" />
      </div>

      {/* DEBT-FE-020: tablist/tab roles + keyboard navigation */}
      <div
        role="tablist"
        aria-label="Método de login"
        className="flex mb-4 bg-[var(--surface-1)] rounded-button p-1"
        onKeyDown={(e) => {
          if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
            e.preventDefault();
            onModeChange(mode === "password" ? "magic" : "password");
          }
        }}
      >
        <button
          role="tab"
          aria-selected={mode === "password"}
          aria-controls="login-panel-password"
          id="login-tab-password"
          onClick={() => onModeChange("password")}
          tabIndex={mode === "password" ? 0 : -1}
          className={`flex-1 py-1.5 text-xs rounded-button transition-colors ${
            mode === "password"
              ? "bg-[var(--surface-0)] text-[var(--ink)] shadow-sm"
              : "text-[var(--ink-muted)]"
          }`}
        >
          Email + Senha
        </button>
        <button
          role="tab"
          aria-selected={mode === "magic"}
          aria-controls="login-panel-magic"
          id="login-tab-magic"
          onClick={() => onModeChange("magic")}
          tabIndex={mode === "magic" ? 0 : -1}
          className={`flex-1 py-1.5 text-xs rounded-button transition-colors ${
            mode === "magic"
              ? "bg-[var(--surface-0)] text-[var(--ink)] shadow-sm"
              : "text-[var(--ink-muted)]"
          }`}
        >
          Magic Link
        </button>
      </div>

      <form
        id={mode === "password" ? "login-panel-password" : "login-panel-magic"}
        aria-labelledby={mode === "password" ? "login-tab-password" : "login-tab-magic"}
        onSubmit={rhfHandleSubmit(onSubmit)}
        className="space-y-4"
        noValidate
      >
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-[var(--ink-secondary)] mb-1">
            Email
          </label>
          <input
            id="email"
            type="email"
            {...register("email")}
            aria-invalid={!!formErrors.email || !!error}
            aria-describedby={formErrors.email ? "email-error" : error ? "login-error" : undefined}
            className={`w-full px-4 py-3 rounded-input border bg-[var(--surface-0)] text-[var(--ink)]
                       focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                       focus:ring-[var(--brand-blue-subtle)] ${
                         formErrors.email ? "border-[var(--error)]" : "border-[var(--border)]"
                       }`}
            placeholder="seu@email.com"
          />
          {formErrors.email && (
            <p id="email-error" className="mt-1 text-xs text-[var(--error)]">
              {formErrors.email.message}
            </p>
          )}
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
                {...register("password")}
                aria-invalid={!!formErrors.password || !!error}
                aria-describedby={formErrors.password ? "password-error" : error ? "login-error" : undefined}
                className={`w-full px-4 py-3 pr-12 rounded-input border bg-[var(--surface-0)] text-[var(--ink)]
                           focus:border-[var(--brand-blue)] focus:outline-none focus:ring-2
                           focus:ring-[var(--brand-blue-subtle)] ${
                             formErrors.password ? "border-[var(--error)]" : "border-[var(--border)]"
                           }`}
                placeholder="Sua senha"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-[var(--ink-muted)]
                           hover:text-[var(--ink)] transition-colors"
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
              >
                {showPassword ? (
                  <svg role="img" aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg role="img" aria-label="Ícone" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            {formErrors.password && (
              <p id="password-error" className="mt-1 text-xs text-[var(--error)]">
                {formErrors.password.message}
              </p>
            )}
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
    </>
  );
}
