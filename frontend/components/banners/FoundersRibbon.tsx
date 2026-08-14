"use client";

import Link from "next/link";

/**
 * BIZ-FOUND-002 / Issue #787: Reusable founders ribbon badge for pSEO contextual CTAs.
 *
 * Static — no client-side data fetching (no useEffect, no availability check).
 * Intended for use in pSEO routes where SSR/SSG context makes client fetches costly.
 *
 * Consumed by issue #788 and other pSEO routes.
 * Fires Mixpanel event: founders_pseo_conversion on CTA click.
 *
 * @param variant  - 'badge' | 'contextual' | 'inline' (default: 'badge')
 * @param copy     - Override default copy text
 * @param src      - UTM source for the CTA link (passed as ?src= query param)
 */
export interface FoundersRibbonProps {
  variant?: "badge" | "contextual" | "inline";
  copy?: string;
  src?: string;
}

export function FoundersRibbon({
  variant = "badge",
  copy = "Pedir um diagnóstico à CONFENGE",
  src,
}: FoundersRibbonProps) {
  const href = `/consultoria-b2g${src ? `?src=${encodeURIComponent(src)}` : "?src=ribbon"}`;

  const handleClick = () => {
    try {
      if (
        typeof window !== "undefined" &&
        window.mixpanel &&
        typeof window.mixpanel.track === "function"
      ) {
        window.mixpanel.track("founders_pseo_conversion", {
          route: src ?? "ribbon",
          variant: copy,
        });
      }
    } catch {
      // Mixpanel not loaded — no-op
    }
  };

  if (variant === "inline") {
    return (
      <Link
        href={href}
        onClick={handleClick}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-orange-600 hover:text-orange-700 dark:text-orange-400 dark:hover:text-orange-300 underline underline-offset-2 transition-colors"
        data-testid="founders-ribbon-inline"
      >
        {copy}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-3.5 w-3.5 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    );
  }

  if (variant === "contextual") {
    return (
      <div
        className="flex items-center gap-3 rounded-lg border border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950/30 px-4 py-3"
        data-testid="founders-ribbon-contextual"
      >
        <span className="flex-1 text-sm font-medium text-orange-900 dark:text-orange-100">
          {copy}
        </span>
        <Link
          href={href}
          onClick={handleClick}
          className="inline-flex items-center px-3 py-1.5 bg-orange-500 hover:bg-orange-600 text-white text-xs font-semibold rounded-md transition-colors whitespace-nowrap"
        >
          Saiba mais
        </Link>
      </div>
    );
  }

  // Default: badge variant
  return (
    <Link
      href={href}
      onClick={handleClick}
      className="inline-flex items-center gap-1.5 px-3 py-1 bg-orange-500 hover:bg-orange-600 text-white text-xs font-semibold rounded-full transition-colors"
      data-testid="founders-ribbon-badge"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-3 w-3 flex-shrink-0"
        fill="currentColor"
        viewBox="0 0 20 20"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z"
          clipRule="evenodd"
        />
      </svg>
      {copy}
    </Link>
  );
}
