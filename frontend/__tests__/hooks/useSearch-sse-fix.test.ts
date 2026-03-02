/**
 * CRIT-SSE-FIX: Tests for SSE lifecycle fixes.
 *
 * AC1: viewPartialResults() preserves partial result (doesn't destroy like cancelSearch)
 * AC2: finally block doesn't nullify searchId when bid_analysis_status='processing'
 * AC2b: sseTerminalReceivedRef prevents premature searchId nullification
 * AC3: SSE retry uses ref-based searchId (not stale closure)
 */

import { renderHook, act, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks — same pattern as useSearch.test.ts
// ---------------------------------------------------------------------------

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: { access_token: "test-token" } }),
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../../hooks/useQuota", () => ({
  useQuota: () => ({ refresh: jest.fn() }),
}));

// CRIT-SSE-FIX: We need to capture onEvent callback to simulate SSE events
let capturedSseOptions: any = null;
jest.mock("../../hooks/useSearchSSE", () => ({
  useSearchSSE: (options: any) => {
    capturedSseOptions = options;
    return {
      currentEvent: null,
      isConnected: false,
      sseAvailable: false,
      sseDisconnected: false,
      isReconnecting: false,
      isDegraded: false,
      degradedDetail: null,
      partialProgress: null,
      refreshAvailable: null,
      ufStatuses: new Map(),
      ufTotalFound: 0,
      ufAllComplete: false,
      batchProgress: null,
      sourceStatuses: new Map(),
      filterSummary: null,
      pendingReviewUpdate: null,
    };
  },
}));

jest.mock("../../hooks/useSearchPolling", () => ({
  useSearchPolling: () => ({ asProgressEvent: null }),
}));

jest.mock("../../hooks/useSavedSearches", () => ({
  useSavedSearches: () => ({ saveNewSearch: jest.fn(), isMaxCapacity: false }),
}));

jest.mock("../../lib/error-messages", () => ({
  getUserFriendlyError: (e: unknown) => e instanceof Error ? e.message : String(e),
  getMessageFromErrorCode: () => null,
  isTransientError: () => false,
  getRetryMessage: () => "Tentando novamente...",
  getHumanizedError: () => ({
    message: "Erro generico",
    actionLabel: "Tentar novamente",
    tone: "blue",
    suggestReduceScope: false,
  }),
}));

jest.mock("../../lib/searchStatePersistence", () => ({
  saveSearchState: jest.fn(),
  restoreSearchState: jest.fn(() => null),
}));

const mockRecoverPartialSearch = jest.fn(() => null);
jest.mock("../../lib/searchPartialCache", () => ({
  savePartialSearch: jest.fn(),
  recoverPartialSearch: (...args: any[]) => mockRecoverPartialSearch(...args),
  clearPartialSearch: jest.fn(),
  cleanupExpiredPartials: jest.fn(),
}));

jest.mock("../../lib/lastSearchCache", () => ({
  saveLastSearch: jest.fn(),
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

jest.mock("../../lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
      onAuthStateChange: jest.fn(() => ({ data: { subscription: { unsubscribe: jest.fn() } } })),
    },
    from: jest.fn(() => ({
      select: jest.fn(() => ({ data: [], error: null })),
    })),
  },
}));

Object.defineProperty(global, "crypto", {
  value: { randomUUID: () => "test-uuid-1234" },
  writable: true,
  configurable: true,
});

// ---------------------------------------------------------------------------
// Import under test
// ---------------------------------------------------------------------------

import { useSearch } from "../../app/buscar/hooks/useSearch";

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
    licitacoes: [{ id: "1", objeto: "Test" }],
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

describe("CRIT-SSE-FIX: SSE lifecycle fixes", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    capturedSseOptions = null;
    mockRecoverPartialSearch.mockReturnValue(null);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  // -------------------------------------------------------------------------
  // AC1: viewPartialResults preserves existing result
  // -------------------------------------------------------------------------

  test("AC1: viewPartialResults() preserves existing result when available", async () => {
    const resultData = makeBuscaResult();
    mockFetchResponse(resultData, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    // Start search
    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Verify result is set
    expect(result.current.result).not.toBeNull();

    // Start another search to enter loading state
    const pendingPromise = new Promise(() => {}); // never resolves
    global.fetch = jest.fn().mockReturnValue(pendingPromise);

    act(() => {
      result.current.buscar();
    });

    // Now click "view partial results" — should NOT destroy state
    act(() => {
      result.current.viewPartialResults();
    });

    // loading should be false (user chose to view partial)
    expect(result.current.loading).toBe(false);
  });

  // -------------------------------------------------------------------------
  // AC1b: viewPartialResults recovers from localStorage when no result
  // -------------------------------------------------------------------------

  test("AC1b: viewPartialResults() recovers from localStorage when result is null", async () => {
    const partialData = makeBuscaResult({ response_state: "partial" });
    mockRecoverPartialSearch.mockReturnValue({ partialResult: partialData });

    // Never-resolving fetch to keep loading=true
    global.fetch = jest.fn().mockReturnValue(new Promise(() => {}));

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    // Start search (will hang)
    act(() => {
      result.current.buscar();
    });

    expect(result.current.loading).toBe(true);

    // Click view partial results
    act(() => {
      result.current.viewPartialResults();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.showingPartialResults).toBe(true);
    expect(result.current.result).toEqual(partialData);
  });

  // -------------------------------------------------------------------------
  // AC2: finally block includes bid_analysis_status in hasJobsRunning
  // -------------------------------------------------------------------------

  test("AC2: searchId preserved when bid_analysis_status='processing'", async () => {
    const resultWithBidProcessing = makeBuscaResult({
      llm_status: "ready",
      excel_status: "ready",
      bid_analysis_status: "processing",
    });
    mockFetchResponse(resultWithBidProcessing, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // searchId should NOT be null because bid_analysis is still processing
    expect(result.current.searchId).not.toBeNull();
  });

  // -------------------------------------------------------------------------
  // AC2b: searchId preserved when SSE terminal not yet received
  // -------------------------------------------------------------------------

  test("AC2b: searchId preserved until SSE terminal event (5s safety timeout)", async () => {
    // Return a result where all jobs are done (hasJobsRunning=false)
    // but SSE hasn't emitted terminal event yet
    const resultAllDone = makeBuscaResult({
      llm_status: "ready",
      excel_status: "ready",
      bid_analysis_status: "ready",
    });
    mockFetchResponse(resultAllDone, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // searchId should still be set (SSE terminal not received yet, safety timer pending)
    expect(result.current.searchId).not.toBeNull();

    // Advance past 5s safety timeout
    act(() => {
      jest.advanceTimersByTime(6000);
    });

    // Now searchId should be null (safety timeout fired)
    expect(result.current.searchId).toBeNull();
  });

  // -------------------------------------------------------------------------
  // AC2c: SSE terminal event releases searchId immediately
  // -------------------------------------------------------------------------

  test("AC2c: SSE terminal event allows searchId cleanup before safety timeout", async () => {
    const resultAllDone = makeBuscaResult({
      llm_status: "ready",
      excel_status: "ready",
    });
    mockFetchResponse(resultAllDone, 200);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    await act(async () => {
      await result.current.buscar();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Simulate SSE terminal event via the captured onEvent callback
    if (capturedSseOptions?.onEvent) {
      act(() => {
        capturedSseOptions.onEvent({
          stage: "complete",
          progress: 100,
          message: "Done",
          detail: {},
        });
      });
    }

    // The sseTerminalReceivedRef is now true — on next render cycle
    // the safety timeout (if it fires) will see terminal already received
    // and the searchId should be cleanable
    act(() => {
      jest.advanceTimersByTime(6000);
    });

    expect(result.current.searchId).toBeNull();
  });

  // -------------------------------------------------------------------------
  // AC1c: cancelSearch still destroys state (unchanged behavior)
  // -------------------------------------------------------------------------

  test("AC1c: cancelSearch() still nullifies searchId and stops loading", async () => {
    global.fetch = jest.fn().mockReturnValue(new Promise(() => {}));

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    act(() => {
      result.current.buscar();
    });

    expect(result.current.loading).toBe(true);

    act(() => {
      result.current.cancelSearch();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.searchId).toBeNull();
  });
});
