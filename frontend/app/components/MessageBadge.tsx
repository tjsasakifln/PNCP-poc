"use client";

import Link from "next/link";
import { useAuth } from "./AuthProvider";
import { useUnreadCount } from "../../hooks/useUnreadCount";

export function MessageBadge() {
  const { user } = useAuth();
  const { unreadCount } = useUnreadCount();

  if (!user) return null;

  return (
    <Link
      href="/mensagens"
      className="relative p-2 rounded-full hover:bg-[var(--surface-1)] transition-colors"
      title="Mensagens"
      aria-label={unreadCount > 0 ? `${unreadCount} mensagens não lidas` : "Mensagens"}
    >
      {/* Envelope icon (Heroicons outline style) */}
      <svg
              role="img"
              aria-label="Ícone"
        className="w-5 h-5 text-[var(--ink-secondary)]"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
        />
      </svg>

      {unreadCount > 0 && (
        <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-[var(--error)] rounded-full leading-none">
          {unreadCount > 99 ? "99+" : unreadCount}
        </span>
      )}
    </Link>
  );
}
