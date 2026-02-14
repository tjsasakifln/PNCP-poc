"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import Link from "next/link";

export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("Admin page error:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)] px-4">
      <div className="max-w-md w-full bg-surface-0 shadow-lg rounded-card p-8 text-center">
        <div className="mb-6">
          <svg
            className="mx-auto h-16 w-16 text-error"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-ink mb-2">
          Erro na administração
        </h1>

        <p className="text-ink-secondary mb-6">
          Ocorreu um erro ao carregar o painel administrativo. Verifique suas permissões ou tente novamente.
        </p>

        {error.message && (
          <div className="mb-6 p-4 bg-surface-2 rounded-md text-left">
            <p className="text-sm text-ink-secondary font-mono break-words">
              {error.message}
            </p>
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={reset}
            className="w-full bg-brand-navy hover:bg-brand-blue-hover text-white font-medium py-3 px-6 rounded-button transition-colors focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2"
          >
            Tentar novamente
          </button>

          <Link
            href="/buscar"
            className="block w-full text-sm text-ink-muted hover:text-brand-blue transition-colors py-2"
          >
            Voltar para a busca
          </Link>
        </div>
      </div>
    </div>
  );
}
