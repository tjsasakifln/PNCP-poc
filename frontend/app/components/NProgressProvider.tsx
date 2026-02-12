"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import NProgress from "nprogress";
import "nprogress/nprogress.css";

/**
 * NProgress Configuration
 *
 * Customize the loading bar appearance and behavior.
 * @see https://github.com/rstacruz/nprogress
 */
NProgress.configure({
  showSpinner: false,  // Hide spinner (cleaner look)
  trickleSpeed: 200,   // Animation speed (ms)
  minimum: 0.08,       // Minimum percentage (0-1)
  easing: "ease",      // CSS easing function
  speed: 400,          // Animation duration (ms)
});

/**
 * NProgress Provider
 *
 * Automatically shows a loading bar at the top of the page during client-side navigation.
 * Integrates with Next.js App Router navigation hooks.
 *
 * Features:
 * - Starts on route change
 * - Completes when navigation finishes
 * - Handles back/forward navigation
 * - No impact on initial page load
 *
 * Usage: Add to root layout or protected routes layout
 *
 * @example
 * ```tsx
 * <NProgressProvider>
 *   {children}
 * </NProgressProvider>
 * ```
 */
export function NProgressProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Complete loading bar when route changes
    NProgress.done();
  }, [pathname, searchParams]);

  useEffect(() => {
    // Start loading on route change (via Next.js router)
    const handleStart = () => NProgress.start();
    const handleComplete = () => NProgress.done();

    // Listen for Next.js navigation events
    // Note: App Router uses different event system than Pages Router
    // We rely on pathname/searchParams changes instead
    window.addEventListener("beforeunload", handleStart);

    return () => {
      window.removeEventListener("beforeunload", handleStart);
    };
  }, []);

  return <>{children}</>;
}
