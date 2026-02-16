'use client';

import { CATEGORY_META, type CategoryId } from '@/lib/data/analysisExamples';

interface CategoryBadgeProps {
  category: CategoryId;
  className?: string;
}

/**
 * GTM-005: Category badge for analysis example cards.
 * Shows sector/category with color coding.
 */
export function CategoryBadge({ category, className = '' }: CategoryBadgeProps) {
  const meta = CATEGORY_META[category];

  return (
    <span
      className={`
        inline-flex items-center
        px-2.5 py-0.5
        text-xs font-semibold
        rounded-full
        ${meta.bgColor} ${meta.color}
        ${meta.darkBgColor} ${meta.darkColor}
        ${className}
      `}
    >
      {meta.label}
    </span>
  );
}
