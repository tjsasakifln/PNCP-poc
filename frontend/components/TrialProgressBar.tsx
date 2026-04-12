"use client";

import { useMemo } from "react";
import Link from "next/link";
import useSWR from "swr";
import { usePathname } from "next/navigation";
import { useAuth } from "../app/components/AuthProvider";
import { usePlan } from "../hooks/usePlan";
import { useAnalytics } from "../hooks/useAnalytics";

/**
 * STORY-448: Trial Progress Bar
 *
 * Shows a top-of-page banner on all authenticated pages (except excluded paths)
 * indicating the current trial day, search count, and opportunities found.
 * Only visible for active free_trial users.
 */

const EXCLUDED_PATHS = [
  "/",
  "/login",
  "/signup",
  "/onboarding",
  "/pricing",
  "/features",
  "/termos",
  "/privacidade",
];

interface AnalyticsSummary {
  total_searches: number;
  total_opportunities: number;
}

export function TrialProgressBar() {
  const pathname = usePathname();
  const { session } = useAuth();
  const { planInfo } = usePlan();
  const { trackEvent } = useAnalytics();

  // AC1: Check excluded paths
  const isExcluded =
    EXCLUDED_PATHS.includes(pathname ?? "") ||
    (pathname?.startsWith("/auth/") ?? true) ||
    (pathname?.startsWith("/blog") ?? true);

  // AC5: Only show for active free_trial users
  const isTrial =
    planInfo?.plan_id === "free_trial" &&
    planInfo?.subscription_status !== "expired";

  // Calculate trial day from trial_expires_at
  // AC2: X = 14 minus days remaining, min 1, max 14
  const trialDay = useMemo(() => {
    if (!planInfo?.trial_expires_at) return null;
    const expiresAt = new Date(planInfo.trial_expires_at);
    const now = new Date();
    const daysLeft = Math.ceil(
      (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    );
    const day = Math.max(1, Math.min(14, 14 - daysLeft + 1));
    return day;
  }, [planInfo?.trial_expires_at]);

  const shouldFetch = !isExcluded && isTrial && !!session?.access_token;

  const { data } = useSWR<AnalyticsSummary>(
    shouldFetch
      ? [`/api/analytics?endpoint=summary`, session?.access_token]
      : null,
    ([url, tok]: [string, string]) =>
      fetch(url, { headers: { Authorization: `Bearer ${tok}` } }).then((r) =>
        r.json()
      ),
    {
      revalidateOnFocus: false,
      dedupingInterval: 300_000,
      shouldRetryOnError: false,
    }
  );

  // Don't render if excluded path or not a trial user or no trial day
  if (isExcluded || !isTrial || trialDay === null) return null;

  // AC3: Colors by urgency
  const urgencyClass =
    trialDay <= 7
      ? "bg-green-50 text-green-800 border-green-200"
      : trialDay <= 11
      ? "bg-yellow-50 text-yellow-800 border-yellow-200"
      : "bg-red-50 text-red-800 border-red-200";

  // AC2: Text with fallback if analytics data unavailable
  const mainText =
    data != null
      ? `Dia ${trialDay} de 14 — Você já fez ${data.total_searches} buscas e encontrou ${data.total_opportunities} editais.`
      : `Dia ${trialDay} de 14 — Veja os planos antes que expire`;

  // AC7: Mixpanel tracking on CTA click
  const handleCtaClick = () => {
    trackEvent("trial_progress_bar_cta_clicked", { trial_day: trialDay });
  };

  return (
    <div
      className={`w-full border-b px-4 py-2 flex items-center justify-center gap-3 text-sm ${urgencyClass}`}
      data-testid="trial-progress-bar"
    >
      <span>{mainText}</span>
      {/* AC4: CTA link via Next.js router */}
      <Link
        href="/planos"
        onClick={handleCtaClick}
        className="font-semibold underline underline-offset-2 hover:no-underline whitespace-nowrap"
        data-testid="trial-progress-bar-cta"
      >
        Ver Planos →
      </Link>
    </div>
  );
}
