"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../app/components/AuthProvider";

interface BottomNavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

// Compact SVG icons (20x20)
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
  more: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM12.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0ZM18.75 12a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z" />
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

const MAIN_ITEMS: BottomNavItem[] = [
  { href: "/buscar", label: "Buscar", icon: icons.search },
  { href: "/pipeline", label: "Pipeline", icon: icons.pipeline },
  { href: "/historico", label: "Historico", icon: icons.history },
  { href: "/mensagens", label: "Msg", icon: icons.messages },
];

const DRAWER_ITEMS: { href: string; label: string; icon: React.ReactNode }[] = [
  { href: "/dashboard", label: "Dashboard", icon: icons.search },
  { href: "/conta", label: "Minha Conta", icon: icons.account },
  { href: "/ajuda", label: "Ajuda", icon: icons.help },
];

export function BottomNav() {
  const pathname = usePathname();
  const { signOut } = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/buscar") return pathname === "/buscar";
    return pathname.startsWith(href);
  };

  // Check if "Mais" should be highlighted (any drawer route is active)
  const moreActive = DRAWER_ITEMS.some((item) => isActive(item.href));

  const closeDrawer = useCallback(() => setDrawerOpen(false), []);

  return (
    <>
      {/* Bottom Navigation Bar */}
      <nav
        data-testid="bottom-nav"
        className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[var(--surface-0)] border-t border-[var(--border)] shadow-[0_-2px_10px_rgba(0,0,0,0.05)]"
        aria-label="Navegacao mobile"
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
                  min-w-[44px] min-h-[44px] px-2 py-1 rounded-lg
                  transition-colors text-center
                  ${active
                    ? "text-[var(--brand-blue)]"
                    : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }
                `}
                aria-current={active ? "page" : undefined}
              >
                {item.icon}
                <span className="text-[10px] font-medium leading-tight">{item.label}</span>
              </Link>
            );
          })}

          {/* "Mais" button */}
          <button
            onClick={() => setDrawerOpen(true)}
            data-testid="bottom-nav-more"
            className={`
              flex flex-col items-center justify-center gap-0.5
              min-w-[44px] min-h-[44px] px-2 py-1 rounded-lg
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
        <div className="lg:hidden fixed inset-0 z-[60]" data-testid="bottom-nav-drawer">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40 transition-opacity"
            onClick={closeDrawer}
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <div className="absolute bottom-0 left-0 right-0 bg-[var(--surface-0)] rounded-t-2xl shadow-2xl animate-slide-up">
            {/* Handle */}
            <div className="flex justify-center py-3">
              <div className="w-10 h-1 rounded-full bg-[var(--ink-faint)]" />
            </div>

            {/* Drawer Items */}
            <div className="px-4 pb-6 space-y-1">
              {DRAWER_ITEMS.map((item) => {
                const active = isActive(item.href);
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
                    {item.icon}
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
