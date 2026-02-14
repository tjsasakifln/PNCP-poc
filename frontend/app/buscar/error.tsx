"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import Link from "next/link";

export default function BuscarError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("Search page error:", error);
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
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-ink mb-2">
          Erro na busca
        </h1>

        <p className="text-ink-secondary mb-6">
          Ocorreu um erro ao processar sua busca de licitações. Seus filtros foram preservados — tente novamente.
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
            Tentar busca novamente
          </button>

          <Link
            href="/mensagens"
            className="block w-full text-sm text-ink-muted hover:text-brand-blue transition-colors py-2"
          >
            Precisa de ajuda? Entre em contato com o suporte
          </Link>
        </div>
      </div>
    </div>
  );
}
