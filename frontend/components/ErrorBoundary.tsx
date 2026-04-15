"use client";

import React, { Component, ErrorInfo } from "react";

interface Props {
  children: React.ReactNode;
  /** Name of the page/section for logging */
  pageName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * DEBT-105 FE-NEW-02: Reusable error boundary for internal pages.
 * Catches render errors in child components and displays a recovery UI
 * with retry action and support link.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(
      `[ErrorBoundary${this.props.pageName ? `:${this.props.pageName}` : ""}] Component crash:`,
      error,
      errorInfo
    );
    try {
      import("@sentry/nextjs")
        .then((Sentry) => {
          Sentry.captureException(error, {
            extra: {
              componentStack: errorInfo.componentStack,
              pageName: this.props.pageName,
            },
          });
        })
        .catch(() => {});
    } catch {}
    // STORY-2.3 AC4: emitir telemetria humanizada (Mixpanel)
    try {
      import("mixpanel-browser")
        .then((mod) => {
          const mp = (mod as { default?: { track?: (e: string, p: Record<string, unknown>) => void } }).default ?? mod;
          if (mp && typeof (mp as { track?: unknown }).track === "function") {
            (mp as { track: (e: string, p: Record<string, unknown>) => void }).track("error_message_shown", {
              error_type: "boundary.render_crash",
              page: this.props.pageName ?? (typeof window !== "undefined" ? window.location.pathname : "unknown"),
              severity: "warning",
            });
          }
        })
        .catch(() => {});
    } catch {}
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          aria-live="assertive"
          className="min-h-[60vh] flex items-center justify-center px-4"
        >
          <div className="max-w-md w-full text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/40">
              <svg
                className="h-8 w-8 text-amber-600 dark:text-amber-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                />
              </svg>
            </div>

            <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">
              Algo deu errado
            </h2>
            <p className="text-sm text-[var(--ink-secondary)] mb-6">
              Ocorreu um erro inesperado ao carregar esta pagina. Tente
              novamente ou entre em contato com o suporte.
            </p>

            <div className="flex flex-col sm:flex-row justify-center gap-3">
              <button
                onClick={this.handleRetry}
                className="rounded-button bg-[var(--brand-navy)] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[var(--brand-blue)] transition-colors"
              >
                Tentar novamente
              </button>
              <a
                href="/ajuda"
                className="rounded-button border border-[var(--border)] bg-[var(--surface-0)] px-5 py-2.5 text-sm font-medium text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] transition-colors"
              >
                Falar com suporte
              </a>
            </div>

            <details className="mt-6 text-left">
              <summary className="cursor-pointer text-xs text-[var(--ink-muted)] hover:underline">
                Detalhes tecnicos
              </summary>
              <pre className="mt-2 rounded-lg bg-[var(--surface-1)] p-3 text-xs text-[var(--ink-secondary)] overflow-auto max-h-32">
                {this.state.error?.message || "Erro desconhecido"}
              </pre>
            </details>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
