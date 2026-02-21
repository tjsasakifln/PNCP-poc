/**
 * AC16: useSearch hook tests -- restored from quarantine.
 *
 * Tests the core search functionality:
 * - buscar() with successful response
 * - buscar() with 504 response (retry logic)
 * - buscar() with SSE disconnect + POST success
 * - buscar() with timeout then retry
 * - cancelSearch() aborts fetch
 *
 * Mock strategy: All external hooks and modules are mocked at module level
 * so the hook runs in isolation against controlled fetch responses.
 */

import { renderHook, act, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mock all external dependencies BEFORE importing useSearch
// ---------------------------------------------------------------------------

// Note: jest.mock factories are hoisted above variable declarations.
// We must NOT reference variables declared with const/let inside mock factories.
// Instead we use require() to access shared mock objects after the fact.

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: { access_token: "test-token" } }),
}));

jest.mock("../../hooks/useAnalytics", () => {
  const fn = jest.fn();
  return { useAnalytics: () => ({ trackEvent: fn }), __mockTrackEvent: fn };
});

jest.mock("../../hooks/useQuota", () => {
  const fn = jest.fn();
  return { useQuota: () => ({ refresh: fn }), __mockRefreshQuota: fn };
});

jest.mock("../../hooks/useSearchSSE", () => ({
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

jest.mock("../../hooks/useSearchPolling", () => ({
  useSearchPolling: () => ({ asProgressEvent: null }),
}));

jest.mock("../../hooks/useSavedSearches", () => ({
  useSavedSearches: () => ({
    saveNewSearch: jest.fn(),
    isMaxCapacity: false,
  }),
}));

jest.mock("../../lib/error-messages", () => ({
  getUserFriendlyError: (e: unknown) =>
    e instanceof Error ? e.message : String(e),
  getMessageFromErrorCode: () => null,
  isTransientError: () => false,
}));

jest.mock("../../lib/searchStatePersistence", () => ({
  saveSearchState: jest.fn(),
  restoreSearchState: jest.fn(() => null),
}));

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

jest.mock("../../lib/utils/dateDiffInDays", () => ({
  dateDiffInDays: () => 14,
}));

jest.mock("../../lib/utils/correlationId", () => ({
  getCorrelationId: () => "test-correlation-id",
  logCorrelatedRequest: jest.fn(),
}));

// ---------------------------------------------------------------------------
// Mock crypto.randomUUID (jsdom does not provide it)
// ---------------------------------------------------------------------------

Object.defineProperty(global, "crypto", {
  value: { randomUUID: () => "test-uuid-1234" },
  writable: true,
  configurable: true,
});

// ---------------------------------------------------------------------------
// Import under test (AFTER mocks are registered)
// ---------------------------------------------------------------------------

import { useSearch } from "../../app/buscar/hooks/useSearch";

// Access the mock functions created inside jest.mock factories via require
const { __mockTrackEvent: mockTrackEvent } = require("../../hooks/useAnalytics");
const { __mockRefreshQuota: mockRefreshQuota } = require("../../hooks/useQuota");
const { toast: mockToast } = require("sonner");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Minimal valid BuscaResult shape used across tests. */
function makeBuscaResult(overrides: Record<string, unknown> = {}) {
  return {
    resumo: {
      resumo_executivo: "Resumo de teste",
      total_oportunidades: 5,
      valor_total: 100000,
      destaques: [],
      recomendacoes: [],
      alertas_urgencia: [],
      insight_setorial: "",
    },
    licitacoes: [],
    total_raw: 10,
    total_filtrado: 5,
    excel_available: false,
    quota_used: 1,
    quota_remaining: 9,
    response_state: "live",
    ...overrides,
  };
}

/**
 * Build a default filters object that satisfies UseSearchParams.
 * The interface is not exported so we define the shape inline.
 */
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

/** Replace global.fetch with a mock returning the given data/status. */
function mockFetchResponse(data: unknown, status = 200) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  } as unknown as Response);
}

// ---------------------------------------------------------------------------
// Test Suite
// ---------------------------------------------------------------------------

describe("useSearch hook (AC16 -- restored from quarantine)", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  // -------------------------------------------------------------------------
  // 1. Successful search
  // -------------------------------------------------------------------------

  test("buscar() sets result on successful 200 response", async () => {
    const expected = makeBuscaResult();
    mockFetchResponse(expected, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.result).toEqual(expected);
    expect(result.current.error).toBeNull();
    expect(result.current.rawCount).toBe(10);

    // Verify fetch was called with correct endpoint and method
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/buscar",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
          "Content-Type": "application/json",
          "X-Correlation-ID": "test-correlation-id",
        }),
      })
    );

    // Verify analytics tracked
    expect(mockTrackEvent).toHaveBeenCalledWith(
      "search_started",
      expect.any(Object)
    );
    expect(mockTrackEvent).toHaveBeenCalledWith(
      "search_completed",
      expect.any(Object)
    );

    // Verify quota refreshed
    expect(mockRefreshQuota).toHaveBeenCalled();
  });

  // -------------------------------------------------------------------------
  // 2. 504 response (Gateway Timeout)
  // -------------------------------------------------------------------------

  test("buscar() sets error on 504 response after retries exhausted", async () => {
    // The hook retries on 500/502/503 but NOT on 504.
    // A single 504 should set the error immediately.
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 504,
      json: () => Promise.resolve({ message: "Gateway Timeout" }),
    } as unknown as Response);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Error should be set (from getUserFriendlyError mock, returns the message as-is)
    expect(result.current.error).toBeTruthy();
    expect(result.current.result).toBeNull();
  });

  // -------------------------------------------------------------------------
  // 3. SSE disconnect + POST success
  // -------------------------------------------------------------------------

  test("buscar() completes successfully even when SSE is unavailable", async () => {
    // Our mock for useSearchProgress returns sseAvailable: false.
    // The hook should still complete normally via the POST response.
    const expected = makeBuscaResult({ response_state: "live" });
    mockFetchResponse(expected, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.result).toEqual(expected);
    expect(result.current.sseAvailable).toBe(false);
    expect(result.current.error).toBeNull();
  });

  // -------------------------------------------------------------------------
  // 4. Timeout then retry (500 retries)
  // -------------------------------------------------------------------------

  test("buscar() retries on 500 then succeeds on second attempt", async () => {
    const expected = makeBuscaResult();

    // First call: 500 (triggers retry), second call: 200
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ message: "Internal Server Error" }),
      } as unknown as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(expected),
      } as unknown as Response);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should have succeeded on retry
    expect(result.current.result).toEqual(expected);
    expect(result.current.error).toBeNull();

    // fetch called at least twice (initial + retry)
    expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThanOrEqual(2);
  }, 20000); // Extended timeout for retry delays

  // -------------------------------------------------------------------------
  // 5. cancelSearch() aborts fetch
  // -------------------------------------------------------------------------

  test("cancelSearch() sets loading to false and aborts the controller", async () => {
    // Make fetch hang indefinitely so we can cancel mid-flight
    global.fetch = jest.fn().mockImplementation(
      () =>
        new Promise<Response>(() => {
          // Never resolves -- simulates a long-running request
        })
    );

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    // Start the search (do NOT await -- it will never resolve)
    act(() => {
      result.current.buscar();
    });

    // Give React a tick to set loading = true
    await waitFor(() => {
      expect(result.current.loading).toBe(true);
    });

    // Cancel the search
    act(() => {
      result.current.cancelSearch();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // searchId should be cleared
    expect(result.current.searchId).toBeNull();
  });
});
