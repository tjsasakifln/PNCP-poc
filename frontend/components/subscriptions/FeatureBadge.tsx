"use client";

import { useState } from "react";

/**
 * FeatureBadge Component
 *
 * Displays feature status badges with tooltips
 * STORY-171 AC16: Coming Soon Badges
 *
 * Features:
 * - Badge types: active, coming_soon, future
 * - Tooltip with launch date for coming_soon
 * - Accessible
 */

export type FeatureStatus = 'active' | 'coming_soon' | 'future';

export interface FeatureBadgeProps {
  status: FeatureStatus;
  launchDate?: string; // e.g., "Março 2026"
  className?: string;
}

export function FeatureBadge({
  status,
  launchDate,
  className = "",
}: FeatureBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const getBadgeConfig = () => {
    switch (status) {
      case 'active':
        return {
          icon: '✅',
          label: 'Ativo',
          bgClass: 'bg-success-subtle',
          borderClass: 'border-success',
          textClass: 'text-success',
        };
      case 'coming_soon':
        return {
          icon: '🚀',
          label: 'Em breve',
          bgClass: 'bg-warning-subtle',
          borderClass: 'border-warning',
          textClass: 'text-warning',
        };
      case 'future':
        return {
          icon: '🔮',
          label: 'Futuro',
          bgClass: 'bg-surface-2',
          borderClass: 'border-strong',
          textClass: 'text-ink-muted',
        };
    }
  };

  const config = getBadgeConfig();
  const hasTooltip = status === 'coming_soon' && launchDate;

  return (
    <div className={`relative inline-block ${className}`}>
      <span
        className={`
          inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
          border ${config.borderClass} ${config.bgClass}
          ${hasTooltip ? 'cursor-help' : ''}
        `}
        onMouseEnter={() => hasTooltip && setShowTooltip(true)}
        onMouseLeave={() => hasTooltip && setShowTooltip(false)}
        onFocus={() => hasTooltip && setShowTooltip(true)}
        onBlur={() => hasTooltip && setShowTooltip(false)}
        tabIndex={hasTooltip ? 0 : undefined}
        role={hasTooltip ? 'button' : undefined}
        aria-label={hasTooltip ? `${config.label} - Previsão: ${launchDate}` : config.label}
      >
        <span aria-hidden="true">{config.icon}</span>
        <span className={`text-xs font-semibold ${config.textClass}`}>
          {config.label}
        </span>
      </span>

      {/* Tooltip */}
      {hasTooltip && showTooltip && (
        <div
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-ink text-white text-xs rounded-card shadow-lg whitespace-nowrap z-50 animate-fade-in"
          role="tooltip"
        >
          Previsão: {launchDate}
          {/* Arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-ink" />
        </div>
      )}
    </div>
  );
}
