/**
 * ContaPageSkeleton — Skeleton loader for account settings page.
 * DEBT-FE-013
 */

export function ContaPageSkeleton() {
  return (
    <div className="min-h-screen bg-[var(--canvas)] animate-pulse">
      {/* Navbar placeholder */}
      <div className="h-16 border-b border-[var(--border)] bg-[var(--surface-0)]" />

      <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
        {/* Page heading */}
        <div className="h-8 w-40 bg-[var(--surface-2)] rounded" />

        {/* Tab bar */}
        <div className="flex gap-4 border-b border-[var(--border)] pb-0">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-8 w-24 bg-[var(--surface-2)] rounded-t" />
          ))}
        </div>

        {/* Profile section card */}
        <div className="rounded-card border border-[var(--border)] bg-[var(--surface-1)] p-6 space-y-5">
          <div className="h-5 w-32 bg-[var(--surface-2)] rounded" />

          {/* Avatar + name row */}
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-[var(--surface-2)]" />
            <div className="space-y-2">
              <div className="h-5 w-40 bg-[var(--surface-2)] rounded" />
              <div className="h-4 w-56 bg-[var(--surface-2)] rounded" />
            </div>
          </div>

          {/* Form fields */}
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="space-y-1.5">
              <div className="h-4 w-24 bg-[var(--surface-2)] rounded" />
              <div className="h-10 w-full bg-[var(--surface-2)] rounded-button" />
            </div>
          ))}

          {/* Save button */}
          <div className="h-10 w-28 bg-[var(--surface-2)] rounded-button" />
        </div>

        {/* Plan section card */}
        <div className="rounded-card border border-[var(--border)] bg-[var(--surface-1)] p-6 space-y-4">
          <div className="h-5 w-28 bg-[var(--surface-2)] rounded" />
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="h-5 w-32 bg-[var(--surface-2)] rounded" />
              <div className="h-4 w-48 bg-[var(--surface-2)] rounded" />
            </div>
            <div className="h-9 w-36 bg-[var(--surface-2)] rounded-button" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default ContaPageSkeleton;
