"use client";

import { useQuota } from "../../hooks/useQuota";
import { useAuth } from "./AuthProvider";
import Link from "next/link";

export function QuotaBadge() {
  const { user } = useAuth();
  const { quota, loading } = useQuota();

  // Don't show if not logged in
  if (!user) return null;

  // Don't show while loading
  if (loading) {
    return (
      <div className="h-6 w-20 bg-surface-1 animate-pulse rounded-full" />
    );
  }

  // Don't show if no quota info
  if (!quota) return null;

  // Unlimited users - show plan badge
  if (quota.isUnlimited) {
    return (
      <span
        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium
                   bg-brand-blue-subtle text-brand-navy dark:text-brand-blue
                   rounded-full border border-brand-blue/20"
        title={`Plano ${quota.planName}`}
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
        {quota.planName}
      </span>
    );
  }

  // Credit-based users - show remaining count
  const isLow = (quota.creditsRemaining || 0) <= 1;
  const isEmpty = (quota.creditsRemaining || 0) === 0;

  if (isEmpty) {
    return (
      <Link
        href="/planos"
        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium
                   bg-error-subtle text-error rounded-full border border-error/20
                   hover:bg-error/10 transition-colors"
        title="Suas buscas acabaram. Clique para ver planos."
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        0 buscas
      </Link>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium
                  rounded-full border transition-colors
                  ${isLow
                    ? "bg-warning-subtle text-warning border-warning/20"
                    : "bg-surface-1 text-ink-secondary border-border"
                  }`}
      title={`${quota.creditsRemaining} busca${quota.creditsRemaining === 1 ? "" : "s"} restante${quota.creditsRemaining === 1 ? "" : "s"}`}
    >
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      {quota.creditsRemaining} {quota.isFreeUser ? "gratis" : "buscas"}
    </span>
  );
}
