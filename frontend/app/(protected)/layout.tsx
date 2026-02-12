"use client";

import { useAuth } from "../components/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppHeader } from "../components/AppHeader";
import { Breadcrumbs } from "../components/Breadcrumbs";

/**
 * Shared layout for all authenticated (protected) pages.
 *
 * Provides:
 * - Auth guard (redirects to / if not logged in)
 * - AppHeader with logo, ThemeToggle, MessageBadge, UserMenu
 * - Consistent max-width content area
 *
 * Pages inside (protected)/ get this shell automatically via Next.js route groups.
 */
export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { session, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !session) {
      router.replace("/");
    }
  }, [loading, session, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--surface-0)]">
        <div className="w-8 h-8 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <>
      <AppHeader />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <Breadcrumbs />
        {children}
      </main>
    </>
  );
}
