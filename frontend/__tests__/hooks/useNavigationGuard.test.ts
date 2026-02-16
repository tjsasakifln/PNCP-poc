/**
 * Tests for hooks/useNavigationGuard.ts — TD-006 AC9-AC15
 * Navigation guard that prevents accidental loss of search results.
 */
import { renderHook, act } from "@testing-library/react";
import { useNavigationGuard } from "@/hooks/useNavigationGuard";

// Helpers
const mockConfirm = jest.fn(() => true);
const mockPreventDefault = jest.fn();
const mockStopPropagation = jest.fn();

let addEventListenerSpy: jest.SpyInstance;
let removeEventListenerSpy: jest.SpyInstance;
let docAddEventListenerSpy: jest.SpyInstance;
let docRemoveEventListenerSpy: jest.SpyInstance;
let pushStateSpy: jest.SpyInstance;
let backSpy: jest.SpyInstance;

beforeEach(() => {
  jest.clearAllMocks();
  window.confirm = mockConfirm;
  addEventListenerSpy = jest.spyOn(window, "addEventListener");
  removeEventListenerSpy = jest.spyOn(window, "removeEventListener");
  docAddEventListenerSpy = jest.spyOn(document, "addEventListener");
  docRemoveEventListenerSpy = jest.spyOn(document, "removeEventListener");
  pushStateSpy = jest.spyOn(window.history, "pushState").mockImplementation(() => {});
  backSpy = jest.spyOn(window.history, "back").mockImplementation(() => {});
});

afterEach(() => {
  addEventListenerSpy.mockRestore();
  removeEventListenerSpy.mockRestore();
  docAddEventListenerSpy.mockRestore();
  docRemoveEventListenerSpy.mockRestore();
  pushStateSpy.mockRestore();
  backSpy.mockRestore();
});

describe("useNavigationGuard", () => {
  describe("when hasResults=false", () => {
    it("should NOT register beforeunload listener", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: false, hasDownloaded: false })
      );
      const beforeunloadCalls = addEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "beforeunload"
      );
      expect(beforeunloadCalls).toHaveLength(0);
    });

    it("should NOT register click listener on document", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: false, hasDownloaded: false })
      );
      const clickCalls = docAddEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "click"
      );
      expect(clickCalls).toHaveLength(0);
    });
  });

  describe("when hasResults=true and hasDownloaded=false", () => {
    it("should register beforeunload listener", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: false })
      );
      const beforeunloadCalls = addEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "beforeunload"
      );
      expect(beforeunloadCalls.length).toBeGreaterThanOrEqual(1);
    });

    it("should register click listener in capture phase on document", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: false })
      );
      const clickCalls = docAddEventListenerSpy.mock.calls.filter(
        ([event, , capture]: [string, unknown, boolean]) =>
          event === "click" && capture === true
      );
      expect(clickCalls.length).toBeGreaterThanOrEqual(1);
    });

    it("should register popstate listener and push sentinel state", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: false })
      );
      expect(pushStateSpy).toHaveBeenCalledWith(
        { __navigationGuard: true },
        ""
      );
      const popstateCalls = addEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "popstate"
      );
      expect(popstateCalls.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("when hasResults=true but hasDownloaded=true (AC15)", () => {
    it("should NOT register beforeunload listener after download", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: true })
      );
      const beforeunloadCalls = addEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "beforeunload"
      );
      expect(beforeunloadCalls).toHaveLength(0);
    });

    it("should NOT register click listener on document after download", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: true })
      );
      const clickCalls = docAddEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "click"
      );
      expect(clickCalls).toHaveLength(0);
    });
  });

  describe("beforeunload handler behavior", () => {
    it("should call preventDefault and set returnValue on beforeunload event", () => {
      renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: false })
      );

      // Get the registered beforeunload handler
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
      expect(event.returnValue).toBe(
        "Você tem resultados de busca que serão perdidos. Deseja sair?"
      );
    });
  });

  describe("cleanup on unmount", () => {
    it("should remove beforeunload listener on unmount", () => {
      const { unmount } = renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: false })
      );
      unmount();
      const removeBeforeunload = removeEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "beforeunload"
      );
      expect(removeBeforeunload.length).toBeGreaterThanOrEqual(1);
    });

    it("should remove click listener on document on unmount", () => {
      const { unmount } = renderHook(() =>
        useNavigationGuard({ hasResults: true, hasDownloaded: false })
      );
      unmount();
      const removeClick = docRemoveEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "click"
      );
      expect(removeClick.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("guard deactivation when results are cleared", () => {
    it("should remove listeners when hasResults changes to false", () => {
      const { rerender } = renderHook(
        ({ hasResults, hasDownloaded }) =>
          useNavigationGuard({ hasResults, hasDownloaded }),
        { initialProps: { hasResults: true, hasDownloaded: false } }
      );

      // At this point, listeners should be registered
      const initialBeforeunload = addEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "beforeunload"
      ).length;
      expect(initialBeforeunload).toBeGreaterThanOrEqual(1);

      // Deactivate guard
      rerender({ hasResults: false, hasDownloaded: false });

      // beforeunload should have been removed
      const removedBeforeunload = removeEventListenerSpy.mock.calls.filter(
        ([event]: [string]) => event === "beforeunload"
      ).length;
      expect(removedBeforeunload).toBeGreaterThanOrEqual(1);
    });
  });

  describe("custom message", () => {
    it("should use custom message in beforeunload", () => {
      const customMsg = "Sair vai apagar seus dados!";
      renderHook(() =>
        useNavigationGuard({
          hasResults: true,
          hasDownloaded: false,
          message: customMsg,
        })
      );

      const beforeunloadCall = addEventListenerSpy.mock.calls.find(
        ([event]: [string]) => event === "beforeunload"
      );
      const handler = beforeunloadCall![1] as EventListener;
      const event = new Event("beforeunload") as BeforeUnloadEvent;
      Object.defineProperty(event, "preventDefault", { value: jest.fn() });
      Object.defineProperty(event, "returnValue", { writable: true, value: "" });

      handler(event);
      expect(event.returnValue).toBe(customMsg);
    });
  });
});
