"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";

interface BreadcrumbItem {
  label: string;
  href: string;
}

/**
 * Breadcrumb navigation component for protected pages
 *
 * Displays navigation trail showing the current page hierarchy
 * and allows users to navigate back to previous levels.
 */
export function Breadcrumbs() {
  const pathname = usePathname();

  // Map pathnames to readable labels
  const pathMap: Record<string, string> = {
    "/buscar": "Busca",
    "/historico": "Histórico",
    "/conta": "Minha Conta",
    "/dashboard": "Dashboard",
    "/admin": "Admin",
    "/mensagens": "Mensagens",
    "/planos": "Planos",
    "/planos/obrigado": "Obrigado",
  };

  // Build breadcrumb trail from pathname
  const buildBreadcrumbs = (): BreadcrumbItem[] => {
    const items: BreadcrumbItem[] = [];
    const segments = pathname.split("/").filter(Boolean);

    let currentPath = "";
    for (const segment of segments) {
      currentPath += `/${segment}`;
      const label = pathMap[currentPath] || segment.charAt(0).toUpperCase() + segment.slice(1);
      items.push({ label, href: currentPath });
    }

    return items;
  };

  const breadcrumbs = buildBreadcrumbs();

  // Don't show breadcrumbs on home/buscar page (top level)
  if (breadcrumbs.length === 0 || (breadcrumbs.length === 1 && breadcrumbs[0].href === "/buscar")) {
    return null;
  }

  return (
    <nav
      aria-label="Breadcrumb"
      className="mb-4 flex items-center gap-2 text-sm text-ink-secondary"
    >
      {/* Home link */}
      <Link
        href="/buscar"
        className="flex items-center gap-1 hover:text-brand-blue transition-colors"
        aria-label="Voltar para busca"
      >
        <Home className="w-4 h-4" />
        <span className="sr-only">Busca</span>
      </Link>

      {/* Breadcrumb trail */}
      {breadcrumbs.map((item, index) => {
        const isLast = index === breadcrumbs.length - 1;

        return (
          <div key={item.href} className="flex items-center gap-2">
            <ChevronRight className="w-4 h-4" aria-hidden="true" />
            {isLast ? (
              <span className="font-medium text-ink" aria-current="page">
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href}
                className="hover:text-brand-blue transition-colors"
              >
                {item.label}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
