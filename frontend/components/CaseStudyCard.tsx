"use client";

/**
 * STORY-372 AC1: CaseStudyCard component.
 * Displays a concrete B2G use case with quantified results.
 */

interface CaseStudyHighlight {
  value: string;
  label: string;
  time: string;
}

interface CaseStudyCardProps {
  sector: string;
  location: string;
  companySize: string;
  problem: string;
  result: string;
  highlight: CaseStudyHighlight;
  quote?: string;
}

export function CaseStudyCard({
  sector,
  location,
  companySize,
  problem,
  result,
  highlight,
  quote,
}: CaseStudyCardProps) {
  return (
    <div className="bg-[var(--canvas)] border border-[var(--border)] rounded-card p-6 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-xs font-medium text-[var(--ink-secondary)] uppercase tracking-wide">
            {sector}
          </span>
          <p className="text-sm text-[var(--ink-secondary)] mt-0.5">
            📍 {location} · {companySize}
          </p>
        </div>
      </div>

      {/* Highlight Number */}
      <div className="bg-[var(--surface)] rounded-lg p-4 text-center">
        <p className="text-3xl font-display font-bold text-[var(--brand-blue)]">
          {highlight.value}
        </p>
        <p className="text-sm text-[var(--ink-secondary)] mt-1">{highlight.label}</p>
        <p className="text-xs text-[var(--ink-secondary)] mt-0.5 opacity-70">
          {highlight.time}
        </p>
      </div>

      {/* Problem → Result */}
      <div className="space-y-2">
        <p className="text-sm text-[var(--ink-secondary)] italic">
          &ldquo;{problem}&rdquo;
        </p>
        <p className="text-sm text-[var(--ink)] font-medium">
          ✅ {result}
        </p>
      </div>

      {/* Optional Quote */}
      {quote && (
        <p className="text-xs text-[var(--ink-secondary)] border-l-2 border-[var(--brand-blue)] pl-3 italic">
          {quote}
        </p>
      )}
    </div>
  );
}
