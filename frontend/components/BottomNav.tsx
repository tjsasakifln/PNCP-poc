"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../app/components/AuthProvider";
import { usePlan } from "../hooks/usePlan";
import {
  Search,
  LayoutDashboard,
  Layers,
  Clock,
  MessageSquare,
  MoreHorizontal,
  Bell,
  User,
  HelpCircle,
  LogOut,
  X,
} from "lucide-react";

interface BottomNavItem {
  href: string;
  label: string;
  ariaLabel?: string;
  icon: React.ReactNode;
}

// Compact icons (20x20 = size 20, strokeWidth 1.5)
const icons = {
  search: <Search className="w-5 h-5" strokeWidth={1.5} />,
  dashboard: <LayoutDashboard className="w-5 h-5" strokeWidth={1.5} />,
  pipeline: <Layers className="w-5 h-5" strokeWidth={1.5} />,
  history: <Clock className="w-5 h-5" strokeWidth={1.5} />,
  messages: <MessageSquare className="w-5 h-5" strokeWidth={1.5} />,
  more: <MoreHorizontal className="w-5 h-5" strokeWidth={1.5} />,
  alerts: <Bell className="w-5 h-5" strokeWidth={1.5} />,
  account: <User className="w-5 h-5" strokeWidth={1.5} />,
  help: <HelpCircle className="w-5 h-5" strokeWidth={1.5} />,
  logout: <LogOut className="w-5 h-5" strokeWidth={1.5} />,
  close: <X className="w-5 h-5" strokeWidth={1.5} />,
};

// SAB-012 AC8: Abbreviated labels for 375px viewport fit
// SHIP-002 AC9: Mensagens hidden — feature-gated
const MAIN_ITEMS: BottomNavItem[] = [
  { href: "/buscar", label: "Busca", icon: icons.search },
  { href: "/pipeline", label: "Pipeline", icon: icons.pipeline },
  { href: "/historico", label: "Hist.", ariaLabel: "Histórico", icon: icons.history },
  { href: "/dashboard", label: "Dash", ariaLabel: "Dashboard", icon: icons.dashboard },
];

// SHIP-002 AC9: Alertas hidden — feature-gated
const DRAWER_ITEMS: { href: string; label: string; icon: React.ReactNode }[] = [
  // { href: "/alertas", label: "Alertas", icon: icons.alerts },
  { href: "/conta", label: "Minha Conta", icon: icons.account },
  { href: "/ajuda", label: "Ajuda", icon: icons.help },
];

const FOCUSABLE_SELECTOR = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function BottomNav() {
  const pathname = usePathname();
  const { signOut } = useAuth();
  const { planInfo } = usePlan();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const isActive = (href: string) => {
    if (href === "/buscar") return pathname === "/buscar";
    return pathname.startsWith(href);
  };

  // Check if "Mais" should be highlighted (any drawer route is active)
  const moreActive = DRAWER_ITEMS.some((item) => isActive(item.href));

  // STORY-309 AC14: Red dot on "Minha Conta" when subscription is past_due
  const isPastDue = planInfo?.subscription_status === "past_due";

  const closeDrawer = useCallback(() => {
    setDrawerOpen(false);
  }, []);

  // STORY-267 AC17: Return focus to trigger button after closing
  useEffect(() => {
    if (!drawerOpen) {
      triggerRef.current?.focus();
    }
  }, [drawerOpen]);

  // STORY-267 AC15-16: Focus trap + Escape to close
  useEffect(() => {
    if (!drawerOpen) return;

    const drawer = drawerRef.current;
    if (!drawer) return;

    // Focus first focusable element in drawer
    const focusableElements = drawer.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      // AC16: Escape closes drawer
      if (e.key === "Escape") {
        e.preventDefault();
        closeDrawer();
        return;
      }

      // AC15: Trap Tab within drawer
      if (e.key === "Tab") {
        const focusable = drawer.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [drawerOpen, closeDrawer]);

  return (
    <>
      {/* Bottom Navigation Bar */}
      <nav
        data-testid="bottom-nav"
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[var(--surface-0)] border-t border-[var(--border)] shadow-[0_-2px_10px_rgba(0,0,0,0.05)]"
        aria-label="Navegação mobile"
      >
        <div className="flex items-center justify-around h-16 px-1">
          {MAIN_ITEMS.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex flex-col items-center justify-center gap-0.5
                  min-w-[44px] min-h-[44px] px-1 py-1 rounded-lg
                  transition-colors text-center
                  ${active
                    ? "text-[var(--brand-blue)]"
                    : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }
                `}
                aria-current={active ? "page" : undefined}
                aria-label={item.ariaLabel || item.label}
              >
                {item.icon}
                <span className="text-[10px] font-medium leading-tight truncate max-w-[56px]">{item.label}</span>
              </Link>
            );
          })}

          {/* "Mais" button */}
          <button
            ref={triggerRef}
            onClick={() => setDrawerOpen(true)}
            data-testid="bottom-nav-more"
            className={`
              flex flex-col items-center justify-center gap-0.5
              min-w-[44px] min-h-[44px] px-1 py-1 rounded-lg
              transition-colors text-center
              ${moreActive
                ? "text-[var(--brand-blue)]"
                : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
              }
            `}
          >
            {icons.more}
            <span className="text-[10px] font-medium leading-tight">Mais</span>
          </button>
        </div>
      </nav>

      {/* Drawer Overlay */}
      {drawerOpen && (
        <div
          className="lg:hidden fixed inset-0 z-[60]"
          data-testid="bottom-nav-drawer"
          role="dialog"
          aria-modal="true"
          aria-label="Menu adicional"
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40 transition-opacity"
            onClick={closeDrawer}
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <div
            ref={drawerRef}
            className="absolute bottom-0 left-0 right-0 bg-[var(--surface-0)] rounded-t-2xl shadow-2xl animate-slide-up"
          >
            {/* Handle */}
            <div className="flex justify-center py-3">
              <div className="w-10 h-1 rounded-full bg-[var(--ink-faint)]" />
            </div>

            {/* Drawer Items */}
            <div className="px-4 pb-6 space-y-1">
              {DRAWER_ITEMS.map((item) => {
                const active = isActive(item.href);
                const showPastDueBadge = item.href === "/conta" && isPastDue;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={closeDrawer}
                    className={`
                      flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium transition-colors
                      ${active
                        ? "bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)]"
                        : "text-[var(--ink)] hover:bg-[var(--surface-1)]"
                      }
                    `}
                  >
                    <span className="relative">
                      {item.icon}
                      {showPastDueBadge && (
                        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full" data-testid="conta-past-due-badge-mobile" />
                      )}
                    </span>
                    <span>{item.label}</span>
                  </Link>
                );
              })}

              <div className="border-t border-[var(--border)] my-2" />

              <button
                onClick={() => { signOut(); closeDrawer(); }}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-base font-medium text-[var(--error)] hover:bg-[var(--surface-1)] transition-colors w-full"
              >
                {icons.logout}
                <span>Sair</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Spacer to prevent content from being hidden behind bottom nav */}
      <div className="lg:hidden h-16" aria-hidden="true" />
    </>
  );
}
