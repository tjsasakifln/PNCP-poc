"use client";

import { useEffect, useCallback, useRef } from "react";

/**
 * TD-006 AC9-AC15: Navigation guard for pages with active results.
 *
 * Prevents accidental loss of search results by:
 * 1. Intercepting browser tab close / reload via `beforeunload`
 * 2. Intercepting Next.js client-side navigation via `popstate` and link click interception
 *
 * The guard deactivates when `hasResults` is false or after the user downloads results.
 */
export interface UseNavigationGuardOptions {
  /** Whether there are active results that would be lost on navigation */
  hasResults: boolean;
  /** Whether the user has already downloaded the results (suppresses guard) */
  hasDownloaded: boolean;
  /** Custom warning message */
  message?: string;
}

const DEFAULT_MESSAGE =
  "Você tem resultados de busca que serão perdidos. Deseja sair?";

export function useNavigationGuard({
  hasResults,
  hasDownloaded,
  message = DEFAULT_MESSAGE,
}: UseNavigationGuardOptions) {
  const shouldGuard = hasResults && !hasDownloaded;
  const shouldGuardRef = useRef(shouldGuard);
  shouldGuardRef.current = shouldGuard;
  const messageRef = useRef(message);
  messageRef.current = message;

  // 1. beforeunload — prevents tab close / browser navigation / reload
  useEffect(() => {
    if (!shouldGuard) return;

    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      // Modern browsers ignore custom text but still show the dialog
      e.returnValue = messageRef.current;
      return messageRef.current;
    };

    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [shouldGuard]);

  // 2. Intercept Next.js client-side link clicks
  //    Next.js App Router uses client-side navigation via <Link> which triggers
  //    pushState/replaceState. We intercept anchor clicks before Next.js processes them.
  useEffect(() => {
    if (!shouldGuard) return;

    const handleClick = (e: MouseEvent) => {
      const anchor = (e.target as HTMLElement).closest("a");
      if (!anchor) return;

      // Only intercept internal navigation links (same origin, not download links)
      const href = anchor.getAttribute("href");
      if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) return;
      if (anchor.target === "_blank") return;
      if (anchor.hasAttribute("download")) return;

      // Check if it's an internal link
      try {
        const url = new URL(href, window.location.origin);
        if (url.origin !== window.location.origin) return;
        // Same page navigation is fine
        if (url.pathname === window.location.pathname) return;
      } catch {
        return;
      }

      if (!window.confirm(messageRef.current)) {
        e.preventDefault();
        e.stopPropagation();
      }
    };

    // Use capture phase to intercept before Next.js router
    document.addEventListener("click", handleClick, true);
    return () => document.removeEventListener("click", handleClick, true);
  }, [shouldGuard]);

  // 3. Intercept browser back/forward (popstate)
  useEffect(() => {
    if (!shouldGuard) return;

    // Push a sentinel state so we can detect back navigation
    const sentinel = { __navigationGuard: true };
    window.history.pushState(sentinel, "");

    const handlePopState = (e: PopStateEvent) => {
      if (!shouldGuardRef.current) return;

      if (!window.confirm(messageRef.current)) {
        // User cancelled — push the sentinel state back
        window.history.pushState(sentinel, "");
      }
      // If user confirmed, the popstate proceeds naturally
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
      // Clean up the sentinel state if the guard is deactivated while still on the page
      // Only go back if our sentinel is the current state
      if (
        window.history.state &&
        (window.history.state as any).__navigationGuard
      ) {
        window.history.back();
      }
    };
  }, [shouldGuard]);
}
