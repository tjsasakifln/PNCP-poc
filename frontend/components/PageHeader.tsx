"use client";

import { useState } from "react";
import Link from "next/link";
import { ThemeToggle } from "../app/components/ThemeToggle";
import { UserMenu } from "../app/components/UserMenu";
import { QuotaBadge } from "../app/components/QuotaBadge";
import { MobileDrawer } from "./MobileDrawer";
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
 * On desktop (≥1024px): shows page title + controls (sidebar has logo).
 * On mobile (<1024px): shows logo + hamburger "Menu" button (UX-340).
 *
 * UX-337 AC11-AC13: Consistent header across all internal pages.
 * UX-340 AC1-AC3, AC10-AC11: Simplified mobile header with drawer.
 */
export function PageHeader({ title, extraControls, statusSlot }: PageHeaderProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const defaultStatusSlot = <QuotaBadge />;

  return (
    <>
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

          {/* UX-340 AC1: Mobile — hamburger with "Menu" label */}
          <button
            onClick={() => setDrawerOpen(true)}
            className="lg:hidden flex items-center gap-1.5 min-w-[44px] min-h-[44px] px-3 rounded-lg text-[var(--ink-secondary)] hover:text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
            aria-label="Abrir menu"
            data-testid="mobile-menu-button"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
            <span className="text-sm font-medium">Menu</span>
          </button>

          {/* AC10: Desktop — full controls (unchanged) */}
          <div className="hidden lg:flex items-center gap-2 sm:gap-3">
            {extraControls}
            <ThemeToggle />
            <UserMenu statusSlot={statusSlot ?? defaultStatusSlot} />
          </div>
        </div>
      </header>

      {/* UX-340 AC4: Mobile drawer */}
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  );
}
