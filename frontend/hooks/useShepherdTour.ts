'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { safeSetItem, safeGetItem, safeRemoveItem } from '../lib/storage';

export interface TourStep {
  id: string;
  title: string;
  text: string;
  attachTo?: { element: string; on: string };
  scrollTo?: boolean | ScrollIntoViewOptions;
  showOn?: () => boolean;
  beforeShowPromise?: () => Promise<void>;
}

export interface UseShepherdTourOptions {
  tourId: string;
  steps: TourStep[];
  onComplete?: (stepsSeen: number) => void;
  onSkip?: (skippedAtStep: number) => void;
  /** UX-414: When true, tour will not start (e.g., page in error state) */
  disabled?: boolean;
}

export function useShepherdTour({ tourId, steps, onComplete, onSkip, disabled = false }: UseShepherdTourOptions) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tourRef = useRef<any>(null);
  const [isActive, setIsActive] = useState(false);
  const stepsSeen = useRef(0);
  const callbacksRef = useRef({ onComplete, onSkip });
  callbacksRef.current = { onComplete, onSkip };

  const storageKey = `onboarding_${tourId}_tour_completed`;

  const isCompleted = useCallback((): boolean => {
    return safeGetItem(storageKey) === 'true';
  }, [storageKey]);

  const markCompleted = useCallback(() => {
    safeSetItem(storageKey, 'true');
  }, [storageKey]);

  const resetCompletion = useCallback(() => {
    safeRemoveItem(storageKey);
  }, [storageKey]);

  // Keep steps in a ref — steps is an array prop that may have a new reference
  // each render; reading from ref inside the effect avoids re-initializing the
  // tour on every parent render.
  const stepsRef = useRef(steps);
  stepsRef.current = steps;

  // Initialize Shepherd tour
  useEffect(() => {
    if (typeof window === 'undefined') return;
    let cancelled = false;

    Promise.all([
      import('shepherd.js'),
      import('shepherd.js/dist/css/shepherd.css'),
      import('../styles/shepherd-theme.css'),
    ]).then(([{ default: Shepherd }]) => {
      if (cancelled) return;

      const tour = new Shepherd.Tour({
        useModalOverlay: true,
        exitOnEsc: true,
        keyboardNavigation: true,
        defaultStepOptions: {
          classes: 'smartlic-shepherd-step',
          scrollTo: { behavior: 'smooth', block: 'center' } as ScrollIntoViewOptions,
          cancelIcon: { enabled: true },
          modalOverlayOpeningPadding: 8,
          modalOverlayOpeningRadius: 8,
        },
      });

      stepsRef.current.forEach((step, index) => {
        const isFirst = index === 0;
        const isLast = index === stepsRef.current.length - 1;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const buttons: Array<{ text: string; action: () => void; secondary?: boolean }> = [];

        if (!isFirst) {
          buttons.push({
            text: 'Voltar',
            action: () => tour.back(),
            secondary: true,
          });
        }
        buttons.push({
          text: 'Pular tour',
          action: () => tour.cancel(),
          secondary: true,
        });
        buttons.push({
          text: isLast ? 'Concluir' : 'Próximo',
          action: () => isLast ? tour.complete() : tour.next(),
        });

        tour.addStep({
          id: step.id,
          title: step.title,
          text: step.text,
          attachTo: step.attachTo ? {
            element: step.attachTo.element,
            on: step.attachTo.on as "top" | "bottom" | "left" | "right",
          } : undefined,
          scrollTo: step.scrollTo ?? { behavior: 'smooth', block: 'center' } as ScrollIntoViewOptions,
          showOn: step.showOn,
          beforeShowPromise: step.beforeShowPromise,
          buttons,
        });
      });

      tour.on('show', () => {
        stepsSeen.current += 1;
      });

      tour.on('complete', () => {
        markCompleted();
        setIsActive(false);
        callbacksRef.current.onComplete?.(stepsSeen.current);
      });

      tour.on('cancel', () => {
        markCompleted();
        setIsActive(false);
        callbacksRef.current.onSkip?.(stepsSeen.current);
      });

      tourRef.current = tour;
    });

    return () => {
      cancelled = true;
      if (tourRef.current?.isActive()) {
        tourRef.current.cancel();
      }
    };
  }, [tourId, markCompleted]);

  const startTour = useCallback(() => {
    // UX-414: Do not start tour when page is in error state or disabled
    if (disabled) return;
    if (tourRef.current && !tourRef.current.isActive()) {
      // UX-414 AC3: Verify all target elements exist before starting
      const missingElement = stepsRef.current.some(
        (step) => step.attachTo?.element && !document.querySelector(step.attachTo.element)
      );
      if (missingElement) return;
      stepsSeen.current = 0;
      tourRef.current.start();
      setIsActive(true);
    }
  }, [disabled]);

  const restartTour = useCallback(() => {
    resetCompletion();
    startTour();
  }, [resetCompletion, startTour]);

  return {
    isCompleted,
    startTour,
    restartTour,
    isActive,
    storageKey,
  };
}
