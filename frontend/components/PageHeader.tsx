"use client";

import Link from "next/link";
import { ThemeToggle } from "../app/components/ThemeToggle";
import { UserMenu } from "../app/components/UserMenu";
import { QuotaBadge } from "../app/components/QuotaBadge";
import { ReactNode } from "react";

interface PageHeaderProps {
  /** Page title shown on desktop (sidebar has logo) */
  title: string;
  /** Optional extra controls before ThemeToggle */
  extraControls?: ReactNode;
  /** Optional custom status slot for UserMenu */
  statusSlot?: ReactNode;
}

/**
 * Standard page header for all authenticated pages.
 * On desktop: shows page title + controls (sidebar has logo).
 * On mobile: shows logo + controls (bottom nav has navigation).
 *
 * UX-337 AC11-AC13: Consistent header across all internal pages.
 */
export function PageHeader({ title, extraControls, statusSlot }: PageHeaderProps) {
  const defaultStatusSlot = <QuotaBadge />;

  return (
    <header className="sticky top-0 z-40 bg-[var(--surface-0)]/95 backdrop-blur-md border-b border-[var(--border)] shadow-sm">
      <div className="px-4 sm:px-6 flex items-center justify-between h-14">
        <div className="flex items-center gap-3">
          {/* Logo: visible only on mobile where sidebar is hidden */}
          <Link
            href="/buscar"
            className="lg:hidden text-xl font-bold text-[var(--brand-navy)] hover:text-[var(--brand-blue)] transition-colors"
          >
            SmartLic<span className="text-[var(--brand-blue)]">.tech</span>
          </Link>
          {/* Page title: visible on desktop */}
          <h1 className="hidden lg:block text-base font-semibold text-[var(--ink)]">
            {title}
          </h1>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          {extraControls}
          <ThemeToggle />
          <UserMenu statusSlot={statusSlot ?? defaultStatusSlot} />
        </div>
      </div>
    </header>
  );
}
