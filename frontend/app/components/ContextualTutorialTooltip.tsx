"use client";

import { useState, useEffect, useCallback } from 'react';

interface ContextualTooltipProps {
  /**
   * Target element selector to attach tooltip to
   */
  target: string;

  /**
   * Message to display
   */
  message: string;

  /**
   * Auto-dismiss after milliseconds (default: 8000ms)
   */
  autoDismiss?: number;

  /**
   * Whether the tooltip is currently active
   */
  isActive: boolean;

  /**
   * Callback when tooltip is dismissed
   */
  onDismiss?: () => void;
}

/**
 * AC13: Contextual Tutorial Tooltip
 *
 * Shows tooltips based on user behavior (not arbitrary timers)
 * Features:
 * - Attaches to specific elements
 * - Auto-dismisses after reading time
 * - Manual dismiss with X button
 * - Calm, non-intrusive styling
 */
export function ContextualTutorialTooltip({
  target,
  message,
  autoDismiss = 8000,
  isActive,
  onDismiss,
}: ContextualTooltipProps) {
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [isVisible, setIsVisible] = useState(false);

  // Calculate position relative to target element
  useEffect(() => {
    if (!isActive) {
      setIsVisible(false);
      return;
    }

    const targetElement = document.querySelector(target);
    if (!targetElement) {
      console.warn(`ContextualTutorialTooltip: Target element "${target}" not found`);
      return;
    }

    const rect = targetElement.getBoundingClientRect();

    // Position tooltip above the target element
    setPosition({
      top: rect.top - 10, // 10px above with arrow space
      left: rect.left + rect.width / 2, // Center horizontally
    });

    setIsVisible(true);

    // Auto-dismiss after specified time
    const timer = setTimeout(() => {
      handleDismiss();
    }, autoDismiss);

    return () => clearTimeout(timer);
  }, [isActive, target, autoDismiss]);

  const handleDismiss = useCallback(() => {
    setIsVisible(false);
    setTimeout(() => {
      onDismiss?.();
    }, 300); // Wait for fade-out animation
  }, [onDismiss]);

  if (!isActive || !isVisible) {
    return null;
  }

  return (
    <>
      {/* Backdrop (subtle, clickable) */}
      <div
        className="fixed inset-0 z-40"
        onClick={handleDismiss}
        aria-hidden="true"
      />

      {/* Tooltip */}
      <div
        className="fixed z-50 animate-fadeIn"
        style={{
          top: `${position.top}px`,
          left: `${position.left}px`,
          transform: 'translate(-50%, -100%)',
        }}
      >
        <div className="relative max-w-xs sm:max-w-sm bg-brand-navy text-white px-4 py-3 rounded-lg shadow-xl border border-brand-blue">
          {/* Message */}
          <p className="text-sm leading-relaxed pr-6">
            {message}
          </p>

          {/* Dismiss button */}
          <button
            onClick={handleDismiss}
            className="absolute top-2 right-2 p-1 text-white/70 hover:text-white transition-colors rounded"
            type="button"
            aria-label="Dispensar dica"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Arrow pointing down to target */}
          <div
            className="absolute left-1/2 -translate-x-1/2 bottom-0 translate-y-full w-0 h-0"
            style={{
              borderLeft: '8px solid transparent',
              borderRight: '8px solid transparent',
              borderTop: '8px solid var(--brand-navy)',
            }}
          />
        </div>
      </div>
    </>
  );
}

/**
 * AC13: Hook for managing contextual tutorial triggers
 *
 * Tracks user behavior and triggers tooltips at the right moments
 */
export function useContextualTutorial() {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);
  const [timeOnPage, setTimeOnPage] = useState(0);
  const [hasSearchedWithoutFilters, setHasSearchedWithoutFilters] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);

  // Track time on page
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeOnPage(prev => prev + 1000);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Load onboarding progress from localStorage
  useEffect(() => {
    const step = parseInt(localStorage.getItem('onboarding_step') || '0', 10);
    setOnboardingStep(step);
  }, []);

  // AC13 Trigger 1: User hesitates (8s without action)
  useEffect(() => {
    if (timeOnPage >= 8000 && onboardingStep === 0 && !activeTooltip) {
      setActiveTooltip('hesitation');
    }
  }, [timeOnPage, onboardingStep, activeTooltip]);

  /**
   * Trigger when user tries to search without filters
   */
  const triggerSearchWithoutFilters = useCallback(() => {
    setHasSearchedWithoutFilters(true);
    setActiveTooltip('no-filters');
  }, []);

  /**
   * Trigger when user clicks help link
   */
  const triggerHelpClick = useCallback(() => {
    setActiveTooltip('help');
  }, []);

  /**
   * Dismiss current tooltip
   */
  const dismissTooltip = useCallback(() => {
    setActiveTooltip(null);

    // Advance onboarding step
    if (onboardingStep < 3) {
      const nextStep = onboardingStep + 1;
      setOnboardingStep(nextStep);
      localStorage.setItem('onboarding_step', nextStep.toString());
    }
  }, [onboardingStep]);

  /**
   * Reset onboarding progress (for testing)
   */
  const resetOnboarding = useCallback(() => {
    setOnboardingStep(0);
    setActiveTooltip(null);
    localStorage.setItem('onboarding_step', '0');
  }, []);

  return {
    activeTooltip,
    dismissTooltip,
    triggerSearchWithoutFilters,
    triggerHelpClick,
    resetOnboarding,
    onboardingStep,
  };
}
