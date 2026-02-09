'use client';

interface StatCardProps {
  value: string;
  label: string;
  sublabel?: string;
  isHero?: boolean;
  loading?: boolean;
  delay?: number;
  isInView?: boolean;
}

export default function StatCard({
  value,
  label,
  sublabel,
  isHero = false,
  loading = false,
  delay = 0,
  isInView = false,
}: StatCardProps) {
  // Skeleton dimensions match final component to prevent CLS
  if (loading) {
    return (
      <div
        className={`${
          isHero
            ? 'p-8 lg:p-12'
            : 'p-6'
        } bg-surface-0 rounded-card border border-[var(--border)] shadow-sm animate-pulse`}
      >
        {/* Value skeleton */}
        <div
          className={`${
            isHero
              ? 'h-24 w-48 sm:h-28 sm:w-56 lg:h-32 lg:w-64'
              : 'h-10 w-24 sm:h-12 sm:w-28'
          } bg-ink-secondary/10 rounded mx-auto mb-2`}
        />

        {/* Label skeleton */}
        <div
          className={`${
            isHero ? 'h-6 w-32' : 'h-4 w-24'
          } bg-ink-secondary/10 rounded mx-auto`}
        />

        {/* Hero divider skeleton */}
        {isHero && (
          <div className="w-16 h-1 bg-ink-secondary/10 rounded-full mx-auto mt-4" />
        )}

        {/* Sublabel skeleton (only for non-hero) */}
        {!isHero && sublabel && (
          <div className="h-3 w-20 bg-ink-secondary/10 rounded mx-auto mt-1" />
        )}
      </div>
    );
  }

  return (
    <div
      className={`text-center transition-all duration-500 ${
        isHero
          ? 'flex-shrink-0 p-8 lg:p-12 bg-surface-0 rounded-card border border-[var(--border)] shadow-sm'
          : 'p-6 bg-surface-0 rounded-card border border-[var(--border)] hover:-translate-y-0.5 hover:shadow-md'
      } ${
        isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      } ${isHero && isInView ? 'scale-100' : isHero ? 'scale-95' : ''}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {/* Value */}
      <div
        className={`${
          isHero
            ? 'text-6xl sm:text-7xl lg:text-8xl font-display tracking-tighter'
            : 'text-3xl sm:text-4xl font-bold'
        } text-brand-blue tabular-nums`}
      >
        {value}
      </div>

      {/* Label */}
      <div
        className={`${
          isHero ? 'text-lg font-medium' : 'text-sm'
        } text-ink-secondary mt-2`}
      >
        {label}
      </div>

      {/* Hero divider */}
      {isHero && (
        <div className="w-16 h-1 bg-brand-blue mx-auto mt-4 rounded-full" />
      )}

      {/* Sublabel (for smaller cards) */}
      {!isHero && sublabel && (
        <div className="text-xs text-ink-secondary/80 mt-1">{sublabel}</div>
      )}
    </div>
  );
}
