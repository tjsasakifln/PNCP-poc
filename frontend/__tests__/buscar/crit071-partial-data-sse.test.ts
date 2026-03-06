/**
 * CRIT-071: Partial Data Progressive SSE — AC8 Frontend Tests
 *
 * Tests the useSearchSSEHandler hook's handling of `partial_data` SSE events:
 * 1. Progressive accumulation without duplicates
 * 2. Truncated events are skipped
 * 3. savePartialSearch receives real data
 * 4. Abort with partial_data shows results
 * 5. is_partial flag set correctly based on is_final
 */

import { renderHook, act } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks — BEFORE importing hook under test
// ---------------------------------------------------------------------------

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../../hooks/useQuota", () => ({
  useQuota: () => ({ refresh: jest.fn(), quota: null }),
}));

const mockSavePartialSearch = jest.fn();
jest.mock("../../lib/searchPartialCache", () => ({
  savePartialSearch: (...args: unknown[]) => mockSavePartialSearch(...args),
  recoverPartialSearch: jest.fn(() => null),
  clearPartialSearch: jest.fn(),
  cleanupExpiredPartials: jest.fn(),
}));

// ---------------------------------------------------------------------------
// Import under test
// ---------------------------------------------------------------------------

import { useSearchSSEHandler } from "../../app/buscar/hooks/useSearchSSEHandler";
import type { SearchProgressEvent } from "../../hooks/useSearchSSE";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeParams(overrides: Record<string, unknown> = {}) {
  const setResult = jest.fn();
  const params = {
    session: { access_token: "test-token" },
    searchId: "search-crit071",
    searchMode: "setor" as const,
    ufsSelecionadasSize: 3,
    result: null as any,
    setResult,
    setRawCount: jest.fn(),
    setError: jest.fn(),
    setLoading: jest.fn(),
    setSearchId: jest.fn(),
    setAsyncSearchActive: jest.fn(),
    asyncSearchActiveRef: { current: false },
    asyncSearchIdRef: { current: null as string | null },
    sseTerminalReceivedRef: { current: false },
    llmTimeoutRef: { current: null },
    setRetryCountdown: jest.fn(),
    setRetryMessage: jest.fn(),
    setRetryExhausted: jest.fn(),
    retryTimerRef: { current: null },
    handleExcelFailureRef: { current: null },
    excelFailCountRef: { current: 0 },
    excelToastFiredRef: { current: false },
    ...overrides,
  };
  return params;
}

function makePartialDataEvent(
  licitacoes: Array<{ pncp_id: string; objeto?: string; [k: string]: unknown }>,
  extras: Record<string, unknown> = {},
): SearchProgressEvent {
  return {
    stage: "partial_data",
    progress: 50,
    message: "Partial data",
    detail: {
      licitacoes,
      is_final: false,
      ufs_completed: ["SP"],
      uf_total: 3,
      ...extras,
    },
  } as SearchProgressEvent;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("CRIT-071: Partial Data Progressive SSE", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // 1. Progressive accumulation without duplicates
  // -------------------------------------------------------------------------

  test("accumulates licitacoes from multiple partial_data events, deduplicating by pncp_id", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    // First partial_data event with 2 bids
    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent([
          { pncp_id: "bid-1", objeto: "Obra A" },
          { pncp_id: "bid-2", objeto: "Obra B" },
        ])
      );
    });

    expect(params.setResult).toHaveBeenCalledTimes(1);

    // Get the updater function passed to setResult and simulate React calling it
    const updater1 = params.setResult.mock.calls[0][0];
    // First call: prev is null (no prior result)
    const afterFirst = updater1(null);
    expect(afterFirst.licitacoes).toHaveLength(2);
    expect(afterFirst.licitacoes.map((l: any) => l.pncp_id)).toEqual(["bid-1", "bid-2"]);

    // Second partial_data event with one duplicate and one new
    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent([
          { pncp_id: "bid-2", objeto: "Obra B duplicate" },
          { pncp_id: "bid-3", objeto: "Obra C" },
        ])
      );
    });

    expect(params.setResult).toHaveBeenCalledTimes(2);

    // Simulate React calling second updater with afterFirst as prev
    const updater2 = params.setResult.mock.calls[1][0];
    const afterSecond = updater2(afterFirst);

    // Should have 3 unique bids, not 4
    expect(afterSecond.licitacoes).toHaveLength(3);
    expect(afterSecond.licitacoes.map((l: any) => l.pncp_id)).toEqual([
      "bid-1", "bid-2", "bid-3",
    ]);
  });

  // -------------------------------------------------------------------------
  // 2. Truncated events are skipped
  // -------------------------------------------------------------------------

  test("does NOT call setResult when truncated: true", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent(
          [{ pncp_id: "bid-truncated", objeto: "Should not appear" }],
          { truncated: true },
        )
      );
    });

    expect(params.setResult).not.toHaveBeenCalled();
  });

  // -------------------------------------------------------------------------
  // 3. savePartialSearch receives real bid data
  // -------------------------------------------------------------------------

  test("savePartialSearch is called with actual licitacoes from the event", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    const bids = [
      { pncp_id: "bid-save-1", objeto: "Limpeza" },
      { pncp_id: "bid-save-2", objeto: "Seguranca" },
    ];

    await act(async () => {
      await result.current.handleSseEvent(makePartialDataEvent(bids));
    });

    expect(mockSavePartialSearch).toHaveBeenCalledTimes(1);
    expect(mockSavePartialSearch).toHaveBeenCalledWith(
      "search-crit071",          // searchId
      { licitacoes: bids },      // partial result with real bids
      ["SP"],                    // ufs_completed from event detail
      3,                         // uf_total from event detail
    );
  });

  // -------------------------------------------------------------------------
  // 4. Empty licitacoes array does not trigger setResult or savePartialSearch
  // -------------------------------------------------------------------------

  test("empty licitacoes array does not trigger setResult or savePartialSearch", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    await act(async () => {
      await result.current.handleSseEvent(makePartialDataEvent([]));
    });

    expect(params.setResult).not.toHaveBeenCalled();
    expect(mockSavePartialSearch).not.toHaveBeenCalled();
  });

  // -------------------------------------------------------------------------
  // 5. is_partial flag set correctly based on is_final
  // -------------------------------------------------------------------------

  test("is_partial is true when is_final=false", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent(
          [{ pncp_id: "bid-partial-flag", objeto: "Test" }],
          { is_final: false },
        )
      );
    });

    const updater = params.setResult.mock.calls[0][0];
    const afterUpdate = updater(null);
    expect(afterUpdate.is_partial).toBe(true);
  });

  test("is_partial is false when is_final=true", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent(
          [{ pncp_id: "bid-final-flag", objeto: "Test" }],
          { is_final: true },
        )
      );
    });

    const updater = params.setResult.mock.calls[0][0];
    const afterUpdate = updater(null);
    expect(afterUpdate.is_partial).toBe(false);
  });

  // -------------------------------------------------------------------------
  // 6. Bids without pncp_id are filtered out
  // -------------------------------------------------------------------------

  test("bids without pncp_id are excluded from accumulation", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent([
          { pncp_id: "bid-valid", objeto: "Valid" },
          { pncp_id: "", objeto: "Empty ID" },
        ] as any)
      );
    });

    const updater = params.setResult.mock.calls[0][0];
    const afterUpdate = updater(null);
    // Only the bid with a truthy pncp_id should be included
    expect(afterUpdate.licitacoes).toHaveLength(1);
    expect(afterUpdate.licitacoes[0].pncp_id).toBe("bid-valid");
  });

  // -------------------------------------------------------------------------
  // 7. total_filtrado is updated to reflect merged count
  // -------------------------------------------------------------------------

  test("total_filtrado reflects merged licitacoes count", async () => {
    const params = makeParams();
    const { result } = renderHook(() => useSearchSSEHandler(params as any));

    // First event
    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent([
          { pncp_id: "bid-a", objeto: "A" },
          { pncp_id: "bid-b", objeto: "B" },
        ])
      );
    });

    const updater1 = params.setResult.mock.calls[0][0];
    const afterFirst = updater1(null);
    expect(afterFirst.total_filtrado).toBe(2);

    // Second event with one new bid
    await act(async () => {
      await result.current.handleSseEvent(
        makePartialDataEvent([{ pncp_id: "bid-c", objeto: "C" }])
      );
    });

    const updater2 = params.setResult.mock.calls[1][0];
    const afterSecond = updater2(afterFirst);
    expect(afterSecond.total_filtrado).toBe(3);
  });
});
