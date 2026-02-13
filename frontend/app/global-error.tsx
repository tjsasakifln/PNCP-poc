"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

/**
 * STORY-211 AC9: Root layout error boundary.
 * Catches errors that `error.tsx` cannot (e.g., root layout crashes).
 * Must define its own <html> and <body> tags since the root layout has failed.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="pt-BR">
      <body>
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "system-ui, -apple-system, sans-serif",
            padding: "1rem",
            backgroundColor: "#f9fafb",
          }}
        >
          <div
            style={{
              maxWidth: "28rem",
              width: "100%",
              backgroundColor: "white",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              borderRadius: "0.5rem",
              padding: "2rem",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>
              &#9888;
            </div>
            <h1
              style={{
                fontSize: "1.5rem",
                fontWeight: "bold",
                marginBottom: "0.5rem",
                color: "#111827",
              }}
            >
              Ops! Algo deu errado
            </h1>
            <p style={{ color: "#6b7280", marginBottom: "1.5rem" }}>
              Ocorreu um erro inesperado na aplica&ccedil;&atilde;o. Por favor,
              tente novamente.
            </p>
            <button
              onClick={reset}
              style={{
                width: "100%",
                backgroundColor: "#16a34a",
                color: "white",
                fontWeight: 500,
                padding: "0.75rem 1.5rem",
                borderRadius: "0.5rem",
                border: "none",
                cursor: "pointer",
                fontSize: "1rem",
              }}
            >
              Tentar novamente
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
