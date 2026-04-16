/**
 * Skeleton — canonical loading-state primitive for lists, cards, text,
 * avatars, and inline blocks. Use this instead of ad-hoc
 * `animate-pulse + bg-[var(--surface-2)]` blocks.
 *
 * STORY-5.12 (TD-FE-015 EPIC-TD-2026Q2 P2): loading-state padronization.
 *
 * Guidelines:
 *  - **Skeleton** (this file): async content within a layout — list rows,
 *    cards, tables, avatars, text blocks. Matches the final shape.
 *  - **Button/inline spinner**: for in-flight actions triggered by the user
 *    (submit, save) — use `animate-spin rounded-full border-b-2` inline.
 *  - **EnhancedLoadingProgress**: long-running operations with real progress
 *    signal (SSE, polling) — not a generic loader.
 */

import { HTMLAttributes } from "react";

type SkeletonVariant = "text" | "card" | "list" | "avatar" | "block";

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant;
  /**
   * Number of skeleton items to render. Only meaningful for `list` and
   * `text` variants. Defaults to 1.
   */
  count?: number;
}

const BASE_CLS =
  "animate-pulse bg-[var(--surface-2)] rounded";

const VARIANT_CLS: Record<SkeletonVariant, string> = {
  text: "h-4 w-full",
  card: "h-32 w-full rounded-card border border-[var(--border)] bg-[var(--surface-1)]",
  list: "h-10 w-full",
  avatar: "h-10 w-10 rounded-full",
  block: "h-full w-full",
};

export function Skeleton({
  variant = "text",
  count = 1,
  className = "",
  ...rest
}: SkeletonProps) {
  const cls = `${BASE_CLS} ${VARIANT_CLS[variant]} ${className}`.trim();

  if (count === 1) {
    return <div aria-hidden="true" className={cls} {...rest} />;
  }

  return (
    <div className="space-y-2" aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={cls} {...rest} />
      ))}
    </div>
  );
}
