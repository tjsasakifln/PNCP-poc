"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to console in development
    console.error("Application error:", error);

    // In production, you would send this to an error tracking service
    // Example: Sentry, LogRocket, Datadog, etc.
    // errorTracker.captureException(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
        <div className="mb-6">
          <svg
            className="mx-auto h-16 w-16 text-red-500"
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

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Ops! Algo deu errado
        </h1>

        <p className="text-gray-600 mb-6">
          Ocorreu um erro inesperado. Por favor, tente novamente.
        </p>

        {error.message && (
          <div className="mb-6 p-4 bg-gray-100 rounded-md text-left">
            <p className="text-sm text-gray-700 font-mono break-words">
              {error.message}
            </p>
          </div>
        )}

        <button
          onClick={reset}
          className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
        >
          Tentar novamente
        </button>

        <p className="mt-4 text-sm text-gray-500">
          Se o problema persistir, entre em contato com o suporte.
        </p>
      </div>
    </div>
  );
}
