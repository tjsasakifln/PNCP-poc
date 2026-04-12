"use client";

/**
 * STORY-449: ReferralToast
 *
 * Appears bottom-right after a successful search with ≥3 results.
 * Smart throttling: 1× per session (sessionStorage) + 1× per 7 days (localStorage).
 * Auto-closes after 8 s. Click → /indicar with Mixpanel tracking.
 */

import { useEffect, useRef } from "react";
import Link from "next/link";

const SESSION_KEY = "referral_shown_session";
const LS_KEY = "smartlic_referral_shown_at";
const THROTTLE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days
const AUTO_CLOSE_MS = 8_000;

interface ReferralToastProps {
  onClose: () => void;
  onTrack?: (event: string) => void;
}

export function ReferralToast({ onClose, onTrack }: ReferralToastProps) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Mark as shown
    if (typeof window !== "undefined") {
      sessionStorage.setItem(SESSION_KEY, "1");
      localStorage.setItem(LS_KEY, String(Date.now()));
    }
    onTrack?.("referral_prompt_shown");

    // Auto-close after 8 s
    timerRef.current = setTimeout(() => {
      onTrack?.("referral_prompt_dismissed");
      onClose();
    }, AUTO_CLOSE_MS);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleDismiss() {
    if (timerRef.current) clearTimeout(timerRef.current);
    onTrack?.("referral_prompt_dismissed");
    if (typeof window !== "undefined") {
      localStorage.setItem(LS_KEY, String(Date.now()));
    }
    onClose();
  }

  function handleClick() {
    if (timerRef.current) clearTimeout(timerRef.current);
    onTrack?.("referral_prompt_clicked");
    if (typeof window !== "undefined") {
      localStorage.setItem(LS_KEY, String(Date.now()));
    }
    onClose();
  }

  return (
    <div
      className="fixed bottom-6 right-4 z-50 max-w-xs w-full sm:w-80 bg-white dark:bg-surface-1 border border-border rounded-xl shadow-lg p-4 flex items-start gap-3 animate-fade-in-up"
      role="status"
      aria-live="polite"
      data-testid="referral-toast"
    >
      {/* Icon */}
      <div className="shrink-0 w-8 h-8 rounded-full bg-brand-blue-subtle flex items-center justify-center">
        <svg
          className="w-4 h-4 text-brand-navy"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-ink leading-snug">
          Encontrou boas oportunidades?{" "}
          <Link
            href="/indicar"
            onClick={handleClick}
            className="font-semibold text-brand-navy dark:text-brand-blue hover:underline"
            data-testid="referral-toast-link"
          >
            Indique um amigo e ganhe 1 mês grátis →
          </Link>
        </p>
      </div>

      {/* Dismiss */}
      <button
        type="button"
        onClick={handleDismiss}
        className="shrink-0 text-ink-muted hover:text-ink transition-colors"
        aria-label="Fechar"
        data-testid="referral-toast-dismiss"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}

/**
 * Check whether the toast should be shown.
 * Returns false if shown in this session or within the last 7 days.
 */
export function shouldShowReferralToast(): boolean {
  if (typeof window === "undefined") return false;

  if (sessionStorage.getItem(SESSION_KEY)) return false;

  const lastShown = localStorage.getItem(LS_KEY);
  if (lastShown && Date.now() - Number(lastShown) < THROTTLE_MS) return false;

  return true;
}
