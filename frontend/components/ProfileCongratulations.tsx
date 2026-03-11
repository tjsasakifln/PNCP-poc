"use client";

import { useState, useEffect } from "react";
import { safeSetItem, safeGetItem } from "../lib/storage";

const DISMISSED_KEY = "profile_congratulations_dismissed";

function isDismissed(): boolean {
  return safeGetItem(DISMISSED_KEY) === "true";
}

function setDismissed(): void {
  if (typeof window === "undefined") return;
  try {
    safeSetItem(DISMISSED_KEY, "true");
  } catch {
    // localStorage unavailable — silently fail
  }
}

interface ConfettiDotProps {
  x: number;
  y: number;
  color: string;
  delay: number;
  size: number;
}

function ConfettiDot({ x, y, color, delay, size }: ConfettiDotProps) {
  return (
    <div
      className="absolute rounded-full pointer-events-none"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        width: size,
        height: size,
        backgroundColor: color,
        animation: `confetti-dot 2s ${delay}s ease-out forwards`,
      }}
    />
  );
}

const CONFETTI_COLORS = [
  "var(--success, #10b981)",
  "var(--warning, #f59e0b)",
  "var(--brand-blue, #3b82f6)",
  "var(--ring, #8b5cf6)",
  "var(--error, #ef4444)",
  "#06b6d4",
];

const CONFETTI_DOTS: ConfettiDotProps[] = Array.from({ length: 18 }, (_, i) => ({
  x: 5 + (i * 5.5) % 90,
  y: 20 + (i * 17) % 60,
  color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
  delay: (i * 0.1) % 0.8,
  size: 4 + (i % 3) * 2,
}));

/**
 * STORY-260: Congratulations card shown when profile is 100% complete.
 * Includes subtle confetti animation via CSS @keyframes (2s).
 * Dismissible — stores dismissed state in localStorage.
 */
export default function ProfileCongratulations() {
  const [visible, setVisible] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);

  // Check localStorage on mount to avoid SSR mismatch
  useEffect(() => {
    if (!isDismissed()) {
      setVisible(true);
      // Trigger confetti after card animates in
      const t = setTimeout(() => setShowConfetti(true), 300);
      return () => clearTimeout(t);
    }
  }, []);

  // Stop confetti after 2s
  useEffect(() => {
    if (!showConfetti) return;
    const t = setTimeout(() => setShowConfetti(false), 2500);
    return () => clearTimeout(t);
  }, [showConfetti]);

  const handleDismiss = () => {
    setDismissed();
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      className="animate-fade-in-up relative overflow-hidden rounded-2xl border border-emerald-200 dark:border-emerald-700 bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-900/30 dark:to-[var(--surface-0)] shadow-sm p-6"
      data-testid="profile-congratulations"
      role="status"
      aria-live="polite"
    >
      {/* Confetti */}
      {showConfetti && (
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          {CONFETTI_DOTS.map((dot, i) => (
            <ConfettiDot key={i} {...dot} />
          ))}
        </div>
      )}

      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        className="absolute top-3 right-3 p-1.5 rounded-full text-emerald-400 hover:text-emerald-700 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors"
        aria-label="Fechar mensagem de parabéns"
        data-testid="dismiss-congratulations"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>

      {/* Content */}
      <div className="flex items-start gap-4">
        {/* Shield/check icon */}
        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-800/40 flex items-center justify-center">
          <svg
            className="w-6 h-6 text-emerald-600 dark:text-emerald-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        </div>

        <div className="flex-1 min-w-0 pr-8">
          {/* Badge */}
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-800/40 dark:text-emerald-300 mb-2">
            <svg
              className="w-3 h-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M5 13l4 4L19 7"
              />
            </svg>
            Perfil Completo
          </span>

          <h3 className="text-base font-semibold text-emerald-800 dark:text-emerald-200">
            Perfil completo!
          </h3>
          <p className="text-sm text-emerald-700 dark:text-emerald-300 mt-0.5 leading-relaxed">
            Suas análises agora são as mais precisas possíveis. O SmartLic usará seu perfil para encontrar as melhores oportunidades para você.
          </p>
        </div>
      </div>
    </div>
  );
}
