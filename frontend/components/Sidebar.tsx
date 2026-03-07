"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../app/components/AuthProvider";
import { usePlan } from "../hooks/usePlan";
import { safeSetItem } from "../lib/storage";
import {
  Search,
  LayoutDashboard,
  ClipboardList,
  Clock,
  User,
  HelpCircle,
  LogOut,
  PanelLeftClose,
  Menu,
} from "lucide-react";

const STORAGE_KEY = "smartlic-sidebar-collapsed";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  badge?: number;
}

const PRIMARY_NAV: NavItem[] = [
  { href: "/buscar", label: "Buscar", icon: <Search className="w-5 h-5" aria-hidden="true" /> },
  { href: "/dashboard", label: "Dashboard", icon: <LayoutDashboard className="w-5 h-5" aria-hidden="true" /> },
  { href: "/pipeline", label: "Pipeline", icon: <ClipboardList className="w-5 h-5" aria-hidden="true" /> },
  // SHIP-002 AC9: Alertas and Mensagens hidden — feature-gated (backend returns 404)
  { href: "/historico", label: "Histórico", icon: <Clock className="w-5 h-5" aria-hidden="true" /> },
];

const SECONDARY_NAV: NavItem[] = [
  { href: "/conta", label: "Minha Conta", icon: <User className="w-5 h-5" aria-hidden="true" /> },
  { href: "/ajuda", label: "Ajuda", icon: <HelpCircle className="w-5 h-5" aria-hidden="true" /> },
];

export function Sidebar() {
  const pathname = usePathname();
  const { signOut } = useAuth();
  const { planInfo } = usePlan();
  const [collapsed, setCollapsed] = useState(false);

  // Load persisted state
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "true") setCollapsed(true);
  }, []);

  const toggleCollapsed = () => {
    const next = !collapsed;
    setCollapsed(next);
    safeSetItem(STORAGE_KEY, String(next));
  };

  const isActive = (href: string) => {
    if (href === "/buscar") return pathname === "/buscar";
    return pathname.startsWith(href);
  };

  // STORY-309 AC14: Show red dot on "Minha Conta" when subscription is past_due
  const isPastDue = planInfo?.subscription_status === "past_due";

  const renderNavItem = (item: NavItem) => {
    const active = isActive(item.href);
    const showPastDueBadge = item.href === "/conta" && isPastDue;
    return (
      <Link
        key={item.href}
        href={item.href}
        title={collapsed ? item.label : undefined}
        aria-label={collapsed ? item.label : undefined}
        className={`
          flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-[background-color] duration-150 ease-in-out relative
          ${active
            ? "bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)] border-l-4 border-[var(--brand-blue)]"
            : "text-[var(--ink-secondary)] hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-[var(--ink)] border-l-4 border-transparent"
          }
          ${collapsed ? "justify-center" : ""}
        `}
        aria-current={active ? "page" : undefined}
      >
        <span className="flex-shrink-0 relative">
          {item.icon}
          {showPastDueBadge && (
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full" data-testid="conta-past-due-badge" />
          )}
        </span>
        {!collapsed && <span>{item.label}</span>}
        {item.badge && item.badge > 0 && (
          <span className={`
            ${collapsed ? "absolute -top-1 -right-1" : "ml-auto"}
            min-w-[20px] h-5 px-1.5 flex items-center justify-center
            rounded-full bg-[var(--error)] text-white text-xs font-bold
          `}>
            {item.badge > 99 ? "99+" : item.badge}
          </span>
        )}
      </Link>
    );
  };

  return (
    <aside
      data-testid="sidebar"
      className={`
        hidden lg:flex flex-col flex-shrink-0
        h-screen sticky top-0
        bg-[var(--surface-0)] border-r border-[var(--border)]
        transition-[width] duration-200 ease-in-out
        ${collapsed ? "w-[56px]" : "w-[200px]"}
      `}
    >
      {/* Logo */}
      <div className={`flex items-center h-16 border-b border-[var(--border)] ${collapsed ? "justify-center px-2" : "px-4"}`}>
        <Link
          href="/buscar"
          className="text-lg font-bold text-[var(--brand-navy)] dark:text-white hover:text-[var(--brand-blue)] transition-colors whitespace-nowrap overflow-hidden"
        >
          {collapsed ? (
            <span className="text-[var(--brand-blue)] text-xl font-bold">S</span>
          ) : (
            <>SmartLic<span className="text-[var(--brand-blue)]">.tech</span></>
          )}
        </Link>
      </div>

      {/* Primary Navigation — SAB-003 AC3: divide-y for dark mode separation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1 divide-y divide-[var(--border)]" aria-label="Navegação principal">
        {PRIMARY_NAV.map(renderNavItem)}
      </nav>

      {/* Divider + Secondary Navigation */}
      <div className="border-t border-[var(--border)] py-3 px-2 space-y-1">
        {SECONDARY_NAV.map(renderNavItem)}

        {/* Sign Out */}
        <button
          onClick={() => signOut()}
          title={collapsed ? "Sair" : undefined}
          aria-label="Sair"
          className={`
            flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors w-full
            text-[var(--ink-secondary)] hover:bg-[var(--surface-1)] hover:text-[var(--error)]
            ${collapsed ? "justify-center" : ""}
          `}
        >
          <span className="flex-shrink-0" aria-hidden="true">
            <LogOut className="w-5 h-5" />
          </span>
          {!collapsed && <span>Sair</span>}
        </button>
      </div>

      {/* Collapse Toggle */}
      <div className="border-t border-[var(--border)] p-2">
        <button
          onClick={toggleCollapsed}
          title={collapsed ? "Expandir menu" : "Recolher menu"}
          aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
          data-testid="sidebar-toggle"
          className="flex items-center justify-center w-full p-2 rounded-lg text-[var(--ink-muted)] hover:bg-[var(--surface-1)] hover:text-[var(--ink)] transition-colors"
        >
          <span aria-hidden="true">
            {collapsed ? <Menu className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
          </span>
        </button>
      </div>
    </aside>
  );
}
