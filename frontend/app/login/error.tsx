"use client";

/**
 * STORY-421 (EPIC-INCIDENT-2026-04-10): Defensive error boundary for /login.
 *
 * Root cause: Sentry issue 7397346898 surfaced `InvariantError: Expected RSC
 * response, got text/plain. This is a bug in Next.js.` — a Next.js routing-layer
 * failure that leaves the login page blank for affected users. The bug
 * originates in the RSC resolver, so a per-page `error.tsx` is the right
 * mitigation layer: it catches the throw inside the client router and lets
 * the user recover without seeing a white screen.
 *
 * Behavior:
 *   1. All errors are reported to Sentry with `page: 'login'` tag so the
 *      alerting rules from STORY-423 can route them correctly.
 *   2. If the error message hints at the RSC invariant, we recommend a
 *      hard reload (which bypasses the poisoned RSC cache) instead of the
 *      default `reset()` (which just re-runs the same segment).
 *   3. Otherwise, we offer `reset()` as a soft retry + a link to /signup as
 *      a safe escape hatch so trial users are never blocked.
 */

import * as Sentry from "@sentry/nextjs";
import { useEffect, useMemo } from "react";
import Link from "next/link";

type LoginErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

function isRscInvariant(error: Error): boolean {
  const msg = (error?.message || "").toLowerCase();
  return (
    msg.includes("invariant") ||
    msg.includes("expected rsc") ||
    msg.includes("rsc response") ||
    msg.includes("text/plain")
  );
}

export default function LoginError({ error, reset }: LoginErrorProps) {
  const rscInvariant = useMemo(() => isRscInvariant(error), [error]);

  useEffect(() => {
    Sentry.captureException(error, {
      tags: {
        page: "login",
        error_type: rscInvariant ? "rsc_invariant" : "runtime_error",
      },
      extra: {
        digest: error?.digest,
        rsc_invariant: rscInvariant,
      },
    });
    // eslint-disable-next-line no-console
    console.error("[STORY-421] Login page error boundary caught:", error);
  }, [error, rscInvariant]);

  const handlePrimaryAction = () => {
    if (rscInvariant && typeof window !== "undefined") {
      // Hard reload bypasses the poisoned RSC cache — `reset()` alone would
      // re-render the same broken segment and throw again.
      window.location.reload();
      return;
    }
    reset();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)] px-4">
      <div className="max-w-md w-full bg-surface-0 shadow-lg rounded-card p-8 text-center">
        <div className="mb-6">
          <svg
            className="mx-auto h-16 w-16 text-warning"
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
        </div>

        <h1 className="text-2xl font-bold text-ink mb-2">
          Problema ao carregar a página de login
        </h1>

        <p className="text-ink-secondary mb-6">
          {rscInvariant
            ? "Encontramos uma inconsistência temporária ao carregar a página. Uma atualização completa costuma resolver."
            : "Ocorreu um erro inesperado. Tente novamente — suas informações não foram afetadas."}
        </p>

        {error?.digest && (
          <div className="mb-6 p-3 bg-surface-2 rounded-md text-left">
            <p className="text-xs text-ink-muted break-words">
              Código de diagnóstico: <span className="font-mono">{error.digest}</span>
            </p>
          </div>
        )}

        <div className="space-y-3">
          <button
            type="button"
            onClick={handlePrimaryAction}
            className="w-full bg-brand-navy hover:bg-brand-blue-hover text-white font-medium py-3 px-6 rounded-button transition-colors focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2"
            data-testid="login-error-retry"
          >
            {rscInvariant ? "Atualizar página" : "Tentar novamente"}
          </button>

          <Link
            href="/"
            className="block w-full text-sm text-ink-muted hover:text-brand-blue transition-colors py-2"
            data-testid="login-error-home"
          >
            Voltar ao início
          </Link>

          <Link
            href="/signup"
            className="block w-full text-xs text-ink-muted hover:text-brand-blue transition-colors py-1"
          >
            Ainda não tem conta? Criar conta gratuita
          </Link>
        </div>
      </div>
    </div>
  );
}
