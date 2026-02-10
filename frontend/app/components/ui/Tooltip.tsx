"use client";

import { useState, type ReactNode } from "react";

interface TooltipProps {
  /** Tooltip content (text or JSX) */
  content: ReactNode;
  /** Element that triggers the tooltip on hover */
  children: ReactNode;
}

/**
 * Reusable tooltip component for explaining technical terms.
 * Shows on hover with a small arrow pointing to the trigger element.
 */
export function Tooltip({ content, children }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span className="relative inline-flex items-center">
      <span
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        tabIndex={0}
        className="cursor-help border-b border-dotted border-ink-muted"
      >
        {children}
      </span>
      {isVisible && (
        <span
          role="tooltip"
          className="absolute z-50 w-56 p-2.5 text-xs bg-surface-0 border border-strong rounded-lg shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2 text-ink pointer-events-none"
        >
          {content}
          <span className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <span className="block w-2 h-2 bg-surface-0 border-r border-b border-strong transform rotate-45" />
          </span>
        </span>
      )}
    </span>
  );
}
