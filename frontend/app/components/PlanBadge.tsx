"use client";

import { useMemo } from "react";
import { getPlanDisplayName, normalizePlanId } from "../../lib/plans";

interface PlanBadgeProps {
  planId: string;  // Accept any plan ID (will be normalized)
  planName: string;
  trialExpiresAt?: string; // ISO timestamp
  onClick?: () => void;
}

/**
 * Plan badge component showing current tier with trial countdown
 * Based on UX design spec in docs/ux/STORY-165-plan-ui-design.md
 */
export function PlanBadge({ planId: rawPlanId, planName, trialExpiresAt, onClick }: PlanBadgeProps) {
  // Normalize plan ID to handle legacy values
  const planId = normalizePlanId(rawPlanId);

  // Get user-friendly display name
  const displayName = useMemo(() => {
    return getPlanDisplayName(rawPlanId, planName);
  }, [rawPlanId, planName]);
  // Calculate days remaining for trial
  const daysRemaining = useMemo(() => {
    if (!trialExpiresAt) return null;

    const expiryDate = new Date(trialExpiresAt);
    const now = new Date();
    const diffTime = expiryDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    return Math.max(0, diffDays);
  }, [trialExpiresAt]);

  // Determine styling based on plan tier
  const badgeStyles = useMemo(() => {
    switch (planId) {
      case "free_trial":
        return "bg-gray-500 text-white border-gray-600";
      case "consultor_agil":
        return "bg-blue-500 text-white border-blue-600";
      case "maquina":
        return "bg-green-500 text-white border-green-600";
      case "sala_guerra":
        return "bg-yellow-500 text-gray-900 border-yellow-600";
      case "smartlic_pro":
        return "bg-brand-navy text-white border-brand-blue";
      default:
        return "bg-gray-500 text-white border-gray-600";
    }
  }, [planId]);

  // Warning state for trial expiring soon (<2 days)
  const isExpiringSoon = daysRemaining !== null && daysRemaining < 2;

  // Plan icon - use text icons instead of emojis for better cross-platform support
  const icon = useMemo(() => {
    if (planId === "free_trial") return "A";  // Avaliação
    if (planId === "consultor_agil") return "C";  // Consultor
    if (planId === "maquina") return "M";  // Maquina
    if (planId === "sala_guerra") return "S";  // Sala de Guerra
    if (planId === "smartlic_pro") return "P";  // Pro
    return "?";
  }, [planId]);

  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium
        border transition-all hover:opacity-90 cursor-pointer
        ${badgeStyles}
        ${isExpiringSoon ? "animate-pulse" : ""}
      `}
      title="Ver planos disponíveis"
      aria-label={`Plano atual: ${displayName}. Clique para ver opções de upgrade`}
    >
      <span aria-hidden="true" className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold">{icon}</span>
      <span>{displayName}</span>

      {/* Trial countdown */}
      {daysRemaining !== null && (
        <span className="text-xs opacity-90">
          ({daysRemaining} dia{daysRemaining === 1 ? "" : "s"} restante{daysRemaining === 1 ? "" : "s"})
        </span>
      )}

      {/* Chevron indicator */}
      <svg
              role="img"
              aria-label="Ícone"
        className="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </button>
  );
}
