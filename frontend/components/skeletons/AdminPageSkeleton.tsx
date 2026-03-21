/**
 * AdminPageSkeleton — Skeleton loader for admin pages.
 * DEBT-FE-013
 */

export function AdminPageSkeleton() {
  return (
    <div className="min-h-screen bg-[var(--canvas)] animate-pulse">
      {/* Navbar placeholder */}
      <div className="h-16 border-b border-[var(--border)] bg-[var(--surface-0)]" />

      <div className="max-w-6xl mx-auto py-8 px-4 space-y-6">
        {/* Page heading */}
        <div className="h-8 w-48 bg-[var(--surface-2)] rounded" />

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-card border border-[var(--border)] bg-[var(--surface-1)] p-4 space-y-2">
              <div className="h-3 w-20 bg-[var(--surface-2)] rounded" />
              <div className="h-7 w-16 bg-[var(--surface-2)] rounded" />
            </div>
          ))}
        </div>

        {/* Table skeleton */}
        <div className="rounded-card border border-[var(--border)] bg-[var(--surface-0)] overflow-hidden">
          {/* Table header */}
          <div className="flex gap-4 px-4 py-3 border-b border-[var(--border)] bg-[var(--surface-1)]">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-4 bg-[var(--surface-2)] rounded flex-1" />
            ))}
          </div>
          {/* Table rows */}
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex gap-4 px-4 py-3 border-b border-[var(--border)] last:border-0">
              {Array.from({ length: 5 }).map((_, j) => (
                <div key={j} className="h-4 bg-[var(--surface-2)] rounded flex-1 opacity-70" />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AdminPageSkeleton;
