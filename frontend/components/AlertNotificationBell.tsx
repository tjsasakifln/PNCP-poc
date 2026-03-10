"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "../app/components/AuthProvider";
import Link from "next/link";
import { Bell } from "lucide-react";

/**
 * STORY-315 AC18+AC19: Notification bell icon with badge count and dropdown.
 *
 * Shows unread alert count as a red badge over a bell icon.
 * Clicking opens a dropdown with recent alert notifications.
 * Placed in PageHeader between extraControls and ThemeToggle.
 */
export function AlertNotificationBell() {
  const { session } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [recentAlerts, setRecentAlerts] = useState<
    Array<{ id: string; name: string; total_count: number; run_at: string }>
  >([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch unread alert count
  const fetchNotifications = useCallback(async () => {
    if (!session?.access_token) return;
    try {
      const res = await fetch("/api/alerts", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const alerts = Array.isArray(data) ? data : data.alerts || [];
      const activeCount = alerts.filter(
        (a: { active: boolean }) => a.active,
      ).length;
      setUnreadCount(activeCount > 0 ? activeCount : 0);
      setRecentAlerts(
        alerts.slice(0, 5).map((a: { id: string; name: string; active: boolean }) => ({
          id: a.id,
          name: a.name,
          total_count: 0,
          run_at: "",
        })),
      );
    } catch {
      // silent
    }
  }, [session?.access_token]);

  useEffect(() => {
    fetchNotifications();
    // Refresh every 5 minutes
    const interval = setInterval(fetchNotifications, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  if (!session?.access_token) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell icon button */}
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-lg text-[var(--ink-secondary)] hover:text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
        aria-label={`Notificacoes${unreadCount > 0 ? ` (${unreadCount} alertas ativos)` : ""}`}
        data-testid="notification-bell"
      >
        <Bell className="w-5 h-5" strokeWidth={1.5} />

        {/* AC18: Badge with count */}
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 flex items-center justify-center w-4.5 h-4.5 min-w-[18px] px-1 text-[10px] font-bold text-white bg-[var(--error)] rounded-full animate-pulse"
            data-testid="notification-badge"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* AC19: Dropdown with recent alerts */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-72 bg-[var(--surface-0)] border border-[var(--border)] rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-[var(--border)]">
            <h3 className="text-sm font-semibold text-[var(--ink)]">Alertas</h3>
          </div>

          {recentAlerts.length === 0 ? (
            <div className="px-4 py-6 text-center">
              <p className="text-sm text-[var(--ink-muted)]">Nenhum alerta configurado</p>
            </div>
          ) : (
            <div className="max-h-64 overflow-y-auto">
              {recentAlerts.map((alert) => (
                <Link
                  key={alert.id}
                  href="/alertas"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--surface-1)] transition-colors border-b border-[var(--border)] last:border-b-0"
                >
                  <span className="flex-shrink-0 w-2 h-2 rounded-full bg-[var(--brand-blue)]" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[var(--ink)] truncate">
                      {alert.name}
                    </p>
                    <p className="text-xs text-[var(--ink-muted)]">
                      Alerta ativo
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}

          <div className="px-4 py-2.5 border-t border-[var(--border)] bg-[var(--surface-1)]">
            <Link
              href="/alertas"
              onClick={() => setOpen(false)}
              className="text-sm font-medium text-[var(--brand-blue)] hover:underline"
            >
              Gerenciar todos os alertas
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
