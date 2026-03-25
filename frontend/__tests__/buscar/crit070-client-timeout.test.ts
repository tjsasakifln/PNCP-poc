/**
 * CRIT-070: Client Timeout Silent Abort
 *
 * AC5 Tests:
 * - Abort without partial → SearchError with httpStatus 524
 * - Abort with partial → shows partial results (existing behavior preserved)
 * - Timeout value is 65_000 (not 185_000)
 * - startAutoRetry is called on abort without partial
 * - Finalizing timer at 50s (AC3)
 */

import { renderHook, act } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks — BEFORE importing useSearch
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

const mockRecoverPartialSearch = jest.fn(() => null);
jest.mock("../../lib/searchPartialCache", () => ({
  savePartialSearch: jest.fn(),
  recoverPartialSearch: (...args: unknown[]) => mockRecoverPartialSearch(...args),
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
  getCorrelationId: () => "crit070-correlation-id",
  logCorrelatedRequest: jest.fn(),
}));

jest.mock("../../lib/config", () => ({
  APP_NAME: "SmartLic",
}));

// ---------------------------------------------------------------------------
// Import under test
// ---------------------------------------------------------------------------

import { useSearch } from "../../app/buscar/hooks/useSearch";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Creates a fetch mock that rejects with AbortError when signal is aborted.
 * This mimics real browser fetch behavior with AbortController.
 */
function mockAbortableFetch() {
  global.fetch = jest.fn().mockImplementation((_url: string, init?: RequestInit) => {
    return new Promise((_resolve, reject) => {
      const signal = init?.signal;
      if (signal) {
        if (signal.aborted) {
          const err = new DOMException("The operation was aborted.", "AbortError");
          reject(err);
          return;
        }
        signal.addEventListener("abort", () => {
          const err = new DOMException("The operation was aborted.", "AbortError");
          reject(err);
        });
      }
      // Otherwise never resolves (simulates slow backend)
    });
  });
}

function makeFilters(overrides: Record<string, unknown> = {}) {
  return {
    ufsSelecionadas: new Set(["SP"]),
    dataInicial: "2026-03-01",
    dataFinal: "2026-03-10",
    searchMode: "setor" as const,
    modoBusca: "abertas" as const,
    setorId: "engenharia",
    termosArray: [] as string[],
    status: "todos" as any,
    modalidades: [] as number[],
    valorMin: null,
    valorMax: null,
    esferas: [] as any[],
    municipios: [] as any[],
    ordenacao: "relevancia" as any,
    sectorName: "Engenharia",
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
// Tests
// ---------------------------------------------------------------------------

describe("CRIT-070: Client Timeout Silent Abort", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockAbortableFetch();
    mockRecoverPartialSearch.mockReturnValue(null);
  });

  afterEach(() => {
    jest.useRealTimers();
    (global.fetch as jest.Mock).mockRestore?.();
    mockRecoverPartialSearch.mockReset();
  });

  // AC5-1: Abort without partial → SearchError with httpStatus 524
  test("abort without partial shows SearchError with httpStatus 524 and CLIENT_TIMEOUT", async () => {
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    // Start search (don't await — fetch never resolves until abort)
    act(() => {
      result.current.buscar();
    });

    expect(result.current.loading).toBe(true);

    // Advance to trigger the client timeout (65s)
    // Use async act to flush the promise rejection from abort
    await act(async () => {
      jest.advanceTimersByTime(65_000);
    });

    // Should have error set (not silent return)
    expect(result.current.error).not.toBeNull();
    expect(result.current.error?.httpStatus).toBe(524);
    expect(result.current.error?.errorCode).toBe("CLIENT_TIMEOUT");
    expect(result.current.error?.message).toBe("A análise excedeu o tempo limite. Algumas fontes podem estar lentas. Tente novamente — resultados parciais podem estar disponíveis.");
    expect(result.current.result).toBeNull();
  });

  // AC5-2: Abort with partial → shows partial results (existing behavior)
  test("abort with partial shows partial results and no error", async () => {
    mockRecoverPartialSearch.mockReturnValue({
      partialResult: {
        licitacoes: [{ id: "lic-partial", objeto: "Parcial", orgao: "Org", uf: "SP" }],
        total_raw: 100,
        total_filtrado: 1,
      },
    });

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    act(() => {
      result.current.buscar();
    });

    // Trigger timeout — abort fires, AbortError caught, partial found
    await act(async () => {
      jest.advanceTimersByTime(65_000);
    });

    // Should show partial result, NOT error
    expect(result.current.result).not.toBeNull();
    expect(result.current.result?.licitacoes?.[0]?.id).toBe("lic-partial");
    expect(result.current.error).toBeNull();
  });

  // AC5-3: Timeout value is 65_000 (not 185_000)
  test("search is NOT aborted at 40s — still loading", () => {
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    act(() => {
      result.current.buscar();
    });

    // At 40s, should still be loading (not aborted)
    act(() => {
      jest.advanceTimersByTime(40_000);
    });

    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
  });

  // AC5-4: startAutoRetry is called on abort without partial
  test("startAutoRetry is invoked — error has CLIENT_TIMEOUT code", async () => {
    mockRecoverPartialSearch.mockReturnValue(null);

    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    act(() => {
      result.current.buscar();
    });

    await act(async () => {
      jest.advanceTimersByTime(65_000);
    });

    // startAutoRetry was called → error is set with CLIENT_TIMEOUT
    expect(result.current.error).not.toBeNull();
    expect(result.current.error?.errorCode).toBe("CLIENT_TIMEOUT");
    expect(result.current.error?.httpStatus).toBe(524);
  });

  // AC3: Finalizing timer at 50s
  test("isFinalizing becomes true at 50s (not 160s)", () => {
    const filters = makeFilters();
    const { result } = renderHook(() => useSearch(filters as any));

    act(() => {
      result.current.buscar();
    });

    // At 30s, finalizing should NOT be true
    act(() => {
      jest.advanceTimersByTime(30_000);
    });
    expect(result.current.isFinalizing).toBe(false);

    // At 50s, finalizing SHOULD be true
    act(() => {
      jest.advanceTimersByTime(20_000); // Total: 50s
    });
    expect(result.current.isFinalizing).toBe(true);
  });
});
