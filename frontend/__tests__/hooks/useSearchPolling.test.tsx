/**
 * CRIT-003: Tests for useSearchPolling hook.
 *
 * Covers:
 * - AC12: Polling starts when SSE disconnects
 * - AC13: Polling stops on terminal status
 * - Polling converts to SearchProgressEvent format
 * - Error handling
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { useSearchPolling } from "../../hooks/useSearchPolling";

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.useFakeTimers();
  mockFetch.mockReset();
});

afterEach(() => {
  jest.useRealTimers();
});

describe("useSearchPolling", () => {
  it("does not poll when disabled", () => {
    renderHook(() =>
      useSearchPolling({
        searchId: "test-123",
        enabled: false,
      })
    );

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("does not poll when searchId is null", () => {
    renderHook(() =>
      useSearchPolling({
        searchId: null,
        enabled: true,
      })
    );

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("polls immediately when enabled with searchId", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-123",
        status: "fetching",
        progress: 30,
        stage: "execute",
        started_at: "2026-01-01T00:00:00Z",
        elapsed_ms: 5000,
        llm_status: "pending",
        excel_status: "pending",
        error_message: null,
        error_code: null,
      }),
    });

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-123",
        enabled: true,
      })
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/search-status?search_id=test-123",
      expect.objectContaining({ headers: expect.any(Object) })
    );

    await waitFor(() => {
      expect(result.current.status?.status).toBe("fetching");
    });
    expect(result.current.isPolling).toBe(true);
  });

  it("stops polling on terminal status (completed)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-done",
        status: "completed",
        progress: 100,
        stage: "persist",
        started_at: "2026-01-01T00:00:00Z",
        elapsed_ms: 15000,
        llm_status: "ready",
        excel_status: "ready",
        error_message: null,
        error_code: null,
      }),
    });

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-done",
        enabled: true,
      })
    );

    await waitFor(() => {
      expect(result.current.status?.status).toBe("completed");
    });

    // AC13: Should stop polling
    expect(result.current.isPolling).toBe(false);
  });

  it("stops polling on terminal status (failed)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-fail",
        status: "failed",
        progress: -1,
        stage: "execute",
        started_at: "2026-01-01T00:00:00Z",
        elapsed_ms: 8000,
        llm_status: "pending",
        excel_status: "pending",
        error_message: "API timeout",
        error_code: "sources_unavailable",
      }),
    });

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-fail",
        enabled: true,
      })
    );

    await waitFor(() => {
      expect(result.current.status?.status).toBe("failed");
    });

    expect(result.current.isPolling).toBe(false);
  });

  it("converts to SearchProgressEvent format", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-conv",
        status: "filtering",
        progress: 60,
        stage: "filter",
        started_at: "2026-01-01T00:00:00Z",
        elapsed_ms: 10000,
        llm_status: "pending",
        excel_status: "pending",
        error_message: null,
        error_code: null,
      }),
    });

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-conv",
        enabled: true,
      })
    );

    await waitFor(() => {
      expect(result.current.asProgressEvent).not.toBeNull();
    });

    expect(result.current.asProgressEvent?.stage).toBe("filter");
    expect(result.current.asProgressEvent?.progress).toBe(60);
    expect(result.current.asProgressEvent?.message).toContain("Filtrando");
  });

  it("converts completed to 'complete' stage", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-comp",
        status: "completed",
        progress: 100,
        stage: "persist",
        started_at: null,
        elapsed_ms: null,
        llm_status: "ready",
        excel_status: "ready",
        error_message: null,
        error_code: null,
      }),
    });

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-comp",
        enabled: true,
      })
    );

    await waitFor(() => {
      expect(result.current.asProgressEvent?.stage).toBe("complete");
    });
  });

  it("converts failed to 'error' stage", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-err",
        status: "failed",
        progress: -1,
        stage: null,
        started_at: null,
        elapsed_ms: null,
        llm_status: "pending",
        excel_status: "pending",
        error_message: "Something broke",
        error_code: "unknown",
      }),
    });

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-err",
        enabled: true,
      })
    );

    await waitFor(() => {
      expect(result.current.asProgressEvent?.stage).toBe("error");
    });
    expect(result.current.asProgressEvent?.message).toBe("Something broke");
  });

  it("handles fetch errors gracefully", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-net-err",
        enabled: true,
      })
    );

    // Should not crash — status remains null
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    expect(result.current.status).toBeNull();
    expect(result.current.isPolling).toBe(true); // Still polling
  });

  it("handles non-ok response gracefully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    const { result } = renderHook(() =>
      useSearchPolling({
        searchId: "test-404",
        enabled: true,
      })
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    expect(result.current.status).toBeNull();
  });

  it("passes auth token in headers", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-auth",
        status: "fetching",
        progress: 30,
        stage: "execute",
        started_at: null,
        elapsed_ms: null,
        llm_status: "pending",
        excel_status: "pending",
        error_message: null,
        error_code: null,
      }),
    });

    renderHook(() =>
      useSearchPolling({
        searchId: "test-auth",
        enabled: true,
        authToken: "my-token",
      })
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].headers.Authorization).toBe("Bearer my-token");
  });

  it("calls onStatusUpdate callback", async () => {
    const onStatusUpdate = jest.fn();

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        search_id: "test-cb",
        status: "completed",
        progress: 100,
        stage: "persist",
        started_at: null,
        elapsed_ms: null,
        llm_status: "ready",
        excel_status: "ready",
        error_message: null,
        error_code: null,
      }),
    });

    renderHook(() =>
      useSearchPolling({
        searchId: "test-cb",
        enabled: true,
        onStatusUpdate,
      })
    );

    await waitFor(() => {
      expect(onStatusUpdate).toHaveBeenCalledWith(
        expect.objectContaining({ status: "completed" })
      );
    });
  });

  it("stops polling when disabled after start", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        search_id: "test-stop",
        status: "fetching",
        progress: 30,
        stage: "execute",
        started_at: null,
        elapsed_ms: null,
        llm_status: "pending",
        excel_status: "pending",
        error_message: null,
        error_code: null,
      }),
    });

    const { result, rerender } = renderHook(
      ({ enabled }) =>
        useSearchPolling({
          searchId: "test-stop",
          enabled,
        }),
      { initialProps: { enabled: true } }
    );

    await waitFor(() => {
      expect(result.current.isPolling).toBe(true);
    });

    // Disable polling
    rerender({ enabled: false });

    expect(result.current.isPolling).toBe(false);
  });
});
