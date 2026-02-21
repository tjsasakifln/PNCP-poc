"use client";

import React, { Component, ErrorInfo } from "react";

interface Props {
  children: React.ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * CRIT-002 AC1: Error boundary for search results area.
 * Catches render errors in child components and displays a recovery UI.
 * The search form stays functional outside this boundary.
 */
export class SearchErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[SearchErrorBoundary] Component crash:", error, errorInfo);
    // Sentry capture (dynamic import, non-blocking)
    try {
      import("@sentry/nextjs").then((Sentry) => {
        Sentry.captureException(error, {
          extra: { componentStack: errorInfo.componentStack },
        });
      }).catch(() => {});
    } catch {}
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-lg border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800 p-6 text-center my-4">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/40">
            <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-800 dark:text-red-300 mb-2">
            Algo deu errado ao exibir os resultados
          </h3>
          <p className="text-sm text-red-600 dark:text-red-400 mb-4">
            Um erro inesperado ocorreu. Você pode tentar recarregar ou iniciar uma nova busca.
          </p>
          <div className="flex justify-center gap-3">
            <button
              onClick={this.handleRetry}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
            >
              Tentar novamente
            </button>
            <button
              onClick={this.handleReset}
              className="rounded-md border border-red-300 dark:border-red-700 bg-white dark:bg-red-950/40 px-4 py-2 text-sm font-medium text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/40 transition-colors"
            >
              Nova busca
            </button>
          </div>
          <details className="mt-4 text-left">
            <summary className="cursor-pointer text-xs text-red-500 dark:text-red-400 hover:underline">
              Detalhes técnicos
            </summary>
            <pre className="mt-2 rounded bg-red-100 dark:bg-red-900/30 p-2 text-xs text-red-800 dark:text-red-300 overflow-auto max-h-32">
              {this.state.error?.message || "Erro desconhecido"}
            </pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
