"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import Link from "next/link";
import { getUserFriendlyError } from "../../lib/error-messages";

export default function MensagensError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error("Mensagens error:", error);
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
              d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
            />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-ink mb-2">
          Erro nas mensagens
        </h1>

        <p className="text-ink-secondary mb-6">
          Ocorreu um erro ao carregar as mensagens. Tente novamente.
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
