"use client";

/**
 * DEBT-204 Track 3: BannerStack
 *
 * Priority-driven banner container that reduces cognitive load by limiting
 * visible banners to 2 (the highest-severity ones) and offering a collapsible
 * "Ver mais alertas" panel for the rest.
 *
 * Priority order: error (4) > warning (3) > info (2) > success (1)
 * aria-live="assertive" for errors, aria-live="polite" for others.
 */

import React, { useState } from "react";

// ============================================================================
// Types
// ============================================================================

export type BannerType = "error" | "warning" | "info" | "success";

export interface BannerItem {
  /** Unique identifier for this banner entry */
  id: string;
  /** Severity type — drives sort order and aria-live level */
  type: BannerType;
  /** The content to render inside the banner */
  content: React.ReactNode;
  /**
   * Optional tie-breaking priority within the same type.
   * Higher value = shown first when severities are equal.
   * Default: 0.
   */
  priority?: number;
}

export interface BannerStackProps {
  /** Ordered list of banners to display */
  banners: BannerItem[];
  /**
   * Maximum number of banners shown before collapsing.
   * Default: 2.
   */
  maxVisible?: number;
  /** Extra className on the container element */
  className?: string;
  /** data-testid for the container */
  "data-testid"?: string;
}

// ============================================================================
// Helpers
// ============================================================================

const SEVERITY_RANK: Record<BannerType, number> = {
  error: 4,
  warning: 3,
  info: 2,
  success: 1,
};

function sortBanners(banners: BannerItem[]): BannerItem[] {
  return [...banners].sort((a, b) => {
    const rankDiff = SEVERITY_RANK[b.type] - SEVERITY_RANK[a.type];
    if (rankDiff !== 0) return rankDiff;
    // Same severity — higher priority value first
    return (b.priority ?? 0) - (a.priority ?? 0);
  });
}

// ============================================================================
// BannerWrapper — renders a single banner item with aria-live
// ============================================================================

interface BannerWrapperProps {
  item: BannerItem;
}

function BannerWrapper({ item }: BannerWrapperProps) {
  // Errors use "assertive" so screen readers announce immediately.
  const ariaLive: React.AriaAttributes["aria-live"] =
    item.type === "error" ? "assertive" : "polite";

  return (
    <div
      data-testid={`banner-item-${item.id}`}
      aria-live={ariaLive}
      aria-atomic="true"
    >
      {item.content}
    </div>
  );
}

// ============================================================================
// BannerStack — main component
// ============================================================================

export function BannerStack({
  banners,
  maxVisible = 2,
  className = "",
  "data-testid": testId = "banner-stack",
}: BannerStackProps) {
  const [expanded, setExpanded] = useState(false);

  // Nothing to render
  if (banners.length === 0) return null;

  const sorted = sortBanners(banners);
  const visible = sorted.slice(0, maxVisible);
  const hidden = sorted.slice(maxVisible);
  const hasMore = hidden.length > 0;

  return (
    <div
      data-testid={testId}
      className={["flex flex-col gap-2", className].filter(Boolean).join(" ")}
    >
      {/* Always-visible top banners */}
      {visible.map((item) => (
        <BannerWrapper key={item.id} item={item} />
      ))}

      {/* Overflow section */}
      {hasMore && (
        <div>
          {/* Toggle button */}
          <button
            type="button"
            data-testid="banner-stack-toggle"
            onClick={() => setExpanded((prev) => !prev)}
            aria-expanded={expanded}
            aria-controls="banner-stack-overflow"
            className={[
              "flex items-center gap-1.5 text-xs font-medium",
              "text-[var(--ink-secondary)] hover:text-[var(--ink)]",
              "transition-colors focus-visible:outline-none",
              "focus-visible:ring-2 focus-visible:ring-[var(--brand-blue)] rounded",
              "py-1 px-0",
            ].join(" ")}
          >
            {expanded ? (
              <>
                {/* Chevron up */}
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 15l7-7 7 7"
                  />
                </svg>
                Ocultar alertas
              </>
            ) : (
              <>
                {/* Chevron down */}
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
                Ver mais alertas (+{hidden.length})
              </>
            )}
          </button>

          {/* Collapsed/expanded overflow banners */}
          <div
            id="banner-stack-overflow"
            data-testid="banner-stack-overflow"
            aria-hidden={!expanded}
            className={[
              "flex flex-col gap-2 overflow-hidden transition-all duration-200",
              expanded ? "mt-2 opacity-100" : "max-h-0 opacity-0 pointer-events-none",
            ].join(" ")}
          >
            {hidden.map((item) => (
              <BannerWrapper key={item.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default BannerStack;
