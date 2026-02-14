"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";
import { useAnalytics } from "../hooks/useAnalytics";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { trackEvent } = useAnalytics();

  useEffect(() => {
    // STORY-211 AC10: Report errors to Sentry
    Sentry.captureException(error);
    console.error("Application error:", error);
    // STORY-219 AC23: Track error in analytics
    trackEvent('error_encountered', {
      error_type: error.name || 'Error',
      error_message: error.message,
      error_digest: error.digest,
      page: typeof window !== 'undefined' ? window.location.pathname : 'unknown',
    });
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--surface-0)] px-4">
      <div className="max-w-md w-full bg-[var(--surface-1)] shadow-lg rounded-lg p-8 text-center">
        <div className="mb-6">
          <svg
            className="mx-auto h-16 w-16 text-[var(--error)]"
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

        <h1 className="text-2xl font-bold text-[var(--ink)] mb-2">
          Ops! Algo deu errado
        </h1>

        <p className="text-[var(--ink-secondary)] mb-6">
          Ocorreu um erro inesperado. Por favor, tente novamente.
        </p>

        {error.message && (
          <div className="mb-6 p-4 bg-[var(--surface-2)] rounded-md text-left">
            <p className="text-sm text-[var(--ink-secondary)] font-mono break-words">
              {error.message}
            </p>
          </div>
        )}

        <button
          onClick={reset}
          className="w-full bg-[var(--brand-green)] hover:opacity-90 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--brand-green)] focus:ring-offset-2"
        >
          Tentar novamente
        </button>

        <p className="mt-4 text-sm text-[var(--ink-muted)]">
          Se o problema persistir,{" "}
          <a href="/mensagens" className="text-[var(--brand-blue)] hover:underline">
            entre em contato com o suporte
          </a>{" "}
          ou consulte a{" "}
          <a href="/ajuda" className="text-[var(--brand-blue)] hover:underline">
            Central de Ajuda
          </a>.
        </p>
      </div>
    </div>
  );
}
