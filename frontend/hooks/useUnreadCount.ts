"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../app/components/AuthProvider";

interface UseUnreadCountReturn {
  unreadCount: number;
  loading: boolean;
  refresh: () => Promise<void>;
}

const POLL_INTERVAL_MS = 60_000; // 60 seconds

export function useUnreadCount(): UseUnreadCountReturn {
  const { session, user } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchCount = useCallback(async () => {
    if (!session?.access_token || !user) {
      setUnreadCount(0);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/messages/unread-count", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUnreadCount(data.unread_count ?? 0);
      }
    } catch {
      // Silently fail — badge just stays at previous count
    } finally {
      setLoading(false);
    }
  }, [session, user]);

  useEffect(() => {
    fetchCount();

    intervalRef.current = setInterval(fetchCount, POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchCount]);

  return { unreadCount, loading, refresh: fetchCount };
}
