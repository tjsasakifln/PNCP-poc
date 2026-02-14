"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import Link from "next/link";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("Dashboard error:", error);
  }, [error]);

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
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-ink mb-2">
          Erro no dashboard
        </h1>

        <p className="text-ink-secondary mb-6">
          Não foi possível carregar os dados do dashboard. Isso pode ser um problema temporário.
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
            Recarregar dashboard
          </button>

          <Link
            href="/buscar"
            className="block w-full text-sm text-ink-muted hover:text-brand-blue transition-colors py-2"
          >
            Ir para a busca de licitações
          </Link>
        </div>
      </div>
    </div>
  );
}
