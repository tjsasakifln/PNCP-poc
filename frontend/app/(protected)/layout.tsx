"use client";

import { useAuth } from "../components/AuthProvider";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { AppHeader } from "../components/AppHeader";
import { Breadcrumbs } from "../components/Breadcrumbs";

/**
 * Shared layout for all authenticated (protected) pages.
 *
 * Provides:
 * - Auth guard (redirects to / if not logged in)
 * - STORY-247 AC11: Redirects first-time users to /onboarding
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
  const pathname = usePathname();
  const onboardingCheckRef = useRef(false);

  useEffect(() => {
    if (!loading && !session) {
      router.replace("/");
    }
  }, [loading, session, router]);

  // STORY-247 AC11: Redirect to onboarding if context_data is empty (first login)
  useEffect(() => {
    if (loading || !session?.access_token || onboardingCheckRef.current) return;
    onboardingCheckRef.current = true;

    // Skip check if already completed or if user is visiting non-search pages
    const completed = typeof window !== 'undefined' && localStorage.getItem("smartlic-onboarding-completed") === "true";
    if (completed) return;

    // Only redirect from /buscar (the main landing after login)
    if (pathname !== "/buscar") return;

    // Check profile context from backend
    fetch("/api/profile-context", {
      headers: { Authorization: `Bearer ${session.access_token}` },
    })
      .then((r) => r.json())
      .then((res) => {
        if (res.completed) {
          // Cache the context and mark as completed
          localStorage.setItem("smartlic-onboarding-completed", "true");
          if (res.context_data && Object.keys(res.context_data).length > 0) {
            localStorage.setItem("smartlic-profile-context", JSON.stringify(res.context_data));
          }
        } else {
          // First time user — redirect to onboarding
          router.push("/onboarding");
        }
      })
      .catch(() => {
        // On error, don't block — let user use the app normally
      });
  }, [loading, session, pathname, router]);

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
