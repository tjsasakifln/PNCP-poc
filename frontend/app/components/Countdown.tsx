"use client";

import { useState, useEffect, useMemo } from "react";

/**
 * Countdown Component
 *
 * Shows time remaining until a target date with real-time updates.
 * Displays in different formats based on remaining time:
 * - "X dias" when > 24 hours
 * - "Xh Ymin" when < 24 hours
 * - "Encerra hoje!" when < 12 hours with urgency styling
 * - "Encerrado" when past due
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 */

interface CountdownProps {
  /** Target date/time (ISO string or Date object) */
  targetDate: string | Date;
  /** Label to show before the countdown (default: none) */
  label?: string;
  /** Show icon (default: true) */
  showIcon?: boolean;
  /** Size variant (default: md) */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
  /** Called when countdown reaches zero */
  onExpire?: () => void;
}

interface TimeRemaining {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  total: number; // total milliseconds remaining
  isExpired: boolean;
}

// SVG Icons
function ClockIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function AlertIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

// Size configurations
const SIZE_CLASSES = {
  sm: {
    container: "px-2 py-0.5 text-xs gap-1",
    icon: "w-3 h-3",
  },
  md: {
    container: "px-2.5 py-1 text-sm gap-1.5",
    icon: "w-4 h-4",
  },
  lg: {
    container: "px-3 py-1.5 text-base gap-2",
    icon: "w-5 h-5",
  },
};

function calculateTimeRemaining(targetDate: Date): TimeRemaining {
  const now = new Date();
  const total = targetDate.getTime() - now.getTime();

  if (total <= 0) {
    return {
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      total: 0,
      isExpired: true,
    };
  }

  const days = Math.floor(total / (1000 * 60 * 60 * 24));
  const hours = Math.floor((total % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((total % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((total % (1000 * 60)) / 1000);

  return {
    days,
    hours,
    minutes,
    seconds,
    total,
    isExpired: false,
  };
}

function formatCountdown(time: TimeRemaining): string {
  if (time.isExpired) {
    return "Encerrado";
  }

  // More than 1 day
  if (time.days > 0) {
    if (time.days === 1) {
      return "1 dia";
    }
    return `${time.days} dias`;
  }

  // Less than 24 hours but more than 1 hour
  if (time.hours > 0) {
    if (time.minutes > 0) {
      return `${time.hours}h ${time.minutes}min`;
    }
    return `${time.hours}h`;
  }

  // Less than 1 hour
  if (time.minutes > 0) {
    return `${time.minutes}min`;
  }

  // Less than 1 minute
  return `${time.seconds}s`;
}

export function Countdown({
  targetDate,
  label,
  showIcon = true,
  size = "md",
  className = "",
  onExpire,
}: CountdownProps) {
  const target = useMemo(() => {
    return typeof targetDate === "string" ? new Date(targetDate) : targetDate;
  }, [targetDate]);

  const [timeRemaining, setTimeRemaining] = useState<TimeRemaining>(() =>
    calculateTimeRemaining(target)
  );

  // Update countdown every second when close to expiry, every minute otherwise
  useEffect(() => {
    const updateTime = () => {
      const newTime = calculateTimeRemaining(target);
      setTimeRemaining(newTime);

      if (newTime.isExpired && onExpire) {
        onExpire();
      }
    };

    // Initial update
    updateTime();

    // Determine update interval based on remaining time
    const getInterval = () => {
      const remaining = calculateTimeRemaining(target);
      if (remaining.isExpired) return null;
      if (remaining.total < 60 * 1000) return 1000; // Every second for last minute
      if (remaining.total < 60 * 60 * 1000) return 30 * 1000; // Every 30s for last hour
      return 60 * 1000; // Every minute otherwise
    };

    const interval = getInterval();
    if (interval === null) return;

    const timerId = setInterval(updateTime, interval);

    return () => clearInterval(timerId);
  }, [target, onExpire]);

  const sizeClasses = SIZE_CLASSES[size];
  const formattedTime = formatCountdown(timeRemaining);

  // Determine urgency level for styling
  const isUrgent = !timeRemaining.isExpired && timeRemaining.days === 0 && timeRemaining.hours < 12;
  const isCritical = !timeRemaining.isExpired && timeRemaining.days === 0 && timeRemaining.hours < 3;
  const isExpired = timeRemaining.isExpired;

  // Determine colors and icon based on urgency
  let containerClasses = "";
  let IconComponent = ClockIcon;

  if (isExpired) {
    containerClasses = "bg-surface-2 text-ink-muted border border-strong";
    IconComponent = CheckIcon;
  } else if (isCritical) {
    containerClasses = "bg-error-subtle text-error border border-error/30 animate-pulse";
    IconComponent = AlertIcon;
  } else if (isUrgent) {
    containerClasses = "bg-warning-subtle text-warning border border-warning/30";
    IconComponent = AlertIcon;
  } else {
    containerClasses = "bg-brand-blue-subtle text-brand-navy border border-accent";
    IconComponent = ClockIcon;
  }

  return (
    <span
      className={`
        inline-flex items-center rounded-full font-medium
        ${sizeClasses.container}
        ${containerClasses}
        ${className}
      `}
      role="timer"
      aria-live="polite"
      aria-label={`Tempo restante: ${formattedTime}`}
    >
      {showIcon && <IconComponent className={sizeClasses.icon} />}
      {label && <span className="font-normal">{label}</span>}
      <span className="font-semibold tabular-nums">
        {isUrgent && !isExpired && !isCritical && "Encerra hoje! "}
        {isCritical && !isExpired && "Urgente! "}
        {formattedTime}
      </span>
    </span>
  );
}

/**
 * Static countdown display (no real-time updates)
 * Useful for server-side rendering or when real-time is not needed
 */
export function CountdownStatic({
  targetDate,
  label,
  showIcon = true,
  size = "md",
  className = "",
}: Omit<CountdownProps, "onExpire">) {
  const target = useMemo(() => {
    return typeof targetDate === "string" ? new Date(targetDate) : targetDate;
  }, [targetDate]);

  const timeRemaining = useMemo(() => calculateTimeRemaining(target), [target]);
  const sizeClasses = SIZE_CLASSES[size];
  const formattedTime = formatCountdown(timeRemaining);

  // Same styling logic
  const isUrgent = !timeRemaining.isExpired && timeRemaining.days === 0 && timeRemaining.hours < 12;
  const isCritical = !timeRemaining.isExpired && timeRemaining.days === 0 && timeRemaining.hours < 3;
  const isExpired = timeRemaining.isExpired;

  let containerClasses = "";
  let IconComponent = ClockIcon;

  if (isExpired) {
    containerClasses = "bg-surface-2 text-ink-muted border border-strong";
    IconComponent = CheckIcon;
  } else if (isCritical) {
    containerClasses = "bg-error-subtle text-error border border-error/30";
    IconComponent = AlertIcon;
  } else if (isUrgent) {
    containerClasses = "bg-warning-subtle text-warning border border-warning/30";
    IconComponent = AlertIcon;
  } else {
    containerClasses = "bg-brand-blue-subtle text-brand-navy border border-accent";
    IconComponent = ClockIcon;
  }

  return (
    <span
      className={`
        inline-flex items-center rounded-full font-medium
        ${sizeClasses.container}
        ${containerClasses}
        ${className}
      `}
      aria-label={`Tempo restante: ${formattedTime}`}
    >
      {showIcon && <IconComponent className={sizeClasses.icon} />}
      {label && <span className="font-normal">{label}</span>}
      <span className="font-semibold tabular-nums">
        {isUrgent && !isExpired && !isCritical && "Encerra hoje! "}
        {isCritical && !isExpired && "Urgente! "}
        {formattedTime}
      </span>
    </span>
  );
}

/**
 * Utility: Calculate days until date
 */
export function daysUntil(targetDate: string | Date): number {
  const target = typeof targetDate === "string" ? new Date(targetDate) : targetDate;
  const time = calculateTimeRemaining(target);
  return time.isExpired ? 0 : time.days + (time.hours > 0 || time.minutes > 0 ? 1 : 0);
}

export { calculateTimeRemaining, formatCountdown };
