"use client";

import { useAuth } from "./AuthProvider";
import { usePathname } from "next/navigation";

/**
 * STORY-253 AC9-AC11: Banner shown when session expires.
 * Displays a non-dismissable banner with redirect-to-login button.
 * After re-login, user is redirected back to the page they were on.
 */
export function SessionExpiredBanner() {
  const { sessionExpired, user } = useAuth();
  const pathname = usePathname();

  // Only show if user was logged in and session expired
  if (!sessionExpired || !user) return null;

  const loginUrl = `/login?reason=session_expired&redirect=${encodeURIComponent(pathname)}`;

  return (
    <div
      role="alert"
      className="fixed top-0 left-0 right-0 z-[9999] bg-amber-50 border-b-2 border-amber-400 px-4 py-3 shadow-lg"
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <svg
            className="w-5 h-5 text-amber-600 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          <p className="text-sm text-amber-800 font-medium">
            Sua sessao expirou. Faca login novamente para continuar.
          </p>
        </div>
        <a
          href={loginUrl}
          className="inline-flex items-center px-4 py-1.5 bg-amber-600 text-white text-sm font-medium rounded-md hover:bg-amber-700 transition-colors whitespace-nowrap"
        >
          Fazer login
        </a>
      </div>
    </div>
  );
}
