"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";
import { User, ShieldCheck, CreditCard, Database, Users } from "lucide-react";
import { PageHeader } from "../../components/PageHeader";
import { ErrorBoundary } from "../../components/ErrorBoundary";

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

const ICON_MAP = {
  "user": User,
  "shield": ShieldCheck,
  "credit-card": CreditCard,
  "database": Database,
  "users": Users,
} as const;

function NavIcon({ icon, className }: { icon: string; className?: string }) {
  const cls = className || "w-5 h-5";
  const Icon = ICON_MAP[icon as keyof typeof ICON_MAP];
  if (!Icon) return null;
  return <Icon className={cls} strokeWidth={1.5} aria-hidden="true" />;
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

          {/* Content area — DEBT-011 FE-030: Suspense boundary + DEBT-105 AC4: Error boundary */}
          <main className="flex-1 min-w-0">
            <ErrorBoundary pageName="conta">
              <Suspense fallback={<div className="space-y-4 animate-pulse"><div className="h-48 bg-[var(--surface-1)] rounded-card" /><div className="h-32 bg-[var(--surface-1)] rounded-card" /></div>}>
                {children}
              </Suspense>
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </div>
  );
}
