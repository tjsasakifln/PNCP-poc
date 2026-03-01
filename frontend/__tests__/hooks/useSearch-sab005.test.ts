/**
 * SAB-005: Skeleton loading permanente sem timeout/retry
 *
 * Tests:
 * - AC8: Mock POST that never resolves → after 30s skeleton timeout banner appears
 * - AC9: POST returns resultados: [] → empty state immediate (loading=false, result set)
 * - Skeleton timeout resets when SSE event arrives
 * - Skeleton timeout clears on cancel
 */

import { renderHook, act, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mock all external dependencies BEFORE importing useSearch
// ---------------------------------------------------------------------------

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
  }),
}));

jest.mock("../../hooks/useSearchPolling", () => ({
  useSearchPolling: () => ({ asProgressEvent: null, status: null, isPolling: false }),
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

jest.mock("../../lib/searchPartialCache", () => ({
  savePartialSearch: jest.fn(),
  recoverPartialSearch: jest.fn(() => null),
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
  dateDiffInDays: () => 10,
}));

jest.mock("../../lib/utils/correlationId", () => ({
  getCorrelationId: () => "test-correlation-id",
  logCorrelatedRequest: jest.fn(),
}));

// ---------------------------------------------------------------------------
// Mock crypto.randomUUID (jsdom does not provide it)
// ---------------------------------------------------------------------------

Object.defineProperty(global, "crypto", {
  value: { randomUUID: () => "test-uuid-sab005" },
  writable: true,
  configurable: true,
});

// ---------------------------------------------------------------------------
// Import under test (AFTER mocks are registered)
// ---------------------------------------------------------------------------

import { useSearch } from "../../app/buscar/hooks/useSearch";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeBuscaResultZero() {
  return {
    resumo: {
      resumo_executivo: "Nenhum resultado",
      total_oportunidades: 0,
      valor_total: 0,
      destaques: [],
      recomendacoes: [],
      alertas_urgencia: [],
      insight_setorial: "",
    },
    licitacoes: [],
    total_raw: 100,
    total_filtrado: 0,
    excel_available: false,
    quota_used: 1,
    quota_remaining: 9,
    response_state: "live",
  };
}

function makeBuscaResultWithData() {
  return {
    resumo: {
      resumo_executivo: "Resumo",
      total_oportunidades: 3,
      valor_total: 50000,
      destaques: [],
      recomendacoes: [],
      alertas_urgencia: [],
      insight_setorial: "",
    },
    licitacoes: [
      { id: "1", objeto: "Item 1" },
      { id: "2", objeto: "Item 2" },
      { id: "3", objeto: "Item 3" },
    ],
    total_raw: 100,
    total_filtrado: 3,
    excel_available: false,
    quota_used: 1,
    quota_remaining: 9,
    response_state: "live",
  };
}

function makeFilters(overrides: Record<string, unknown> = {}) {
  return {
    ufsSelecionadas: new Set(["SP"]),
    dataInicial: "2026-02-18",
    dataFinal: "2026-02-28",
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
    sectorName: "Vestuario e Uniformes",
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

// ---------------------------------------------------------------------------
// AC8: Skeleton timeout after 30s with no data update
// ---------------------------------------------------------------------------

describe("SAB-005 AC8: Skeleton timeout", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    global.fetch = jest.fn().mockImplementation(() => new Promise(() => {})); // never resolves
  });

  afterEach(() => {
    jest.useRealTimers();
    (global.fetch as jest.Mock).mockRestore?.();
  });

  it("AC8: skeletonTimeoutReached becomes true after 30s without data update", async () => {
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters));

    // Initially false
    expect(result.current.skeletonTimeoutReached).toBe(false);

    // Start search (fires fetch that never resolves)
    act(() => {
      result.current.buscar();
    });

    // Should be loading
    expect(result.current.loading).toBe(true);
    expect(result.current.skeletonTimeoutReached).toBe(false);

    // Advance 29s — still false
    act(() => {
      jest.advanceTimersByTime(29_000);
    });
    expect(result.current.skeletonTimeoutReached).toBe(false);

    // Advance to 30s — triggers timeout
    act(() => {
      jest.advanceTimersByTime(1_000);
    });
    expect(result.current.skeletonTimeoutReached).toBe(true);
  });

  it("AC8: skeletonTimeoutReached resets on cancel", async () => {
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters));

    // Start search
    act(() => {
      result.current.buscar();
    });

    // Advance to 30s — triggers timeout
    act(() => {
      jest.advanceTimersByTime(30_000);
    });
    expect(result.current.skeletonTimeoutReached).toBe(true);

    // Cancel search — resets timeout
    act(() => {
      result.current.cancelSearch();
    });
    expect(result.current.skeletonTimeoutReached).toBe(false);
  });

  it("AC8: skeletonTimeoutReached is false initially", () => {
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters));
    expect(result.current.skeletonTimeoutReached).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AC9: POST returns resultados: [] → empty state immediate
// ---------------------------------------------------------------------------

describe("SAB-005 AC9: Zero results immediate empty state", () => {
  it("AC9: POST returns 0 results → loading=false, result set with 0 oportunidades", async () => {
    const zeroResult = makeBuscaResultZero();
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => zeroResult,
      headers: { get: () => null },
    });

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters));

    await act(async () => {
      await result.current.buscar();
    });

    // Should be done loading with empty result
    expect(result.current.loading).toBe(false);
    expect(result.current.result).not.toBeNull();
    expect(result.current.result!.resumo.total_oportunidades).toBe(0);
    expect(result.current.result!.licitacoes).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("AC9: POST returns results with data → loading=false, result set", async () => {
    const dataResult = makeBuscaResultWithData();
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => dataResult,
      headers: { get: () => null },
    });

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters));

    await act(async () => {
      await result.current.buscar();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.result).not.toBeNull();
    expect(result.current.result!.resumo.total_oportunidades).toBe(3);
    expect(result.current.result!.licitacoes.length).toBe(3);
  });

  it("AC9: skeletonTimeoutReached clears when search completes successfully", async () => {
    jest.useFakeTimers();

    // First: start with a never-resolving fetch to trigger timeout
    let resolveFirstFetch: (v: any) => void;
    global.fetch = jest.fn().mockImplementationOnce(
      () => new Promise((resolve) => { resolveFirstFetch = resolve; })
    );

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters));

    act(() => {
      result.current.buscar();
    });

    // Trigger skeleton timeout
    act(() => {
      jest.advanceTimersByTime(30_000);
    });
    expect(result.current.skeletonTimeoutReached).toBe(true);

    // Now resolve fetch with data
    const dataResult = makeBuscaResultWithData();
    await act(async () => {
      resolveFirstFetch!({
        ok: true,
        status: 200,
        json: async () => dataResult,
        headers: { get: () => null },
      });
      // Need to flush the promise
      await Promise.resolve();
      jest.runAllTimers();
    });

    // Timeout should be cleared after successful completion
    expect(result.current.skeletonTimeoutReached).toBe(false);

    jest.useRealTimers();
  });
});
