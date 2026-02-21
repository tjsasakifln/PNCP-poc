/**
 * AC17: useSearch failure scenarios.
 *
 * Tests edge cases and failure modes:
 * - Search timeout preserves partial/previous results
 * - SSE disconnect does not block search completion
 * - getRetryCooldown scales by error type (429, 500, 504, default)
 * - cancelSearch aborts fetch and clears loading
 * - forceFresh failure preserves previous results and shows toast
 */

import { renderHook, act, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mock all external dependencies BEFORE importing useSearch
// ---------------------------------------------------------------------------

// Note: jest.mock factories are hoisted above variable declarations.
// We must NOT reference variables declared with const/let inside mock factories.

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
// Mock crypto.randomUUID
// ---------------------------------------------------------------------------

Object.defineProperty(global, "crypto", {
  value: { randomUUID: () => "test-uuid-failure-5678" },
  writable: true,
  configurable: true,
});

// ---------------------------------------------------------------------------
// Import under test
// ---------------------------------------------------------------------------

import { useSearch } from "../../app/buscar/hooks/useSearch";

// Access the mock functions created inside jest.mock factories via require
const { __mockTrackEvent: mockTrackEvent } = require("../../hooks/useAnalytics");
const { __mockRefreshQuota: mockRefreshQuota } = require("../../hooks/useQuota");
const { toast: mockToast } = require("sonner");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
    licitacoes: [
      { id: "lic-1", titulo: "Licitacao de teste", valor: 50000 },
    ],
    total_raw: 10,
    total_filtrado: 5,
    excel_available: false,
    quota_used: 1,
    quota_remaining: 9,
    response_state: "live",
    ...overrides,
  };
}

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

describe("useSearch failure scenarios (AC17)", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  // -------------------------------------------------------------------------
  // 1. Timeout preserves previous results (CRIT-005 AC23)
  // -------------------------------------------------------------------------

  test("timeout preserves previous results when licitacoes exist", async () => {
    // First: perform a successful search to populate result
    const previousResult = makeBuscaResult();
    mockFetchResponse(previousResult, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.result).toEqual(previousResult);
    });

    // Second: simulate a network error (non-AbortError)
    global.fetch = jest
      .fn()
      .mockRejectedValue(new Error("A busca demorou demais"));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // CRIT-005 AC23: Previous result should be preserved because licitacoes had entries
    expect(result.current.result).toEqual(previousResult);
    // Error should NOT be set (toast shown instead)
    expect(result.current.error).toBeNull();
    expect(mockToast.error).toHaveBeenCalled();
  });

  // -------------------------------------------------------------------------
  // 2. SSE disconnect does not block search completion
  // -------------------------------------------------------------------------

  test("SSE disconnect does not block search completion", async () => {
    // useSearchProgress is mocked to return sseAvailable: false, sseDisconnected: false
    // The search should still complete normally via fetch POST.
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
    expect(result.current.sseAvailable).toBe(false);
    expect(result.current.error).toBeNull();
  });

  // -------------------------------------------------------------------------
  // 3. getRetryCooldown scales by error type (CRIT-006 AC18)
  // -------------------------------------------------------------------------

  test("getRetryCooldown returns 30 for HTTP 429 (rate limit)", () => {
    mockFetchResponse({}, 200);
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    expect(result.current.getRetryCooldown(null, 429)).toBe(30);
  });

  test("getRetryCooldown returns 20 for HTTP 500 (server error)", () => {
    mockFetchResponse({}, 200);
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    expect(result.current.getRetryCooldown(null, 500)).toBe(20);
  });

  test("getRetryCooldown returns 15 for HTTP 504 (gateway timeout)", () => {
    mockFetchResponse({}, 200);
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    expect(result.current.getRetryCooldown(null, 504)).toBe(15);
  });

  test("getRetryCooldown returns 15 for timeout error message", () => {
    mockFetchResponse({}, 200);
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    expect(
      result.current.getRetryCooldown("A busca demorou demais", undefined)
    ).toBe(15);
  });

  test("getRetryCooldown returns 10 for generic network error", () => {
    mockFetchResponse({}, 200);
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    expect(result.current.getRetryCooldown("Erro de conexao", undefined)).toBe(
      10
    );
  });

  // -------------------------------------------------------------------------
  // 4. cancelSearch aborts and clears loading
  // -------------------------------------------------------------------------

  test("cancelSearch aborts fetch and clears loading state", async () => {
    // Make fetch hang forever
    global.fetch = jest.fn().mockImplementation(
      () =>
        new Promise<Response>(() => {
          /* never resolves */
        })
    );

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    // Start search without awaiting
    act(() => {
      result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(true);
    });

    // Cancel
    act(() => {
      result.current.cancelSearch();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.searchId).toBeNull();
    expect(result.current.useRealProgress).toBe(false);
  });

  // -------------------------------------------------------------------------
  // 5. forceFresh failure preserves previous results
  // -------------------------------------------------------------------------

  test("forceFresh failure preserves previous results and shows info toast", async () => {
    // Step 1: Successful initial search
    const previousResult = makeBuscaResult({ download_id: "dl-123" });
    mockFetchResponse(previousResult, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.result).toEqual(previousResult);
    });

    // Step 2: forceFresh search that fails
    global.fetch = jest
      .fn()
      .mockRejectedValue(new Error("Erro ao atualizar dados"));

    await act(async () => {
      await result.current.buscar({ forceFresh: true });
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // forceFresh failure should keep previous result visible (A-04 AC9)
    expect(result.current.result).toEqual(previousResult);
    expect(result.current.error).toBeNull();

    // Should show info toast instead of error
    expect(mockToast.info).toHaveBeenCalledWith(
      expect.stringContaining("resultados anteriores")
    );
  });
});
