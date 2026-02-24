"use client";

import React from "react";

interface ProfileProgressBarProps {
  /** Completion percentage, 0–100 */
  percentage: number;
  /** Called when user clicks to open the next question */
  onClickNext?: () => void;
  /** Size in pixels (SVG will be square). Defaults to 64. */
  size?: number;
}

/**
 * STORY-260: Circular SVG progress indicator for profile completion.
 * Red (<40%), Yellow (40-69%), Green (>=70%).
 * Clickable — opens the next profile question.
 */
export default function ProfileProgressBar({
  percentage,
  onClickNext,
  size = 64,
}: ProfileProgressBarProps) {
  const pct = Math.min(100, Math.max(0, Math.round(percentage)));
  const radius = (size - 8) / 2; // 4px stroke half on each side
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  let strokeColor: string;
  let textColor: string;
  let ariaLabel: string;

  if (pct >= 70) {
    strokeColor = "#10b981"; // emerald-500
    textColor = "text-emerald-600 dark:text-emerald-400";
    ariaLabel = `Perfil ${pct}% completo — excelente`;
  } else if (pct >= 40) {
    strokeColor = "#f59e0b"; // amber-500
    textColor = "text-amber-600 dark:text-amber-400";
    ariaLabel = `Perfil ${pct}% completo — em progresso`;
  } else {
    strokeColor = "#ef4444"; // red-500
    textColor = "text-red-600 dark:text-red-400";
    ariaLabel = `Perfil ${pct}% completo — incompleto`;
  }

  const element = (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
        aria-hidden="true"
      >
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={4}
          className="text-slate-200 dark:text-slate-700"
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={4}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      {/* Percentage text in center */}
      <span
        className={`absolute text-xs font-bold ${textColor}`}
        style={{ fontSize: size < 56 ? 10 : 12 }}
      >
        {pct}%
      </span>
    </div>
  );

  if (onClickNext) {
    return (
      <button
        onClick={onClickNext}
        aria-label={`${ariaLabel}. Clique para completar seu perfil.`}
        className="rounded-full focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)] focus:ring-offset-2 hover:opacity-80 transition-opacity"
        data-testid="profile-progress-bar"
      >
        {element}
      </button>
    );
  }

  return (
    <div
      aria-label={ariaLabel}
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      data-testid="profile-progress-bar"
    >
      {element}
    </div>
  );
}
