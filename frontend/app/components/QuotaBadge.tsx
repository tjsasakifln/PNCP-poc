"use client";

import { useQuota } from "../../hooks/useQuota";
import { useAuth } from "./AuthProvider";
import { getPlanDisplayName } from "../../lib/plans";
import Link from "next/link";

export function QuotaBadge() {
  const { user } = useAuth();
  const { quota, loading } = useQuota();

  // Get user-friendly plan name
  const friendlyPlanName = quota?.planId
    ? getPlanDisplayName(quota.planId, quota.planName ?? undefined)
    : null;

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

  // Admin users - show admin badge
  if (quota.isAdmin) {
    return (
      <span
        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium
                   bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300
                   rounded-full border border-purple-300/30"
        title="Acesso Administrativo"
      >
        <svg
              aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        Admin
      </span>
    );
  }

  // Unlimited users (non-admin) - show plan badge
  if (quota.isUnlimited) {
    return (
      <span
        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium
                   bg-brand-blue-subtle text-brand-navy dark:text-brand-blue
                   rounded-full border border-brand-blue/20"
        title={`Plano ${friendlyPlanName || quota.planName}`}
      >
        <svg
              aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
        {friendlyPlanName || quota.planName}
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
        title="Suas análises acabaram. Clique para ver opções."
      >
        <svg
              aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        0 análises
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
      title={`${quota.creditsRemaining} análise${quota.creditsRemaining === 1 ? "" : "s"} restante${quota.creditsRemaining === 1 ? "" : "s"}`}
    >
      <svg
              aria-hidden="true" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      {quota.creditsRemaining} {quota.isFreeUser ? "análises" : "análises"}
    </span>
  );
}
