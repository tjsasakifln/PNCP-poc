"use client";

import { useMemo } from "react";
import Link from "next/link";

interface TrialCountdownProps {
  daysRemaining: number;
  className?: string;
}

/**
 * Color-coded countdown badge for active trial.
 * GTM-010 AC10: Badge showing "X dias restantes no trial"
 * Colors: green (5-7), yellow (3-4), red (1-2)
 */
export function TrialCountdown({ daysRemaining, className = "" }: TrialCountdownProps) {
  const { bgColor, textColor, borderColor, dotColor } = useMemo(() => {
    if (daysRemaining >= 5) {
      return {
        bgColor: "bg-emerald-50 dark:bg-emerald-900/20",
        textColor: "text-emerald-700 dark:text-emerald-300",
        borderColor: "border-emerald-200 dark:border-emerald-800",
        dotColor: "bg-emerald-500",
      };
    }
    if (daysRemaining >= 3) {
      return {
        bgColor: "bg-amber-50 dark:bg-amber-900/20",
        textColor: "text-amber-700 dark:text-amber-300",
        borderColor: "border-amber-200 dark:border-amber-800",
        dotColor: "bg-amber-500",
      };
    }
    return {
      bgColor: "bg-red-50 dark:bg-red-900/20",
      textColor: "text-red-700 dark:text-red-300",
      borderColor: "border-red-200 dark:border-red-800",
      dotColor: "bg-red-500",
    };
  }, [daysRemaining]);

  if (daysRemaining <= 0) return null;

  return (
    <Link
      href="/planos"
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
        border transition-all hover:opacity-80
        ${bgColor} ${textColor} ${borderColor}
        ${className}
      `}
      title="Ver níveis de compromisso"
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor} ${daysRemaining <= 2 ? "animate-pulse" : ""}`} />
      {daysRemaining} dia{daysRemaining === 1 ? "" : "s"} restante{daysRemaining === 1 ? "" : "s"}
    </Link>
  );
}
