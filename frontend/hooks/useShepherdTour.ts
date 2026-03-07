'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import Shepherd from 'shepherd.js';
import 'shepherd.js/dist/css/shepherd.css';
import '../styles/shepherd-theme.css';
import { safeSetItem } from '../lib/storage';

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
}

export function useShepherdTour({ tourId, steps, onComplete, onSkip }: UseShepherdTourOptions) {
  const tourRef = useRef<InstanceType<typeof Shepherd.Tour> | null>(null);
  const [isActive, setIsActive] = useState(false);
  const stepsSeen = useRef(0);
  const callbacksRef = useRef({ onComplete, onSkip });
  callbacksRef.current = { onComplete, onSkip };

  const storageKey = `onboarding_${tourId}_tour_completed`;

  const isCompleted = useCallback((): boolean => {
    if (typeof window === 'undefined') return true;
    return localStorage.getItem(storageKey) === 'true';
  }, [storageKey]);

  const markCompleted = useCallback(() => {
    safeSetItem(storageKey, 'true');
  }, [storageKey]);

  const resetCompletion = useCallback(() => {
    localStorage.removeItem(storageKey);
  }, [storageKey]);

  // Initialize Shepherd tour
  useEffect(() => {
    if (typeof window === 'undefined') return;

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

    steps.forEach((step, index) => {
      const isFirst = index === 0;
      const isLast = index === steps.length - 1;

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const buttons: any[] = [];

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

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      tour.addStep({
        id: step.id,
        title: step.title,
        text: step.text,
        attachTo: step.attachTo ? {
          element: step.attachTo.element,
          on: step.attachTo.on,
        } as any : undefined,
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

    return () => {
      if (tour.isActive()) {
        tour.cancel();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tourId]);

  const startTour = useCallback(() => {
    if (tourRef.current && !tourRef.current.isActive()) {
      stepsSeen.current = 0;
      tourRef.current.start();
      setIsActive(true);
    }
  }, []);

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
