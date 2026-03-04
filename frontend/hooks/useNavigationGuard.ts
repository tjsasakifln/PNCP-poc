"use client";

import { useEffect, useRef, useState } from "react";

/**
 * UX-407: Navigation guard — only protects against tab close during active search.
 *
 * - `beforeunload` fires only while loading or within 30s grace period after loading ends.
 * - Internal SmartLic navigation (links, back/forward) is NEVER blocked.
 * - No dependency on download state.
 */
export interface UseNavigationGuardOptions {
  /** Whether a search is currently in progress */
  isLoading: boolean;
}

/** Grace period in ms after loading finishes before guard deactivates */
export const GUARD_GRACE_MS = 30_000;

export function useNavigationGuard({ isLoading }: UseNavigationGuardOptions) {
  const [shouldGuard, setShouldGuard] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const wasLoadingRef = useRef(false);

  useEffect(() => {
    if (isLoading) {
      // Search started — activate guard, cancel any pending deactivation
      wasLoadingRef.current = true;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = undefined;
      }
      setShouldGuard(true);
    } else if (wasLoadingRef.current) {
      // Search just finished — start grace period
      wasLoadingRef.current = false;
      timerRef.current = setTimeout(() => {
        setShouldGuard(false);
        timerRef.current = undefined;
      }, GUARD_GRACE_MS);
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = undefined;
      }
    };
  }, [isLoading]);

  // beforeunload — prevents tab close / browser reload during active search
  useEffect(() => {
    if (!shouldGuard) return;

    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };

    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [shouldGuard]);
}
