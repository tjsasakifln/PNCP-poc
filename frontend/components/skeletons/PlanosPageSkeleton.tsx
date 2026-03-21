/**
 * PlanosPageSkeleton — Skeleton loader for the pricing page.
 * Used as the Next.js loading.tsx fallback while the page hydrates.
 * DEBT-FE-013
 */

export function PlanosPageSkeleton() {
  return (
    <div className="min-h-screen bg-[var(--canvas)] animate-pulse">
      {/* Navbar placeholder */}
      <div className="h-16 border-b border-[var(--border)] bg-[var(--surface-0)]" />

      <div className="max-w-4xl mx-auto py-12 px-4">
        {/* Hero */}
        <div className="text-center mb-12 space-y-4">
          <div className="h-10 w-80 bg-[var(--surface-2)] rounded-lg mx-auto" />
          <div className="h-5 w-96 bg-[var(--surface-2)] rounded mx-auto" />
        </div>

        {/* Billing toggle */}
        <div className="flex justify-center mb-8">
          <div className="h-10 w-72 bg-[var(--surface-2)] rounded-full" />
        </div>

        {/* Plan card */}
        <div className="max-w-lg mx-auto rounded-card border-2 border-[var(--surface-2)] p-8 bg-[var(--surface-1)] space-y-6">
          {/* Plan name */}
          <div className="text-center space-y-2">
            <div className="h-7 w-40 bg-[var(--surface-2)] rounded mx-auto" />
            <div className="h-4 w-64 bg-[var(--surface-2)] rounded mx-auto" />
          </div>

          {/* Price */}
          <div className="text-center space-y-2">
            <div className="h-14 w-32 bg-[var(--surface-2)] rounded mx-auto" />
            <div className="h-6 w-28 bg-[var(--surface-2)] rounded-full mx-auto" />
          </div>

          {/* Feature list */}
          <ul className="space-y-3">
            {Array.from({ length: 7 }).map((_, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-[var(--surface-2)] flex-shrink-0 mt-0.5" />
                <div className="flex-1 space-y-1">
                  <div className="h-4 bg-[var(--surface-2)] rounded w-3/4" />
                  <div className="h-3 bg-[var(--surface-2)] rounded w-1/2" />
                </div>
              </li>
            ))}
          </ul>

          {/* CTA button */}
          <div className="h-12 w-full bg-[var(--surface-2)] rounded-button" />

          {/* Trust badges */}
          <div className="flex justify-center gap-4 pt-4 border-t border-[var(--border)]">
            <div className="h-4 w-16 bg-[var(--surface-2)] rounded" />
            <div className="h-4 w-24 bg-[var(--surface-2)] rounded" />
          </div>
        </div>

        {/* FAQ skeleton */}
        <div className="mt-16 max-w-2xl mx-auto space-y-3">
          <div className="h-8 w-48 bg-[var(--surface-2)] rounded mx-auto mb-6" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-14 bg-[var(--surface-1)] rounded-card border border-[var(--border)]" />
          ))}
        </div>
      </div>
    </div>
  );
}

export default PlanosPageSkeleton;
