"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";
import { PageHeader } from "../../components/PageHeader";

/**
 * DEBT-011 FE-001 AC3: Shared sidebar layout for /conta sub-routes.
 */

const NAV_ITEMS = [
  { href: "/conta/perfil", label: "Perfil", icon: "user" },
  { href: "/conta/seguranca", label: "Seguranca", icon: "shield" },
  { href: "/conta/plano", label: "Acesso", icon: "credit-card" },
  { href: "/conta/dados", label: "Dados e LGPD", icon: "database" },
  { href: "/conta/equipe", label: "Equipe", icon: "users" },
] as const;

function NavIcon({ icon, className }: { icon: string; className?: string }) {
  const cls = className || "w-5 h-5";
  switch (icon) {
    case "user":
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
        </svg>
      );
    case "shield":
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      );
    case "credit-card":
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
        </svg>
      );
    case "database":
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
        </svg>
      );
    case "users":
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      );
    default:
      return null;
  }
}

export default function ContaLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[var(--canvas)]">
      <PageHeader title="Minha Conta" />

      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar navigation */}
          <nav
            className="md:w-56 flex-shrink-0"
            aria-label="Navegacao da conta"
            data-testid="conta-sidebar"
          >
            {/* Mobile: horizontal scroll tabs */}
            <div className="md:hidden flex gap-1 overflow-x-auto pb-2 scrollbar-hide">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                      isActive
                        ? "bg-[var(--brand-navy)] text-white"
                        : "text-[var(--ink-secondary)] hover:bg-[var(--surface-1)]"
                    }`}
                  >
                    <NavIcon icon={item.icon} className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>

            {/* Desktop: vertical sidebar */}
            <div className="hidden md:block space-y-1 sticky top-20">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-[var(--brand-navy)] text-white"
                        : "text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--ink)]"
                    }`}
                  >
                    <NavIcon icon={item.icon} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </nav>

          {/* Content area — DEBT-011 FE-030: Suspense boundary */}
          <main className="flex-1 min-w-0">
            <Suspense fallback={<div className="space-y-4 animate-pulse"><div className="h-48 bg-[var(--surface-1)] rounded-card" /><div className="h-32 bg-[var(--surface-1)] rounded-card" /></div>}>
              {children}
            </Suspense>
          </main>
        </div>
      </div>
    </div>
  );
}
