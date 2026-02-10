"use client";

import { useMemo } from "react";

interface QuotaCounterProps {
  quotaUsed: number;
  quotaLimit: number;
  resetDate: string; // ISO timestamp
  planId: string;
  onUpgradeClick?: () => void;
}

/**
 * Quota counter component with progress bar and reset date
 * Based on UX design spec in docs/ux/STORY-165-plan-ui-design.md
 */
export function QuotaCounter({
  quotaUsed,
  quotaLimit,
  resetDate,
  planId,
  onUpgradeClick,
}: QuotaCounterProps) {
  // Calculate percentage and color
  const percentage = useMemo(() => {
    if (quotaLimit === 0) return 0;
    return Math.min(100, Math.round((quotaUsed / quotaLimit) * 100));
  }, [quotaUsed, quotaLimit]);

  const progressColor = useMemo(() => {
    if (percentage >= 100) return "bg-red-500";
    if (percentage >= 90) return "bg-orange-500";
    if (percentage >= 70) return "bg-yellow-500";
    return "bg-green-500";
  }, [percentage]);

  // Format reset date
  const formattedResetDate = useMemo(() => {
    const date = new Date(resetDate);
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }, [resetDate]);

  // Check if quota is exhausted
  const isExhausted = quotaUsed >= quotaLimit;

  // Handle unlimited quota (free trial)
  const isUnlimited = quotaLimit >= 999999;

  // Detect free tier (planId "free" or quotaLimit <= 5)
  const isFreeTier = planId === "free" || quotaLimit <= 5;

  if (isUnlimited) {
    return (
      <div className="p-4 bg-surface-1 rounded-card border border-border">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-ink">Buscas ilimitadas</span>
          <span className="text-xs text-ink-muted">Durante o trial</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className="p-4 bg-surface-1 rounded-card border border-border"
      role="status"
      aria-live="polite"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-ink">
          {isFreeTier ? `Buscas gratuitas: ${quotaUsed}/${quotaLimit}` : `Buscas este mês: ${quotaUsed}/${quotaLimit}`}
        </span>
        <span className="text-xs text-ink-muted">
          {isFreeTier ? "Plano gratuito" : `Renovação: ${formattedResetDate}`}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-surface-0 rounded-full h-2 overflow-hidden mb-3">
        <div
          className={`h-full transition-all duration-300 ${progressColor}`}
          style={{ width: `${percentage}%` }}
          aria-label={`${percentage}% do quota utilizado`}
        />
      </div>

      {/* Exhausted state with upgrade CTA */}
      {isExhausted && onUpgradeClick && (
        <div className="mt-3 pt-3 border-t border-border">
          <p className="text-sm text-error mb-2 flex items-center gap-1">
            <span aria-hidden="true">❌</span>
            Suas buscas acabaram ({quotaUsed}/{quotaLimit})
          </p>
          <button
            onClick={onUpgradeClick}
            className="w-full px-4 py-2 bg-brand-navy text-white rounded-button
                       font-medium hover:bg-brand-blue-hover transition-colors"
          >
            Fazer Upgrade →
          </button>
        </div>
      )}

      {/* Warning for approaching limit (70-99%) */}
      {!isExhausted && percentage >= 70 && (
        <p className="text-xs text-warning mt-2">
          ⚠️ Você está próximo do limite mensal
        </p>
      )}
    </div>
  );
}
