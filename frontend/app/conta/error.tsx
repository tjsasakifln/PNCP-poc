"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import Link from "next/link";
import { getUserFriendlyError } from "../../lib/error-messages";

export default function ContaError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("Conta error:", error);
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
              d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
            />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-ink mb-2">
          Erro na conta
        </h1>

        <p className="text-ink-secondary mb-6">
          Ocorreu um erro ao carregar sua conta. Tente novamente.
        </p>

        <div className="mb-6 p-4 bg-surface-2 rounded-md text-left">
          <p className="text-sm text-ink-secondary break-words">
            {getUserFriendlyError(error)}
          </p>
        </div>

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
