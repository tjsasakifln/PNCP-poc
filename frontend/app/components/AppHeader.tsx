"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { ThemeToggle } from "./ThemeToggle";
import { MessageBadge } from "./MessageBadge";
import { UserMenu } from "./UserMenu";
import { QuotaBadge } from "./QuotaBadge";
interface AppHeaderProps {
  /** Optional extra items to render before the standard controls */
  extraControls?: ReactNode;
  /** Optional status slot passed into UserMenu (overrides default QuotaBadge) */
  statusSlot?: ReactNode;
}

/**
 * Shared application header for authenticated pages.
 *
 * Provides: Logo, ThemeToggle, MessageBadge, UserMenu with QuotaBadge.
 * Used by the (protected)/layout.tsx route group.
 * Pass a custom statusSlot to add PlanBadge or other widgets.
 */
export function AppHeader({ extraControls, statusSlot }: AppHeaderProps) {
  const defaultStatusSlot = <QuotaBadge />;

  return (
    <header className="sticky top-0 z-40 bg-[var(--surface-0)] border-b border-[var(--border)] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/buscar"
            className="text-xl font-bold text-brand-navy hover:text-brand-blue transition-colors"
          >
            SmartLic<span className="text-brand-blue">.tech</span>
          </Link>
        </div>
        <div className="flex items-center gap-3">
          {extraControls}
          <ThemeToggle />
          <MessageBadge />
          <UserMenu statusSlot={statusSlot ?? defaultStatusSlot} />
        </div>
      </div>
    </header>
  );
}
