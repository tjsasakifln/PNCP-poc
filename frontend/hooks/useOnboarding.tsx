/**
 * useOnboarding Hook - Feature #3 Interactive Onboarding
 * Phase 3 - Day 8 Implementation (Skeleton)
 *
 * Manages Shepherd.js tour lifecycle:
 * - Step 1: Welcome & value proposition
 * - Step 2: Interactive demo (trigger real search)
 * - Step 3: Your turn (prompt user's first search)
 *
 * Persistence: localStorage flag `smartlic_onboarding_completed`
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import Shepherd from 'shepherd.js';
import 'shepherd.js/dist/css/shepherd.css';

// Type definitions for Shepherd.js (using any temporarily until @types available)
// TODO: Add @types/shepherd.js if available or create custom types
type ShepherdTour = any;
type ShepherdStep = any;

const ONBOARDING_STORAGE_KEY = 'smartlic_onboarding_completed';
const ONBOARDING_DISMISSED_KEY = 'smartlic_onboarding_dismissed';

export interface OnboardingOptions {
  /**
   * Auto-start onboarding if user hasn't completed it
   * Default: true
   */
  autoStart?: boolean;

  /**
   * Callback when user completes all steps
   */
  onComplete?: () => void;

  /**
   * Callback when user skips/exits early
   */
  onDismiss?: () => void;

  /**
   * Callback for analytics tracking per step
   */
  onStepChange?: (stepId: string, stepIndex: number) => void;
}

export function useOnboarding(options: OnboardingOptions = {}) {
  const {
    autoStart = true,
    onComplete,
    onDismiss,
    onStepChange,
  } = options;

  const tourRef = useRef<ShepherdTour | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasCompleted, setHasCompleted] = useState(false);
  const [hasDismissed, setHasDismissed] = useState(false);

  // Check localStorage on mount
  useEffect(() => {
    // Migrate legacy keys
    const legacyCompleted = localStorage.getItem('bidiq_onboarding_completed');
    if (legacyCompleted) {
      localStorage.setItem(ONBOARDING_STORAGE_KEY, legacyCompleted);
      localStorage.removeItem('bidiq_onboarding_completed');
    }
    const legacyDismissed = localStorage.getItem('bidiq_onboarding_dismissed');
    if (legacyDismissed) {
      localStorage.setItem(ONBOARDING_DISMISSED_KEY, legacyDismissed);
      localStorage.removeItem('bidiq_onboarding_dismissed');
    }
    const completed = localStorage.getItem(ONBOARDING_STORAGE_KEY) === 'true';
    const dismissed = localStorage.getItem(ONBOARDING_DISMISSED_KEY) === 'true';
    setHasCompleted(completed);
    setHasDismissed(dismissed);
  }, []);

  // Initialize Shepherd tour
  useEffect(() => {
    if (tourRef.current) return; // Already initialized

    const tour = new Shepherd.Tour({
      useModalOverlay: true,
      defaultStepOptions: {
        classes: 'shepherd-theme-custom',
        scrollTo: { behavior: 'smooth', block: 'center' },
        cancelIcon: {
          enabled: true,
        },
      },
    });

    // Step 1: Welcome & Value Proposition
    tour.addStep({
      id: 'welcome',
      title: '👋 Bem-vindo ao SmartLic!',
      text: `
        <p class="mb-3">
          Descubra oportunidades de licitação de forma <strong>inteligente e automatizada</strong>.
        </p>
        <ul class="list-disc list-inside space-y-1 text-sm">
          <li>🔍 Busca em 27 estados simultaneamente</li>
          <li>🤖 Avaliação estratégica por IA</li>
          <li>📊 Relatórios Excel prontos para análise</li>
        </ul>
      `,
      buttons: [
        {
          text: 'Pular Tutorial',
          action: tour.cancel,
          secondary: true,
        },
        {
          text: 'Começar',
          action: tour.next,
        },
      ],
    });

    // Step 2: Interactive Demo (Real Search)
    tour.addStep({
      id: 'demo-search',
      title: '🎯 Vamos fazer uma busca de demonstração',
      text: `
        <p class="mb-2">
          Selecionamos <strong>SC, PR e RS</strong> (região Sul) para mostrar como funciona.
        </p>
        <p class="text-sm text-gray-600">
          Clique em "Buscar" para ver os resultados em ação!
        </p>
      `,
      attachTo: {
        element: 'button[type="button"][aria-busy]', // Main search button
        on: 'bottom',
      },
      buttons: [
        {
          text: 'Voltar',
          action: tour.back,
          secondary: true,
        },
        {
          text: 'Fazer Busca Demo',
          action: function() {
            // Trigger demo search (handled by callback)
            tour.next();
          },
        },
      ],
      when: {
        show() {
          // Pre-populate demo search parameters (handled by parent component)
        },
      },
    });

    // Step 3: Your Turn (First Personalized Search)
    tour.addStep({
      id: 'your-turn',
      title: '🚀 Agora é sua vez!',
      text: `
        <p class="mb-3">
          Personalize sua busca:
        </p>
        <ol class="list-decimal list-inside space-y-2 text-sm">
          <li>Escolha os <strong>estados</strong> de interesse</li>
          <li>Ajuste o <strong>período</strong> (últimos 7, 15 ou 30 dias)</li>
          <li>Selecione o <strong>setor</strong> ou use termos específicos</li>
          <li>Clique em <strong>"Buscar"</strong> e aguarde os resultados!</li>
        </ol>
        <p class="text-xs text-gray-500 mt-3">
          💡 Dica: Quanto mais estados, maior o tempo de busca (~6s por estado)
        </p>
      `,
      attachTo: {
        element: '.min-h-screen', // Center of screen
        on: 'top',
      },
      buttons: [
        {
          text: 'Voltar',
          action: tour.back,
          secondary: true,
        },
        {
          text: 'Entendi, vamos lá!',
          action: function() {
            tour.complete();
          },
        },
      ],
    });

    // Event listeners
    tour.on('complete', () => {
      localStorage.setItem(ONBOARDING_STORAGE_KEY, 'true');
      setHasCompleted(true);
      setIsActive(false);
      onComplete?.();
    });

    tour.on('cancel', () => {
      localStorage.setItem(ONBOARDING_DISMISSED_KEY, 'true');
      setHasDismissed(true);
      setIsActive(false);
      onDismiss?.();
    });

    tour.on('show', (event: { step: ShepherdStep }) => {
      const step = event.step;
      const stepId = step.id || '';
      const stepIndex = tour.steps.indexOf(step);
      setCurrentStep(stepIndex);
      onStepChange?.(stepId, stepIndex);
    });

    tourRef.current = tour;

    return () => {
      tour.complete();
    };
  }, [onComplete, onDismiss, onStepChange]);

  /**
   * Start the onboarding tour
   */
  const startTour = useCallback(() => {
    if (tourRef.current) {
      tourRef.current.start();
      setIsActive(true);
    }
  }, []);

  // Auto-start logic
  // Bug fix P2-4 & P2-5: Prevent race conditions with rapid mount/unmount and dismissed flag
  useEffect(() => {
    // Add a small delay to prevent race conditions during rapid component mount/unmount
    const timeout = setTimeout(() => {
      if (autoStart && !hasCompleted && !hasDismissed && tourRef.current && !isActive) {
        startTour();
      }
    }, 100); // 100ms debounce

    return () => clearTimeout(timeout);
  }, [autoStart, hasCompleted, hasDismissed, isActive, startTour]);

  /**
   * Manually trigger the tour (for returning users)
   */
  const restartTour = useCallback(() => {
    localStorage.removeItem(ONBOARDING_STORAGE_KEY);
    localStorage.removeItem(ONBOARDING_DISMISSED_KEY);
    setHasCompleted(false);
    setHasDismissed(false);
    startTour();
  }, [startTour]);

  /**
   * Cancel the tour
   */
  const cancelTour = useCallback(() => {
    if (tourRef.current) {
      tourRef.current.cancel();
    }
  }, []);

  /**
   * Check if onboarding should show (new user)
   */
  const shouldShowOnboarding = !hasCompleted && !hasDismissed;

  return {
    /**
     * Start the tour
     */
    startTour,

    /**
     * Restart tour (clears completion flag)
     */
    restartTour,

    /**
     * Cancel/dismiss tour
     */
    cancelTour,

    /**
     * Whether tour is currently active
     */
    isActive,

    /**
     * Current step index (0-based)
     */
    currentStep,

    /**
     * Whether user has completed onboarding
     */
    hasCompleted,

    /**
     * Whether user dismissed without completing
     */
    hasDismissed,

    /**
     * Whether onboarding should auto-show (new user)
     */
    shouldShowOnboarding,

    /**
     * Direct access to Shepherd tour instance
     */
    tour: tourRef.current as ShepherdTour | null,
  };
}
