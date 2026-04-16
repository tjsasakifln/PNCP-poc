"use client";

/**
 * GTM-POLISH-001 AC1-AC3: Unified auth loading screen.
 * Used by ALL protected pages for consistent loading UX.
 * - Logo + page skeleton (not a generic spinner)
 * - Smooth fade transition when auth resolves
 */
export function AuthLoadingScreen() {
  return (
    <div
      className="min-h-screen bg-[var(--canvas)] flex flex-col animate-fade-in"
      data-testid="auth-loading-screen"
      role="status"
      aria-busy="true"
      aria-label="Verificando autenticacao"
    >
      {/* Header skeleton matching PageHeader */}
      <div className="h-14 border-b border-[var(--border)] bg-[var(--surface-0)] flex items-center px-4">
        <div className="h-6 w-28 bg-[var(--surface-1)] rounded animate-pulse" />
        <div className="ml-auto h-8 w-8 bg-[var(--surface-1)] rounded-full animate-pulse" />
      </div>

      {/* Content skeleton */}
      <div className="flex-1 max-w-6xl mx-auto w-full px-4 py-8">
        {/* Title skeleton */}
        <div className="h-7 w-48 bg-[var(--surface-1)] rounded animate-pulse mb-2" />
        <div className="h-4 w-72 bg-[var(--surface-1)] rounded animate-pulse mb-8" />

        {/* Card grid skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {[1, 2, 3].map((i) => (
            // eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: animationDelay computed from array index to stagger skeleton pulses
            <div
              key={i}
              className="h-32 bg-[var(--surface-1)] rounded-card animate-pulse"
              style={{ animationDelay: `${i * 100}ms` }}
            />
          ))}
        </div>

        {/* List skeleton */}
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            // eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: animationDelay computed from array index to stagger skeleton pulses
            <div
              key={i}
              className="h-20 bg-[var(--surface-1)] rounded-card animate-pulse"
              style={{ animationDelay: `${(i + 3) * 100}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
