"use client";

import Link from "next/link";

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  steps?: string[];
  ctaLabel: string;
  ctaHref: string;
}

export function EmptyState({
  icon,
  title,
  description,
  steps,
  ctaLabel,
  ctaHref,
}: EmptyStateProps) {
  return (
    <div className="text-center py-16 px-4" data-testid="empty-state">
      <div className="mx-auto mb-6 w-16 h-16 flex items-center justify-center rounded-full bg-[var(--brand-blue-subtle)]">
        {icon}
      </div>
      <h2 className="text-xl font-display font-semibold text-[var(--ink)] mb-3">
        {title}
      </h2>
      <p className="text-[var(--ink-secondary)] mb-6 max-w-md mx-auto">
        {description}
      </p>
      {steps && steps.length > 0 && (
        <ol className="text-left max-w-sm mx-auto mb-8 space-y-3">
          {steps.map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--brand-blue)] text-white text-xs font-bold flex items-center justify-center mt-0.5">
                {i + 1}
              </span>
              <span className="text-sm text-[var(--ink-secondary)]">{step}</span>
            </li>
          ))}
        </ol>
      )}
      <Link
        href={ctaHref}
        className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--brand-navy)] text-white
                   rounded-button hover:bg-[var(--brand-blue)] transition-colors font-medium"
        data-testid="empty-state-cta"
      >
        {ctaLabel}
        <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </Link>
    </div>
  );
}
