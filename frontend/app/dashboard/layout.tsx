"use client";

import { ErrorBoundary } from "../../components/ErrorBoundary";
import ConsultoriaUpsellBanner from "../../components/ConsultoriaUpsellBanner";
import { usePlan } from "../../hooks/usePlan";

/**
 * DEBT-105 AC1: Error boundary wrapping dashboard page.
 * STORY-BIZ-002: Consultoria upsell banner for trial users whose CNAE marks
 * them as a consultancy (70.2 / 74.9 / 82.9).
 */
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { planInfo } = usePlan();
  const isTrialing = planInfo?.subscription_status === "trial";

  return (
    <ErrorBoundary pageName="dashboard">
      <div className="px-4 pt-4">
        <ConsultoriaUpsellBanner isTrialing={Boolean(isTrialing)} />
      </div>
      {children}
    </ErrorBoundary>
  );
}
