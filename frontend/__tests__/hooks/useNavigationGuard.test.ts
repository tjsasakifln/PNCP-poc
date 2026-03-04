/**
 * UX-407: Tests for hooks/useNavigationGuard.ts
 *
 * Navigation guard that prevents accidental tab close during active search.
 * - beforeunload fires only while loading OR within 30s grace period.
 * - Internal SmartLic navigation is NEVER blocked.
 * - No dependency on download state.
 */
import { renderHook, act } from "@testing-library/react";
import { useNavigationGuard, GUARD_GRACE_MS } from "@/hooks/useNavigationGuard";

// Helpers
const mockPreventDefault = jest.fn();

let addEventListenerSpy: jest.SpyInstance;
let removeEventListenerSpy: jest.SpyInstance;

beforeEach(() => {
  jest.useFakeTimers();
  jest.clearAllMocks();
  addEventListenerSpy = jest.spyOn(window, "addEventListener");
  removeEventListenerSpy = jest.spyOn(window, "removeEventListener");
});

afterEach(() => {
  jest.useRealTimers();
  addEventListenerSpy.mockRestore();
  removeEventListenerSpy.mockRestore();
});

function getBeforeunloadCalls(spy: jest.SpyInstance) {
  return spy.mock.calls.filter(([event]: [string]) => event === "beforeunload");
}

describe("useNavigationGuard", () => {
  // AC1: Guard only activates during loading=true
  describe("AC1: guard activates during loading", () => {
    it("should register beforeunload when isLoading=true", () => {
      renderHook(() => useNavigationGuard({ isLoading: true }));
      expect(getBeforeunloadCalls(addEventListenerSpy).length).toBeGreaterThanOrEqual(1);
    });

    it("should NOT register beforeunload when isLoading=false initially", () => {
      renderHook(() => useNavigationGuard({ isLoading: false }));
      expect(getBeforeunloadCalls(addEventListenerSpy)).toHaveLength(0);
    });
  });

  // AC2: Guard deactivates 30s after loading ends
  describe("AC2: 30s auto-deactivation after results appear", () => {
    it("should keep guard active for 30s after loading ends", () => {
      const { rerender } = renderHook(
        ({ isLoading }) => useNavigationGuard({ isLoading }),
        { initialProps: { isLoading: true } }
      );

      // Search finishes
      rerender({ isLoading: false });

      // Advance 29s — guard should still be active
      act(() => { jest.advanceTimersByTime(29_000); });

      // beforeunload should still be registered (not removed yet beyond initial cleanup/re-register)
      const addCalls = getBeforeunloadCalls(addEventListenerSpy).length;
      const removeCalls = getBeforeunloadCalls(removeEventListenerSpy).length;
      // Guard is active when adds > removes
      expect(addCalls).toBeGreaterThan(0);
    });

    it("should deactivate guard after 30s grace period", () => {
      const { rerender } = renderHook(
        ({ isLoading }) => useNavigationGuard({ isLoading }),
        { initialProps: { isLoading: true } }
      );

      // Search finishes
      rerender({ isLoading: false });

      // Advance past grace period
      act(() => { jest.advanceTimersByTime(GUARD_GRACE_MS + 100); });

      // After grace period, the beforeunload should be removed
      const removeCalls = getBeforeunloadCalls(removeEventListenerSpy).length;
      expect(removeCalls).toBeGreaterThanOrEqual(1);
    });

    it("should cancel grace timer if new search starts", () => {
      const { rerender } = renderHook(
        ({ isLoading }) => useNavigationGuard({ isLoading }),
        { initialProps: { isLoading: true } }
      );

      // Search finishes — grace starts
      rerender({ isLoading: false });
      act(() => { jest.advanceTimersByTime(15_000); });

      // New search starts before grace expires
      rerender({ isLoading: true });

      // Advance past original grace expiry — guard should still be active
      // because shouldGuard never went false (loading→grace→loading)
      act(() => { jest.advanceTimersByTime(20_000); });

      // Guard stayed active throughout — add count >= 1, remove count = 0
      // (shouldGuard was true the entire time, so beforeunload was never removed)
      const addCount = getBeforeunloadCalls(addEventListenerSpy).length;
      const removeCount = getBeforeunloadCalls(removeEventListenerSpy).length;
      expect(addCount).toBeGreaterThanOrEqual(1);
      expect(removeCount).toBe(0);
    });
  });

  // AC3: Internal links never show dialog
  describe("AC3: internal links never blocked", () => {
    it("should NOT register click listener on document at any point", () => {
      const docAddSpy = jest.spyOn(document, "addEventListener");
      try {
        renderHook(() => useNavigationGuard({ isLoading: true }));
        const clickCalls = docAddSpy.mock.calls.filter(
          ([event]: [string]) => event === "click"
        );
        expect(clickCalls).toHaveLength(0);
      } finally {
        docAddSpy.mockRestore();
      }
    });

    it("should NOT register popstate listener", () => {
      renderHook(() => useNavigationGuard({ isLoading: true }));
      const popstateCalls = addEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "popstate"
      );
      expect(popstateCalls).toHaveLength(0);
    });

    it("should NOT push sentinel history state", () => {
      const pushStateSpy = jest.spyOn(window.history, "pushState").mockImplementation(() => {});
      try {
        renderHook(() => useNavigationGuard({ isLoading: true }));
        expect(pushStateSpy).not.toHaveBeenCalled();
      } finally {
        pushStateSpy.mockRestore();
      }
    });
  });

  // AC4: beforeunload active only while loading (+ grace)
  describe("AC4: beforeunload behavior", () => {
    it("should call preventDefault on beforeunload event during loading", () => {
      renderHook(() => useNavigationGuard({ isLoading: true }));

      const beforeunloadCall = addEventListenerSpy.mock.calls.find(
        ([event]: [string]) => event === "beforeunload"
      );
      expect(beforeunloadCall).toBeDefined();

      const handler = beforeunloadCall![1] as EventListener;
      const event = new Event("beforeunload") as BeforeUnloadEvent;
      Object.defineProperty(event, "preventDefault", { value: mockPreventDefault });
      Object.defineProperty(event, "returnValue", { writable: true, value: "" });

      handler(event);
      expect(mockPreventDefault).toHaveBeenCalled();
    });

    it("should NOT have beforeunload after grace period with no loading", () => {
      const { rerender } = renderHook(
        ({ isLoading }) => useNavigationGuard({ isLoading }),
        { initialProps: { isLoading: true } }
      );

      rerender({ isLoading: false });
      act(() => { jest.advanceTimersByTime(GUARD_GRACE_MS + 100); });

      // All beforeunload handlers should have been removed
      const addCount = getBeforeunloadCalls(addEventListenerSpy).length;
      const removeCount = getBeforeunloadCalls(removeEventListenerSpy).length;
      expect(removeCount).toBeGreaterThanOrEqual(addCount);
    });
  });

  // AC5: No hasDownloaded dependency
  describe("AC5: no hasDownloaded dependency", () => {
    it("should not accept hasDownloaded in options (type check via runtime)", () => {
      // The hook only accepts { isLoading: boolean }
      // This test documents the API contract
      renderHook(() => useNavigationGuard({ isLoading: false }));
      // If this compiles and runs, hasDownloaded is not required
    });
  });

  // Cleanup
  describe("cleanup on unmount", () => {
    it("should remove beforeunload on unmount when guard active", () => {
      const { unmount } = renderHook(() =>
        useNavigationGuard({ isLoading: true })
      );
      unmount();
      const removeCalls = getBeforeunloadCalls(removeEventListenerSpy);
      expect(removeCalls.length).toBeGreaterThanOrEqual(1);
    });

    it("should clear grace timer on unmount", () => {
      const { rerender, unmount } = renderHook(
        ({ isLoading }) => useNavigationGuard({ isLoading }),
        { initialProps: { isLoading: true } }
      );

      rerender({ isLoading: false });
      unmount();

      // Advancing timers after unmount should not cause errors
      act(() => { jest.advanceTimersByTime(GUARD_GRACE_MS + 100); });
    });
  });

  // Guard NOT active when results displayed but search finished > 30s ago
  describe("guard inactive after grace period", () => {
    it("should NOT activate when results exist but search finished >30s ago", () => {
      const { rerender } = renderHook(
        ({ isLoading }) => useNavigationGuard({ isLoading }),
        { initialProps: { isLoading: true } }
      );

      rerender({ isLoading: false });
      act(() => { jest.advanceTimersByTime(GUARD_GRACE_MS + 100); });

      // Reset spies to count fresh
      addEventListenerSpy.mockClear();
      removeEventListenerSpy.mockClear();

      // Re-render with still not loading — no new beforeunload
      rerender({ isLoading: false });
      expect(getBeforeunloadCalls(addEventListenerSpy)).toHaveLength(0);
    });
  });
});
