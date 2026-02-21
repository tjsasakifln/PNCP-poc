"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export type BackendStatus = "online" | "offline" | "recovering";

/**
 * CRIT-008 AC9: Hook for tracking backend connectivity.
 * Polls /api/health every 30s, only when page is visible.
 */
export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>("online");
  const [isPolling, setIsPolling] = useState(false);
  const recoveryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const previousStatusRef = useRef<BackendStatus>("online");

  const checkHealth = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const res = await fetch("/api/health", { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!res.ok) {
        setStatus("offline");
        return false;
      }

      const data = await res.json();
      const isHealthy = data.backend === "healthy";

      if (isHealthy) {
        // Was offline → now online = recovering
        if (previousStatusRef.current === "offline") {
          setStatus("recovering");
          // Clear any existing recovery timer
          if (recoveryTimerRef.current) clearTimeout(recoveryTimerRef.current);
          recoveryTimerRef.current = setTimeout(() => {
            setStatus("online");
            recoveryTimerRef.current = null;
          }, 3000);
        } else if (previousStatusRef.current !== "recovering") {
          setStatus("online");
        }
        return true;
      } else {
        setStatus("offline");
        return false;
      }
    } catch {
      setStatus("offline");
      return false;
    }
  }, []);

  // Track previous status for offline→online transition detection
  useEffect(() => {
    if (status !== "recovering") {
      previousStatusRef.current = status;
    }
  }, [status]);

  useEffect(() => {
    const POLL_INTERVAL_MS = 30_000;

    const startPolling = () => {
      if (intervalRef.current) return;
      setIsPolling(true);
      // Initial check
      checkHealth();
      intervalRef.current = setInterval(checkHealth, POLL_INTERVAL_MS);
    };

    const stopPolling = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsPolling(false);
    };

    const handleVisibilityChange = () => {
      if (typeof document === "undefined") return;
      if (document.visibilityState === "visible") {
        startPolling();
      } else {
        stopPolling();
      }
    };

    // SSR guard
    if (typeof document === "undefined") return;

    // Start if page is currently visible
    if (document.visibilityState === "visible") {
      startPolling();
    }

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (recoveryTimerRef.current) clearTimeout(recoveryTimerRef.current);
    };
  }, [checkHealth]);

  return { status, isPolling, checkHealth };
}

/**
 * CRIT-008 AC9: Discrete backend connectivity indicator.
 * - Online: nothing visible (default)
 * - Offline: pulsing red dot + tooltip "Servidor reiniciando..."
 * - Recovering: green dot for 3s → disappears
 */
export default function BackendStatusIndicator() {
  const { status } = useBackendStatus();

  if (status === "online") return null;

  return (
    <div className="relative flex items-center" title={
      status === "offline"
        ? "Servidor reiniciando..."
        : "Servidor disponível"
    }>
      <span
        className={`inline-block w-2.5 h-2.5 rounded-full transition-all duration-300 ${
          status === "offline"
            ? "bg-red-500 animate-pulse"
            : "bg-green-500 animate-fade-in-up"
        }`}
        role="status"
        aria-label={status === "offline" ? "Servidor indisponível" : "Servidor recuperado"}
      />
    </div>
  );
}
