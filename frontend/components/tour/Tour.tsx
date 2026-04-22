/**
 * STORY-4.2 (TD-FE-002) — Accessible tour component.
 *
 * Drop-in replacement foundation for Shepherd.js with first-class ARIA,
 * `focus-trap-react` for keyboard trapping, and a permanent-dismiss control
 * (also resolves TD-FE-017).
 *
 * Design notes:
 *
 * - `role="dialog"` + `aria-modal="false"` — a tour step is NOT a blocking
 *   modal. It spotlights a target without removing the page from a11y tree.
 * - `aria-live="polite"` announces "Passo N de M: {title}" whenever the
 *   step changes. Screen readers narrate progress without hijacking focus.
 * - Focus trap is restricted to the tour card itself so Tab/Shift+Tab cycle
 *   through the step actions without wandering into the page.
 * - ESC cancels the tour and fires `onSkip` for telemetry consistency with
 *   the prior Shepherd behaviour.
 * - `dismissPermanently` writes a localStorage flag that the hook checks
 *   before re-starting the tour.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import FocusTrap from 'focus-trap-react';

export interface TourStepDef {
  id: string;
  title: string;
  text: string;
  attachTo?: { selector: string; placement?: 'top' | 'bottom' | 'left' | 'right' };
  showOn?: () => boolean;
  beforeShow?: () => Promise<void> | void;
}

export interface TourProps {
  tourId: string;
  steps: TourStepDef[];
  active: boolean;
  onComplete?: (stepsSeen: number) => void;
  onSkip?: (skippedAtStep: number) => void;
  onStepChange?: (index: number, step: TourStepDef) => void;
  /** UX-414 parity — tour will not render when true. */
  disabled?: boolean;
  /** Override the localStorage key used for the permanent-dismiss flag. */
  storageKey?: string;
}

const DEFAULT_STORAGE_PREFIX = 'smartlic_tour_';

/**
 * Scan `steps` from `from` in direction `dir` (+1 = forward, -1 = back)
 * and return the first index where `showOn` is absent or returns true.
 * Returns -1 when no valid step exists in that direction.
 */
function findValidIndex(steps: TourStepDef[], from: number, dir: 1 | -1): number {
  let i = from;
  while (i >= 0 && i < steps.length) {
    const s = steps[i];
    if (!s.showOn || s.showOn()) return i;
    i += dir;
  }
  return -1;
}

function getStorageKey(tourId: string, override?: string): string {
  return override ?? `${DEFAULT_STORAGE_PREFIX}${tourId}_dismissed_permanent`;
}

export function isTourPermanentlyDismissed(tourId: string, storageKey?: string): boolean {
  if (typeof window === 'undefined') return false;
  try {
    return window.localStorage.getItem(getStorageKey(tourId, storageKey)) === 'true';
  } catch {
    return false;
  }
}

export function markTourPermanentlyDismissed(tourId: string, storageKey?: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(getStorageKey(tourId, storageKey), 'true');
  } catch {
    /* noop — quota / private mode */
  }
}

export function Tour({
  tourId,
  steps,
  active,
  onComplete,
  onSkip,
  onStepChange,
  disabled,
  storageKey,
}: TourProps) {
  const [index, setIndex] = useState(0);
  const total = steps.length;
  const stepRef = useRef<HTMLDivElement | null>(null);
  // Guard against concurrent navigations while `beforeShow` awaits.
  const isTransitioningRef = useRef(false);

  // Honor `disabled` + permanent dismiss — evaluated every render because the
  // localStorage flag is flipped imperatively by the "Não mostrar novamente"
  // button and must suppress the next render without waiting on a state change.
  const shouldRender =
    active &&
    !disabled &&
    total > 0 &&
    !isTourPermanentlyDismissed(tourId, storageKey);

  // On (re)open: find the first visible step, call its beforeShow, then show it.
  useEffect(() => {
    if (!active) return;
    const first = findValidIndex(steps, 0, 1);
    if (first === -1) {
      onComplete?.(0);
      return;
    }
    setIndex(first);
    void steps[first].beforeShow?.();
    // `steps` and `onComplete` refs are intentionally omitted — we only want
    // to re-run when the tour is (re)opened or switched to a new tourId.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, tourId]);

  const current = steps[Math.min(index, total - 1)] ?? null;

  // Notify on step change (keeps parity with Shepherd MutationObserver hook).
  useEffect(() => {
    if (shouldRender && current) {
      onStepChange?.(index, current);
    }
    // intentionally not adding `onStepChange` to deps — callers may pass unstable fn identity
    // and we only care about actual step transitions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldRender, index, current?.id]);

  const handleComplete = useCallback(() => {
    onComplete?.(index + 1);
  }, [index, onComplete]);

  const handleSkip = useCallback(() => {
    onSkip?.(index);
  }, [index, onSkip]);

  const handleNext = useCallback(async () => {
    if (isTransitioningRef.current) return;
    if (index >= total - 1) {
      handleComplete();
      return;
    }
    const next = findValidIndex(steps, index + 1, 1);
    if (next === -1) {
      handleComplete();
      return;
    }
    // Sync path when there's no beforeShow — avoids a microtask hop so
    // synchronous `fireEvent.click` tests observe the new step immediately.
    if (!steps[next].beforeShow) {
      setIndex(next);
      return;
    }
    isTransitioningRef.current = true;
    try {
      await steps[next].beforeShow();
    } finally {
      isTransitioningRef.current = false;
    }
    setIndex(next);
  }, [index, total, steps, handleComplete]);

  const handleBack = useCallback(async () => {
    if (isTransitioningRef.current) return;
    const prev = findValidIndex(steps, index - 1, -1);
    if (prev < 0) return;
    if (!steps[prev].beforeShow) {
      setIndex(prev);
      return;
    }
    isTransitioningRef.current = true;
    try {
      await steps[prev].beforeShow();
    } finally {
      isTransitioningRef.current = false;
    }
    setIndex(prev);
  }, [index, steps]);

  const handleDismissPermanently = useCallback(() => {
    markTourPermanentlyDismissed(tourId, storageKey);
    handleSkip();
  }, [tourId, storageKey, handleSkip]);

  // Keyboard handling — ESC cancels, arrow keys navigate.
  useEffect(() => {
    if (!shouldRender) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.stopPropagation();
        handleSkip();
      } else if (event.key === 'ArrowRight') {
        event.stopPropagation();
        handleNext();
      } else if (event.key === 'ArrowLeft') {
        event.stopPropagation();
        handleBack();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [shouldRender, handleSkip, handleNext, handleBack]);

  if (!shouldRender || !current) return null;

  const titleId = `tour-${tourId}-step-${current.id}-title`;
  const descId = `tour-${tourId}-step-${current.id}-desc`;
  const isLast = index === total - 1;
  const progressLabel = `Passo ${index + 1} de ${total}: ${current.title}`;

  return (
    <FocusTrap
      focusTrapOptions={{
        clickOutsideDeactivates: true,
        escapeDeactivates: false, // we handle ESC ourselves for analytics parity
        returnFocusOnDeactivate: true,
        initialFocus: false,
        // jsdom returns offsetWidth/Height === 0 for everything — bypass the
        // display check so focus-trap sees our buttons as tabbable in tests.
        tabbableOptions: { displayCheck: 'none' },
        // Belt-and-suspenders: when tabbable query returns empty (e.g. jsdom
        // quirks), focus the step container itself.
        fallbackFocus: () => stepRef.current as HTMLElement,
      }}
    >
      <div
        data-testid={`tour-${tourId}`}
        className="smartlic-tour fixed bottom-6 right-6 z-[70] max-w-md rounded-lg border border-slate-200 bg-white p-5 shadow-xl dark:border-slate-700 dark:bg-slate-900"
      >
        <div
          ref={stepRef}
          role="dialog"
          aria-modal="false"
          aria-labelledby={titleId}
          aria-describedby={descId}
          className="focus:outline-none"
          tabIndex={-1}
        >
          {/* Screen reader live region */}
          <div aria-live="polite" aria-atomic="true" className="sr-only">
            {progressLabel}
          </div>

          <h2 id={titleId} className="text-base font-semibold text-slate-900 dark:text-slate-50">
            {current.title}
          </h2>
          <p id={descId} className="mt-2 text-sm text-slate-700 dark:text-slate-200">
            {current.text}
          </p>

          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {index + 1} / {total}
            </span>

            <div className="flex items-center gap-2">
              {index > 0 && (
                <button
                  type="button"
                  onClick={handleBack}
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                >
                  Voltar
                </button>
              )}
              <button
                type="button"
                onClick={handleSkip}
                className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              >
                Pular
              </button>
              <button
                type="button"
                onClick={handleNext}
                autoFocus
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                {isLast ? 'Concluir' : 'Próximo'}
              </button>
            </div>
          </div>

          <button
            type="button"
            onClick={handleDismissPermanently}
            className="mt-3 text-xs text-slate-400 underline hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
          >
            Não mostrar novamente
          </button>
        </div>
      </div>
    </FocusTrap>
  );
}

export default Tour;
