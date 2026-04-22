"use client";

import { useEffect, useRef } from "react";
import FocusTrap from "focus-trap-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../app/components/AuthProvider";
import { useTheme } from "../app/components/ThemeProvider";
import { useAnalytics } from "../hooks/useAnalytics";
import {
  Search,
  ClipboardList,
  Bell,
  Clock,
  MessageSquare,
  LayoutDashboard,
  Bookmark,
  User,
  HelpCircle,
  Sun,
  Moon,
  LogOut,
  X,
} from "lucide-react";

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
}

/* -- Icons via lucide-react (w-5 h-5, strokeWidth 1.5) -- */
const ICON_PROPS = { className: "w-5 h-5", strokeWidth: 1.5 } as const;

const icons = {
  search: <Search {...ICON_PROPS} />,
  pipeline: <ClipboardList {...ICON_PROPS} />,
  alerts: <Bell {...ICON_PROPS} />,
  history: <Clock {...ICON_PROPS} />,
  messages: <MessageSquare {...ICON_PROPS} />,
  dashboard: <LayoutDashboard {...ICON_PROPS} />,
  savedSearches: <Bookmark {...ICON_PROPS} />,
  account: <User {...ICON_PROPS} />,
  help: <HelpCircle {...ICON_PROPS} />,
  sun: <Sun {...ICON_PROPS} />,
  moon: <Moon {...ICON_PROPS} />,
  logout: <LogOut {...ICON_PROPS} />,
  close: <X {...ICON_PROPS} />,
};

/* -- Navigation items (SHIP-002 AC9: /mensagens feature-gated) -- */
const PRIMARY_NAV = [
  { href: "/buscar", label: "Buscar", icon: icons.search },
  { href: "/pipeline", label: "Pipeline", icon: icons.pipeline },
  { href: "/historico", label: "Histórico", icon: icons.history },
  { href: "/dashboard", label: "Dashboard", icon: icons.dashboard },
];

const SECONDARY_NAV = [
  { href: "/historico", label: "Buscas Salvas", icon: icons.savedSearches },
  { href: "/conta", label: "Minha Conta", icon: icons.account },
  { href: "/ajuda", label: "Ajuda", icon: icons.help },
];

/**
 * UX-340: Mobile drawer for authenticated area.
 * Replaces cluttered header icons with a clean hamburger -> drawer pattern.
 * Slides from right (200ms), includes user info, nav, theme toggle, sign out.
 */
export function MobileDrawer({ open, onClose }: MobileDrawerProps) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const { resetUser } = useAnalytics();
  const { theme, setTheme } = useTheme();

  // AC7: Close drawer on route change (skip initial render)
  const prevPathnameRef = useRef(pathname);
  useEffect(() => {
    if (prevPathnameRef.current !== pathname && open) {
      onClose();
    }
    prevPathnameRef.current = pathname;
  }, [pathname, open, onClose]);

  // AC6: Close on Escape key
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Lock body scroll while open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  const userEmail = user?.email || "";
  const userName =
    user?.user_metadata?.full_name || userEmail.split("@")[0] || "Usuario";
  const isDark = theme === "dark";

  const isActive = (href: string) => {
    if (href === "/buscar") return pathname === "/buscar";
    return pathname.startsWith(href);
  };

  const handleSignOut = () => {
    resetUser();
    signOut();
    onClose();
  };

  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <FocusTrap
      active={open}
      focusTrapOptions={{
        escapeDeactivates: true,
        onDeactivate: onClose,
        allowOutsideClick: true,
        returnFocusOnDeactivate: true,
        tabbableOptions: { displayCheck: "none" },
      }}
    >
    <div className="lg:hidden fixed inset-0 z-[70]" data-testid="mobile-drawer">
      {/* AC6: Backdrop -- click to close */}
      <div
        className="absolute inset-0 bg-black/40 transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
        data-testid="mobile-drawer-backdrop"
      />

      {/* AC9: Panel -- slide from right, 200ms */}
      {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: animationDuration overrides the CSS animation timing for precise slide-in control */}
      <div
        className="absolute top-0 right-0 bottom-0 w-[280px] max-w-[85vw] bg-[var(--surface-0)] shadow-2xl flex flex-col animate-slide-in-right"
        style={{ animationDuration: "200ms" }}
        role="dialog"
        aria-modal="true"
        aria-label="Menu de navegação"
        data-testid="mobile-drawer-panel"
      >
        {/* AC5: User name + email */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
          <div className="min-w-0 flex-1 mr-2">
            <p
              className="text-sm font-semibold text-[var(--ink)] truncate"
              data-testid="drawer-user-name"
            >
              {userName}
            </p>
            <p
              className="text-xs text-[var(--ink-muted)] truncate"
              data-testid="drawer-user-email"
            >
              {userEmail}
            </p>
          </div>
          {/* AC6 + AC8: Close button >= 44px */}
          <button
            onClick={onClose}
            className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
            aria-label="Fechar menu"
            data-testid="mobile-drawer-close"
          >
            {icons.close}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-2" aria-label="Menu principal">
          {/* Primary nav items */}
          <div className="px-3 space-y-0.5">
            {PRIMARY_NAV.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium min-h-[44px] transition-colors ${
                    active
                      ? "bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)]"
                      : "text-[var(--ink)] hover:bg-[var(--surface-1)]"
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="border-t border-[var(--border)] mx-3 my-2" />

          {/* Secondary nav items (AC3: Buscas Salvas moved here) */}
          <div className="px-3 space-y-0.5">
            {SECONDARY_NAV.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                onClick={onClose}
                className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium min-h-[44px] transition-colors ${
                  isActive(item.href)
                    ? "bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)]"
                    : "text-[var(--ink)] hover:bg-[var(--surface-1)]"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            ))}
          </div>

          <div className="border-t border-[var(--border)] mx-3 my-2" />

          {/* AC2: Theme toggle (moved from header to drawer) */}
          <div className="px-3">
            <button
              onClick={toggleTheme}
              className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium min-h-[44px] w-full text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
              data-testid="drawer-theme-toggle"
            >
              {isDark ? icons.moon : icons.sun}
              <span className="flex-1 text-left">Tema Escuro</span>
              {/* Toggle switch */}
              <div
                className={`w-9 h-5 rounded-full transition-colors relative ${
                  isDark ? "bg-[var(--brand-blue)]" : "bg-[var(--ink-faint)]"
                }`}
              >
                <div
                  className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                    isDark ? "translate-x-4" : "translate-x-0.5"
                  }`}
                />
              </div>
            </button>
          </div>
        </nav>

        {/* Sign out -- pinned to bottom */}
        <div className="border-t border-[var(--border)] px-3 py-3">
          <button
            onClick={handleSignOut}
            className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium min-h-[44px] w-full text-[var(--error)] hover:bg-[var(--surface-1)] transition-colors"
            data-testid="drawer-sign-out"
          >
            {icons.logout}
            <span>Sair</span>
          </button>
        </div>
      </div>
    </div>
    </FocusTrap>
  );
}
