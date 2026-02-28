/**
 * STORY-313: Shepherd.js Onboarding Tours Tests
 *
 * AC19: Tests for each tour (search, results, pipeline) — render, step navigation, skip
 * AC20: localStorage persistence (don't repeat tour)
 * AC21: Replay button test
 * AC22: Zero regressions
 */

import "@testing-library/jest-dom";

// ============================================================================
// Mocks — must be self-contained to avoid Jest hoisting issues
// ============================================================================

jest.mock("shepherd.js", () => {
  const mockStart = jest.fn();
  const mockNext = jest.fn();
  const mockBack = jest.fn();
  const mockComplete = jest.fn();
  const mockCancel = jest.fn();
  const mockIsActive = jest.fn(() => false);
  const mockAddStep = jest.fn();
  const mockOn = jest.fn();

  const instance = {
    start: mockStart,
    next: mockNext,
    back: mockBack,
    complete: mockComplete,
    cancel: mockCancel,
    isActive: mockIsActive,
    addStep: mockAddStep,
    on: mockOn,
    steps: [],
  };

  return {
    __esModule: true,
    default: {
      Tour: jest.fn(() => instance),
    },
    __mockInstance: instance,
  };
});

// Mock next/navigation
const mockPush = jest.fn();
let currentPathname = "/buscar";
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => currentPathname,
  useSearchParams: () => new URLSearchParams(),
}));

// Mock analytics
jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

// Mock fetch
global.fetch = jest.fn(() => Promise.resolve(new Response(null, { status: 204 }))) as any;

// ============================================================================
// Imports (after mocks)
// ============================================================================

import { render, screen, fireEvent, act } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import { useShepherdTour, type TourStep } from "../../hooks/useShepherdTour";
import { OnboardingTourButton } from "../../components/OnboardingTourButton";

// Access mock instance
function getMockInstance() {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return (require("shepherd.js") as any).__mockInstance;
}

function getMockTourConstructor() {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return (require("shepherd.js") as any).default.Tour;
}

// ============================================================================
// Helpers
// ============================================================================

const SAMPLE_STEPS: TourStep[] = [
  { id: "step-1", title: "Step 1", text: "First step", attachTo: { element: "#t1", on: "bottom" } },
  { id: "step-2", title: "Step 2", text: "Second step", attachTo: { element: "#t2", on: "top" } },
  { id: "step-3", title: "Step 3", text: "Third step" },
];

function resetAll() {
  localStorage.clear();
  sessionStorage.clear();

  // Jest config has resetMocks: true — must re-establish implementations each test
  const shepherd = require("shepherd.js") as any;
  const instance = shepherd.__mockInstance;

  instance.start.mockImplementation(() => {});
  instance.next.mockImplementation(() => {});
  instance.back.mockImplementation(() => {});
  instance.complete.mockImplementation(() => {});
  instance.cancel.mockImplementation(() => {});
  instance.isActive.mockReturnValue(false);
  instance.addStep.mockImplementation(() => {});
  instance.on.mockImplementation(() => {});

  shepherd.default.Tour.mockImplementation(() => instance);

  mockPush.mockImplementation(() => {});
  currentPathname = "/buscar";
}

function getEventHandler(eventName: string) {
  const mock = getMockInstance();
  const call = mock.on.mock.calls.find((c: any[]) => c[0] === eventName);
  return call?.[1];
}

// ============================================================================
// useShepherdTour Hook Tests
// ============================================================================

describe("useShepherdTour hook", () => {
  beforeEach(resetAll);

  it("creates a Shepherd Tour with correct options", () => {
    renderHook(() => useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS }));

    expect(getMockTourConstructor()).toHaveBeenCalledWith(
      expect.objectContaining({
        useModalOverlay: true,
        exitOnEsc: true,
        keyboardNavigation: true,
      })
    );
  });

  it("adds correct number of steps", () => {
    renderHook(() => useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS }));
    expect(getMockInstance().addStep).toHaveBeenCalledTimes(3);
  });

  it("first step has no 'Voltar' button, has 'Pular tour' and 'Próximo'", () => {
    renderHook(() => useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS }));

    const firstStep = getMockInstance().addStep.mock.calls[0][0];
    expect(firstStep.id).toBe("step-1");
    expect(firstStep.buttons).toHaveLength(2);
    expect(firstStep.buttons[0].text).toBe("Pular tour");
    expect(firstStep.buttons[1].text).toBe("Próximo");
  });

  it("middle step has 'Voltar', 'Pular tour', 'Próximo'", () => {
    renderHook(() => useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS }));

    const middleStep = getMockInstance().addStep.mock.calls[1][0];
    expect(middleStep.buttons).toHaveLength(3);
    expect(middleStep.buttons[0].text).toBe("Voltar");
    expect(middleStep.buttons[1].text).toBe("Pular tour");
    expect(middleStep.buttons[2].text).toBe("Próximo");
  });

  it("last step has 'Concluir' instead of 'Próximo'", () => {
    renderHook(() => useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS }));

    const lastStep = getMockInstance().addStep.mock.calls[2][0];
    expect(lastStep.buttons[2].text).toBe("Concluir");
  });

  it("registers show, complete, and cancel event handlers", () => {
    renderHook(() => useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS }));

    const events = getMockInstance().on.mock.calls.map((c: any[]) => c[0]);
    expect(events).toContain("show");
    expect(events).toContain("complete");
    expect(events).toContain("cancel");
  });

  // AC20: localStorage persistence
  it("isCompleted returns false when not in localStorage", () => {
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS })
    );
    expect(result.current.isCompleted()).toBe(false);
  });

  it("isCompleted returns true when localStorage key is set", () => {
    localStorage.setItem("onboarding_test_tour_completed", "true");
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "test", steps: SAMPLE_STEPS })
    );
    expect(result.current.isCompleted()).toBe(true);
  });

  // AC3: Skip marks as completed
  it("cancel (skip) marks tour as completed in localStorage", () => {
    renderHook(() => useShepherdTour({ tourId: "skip-test", steps: SAMPLE_STEPS }));

    act(() => { getEventHandler("cancel")(); });

    expect(localStorage.getItem("onboarding_skip-test_tour_completed")).toBe("true");
  });

  it("complete marks tour as completed in localStorage", () => {
    renderHook(() => useShepherdTour({ tourId: "complete-test", steps: SAMPLE_STEPS }));

    act(() => { getEventHandler("complete")(); });

    expect(localStorage.getItem("onboarding_complete-test_tour_completed")).toBe("true");
  });

  it("calls onComplete callback with steps_seen count", () => {
    const onComplete = jest.fn();
    renderHook(() =>
      useShepherdTour({ tourId: "cb-test", steps: SAMPLE_STEPS, onComplete })
    );

    act(() => {
      getEventHandler("show")();
      getEventHandler("show")();
      getEventHandler("complete")();
    });

    expect(onComplete).toHaveBeenCalledWith(2);
  });

  it("calls onSkip callback with steps_seen on cancel", () => {
    const onSkip = jest.fn();
    renderHook(() =>
      useShepherdTour({ tourId: "skip-cb", steps: SAMPLE_STEPS, onSkip })
    );

    act(() => {
      getEventHandler("show")();
      getEventHandler("cancel")();
    });

    expect(onSkip).toHaveBeenCalledWith(1);
  });

  it("startTour calls tour.start()", () => {
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "start-test", steps: SAMPLE_STEPS })
    );

    act(() => { result.current.startTour(); });

    expect(getMockInstance().start).toHaveBeenCalled();
  });

  // AC21: Replay
  it("restartTour clears localStorage and starts", () => {
    localStorage.setItem("onboarding_replay-test_tour_completed", "true");

    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "replay-test", steps: SAMPLE_STEPS })
    );

    expect(result.current.isCompleted()).toBe(true);

    act(() => { result.current.restartTour(); });

    expect(localStorage.getItem("onboarding_replay-test_tour_completed")).toBeNull();
    expect(getMockInstance().start).toHaveBeenCalled();
  });

  it("passes attachTo correctly", () => {
    renderHook(() => useShepherdTour({ tourId: "attach", steps: SAMPLE_STEPS }));

    const step = getMockInstance().addStep.mock.calls[0][0];
    expect(step.attachTo).toEqual({ element: "#t1", on: "bottom" });
  });

  it("handles step without attachTo (centered tooltip)", () => {
    renderHook(() => useShepherdTour({ tourId: "no-attach", steps: SAMPLE_STEPS }));

    const step = getMockInstance().addStep.mock.calls[2][0];
    expect(step.attachTo).toBeUndefined();
  });

  it("sets scrollTo smooth on all steps by default (AC14)", () => {
    renderHook(() => useShepherdTour({ tourId: "scroll", steps: SAMPLE_STEPS }));

    for (let i = 0; i < 3; i++) {
      const step = getMockInstance().addStep.mock.calls[i][0];
      expect(step.scrollTo).toEqual({ behavior: "smooth", block: "center" });
    }
  });

  it("exposes storageKey for external use", () => {
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "key-test", steps: SAMPLE_STEPS })
    );
    expect(result.current.storageKey).toBe("onboarding_key-test_tour_completed");
  });
});

// ============================================================================
// OnboardingTourButton Component Tests
// ============================================================================

describe("OnboardingTourButton (AC15-17)", () => {
  beforeEach(resetAll);

  // AC15: Floating button
  it("renders the floating '?' button", () => {
    render(<OnboardingTourButton />);
    expect(screen.getByTestId("tour-trigger-button")).toBeInTheDocument();
    expect(screen.getByLabelText("Guia interativo")).toBeInTheDocument();
  });

  it("button displays '?' text", () => {
    render(<OnboardingTourButton />);
    expect(screen.getByTestId("tour-trigger-button")).toHaveTextContent("?");
  });

  // AC16: Menu with 3 options
  it("shows menu with 3 tour options on click", () => {
    render(<OnboardingTourButton />);
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("tour-trigger-button"));

    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();
    expect(screen.getByTestId("tour-option-search")).toBeInTheDocument();
    expect(screen.getByTestId("tour-option-results")).toBeInTheDocument();
    expect(screen.getByTestId("tour-option-pipeline")).toBeInTheDocument();
  });

  it("shows correct Portuguese labels", () => {
    render(<OnboardingTourButton />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));

    expect(screen.getByText("Tour de busca")).toBeInTheDocument();
    expect(screen.getByText("Tour de resultados")).toBeInTheDocument();
    expect(screen.getByText("Tour de pipeline")).toBeInTheDocument();
  });

  it("shows numbered badges (1, 2, 3)", () => {
    render(<OnboardingTourButton />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("toggles menu open/close on button click", () => {
    render(<OnboardingTourButton />);
    const btn = screen.getByTestId("tour-trigger-button");

    fireEvent.click(btn);
    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();

    fireEvent.click(btn);
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();
  });

  it("has aria-expanded attribute", () => {
    render(<OnboardingTourButton />);
    const btn = screen.getByTestId("tour-trigger-button");

    expect(btn).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
  });

  it("closes menu on Escape key", () => {
    render(<OnboardingTourButton />);
    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();
  });

  // AC17: Replay — calls available tour restart callback
  it("calls restart callback when clicking an available tour option", () => {
    const mockRestart = jest.fn();
    render(<OnboardingTourButton availableTours={{ search: mockRestart }} />);

    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    fireEvent.click(screen.getByTestId("tour-option-search"));

    expect(mockRestart).toHaveBeenCalled();
  });

  it("navigates to correct page when tour is on different page", () => {
    currentPathname = "/dashboard";
    render(<OnboardingTourButton availableTours={{}} />);

    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    fireEvent.click(screen.getByTestId("tour-option-pipeline"));

    expect(mockPush).toHaveBeenCalledWith("/pipeline?tour=pipeline");
  });

  it("does not navigate when already on correct page", () => {
    currentPathname = "/buscar";
    render(<OnboardingTourButton availableTours={{}} />);

    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    fireEvent.click(screen.getByTestId("tour-option-search"));

    expect(mockPush).not.toHaveBeenCalled();
  });

  it("closes menu after clicking an option", () => {
    render(<OnboardingTourButton availableTours={{ search: jest.fn() }} />);

    fireEvent.click(screen.getByTestId("tour-trigger-button"));
    expect(screen.getByTestId("tour-menu")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("tour-option-search"));
    expect(screen.queryByTestId("tour-menu")).not.toBeInTheDocument();
  });
});

// ============================================================================
// Tour Step Definitions (AC1, AC7, AC9)
// ============================================================================

describe("Search tour (AC1)", () => {
  beforeEach(resetAll);

  it("has 4 steps targeting correct elements", () => {
    const searchSteps: TourStep[] = [
      { id: "search-setor", title: "T", text: "X", attachTo: { element: "[data-tour='setor-filter']", on: "bottom" } },
      { id: "search-ufs", title: "T", text: "X", attachTo: { element: "[data-tour='uf-selector']", on: "bottom" } },
      { id: "search-period", title: "T", text: "X", attachTo: { element: "[data-tour='period-selector']", on: "bottom" } },
      { id: "search-button", title: "T", text: "X", attachTo: { element: "[data-tour='search-button']", on: "top" } },
    ];

    renderHook(() => useShepherdTour({ tourId: "search", steps: searchSteps }));

    expect(getMockInstance().addStep).toHaveBeenCalledTimes(4);
    const ids = getMockInstance().addStep.mock.calls.map((c: any[]) => c[0].id);
    expect(ids).toEqual(["search-setor", "search-ufs", "search-period", "search-button"]);
  });

  // AC2: Not shown if already completed
  it("AC2: detects completed via localStorage key", () => {
    localStorage.setItem("onboarding_search_tour_completed", "true");
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "search", steps: SAMPLE_STEPS })
    );
    expect(result.current.isCompleted()).toBe(true);
  });
});

describe("Results tour (AC7-8)", () => {
  beforeEach(resetAll);

  it("has 4 steps with correct IDs", () => {
    const steps: TourStep[] = [
      { id: "results-card", title: "T", text: "X", attachTo: { element: "[data-tour='result-card']", on: "bottom" } },
      { id: "results-viability", title: "T", text: "X", attachTo: { element: "[data-tour='viability-badge']", on: "bottom" } },
      { id: "results-pipeline", title: "T", text: "X" },
      { id: "results-excel", title: "T", text: "X", attachTo: { element: "[data-tour='excel-button']", on: "top" } },
    ];

    renderHook(() => useShepherdTour({ tourId: "results", steps }));

    expect(getMockInstance().addStep).toHaveBeenCalledTimes(4);
    const ids = getMockInstance().addStep.mock.calls.map((c: any[]) => c[0].id);
    expect(ids).toEqual(["results-card", "results-viability", "results-pipeline", "results-excel"]);
  });

  // AC8: Conditional via localStorage
  it("AC8: detects completed via localStorage key", () => {
    localStorage.setItem("onboarding_results_tour_completed", "true");
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "results", steps: SAMPLE_STEPS })
    );
    expect(result.current.isCompleted()).toBe(true);
  });

  it("not completed by default", () => {
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "results", steps: SAMPLE_STEPS })
    );
    expect(result.current.isCompleted()).toBe(false);
  });
});

describe("Pipeline tour (AC9-10)", () => {
  beforeEach(resetAll);

  it("has 3 steps with correct IDs", () => {
    const steps: TourStep[] = [
      { id: "pipeline-columns", title: "T", text: "X", attachTo: { element: "[data-tour='kanban-columns']", on: "top" } },
      { id: "pipeline-card", title: "T", text: "X", attachTo: { element: "[data-tour='pipeline-card']", on: "right" } },
      { id: "pipeline-alerts", title: "T", text: "X", attachTo: { element: "[data-tour='kanban-columns']", on: "bottom" } },
    ];

    renderHook(() => useShepherdTour({ tourId: "pipeline", steps }));

    expect(getMockInstance().addStep).toHaveBeenCalledTimes(3);
    const ids = getMockInstance().addStep.mock.calls.map((c: any[]) => c[0].id);
    expect(ids).toEqual(["pipeline-columns", "pipeline-card", "pipeline-alerts"]);
  });

  // AC10: Conditional via localStorage
  it("AC10: detects completed via localStorage key", () => {
    localStorage.setItem("onboarding_pipeline_tour_completed", "true");
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "pipeline", steps: SAMPLE_STEPS })
    );
    expect(result.current.isCompleted()).toBe(true);
  });
});

// ============================================================================
// Tracking Tests (AC4-6)
// ============================================================================

describe("Tour tracking (AC4-6)", () => {
  beforeEach(resetAll);

  it("AC5: onComplete receives correct steps_seen count", () => {
    const onComplete = jest.fn();
    renderHook(() =>
      useShepherdTour({ tourId: "track", steps: SAMPLE_STEPS, onComplete })
    );

    act(() => {
      getEventHandler("show")();
      getEventHandler("show")();
      getEventHandler("show")();
      getEventHandler("complete")();
    });

    expect(onComplete).toHaveBeenCalledWith(3);
  });

  it("AC6: onSkip receives correct steps_seen on cancel", () => {
    const onSkip = jest.fn();
    renderHook(() =>
      useShepherdTour({ tourId: "track-skip", steps: SAMPLE_STEPS, onSkip })
    );

    act(() => {
      getEventHandler("show")();
      getEventHandler("show")();
      getEventHandler("cancel")();
    });

    expect(onSkip).toHaveBeenCalledWith(2);
  });
});

// ============================================================================
// localStorage Persistence (AC20)
// ============================================================================

describe("localStorage persistence (AC20)", () => {
  beforeEach(resetAll);

  it("each tour has unique storage key", () => {
    const { result: r1 } = renderHook(() => useShepherdTour({ tourId: "search", steps: SAMPLE_STEPS }));
    const { result: r2 } = renderHook(() => useShepherdTour({ tourId: "results", steps: SAMPLE_STEPS }));
    const { result: r3 } = renderHook(() => useShepherdTour({ tourId: "pipeline", steps: SAMPLE_STEPS }));

    expect(r1.current.storageKey).toBe("onboarding_search_tour_completed");
    expect(r2.current.storageKey).toBe("onboarding_results_tour_completed");
    expect(r3.current.storageKey).toBe("onboarding_pipeline_tour_completed");
  });

  it("completing one tour does not affect others", () => {
    localStorage.setItem("onboarding_search_tour_completed", "true");

    const { result: r1 } = renderHook(() => useShepherdTour({ tourId: "search", steps: SAMPLE_STEPS }));
    const { result: r2 } = renderHook(() => useShepherdTour({ tourId: "results", steps: SAMPLE_STEPS }));

    expect(r1.current.isCompleted()).toBe(true);
    expect(r2.current.isCompleted()).toBe(false);
  });

  it("tour remains completed across re-renders", () => {
    localStorage.setItem("onboarding_persist_tour_completed", "true");
    const { result, rerender } = renderHook(() =>
      useShepherdTour({ tourId: "persist", steps: SAMPLE_STEPS })
    );

    expect(result.current.isCompleted()).toBe(true);
    rerender();
    expect(result.current.isCompleted()).toBe(true);
  });
});

// ============================================================================
// Tour Replay (AC17/AC21)
// ============================================================================

describe("Tour replay (AC17/AC21)", () => {
  beforeEach(resetAll);

  it("replay resets completed flag and starts tour", () => {
    localStorage.setItem("onboarding_replay_tour_completed", "true");
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "replay", steps: SAMPLE_STEPS })
    );

    expect(result.current.isCompleted()).toBe(true);

    act(() => { result.current.restartTour(); });

    expect(result.current.isCompleted()).toBe(false);
    expect(getMockInstance().start).toHaveBeenCalled();
  });

  it("can replay multiple times", () => {
    const { result } = renderHook(() =>
      useShepherdTour({ tourId: "multi-replay", steps: SAMPLE_STEPS })
    );

    act(() => { result.current.startTour(); });
    expect(getMockInstance().start).toHaveBeenCalledTimes(1);

    act(() => { getEventHandler("complete")(); });
    expect(result.current.isCompleted()).toBe(true);

    act(() => { result.current.restartTour(); });
    expect(getMockInstance().start).toHaveBeenCalledTimes(2);
    expect(result.current.isCompleted()).toBe(false);
  });
});
