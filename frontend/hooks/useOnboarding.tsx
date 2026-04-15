/**
 * useOnboarding Hook — STORY-4.2 (TD-FE-002)
 *
 * Manages onboarding tour lifecycle using the accessible Tour component
 * (replaces Shepherd.js — resolves TD-FE-002 for this callsite).
 *
 * Steps:
 * - Step 1: Welcome & value proposition
 * - Step 2: Interactive demo (trigger real search)
 * - Step 3: Your turn (prompt user's first search)
 *
 * Persistence:
 * - `smartlic_onboarding_completed` — completed flag
 * - `smartlic_onboarding_dismissed` — early-exit flag
 *
 * Returns `tourElement: React.ReactNode` that the consumer MUST render in
 * its JSX tree (previously Shepherd managed its own DOM; now we rely on React).
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { safeSetItem, safeGetItem, safeRemoveItem } from '../lib/storage';
import { Tour, type TourStepDef } from '../components/tour/Tour';

const ONBOARDING_STORAGE_KEY = 'smartlic_onboarding_completed';
const ONBOARDING_DISMISSED_KEY = 'smartlic_onboarding_dismissed';

const ONBOARDING_STEPS: TourStepDef[] = [
  {
    id: 'welcome',
    title: 'Bem-vindo ao SmartLic!',
    text: 'Descubra oportunidades de licitação de forma inteligente e automatizada — busca em 27 estados, avaliação por IA e relatórios Excel prontos.',
  },
  {
    id: 'demo-search',
    title: 'Vamos fazer uma busca de demonstração',
    text: 'Selecionamos SC, PR e RS (região Sul) para mostrar como funciona. Clique em Buscar para ver os resultados!',
    attachTo: { selector: '[data-tour="search-button"]', placement: 'bottom' },
  },
  {
    id: 'your-turn',
    title: 'Agora é sua vez!',
    text: 'Personalize sua busca: escolha os estados, ajuste o período, selecione o setor e clique em Buscar para ver suas oportunidades!',
  },
];

export interface OnboardingOptions {
  /** Auto-start onboarding if user hasn't completed it. Default: true */
  autoStart?: boolean;
  /** Callback when user completes all steps */
  onComplete?: () => void;
  /** Callback when user skips/exits early */
  onDismiss?: () => void;
  /** Callback for analytics tracking per step */
  onStepChange?: (stepId: string, stepIndex: number) => void;
}

export function useOnboarding(options: OnboardingOptions = {}) {
  const {
    autoStart = true,
    onComplete,
    onDismiss,
    onStepChange,
  } = options;

  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasCompleted, setHasCompleted] = useState(false);
  const [hasDismissed, setHasDismissed] = useState(false);

  // Check localStorage on mount + migrate legacy keys
  useEffect(() => {
    const legacyCompleted = safeGetItem('bidiq_onboarding_completed');
    if (legacyCompleted) {
      safeSetItem(ONBOARDING_STORAGE_KEY, legacyCompleted);
      safeRemoveItem('bidiq_onboarding_completed');
    }
    const legacyDismissed = safeGetItem('bidiq_onboarding_dismissed');
    if (legacyDismissed) {
      safeSetItem(ONBOARDING_DISMISSED_KEY, legacyDismissed);
      safeRemoveItem('bidiq_onboarding_dismissed');
    }
    const completed = safeGetItem(ONBOARDING_STORAGE_KEY) === 'true';
    const dismissed = safeGetItem(ONBOARDING_DISMISSED_KEY) === 'true';
    setHasCompleted(completed);
    setHasDismissed(dismissed);
  }, []);

  const startTour = useCallback(() => {
    setIsActive(true);
  }, []);

  const restartTour = useCallback(() => {
    safeRemoveItem(ONBOARDING_STORAGE_KEY);
    safeRemoveItem(ONBOARDING_DISMISSED_KEY);
    setHasCompleted(false);
    setHasDismissed(false);
    setIsActive(true);
  }, []);

  const cancelTour = useCallback(() => {
    safeSetItem(ONBOARDING_DISMISSED_KEY, 'true');
    setHasDismissed(true);
    setIsActive(false);
    onDismiss?.();
  }, [onDismiss]);

  // Auto-start: small delay to prevent race during rapid mount/unmount
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (autoStart && !hasCompleted && !hasDismissed && !isActive) {
        startTour();
      }
    }, 100);
    return () => clearTimeout(timeout);
  }, [autoStart, hasCompleted, hasDismissed, isActive, startTour]);

  const shouldShowOnboarding = !hasCompleted && !hasDismissed;

  // Tour element — consumer MUST render this in their JSX tree
  const tourElement = useMemo(
    () => (
      <Tour
        tourId="onboarding"
        steps={ONBOARDING_STEPS}
        active={isActive}
        onComplete={() => {
          safeSetItem(ONBOARDING_STORAGE_KEY, 'true');
          setHasCompleted(true);
          setIsActive(false);
          onComplete?.();
        }}
        onSkip={() => {
          safeSetItem(ONBOARDING_DISMISSED_KEY, 'true');
          setHasDismissed(true);
          setIsActive(false);
          onDismiss?.();
        }}
        onStepChange={(stepIndex, step) => {
          setCurrentStep(stepIndex);
          onStepChange?.(step.id, stepIndex);
        }}
      />
    ),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [isActive],
  );

  return {
    startTour,
    restartTour,
    cancelTour,
    isActive,
    currentStep,
    hasCompleted,
    hasDismissed,
    shouldShowOnboarding,
    /** @deprecated — was Shepherd.js instance; now always null */
    tour: null,
    /** Render this element in the consumer's JSX tree */
    tourElement,
  };
}
