"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../app/components/AuthProvider";
import { useTheme } from "../app/components/ThemeProvider";
import { useAnalytics } from "../hooks/useAnalytics";

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
}

/* ── SVG icons (20×20, strokeWidth 1.5) ── */
const icons = {
  search: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  ),
  pipeline: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15a2.25 2.25 0 0 1 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />
    </svg>
  ),
  history: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  ),
  messages: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
    </svg>
  ),
  dashboard: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  ),
  savedSearches: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0Z" />
    </svg>
  ),
  account: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
    </svg>
  ),
  help: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
    </svg>
  ),
  sun: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
    </svg>
  ),
  moon: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
    </svg>
  ),
  logout: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 9V5.25A2.25 2.25 0 0 1 10.5 3h6a2.25 2.25 0 0 1 2.25 2.25v13.5A2.25 2.25 0 0 1 16.5 21h-6a2.25 2.25 0 0 1-2.25-2.25V15m-3 0-3-3m0 0 3-3m-3 3H15" />
    </svg>
  ),
  close: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  ),
};

/* ── Navigation items ── */
const PRIMARY_NAV = [
  { href: "/buscar", label: "Buscar", icon: icons.search },
  { href: "/pipeline", label: "Pipeline", icon: icons.pipeline },
  { href: "/historico", label: "Historico", icon: icons.history },
  { href: "/mensagens", label: "Mensagens", icon: icons.messages },
  { href: "/dashboard", label: "Dashboard", icon: icons.dashboard },
];

const SECONDARY_NAV = [
  { href: "/historico", label: "Buscas Salvas", icon: icons.savedSearches },
  { href: "/conta", label: "Minha Conta", icon: icons.account },
  { href: "/ajuda", label: "Ajuda", icon: icons.help },
];

/**
 * UX-340: Mobile drawer for authenticated area.
 * Replaces cluttered header icons with a clean hamburger → drawer pattern.
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
    <div className="lg:hidden fixed inset-0 z-[70]" data-testid="mobile-drawer">
      {/* AC6: Backdrop — click to close */}
      <div
        className="absolute inset-0 bg-black/40 transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
        data-testid="mobile-drawer-backdrop"
      />

      {/* AC9: Panel — slide from right, 200ms */}
      <div
        className="absolute top-0 right-0 bottom-0 w-[280px] max-w-[85vw] bg-[var(--surface-0)] shadow-2xl flex flex-col animate-slide-in-right"
        style={{ animationDuration: "200ms" }}
        role="dialog"
        aria-modal="true"
        aria-label="Menu de navegacao"
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
          {/* AC6 + AC8: Close button ≥ 44px */}
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

        {/* Sign out — pinned to bottom */}
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
  );
}
