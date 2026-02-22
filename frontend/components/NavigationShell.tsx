"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "../app/components/AuthProvider";
import { Sidebar } from "./Sidebar";
import { BottomNav } from "./BottomNav";

/**
 * Routes where the sidebar/bottom nav should appear.
 * Only authenticated (protected) routes get navigation chrome.
 */
const PROTECTED_ROUTES = [
  "/buscar",
  "/dashboard",
  "/pipeline",
  "/historico",
  "/mensagens",
  "/conta",
  "/admin",
];

function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + "/")
  );
}

/**
 * NavigationShell conditionally wraps children with sidebar (desktop)
 * and bottom nav (mobile) based on auth state and current route.
 *
 * - Public pages (/, /login, /signup, /planos, /ajuda): no navigation chrome
 * - Protected pages (/buscar, /dashboard, etc.): sidebar + bottom nav
 */
export function NavigationShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { session, loading } = useAuth();

  const showNav = !loading && !!session && isProtectedRoute(pathname);

  if (!showNav) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        {children}
        <BottomNav />
      </div>
    </div>
  );
}
