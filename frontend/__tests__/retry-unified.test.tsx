/**
 * GTM-UX-003: Unified Retry UX Tests
 *
 * T1: Auto-retry uses contextual message (not "reiniciando")
 * T2: Cooldown 5s→10s→15s (not 10s→20s→30s)
 * T3: "Tentar agora" button works without extra cooldown
 * T4: After 3 failures shows partial results option
 * T5: Only 1 retry mechanism active
 */

import { renderHook, act, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mock dependencies BEFORE importing
// ---------------------------------------------------------------------------

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: { access_token: "test-token" } }),
}));

jest.mock("../hooks/useAnalytics", () => {
  const fn = jest.fn();
  return { useAnalytics: () => ({ trackEvent: fn }), __mockTrackEvent: fn };
});

jest.mock("../hooks/useQuota", () => {
  const fn = jest.fn();
  return { useQuota: () => ({ refresh: fn }), __mockRefreshQuota: fn };
});

jest.mock("../hooks/useSearchSSE", () => ({
  useSearchSSE: () => ({
    currentEvent: null,
    sseAvailable: false,
    sseDisconnected: false,
    isDegraded: false,
    degradedDetail: null,
    partialProgress: null,
    refreshAvailable: null,
    ufStatuses: new Map(),
    ufTotalFound: 0,
    ufAllComplete: false,
    batchProgress: null,
  }),
}));

jest.mock("../hooks/useSearchPolling", () => ({
  useSearchPolling: () => ({ asProgressEvent: null }),
}));

jest.mock("../hooks/useSavedSearches", () => ({
  useSavedSearches: () => ({
    saveNewSearch: jest.fn(),
    isMaxCapacity: false,
  }),
}));

jest.mock("../lib/searchStatePersistence", () => ({
  saveSearchState: jest.fn(),
  restoreSearchState: jest.fn(() => null),
}));

jest.mock("../lib/lastSearchCache", () => ({
  saveLastSearch: jest.fn(),
}));

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

jest.mock("../lib/utils/dateDiffInDays", () => ({
  dateDiffInDays: () => 14,
}));

jest.mock("../lib/utils/correlationId", () => ({
  getCorrelationId: () => "test-correlation-id",
  logCorrelatedRequest: jest.fn(),
}));

Object.defineProperty(global, "crypto", {
  value: { randomUUID: () => "test-uuid-retry-" + Math.random().toString(36).slice(2) },
  writable: true,
  configurable: true,
});

// ---------------------------------------------------------------------------
// Import modules under test
// ---------------------------------------------------------------------------

import { useSearch } from "../app/buscar/hooks/useSearch";
import { getRetryMessage } from "../lib/error-messages";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeFilters(overrides: Record<string, unknown> = {}) {
  return {
    ufsSelecionadas: new Set(["SP"]),
    dataInicial: "2026-02-01",
    dataFinal: "2026-02-15",
    searchMode: "setor" as const,
    modoBusca: "abertas" as const,
    setorId: "vestuario",
    termosArray: [] as string[],
    status: "todos" as any,
    modalidades: [] as number[],
    valorMin: null,
    valorMax: null,
    esferas: [] as any[],
    municipios: [] as any[],
    ordenacao: "relevancia" as any,
    sectorName: "Vestuario",
    canSearch: true,
    setOrdenacao: jest.fn(),
    setUfsSelecionadas: jest.fn(),
    setDataInicial: jest.fn(),
    setDataFinal: jest.fn(),
    setSearchMode: jest.fn(),
    setSetorId: jest.fn(),
    setTermosArray: jest.fn(),
    setStatus: jest.fn(),
    setModalidades: jest.fn(),
    setValorMin: jest.fn(),
    setValorMax: jest.fn(),
    setEsferas: jest.fn(),
    setMunicipios: jest.fn(),
    ...overrides,
  };
}

/**
 * Mock fetch returning HTTP error response.
 * Use 504 for transient errors — it triggers auto-retry countdown
 * but does NOT trigger client-side retry loop in buscar (only 500/502/503 do).
 */
function mockFetchHttpError(status: number, body: Record<string, unknown> = {}) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status,
    json: () => Promise.resolve({ message: body.message || "Error", ...body }),
    text: () => Promise.resolve(JSON.stringify(body)),
  } as unknown as Response);
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe("GTM-UX-003: Unified Retry UX", () => {
  // -------------------------------------------------------------------------
  // T1: Auto-retry uses contextual message (not "reiniciando")
  // -------------------------------------------------------------------------

  describe("T1: Contextual retry messages", () => {
    test("getRetryMessage returns timeout message for HTTP 504", () => {
      const msg = getRetryMessage(504, "Gateway Timeout");
      expect(msg).toContain("demorando mais que o esperado");
      expect(msg).not.toContain("reiniciando");
    });

    test("getRetryMessage returns service unavailable for HTTP 502", () => {
      const msg = getRetryMessage(502, "Bad Gateway");
      expect(msg).toContain("temporariamente indisponível");
      expect(msg).not.toContain("reiniciando");
    });

    test("getRetryMessage returns service unavailable for HTTP 503", () => {
      const msg = getRetryMessage(503, "Service Unavailable");
      expect(msg).toContain("temporariamente indisponível");
      expect(msg).not.toContain("reiniciando");
    });

    test("getRetryMessage returns network message for fetch failed", () => {
      const msg = getRetryMessage(null, "Failed to fetch");
      expect(msg).toContain("Sem conexão");
      expect(msg).not.toContain("reiniciando");
    });

    test("getRetryMessage returns timeout message for PNCP timeout", () => {
      const msg = getRetryMessage(null, "PNCP timeout exceeded");
      expect(msg).toContain("demorando mais que o esperado");
    });

    test("getRetryMessage NEVER returns 'reiniciando' for any transient error", () => {
      const cases = [
        { status: 502 as number | null, msg: "Bad Gateway" },
        { status: 503 as number | null, msg: "Service Unavailable" },
        { status: 504 as number | null, msg: "Gateway Timeout" },
        { status: null, msg: "Failed to fetch" },
        { status: null, msg: "NetworkError" },
        { status: null, msg: "fetch failed" },
        { status: null, msg: "timeout" },
        { status: null, msg: "demorou demais" },
      ];
      for (const { status, msg } of cases) {
        const result = getRetryMessage(status, msg);
        expect(result).not.toContain("reiniciando");
      }
    });
  });

  // -------------------------------------------------------------------------
  // T2: Cooldown 5s→10s→15s (not 10s→20s→30s)
  // -------------------------------------------------------------------------

  describe("T2: Reduced cooldown timing", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => {
      jest.useRealTimers();
      jest.restoreAllMocks();
    });

    test("first retry starts at 5s countdown (not 10s)", async () => {
      // 504 is transient but bypasses client-side retry loop
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      await act(async () => {
        await result.current.buscar();
      });

      expect(result.current.retryCountdown).toBe(5);
    });

    test("second retry starts at 10s countdown (not 20s)", async () => {
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      // First search → 5s countdown
      await act(async () => {
        await result.current.buscar();
      });
      expect(result.current.retryCountdown).toBe(5);

      // Advance 5s to trigger auto-retry
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // Wait for auto-retry fetch to complete (fails again with 504)
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });

      // Second countdown should be 10s
      await waitFor(() => {
        expect(result.current.retryCountdown).toBe(10);
      });
    });

    test("third retry starts at 15s countdown (not 30s)", async () => {
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      // 1st attempt → 5s countdown
      await act(async () => {
        await result.current.buscar();
      });
      expect(result.current.retryCountdown).toBe(5);

      // Exhaust 1st → auto-retry → 10s countdown
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      await waitFor(() => {
        expect(result.current.retryCountdown).toBe(10);
      });

      // Exhaust 2nd → auto-retry → 15s countdown
      await act(async () => {
        jest.advanceTimersByTime(10000);
      });
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      await waitFor(() => {
        expect(result.current.retryCountdown).toBe(15);
      });
    });
  });

  // -------------------------------------------------------------------------
  // T3: "Tentar agora" button works without extra cooldown
  // -------------------------------------------------------------------------

  describe("T3: Tentar agora without cooldown", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => {
      jest.useRealTimers();
      jest.restoreAllMocks();
    });

    test("retryNow clears countdown immediately", async () => {
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      await act(async () => {
        await result.current.buscar();
      });

      expect(result.current.retryCountdown).toBe(5);

      // Hit "Tentar agora"
      act(() => {
        result.current.retryNow();
      });

      expect(result.current.retryCountdown).toBeNull();
    });

    test("no 30-second cooldown on manual retry — non-transient error has no countdown at all", async () => {
      // 400 is not transient, so no auto-retry and no cooldown
      mockFetchHttpError(400, { message: "Bad Request" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      await act(async () => {
        await result.current.buscar();
      });

      // No countdown should be set — manual retry is immediately available
      expect(result.current.retryCountdown).toBeNull();
      expect(result.current.error).toBeTruthy();
    });
  });

  // -------------------------------------------------------------------------
  // T4: After 3 failures shows partial results option
  // -------------------------------------------------------------------------

  describe("T4: Retry exhaustion with partial results", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => {
      jest.useRealTimers();
      jest.restoreAllMocks();
    });

    test("retryExhausted is true after 3 auto-retry attempts", async () => {
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      // Attempt 1 → 5s countdown
      await act(async () => {
        await result.current.buscar();
      });
      expect(result.current.retryExhausted).toBe(false);
      expect(result.current.retryCountdown).toBe(5);

      // Exhaust 1st → auto-retry attempt 2 → 10s
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      await waitFor(() => {
        expect(result.current.retryCountdown).toBe(10);
      });
      expect(result.current.retryExhausted).toBe(false);

      // Exhaust 2nd → auto-retry attempt 3 → 15s
      await act(async () => {
        jest.advanceTimersByTime(10000);
      });
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      await waitFor(() => {
        expect(result.current.retryCountdown).toBe(15);
      });
      expect(result.current.retryExhausted).toBe(false);

      // Exhaust 3rd → no more retries → exhausted
      await act(async () => {
        jest.advanceTimersByTime(15000);
      });
      await act(async () => {
        await Promise.resolve();
        await Promise.resolve();
      });
      await waitFor(() => {
        expect(result.current.retryExhausted).toBe(true);
      });
      expect(result.current.retryCountdown).toBeNull();
    });
  });

  // -------------------------------------------------------------------------
  // T5: Only 1 retry mechanism active
  // -------------------------------------------------------------------------

  describe("T5: Single retry mechanism", () => {
    beforeEach(() => jest.useFakeTimers());
    afterEach(() => {
      jest.useRealTimers();
      jest.restoreAllMocks();
    });

    test("retryCountdown and retryMessage are set together for transient error", async () => {
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      await act(async () => {
        await result.current.buscar();
      });

      // Both should be set together — single unified mechanism
      expect(result.current.retryCountdown).toBe(5);
      expect(result.current.retryMessage).toBeTruthy();
      expect(result.current.retryMessage).not.toContain("reiniciando");
    });

    test("new user search resets ALL retry state", async () => {
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      // First search triggers auto-retry
      await act(async () => {
        await result.current.buscar();
      });
      expect(result.current.retryCountdown).toBe(5);
      expect(result.current.retryMessage).toBeTruthy();

      // User starts a new manual search — should reset retry state
      await act(async () => {
        await result.current.buscar();
      });

      // Should start fresh (attempt counter reset, first delay = 5s)
      expect(result.current.retryCountdown).toBe(5);
    });

    test("contextual message matches 504 timeout error type", async () => {
      mockFetchHttpError(504, { message: "Gateway Timeout" });

      const filters = makeFilters();
      const { result } = renderHook(() => useSearch(filters as any));

      await act(async () => {
        await result.current.buscar();
      });

      expect(result.current.retryMessage).toContain("demorando mais que o esperado");
    });
  });
});
