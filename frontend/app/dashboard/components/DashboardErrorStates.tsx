"use client";

import Link from "next/link";

// CRIT-031 AC1-AC3: Full-page error state when ALL sections failed / no data
export function DashboardFullPageError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto text-center py-16" data-testid="dashboard-empty-state">
        <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--surface-1)]">
          <svg
            aria-hidden="true"
            className="w-8 h-8 text-[var(--ink-muted)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M2 15a5 5 0 005 5h9a5 5 0 10-4.5-7.17A4 4 0 002 15z"
            />
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.5 12.5l5 5m0-5l-5 5" />
          </svg>
        </div>
        <p className="text-lg font-display font-semibold text-[var(--ink)] mb-2">
          {`Dados temporariamente indisponíveis`}
        </p>
        <p className="text-sm text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
          Tente novamente em alguns minutos.
        </p>
        <button
          onClick={onRetry}
          className="px-5 py-2.5 bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
          data-testid="dashboard-retry-button"
        >
          Tentar novamente
        </button>
        <div className="mt-3 text-center">
          <Link href="/ajuda" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
            Precisa de ajuda?
          </Link>
        </div>
      </div>
    </div>
  );
}

// Transient error during retries — still retrying automatically
export function DashboardRetryingState({ retryCount }: { retryCount: number }) {
  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4">
      <div className="max-w-6xl mx-auto text-center py-16" data-testid="dashboard-retrying">
        <div className="mx-auto mb-4 w-8 h-8 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-[var(--ink-secondary)]">
          Tentando reconectar... ({retryCount}/3)
        </p>
      </div>
    </div>
  );
}

// UX-416 AC3: Labeled loading skeleton shown on initial load (max 10s)
export function DashboardLoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[var(--canvas)] py-8 px-4" data-testid="dashboard-skeleton">
      <div className="max-w-6xl mx-auto">
        <div className="h-8 w-48 bg-[var(--surface-1)] rounded animate-pulse mb-8" />
        {/* UX-416 AC3: Labeled skeleton sections */}
        <p className="text-xs text-[var(--ink-muted)] mb-2">Carregando métricas...</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {['Análises', 'Oportunidades', 'Valor descoberto', 'Tempo economizado'].map((label) => (
            <div key={label} className="h-32 bg-[var(--surface-1)] rounded-card animate-pulse flex items-end p-3">
              <span className="text-[10px] text-[var(--ink-faint)]">{label}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-[var(--ink-muted)] mb-2">Carregando gráfico de atividade...</p>
        <div className="h-64 bg-[var(--surface-1)] rounded-card animate-pulse mb-8" />
        <p className="text-xs text-[var(--ink-muted)] mb-2">Carregando distribuição...</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-48 bg-[var(--surface-1)] rounded-card animate-pulse" />
          <div className="h-48 bg-[var(--surface-1)] rounded-card animate-pulse" />
        </div>
      </div>
    </div>
  );
}

// Not-authenticated state
export function DashboardNotAuthenticated() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
      <div className="text-center">
        <p className="text-[var(--ink-secondary)] mb-4">{`Faça login para acessar o dashboard`}</p>
        <Link href="/login" className="text-[var(--brand-blue)] hover:underline">
          Ir para login
        </Link>
      </div>
    </div>
  );
}

// Empty state — no searches yet
export function DashboardEmptyState() {
  return (
    <div className="text-center py-16 px-4" data-testid="empty-state">
      <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--brand-blue-subtle)]">
        <svg
          aria-hidden="true"
          className="w-8 h-8 text-[var(--brand-blue)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
          />
        </svg>
      </div>
      <h2 className="text-xl font-display font-semibold text-[var(--ink)] mb-3">
        {`Seu Painel de Inteligência`}
      </h2>
      <p className="text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
        {`Após suas primeiras análises, você verá aqui:`}
      </p>
      <ul className="text-left max-w-sm mx-auto mb-8 space-y-2">
        <li className="flex items-center gap-2 text-sm text-[var(--ink-secondary)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-blue)] flex-shrink-0" />
          Resumo de oportunidades encontradas
        </li>
        <li className="flex items-center gap-2 text-sm text-[var(--ink-secondary)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-blue)] flex-shrink-0" />
          {`Tendências do seu setor`}
        </li>
        <li className="flex items-center gap-2 text-sm text-[var(--ink-secondary)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand-blue)] flex-shrink-0" />
          Valor total de oportunidades analisadas
        </li>
      </ul>
      <Link
        href="/buscar"
        className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                   rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
        data-testid="empty-state-cta"
      >
        Fazer primeira análise
        <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </Link>
      <div className="mt-3 text-center">
        <Link href="/ajuda#como-buscar" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
          Precisa de ajuda?
        </Link>
      </div>
    </div>
  );
}

// CRIT-031 AC4: Stale data banner when showing cached data after error
export function DashboardStaleBanner({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="max-w-6xl mx-auto px-4 pt-4" data-testid="stale-data-banner">
      <div className="flex items-center justify-between p-3 rounded-card border border-[var(--border)] bg-[var(--surface-1)]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[var(--warning)] flex-shrink-0" />
          <span className="text-sm text-[var(--ink-secondary)]">
            Dados podem estar desatualizados
          </span>
        </div>
        <button
          onClick={onRetry}
          className="text-sm font-medium text-[var(--brand-blue)] hover:underline"
          data-testid="stale-data-retry"
        >
          Tentar novamente
        </button>
      </div>
    </div>
  );
}
