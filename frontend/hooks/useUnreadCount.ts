"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../app/components/AuthProvider";
import { fetchWithAuth } from "../lib/fetchWithAuth";

interface UseUnreadCountReturn {
  unreadCount: number;
  loading: boolean;
  refresh: () => Promise<void>;
}

const POLL_INTERVAL_MS = 60_000; // 60 seconds

export function useUnreadCount(): UseUnreadCountReturn {
  const { user } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchCount = useCallback(async () => {
    if (!user) {
      setUnreadCount(0);
      return;
    }

    setLoading(true);
    try {
      // STORY-253 AC6: Use fetchWithAuth instead of plain fetch
      // fetchWithAuth automatically handles 401 → refresh → retry
      const res = await fetchWithAuth("/api/messages/unread-count");
      if (res.ok) {
        const data = await res.json();
        setUnreadCount(data.unread_count ?? 0);
      }
    } catch {
      // Network error — badge stays at previous count
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchCount();

    intervalRef.current = setInterval(fetchCount, POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchCount]);

  return { unreadCount, loading, refresh: fetchCount };
}
