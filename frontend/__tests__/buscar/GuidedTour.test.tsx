/**
 * STORY-442: Testes do componente GuidedTour
 *
 * Cobre:
 * 1. Não inicia se tour já completado (localStorage — AC4)
 * 2. Inicia automaticamente na primeira visita pós-onboarding (AC1)
 * 3. Dispara trackEvent 'tour_started' (AC6)
 * 4. Marca como completado no localStorage ao finalizar (AC4)
 */
import React from "react";
import { render, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// Refs para capturar mocks — inicializados na factory e acessíveis nos testes
const mockFns = {
  trackEvent: jest.fn(),
  startTour: jest.fn(),
  onComplete: undefined as ((stepsSeen: number) => void) | undefined,
  onSkip: undefined as ((stepsSeen: number) => void) | undefined,
};

// Mock storage — usa Map para simular localStorage
const storageMap = new Map<string, string>();

jest.mock("@/hooks/useShepherdTour", () => ({
  useShepherdTour: (opts: {
    tourId: string;
    steps: unknown[];
    onComplete?: (s: number) => void;
    onSkip?: (s: number) => void;
  }) => {
    mockFns.onComplete = opts.onComplete;
    mockFns.onSkip = opts.onSkip;
    return {
      isCompleted: () => false,
      startTour: mockFns.startTour,
      restartTour: jest.fn(),
      isActive: false,
    };
  },
}));

jest.mock("@/hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: mockFns.trackEvent,
  }),
}));

jest.mock("@/lib/storage", () => ({
  safeGetItem: (key: string) => storageMap.get(key) ?? null,
  safeSetItem: (key: string, value: string) => { storageMap.set(key, value); },
  safeRemoveItem: (key: string) => { storageMap.delete(key); },
}));

// Imports após todos os mocks
import { GuidedTour, GUIDED_TOUR_STORAGE_KEY } from "@/app/buscar/components/GuidedTour";

describe("GuidedTour", () => {
  beforeEach(() => {
    mockFns.trackEvent.mockClear();
    mockFns.startTour.mockClear();
    mockFns.onComplete = undefined;
    mockFns.onSkip = undefined;
    storageMap.clear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("não inicia o tour se já foi completado (AC4)", () => {
    storageMap.set(GUIDED_TOUR_STORAGE_KEY, "true");
    storageMap.set("smartlic_onboarding_completed", "true");

    render(<GuidedTour />);

    act(() => {
      jest.runAllTimers();
    });

    expect(mockFns.startTour).not.toHaveBeenCalled();
  });

  it("não inicia o tour se onboarding não foi concluído (AC1)", () => {
    render(<GuidedTour />);

    act(() => {
      jest.runAllTimers();
    });

    expect(mockFns.startTour).not.toHaveBeenCalled();
  });

  it("inicia automaticamente após onboarding concluído e tour não completado (AC1)", () => {
    storageMap.set("smartlic_onboarding_completed", "true");

    render(<GuidedTour />);

    act(() => {
      jest.advanceTimersByTime(700);
    });

    expect(mockFns.startTour).toHaveBeenCalledTimes(1);
  });

  it("inicia quando onboarding foi dispensado (AC1 — dismissed)", () => {
    storageMap.set("smartlic_onboarding_dismissed", "true");

    render(<GuidedTour />);

    act(() => {
      jest.advanceTimersByTime(700);
    });

    expect(mockFns.startTour).toHaveBeenCalledTimes(1);
  });

  it("dispara trackEvent 'tour_started' ao iniciar (AC6)", () => {
    storageMap.set("smartlic_onboarding_completed", "true");

    render(<GuidedTour />);

    act(() => {
      jest.advanceTimersByTime(700);
    });

    expect(mockFns.trackEvent).toHaveBeenCalledWith("tour_started", {
      tour: "buscar_guided",
    });
  });

  it("marca como completado no localStorage ao finalizar (AC4)", () => {
    storageMap.set("smartlic_onboarding_completed", "true");

    render(<GuidedTour />);

    act(() => {
      jest.advanceTimersByTime(700);
    });

    act(() => {
      mockFns.onComplete?.(5);
    });

    expect(storageMap.get(GUIDED_TOUR_STORAGE_KEY)).toBe("true");
  });

  it("dispara trackEvent 'tour_completed' ao concluir (AC6)", () => {
    storageMap.set("smartlic_onboarding_completed", "true");

    render(<GuidedTour />);

    act(() => {
      jest.advanceTimersByTime(700);
    });

    act(() => {
      mockFns.onComplete?.(5);
    });

    expect(mockFns.trackEvent).toHaveBeenCalledWith("tour_completed", {
      tour: "buscar_guided",
      steps_seen: 5,
    });
  });

  it("dispara trackEvent 'tour_skipped' ao pular (AC6)", () => {
    storageMap.set("smartlic_onboarding_completed", "true");

    render(<GuidedTour />);

    act(() => {
      jest.advanceTimersByTime(700);
    });

    act(() => {
      mockFns.onSkip?.(2);
    });

    expect(mockFns.trackEvent).toHaveBeenCalledWith("tour_skipped", {
      tour: "buscar_guided",
      skipped_at_step: 2,
    });
  });

  it("retorna null (não renderiza nada no DOM)", () => {
    const { container } = render(<GuidedTour />);
    expect(container.firstChild).toBeNull();
  });
});
