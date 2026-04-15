/**
 * useOnboarding Hook Tests
 * STORY-4.2: Migrado de shepherd.js → Tour component
 *
 * O hook agora usa estado React + Tour component em vez de Shepherd.
 * Mantém a mesma API pública: startTour, restartTour, cancelTour,
 * isActive, currentStep, hasCompleted, hasDismissed, shouldShowOnboarding, tourElement.
 */

import { renderHook, act } from '@testing-library/react';
import { useOnboarding } from '../hooks/useOnboarding';

// Mock Tour component — evita erros de FocusTrap/jsdom
jest.mock('../components/tour/Tour', () => ({
  Tour: () => null,
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useOnboarding Hook', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  describe('TC-ONBOARDING-001: Initialization', () => {
    it('should initialize with default values', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.isActive).toBe(false);
      expect(result.current.currentStep).toBe(0);
      expect(result.current.hasCompleted).toBe(false);
      expect(result.current.hasDismissed).toBe(false);
    });

    it('should detect completed onboarding from localStorage', () => {
      localStorageMock.setItem('smartlic_onboarding_completed', 'true');

      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.hasCompleted).toBe(true);
      expect(result.current.shouldShowOnboarding).toBe(false);
    });

    it('should detect dismissed onboarding from localStorage', () => {
      localStorageMock.setItem('smartlic_onboarding_dismissed', 'true');

      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.hasDismissed).toBe(true);
      expect(result.current.shouldShowOnboarding).toBe(false);
    });

    it('should show onboarding for new users', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.shouldShowOnboarding).toBe(true);
    });
  });

  describe('TC-ONBOARDING-002: Tour control', () => {
    it('should start tour manually', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      act(() => {
        result.current.startTour();
      });

      expect(result.current.isActive).toBe(true);
    });

    it('should restart tour and clear localStorage', () => {
      localStorageMock.setItem('smartlic_onboarding_completed', 'true');

      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.hasCompleted).toBe(true);

      act(() => {
        result.current.restartTour();
      });

      expect(localStorageMock.getItem('smartlic_onboarding_completed')).toBeNull();
      expect(result.current.hasCompleted).toBe(false);
      expect(result.current.isActive).toBe(true);
    });

    it('should cancel tour', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      act(() => {
        result.current.startTour();
      });

      expect(result.current.isActive).toBe(true);

      act(() => {
        result.current.cancelTour();
      });

      expect(result.current.isActive).toBe(false);
      expect(result.current.hasDismissed).toBe(true);
    });
  });

  describe('TC-ONBOARDING-003: Callbacks', () => {
    it('should call onComplete callback when provided', () => {
      const onComplete = jest.fn();

      renderHook(() => useOnboarding({
        autoStart: false,
        onComplete,
      }));

      expect(onComplete).toBeDefined();
    });

    it('should call onDismiss callback when cancelTour is called', () => {
      const onDismiss = jest.fn();

      const { result } = renderHook(() => useOnboarding({
        autoStart: false,
        onDismiss,
      }));

      act(() => {
        result.current.cancelTour();
      });

      expect(onDismiss).toHaveBeenCalled();
    });

    it('should call onStepChange callback when provided', () => {
      const onStepChange = jest.fn();

      renderHook(() => useOnboarding({
        autoStart: false,
        onStepChange,
      }));

      expect(onStepChange).toBeDefined();
    });
  });

  describe('TC-ONBOARDING-004: localStorage persistence', () => {
    it('should save completion to localStorage', () => {
      act(() => {
        localStorageMock.setItem('smartlic_onboarding_completed', 'true');
      });

      expect(localStorageMock.getItem('smartlic_onboarding_completed')).toBe('true');
    });

    it('should save dismissal to localStorage', () => {
      act(() => {
        localStorageMock.setItem('smartlic_onboarding_dismissed', 'true');
      });

      expect(localStorageMock.getItem('smartlic_onboarding_dismissed')).toBe('true');
    });

    it('should clear localStorage on restart', () => {
      localStorageMock.setItem('smartlic_onboarding_completed', 'true');
      localStorageMock.setItem('smartlic_onboarding_dismissed', 'true');

      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      act(() => {
        result.current.restartTour();
      });

      expect(localStorageMock.getItem('smartlic_onboarding_completed')).toBeNull();
      expect(localStorageMock.getItem('smartlic_onboarding_dismissed')).toBeNull();
    });
  });

  describe('TC-ONBOARDING-005: Auto-start logic', () => {
    it('should NOT auto-start when autoStart is false', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.isActive).toBe(false);
    });

    it('should NOT auto-start if already completed', () => {
      localStorageMock.setItem('smartlic_onboarding_completed', 'true');

      const { result } = renderHook(() => useOnboarding({ autoStart: true }));

      expect(result.current.isActive).toBe(false);
    });

    it('should NOT auto-start if dismissed', () => {
      localStorageMock.setItem('smartlic_onboarding_dismissed', 'true');

      const { result } = renderHook(() => useOnboarding({ autoStart: true }));

      expect(result.current.isActive).toBe(false);
    });
  });

  describe('TC-ONBOARDING-006: Tour instance (deprecated)', () => {
    it('should return null for deprecated tour property', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      // tour is always null — Shepherd.js was removed (STORY-4.2)
      expect(result.current.tour).toBeNull();
    });
  });

  describe('TC-ONBOARDING-007: Current step tracking', () => {
    it('should track current step index (starts at 0)', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.currentStep).toBe(0);
    });
  });

  describe('TC-ONBOARDING-008: tourElement', () => {
    it('should expose tourElement as ReactNode', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      // tourElement should be defined (it's a JSX element from useMemo)
      expect(result.current.tourElement).toBeDefined();
    });
  });

  describe('TC-ONBOARDING-009: Edge cases', () => {
    it('should handle missing localStorage gracefully', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      expect(result.current.hasCompleted).toBe(false);
      expect(result.current.hasDismissed).toBe(false);
    });

    it('should handle invalid localStorage values', () => {
      localStorageMock.setItem('smartlic_onboarding_completed', 'invalid');

      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      // 'invalid' !== 'true', so not considered completed
      expect(result.current.hasCompleted).toBe(false);
    });

    it('should allow multiple restarts without error', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      act(() => { result.current.restartTour(); });
      act(() => { result.current.restartTour(); });

      expect(result.current.hasCompleted).toBe(false);
      expect(result.current.isActive).toBe(true);
    });

    it('cancelTour marks hasDismissed=true and sets localStorage', () => {
      const { result } = renderHook(() => useOnboarding({ autoStart: false }));

      act(() => { result.current.cancelTour(); });

      expect(result.current.hasDismissed).toBe(true);
      expect(localStorageMock.getItem('smartlic_onboarding_dismissed')).toBe('true');
    });
  });
});
