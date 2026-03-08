"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

/**
 * STORY-211 AC9: Root layout error boundary.
 * Catches errors that `error.tsx` cannot (e.g., root layout crashes).
 * Must define its own <html> and <body> tags since the root layout has failed.
 *
 * STORY-267 AC12-14: Brand alignment + dark mode.
 * Cannot use Tailwind/CSS imports (root layout failed). Uses inline styles + <style> tag.
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
      <head>
        <style dangerouslySetInnerHTML={{ __html: `
          :root {
            --ge-bg: #f8fafc;
            --ge-card-bg: #ffffff;
            --ge-text: #0f172a;
            --ge-text-secondary: #64748b;
            --ge-brand-navy: #0a1e3f;
            --ge-brand-blue: #116dff;
            --ge-brand-blue-hover: #0e5cd6;
            --ge-shadow: rgba(0, 0, 0, 0.1);
            --ge-link: #116dff;
          }
          @media (prefers-color-scheme: dark) {
            :root {
              --ge-bg: #0f172a;
              --ge-card-bg: #1e293b;
              --ge-text: #f1f5f9;
              --ge-text-secondary: #94a3b8;
              --ge-brand-navy: #3b82f6;
              --ge-brand-blue: #60a5fa;
              --ge-brand-blue-hover: #3b82f6;
              --ge-shadow: rgba(0, 0, 0, 0.3);
              --ge-link: #60a5fa;
            }
          }
        `}} />
      </head>
      <body>
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "system-ui, -apple-system, sans-serif",
            padding: "1rem",
            backgroundColor: "var(--ge-bg)",
          }}
        >
          <div
            style={{
              maxWidth: "28rem",
              width: "100%",
              backgroundColor: "var(--ge-card-bg)",
              boxShadow: "0 4px 6px var(--ge-shadow)",
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
                color: "var(--ge-text)",
              }}
            >
              Ops! Algo deu errado
            </h1>
            <p style={{ color: "var(--ge-text-secondary)", marginBottom: "1.5rem" }}>
              Ocorreu um erro inesperado na aplicação. Por favor,
              tente novamente.
            </p>
            <button
              onClick={reset}
              style={{
                width: "100%",
                backgroundColor: "var(--ge-brand-navy)",
                color: "white",
                fontWeight: 500,
                padding: "0.75rem 1.5rem",
                borderRadius: "0.5rem",
                border: "none",
                cursor: "pointer",
                fontSize: "1rem",
                transition: "background-color 0.2s",
              }}
              onMouseOver={(e) => { (e.target as HTMLButtonElement).style.backgroundColor = "var(--ge-brand-blue-hover)"; }}
              onMouseOut={(e) => { (e.target as HTMLButtonElement).style.backgroundColor = "var(--ge-brand-navy)"; }}
            >
              Tentar novamente
            </button>
            <p style={{ marginTop: "1rem", fontSize: "0.875rem", color: "var(--ge-text-secondary)" }}>
              Se o problema persistir,{" "}
              <a href="/mensagens" style={{ color: "var(--ge-link)", textDecoration: "underline" }}>
                entre em contato com o suporte
              </a>{" "}
              ou consulte a{" "}
              <a href="/ajuda" style={{ color: "var(--ge-link)", textDecoration: "underline" }}>
                Central de Ajuda
              </a>.
            </p>
          </div>
        </div>
      </body>
    </html>
  );
}
