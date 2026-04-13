/**
 * CRIT-082 AC9: useSearchRetry — Retry simplification tests.
 *
 * Verifies:
 * - Max 2 auto-retries (never fires a 3rd)
 * - Correct delays: first retry 10s, second retry 20s
 * - retryExhausted = true after 2 retries
 * - cancelRetry clears state
 */

import { renderHook, act } from "@testing-library/react";
import { useSearchRetry } from "../app/buscar/hooks/useSearchRetry";
import type { SearchError } from "../app/buscar/hooks/useSearch";

function makeTransientError(httpStatus: 502 | 503 | 504 = 502): SearchError {
  return {
    message: "Servidor indisponível",
    rawMessage: "Bad Gateway",
    errorCode: null,
    httpStatus,
    searchId: "test-search-id",
    correlationId: null,
    requestId: null,
    timestamp: new Date().toISOString(),
  };
}

describe("CRIT-082 AC9: useSearchRetry simplification", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("AC3: starts retry countdown on first transient error (delay 10s)", () => {
    const { result } = renderHook(() => useSearchRetry());
    const setError = jest.fn();
    result.current.buscarRef.current = jest.fn();

    act(() => {
      result.current.startAutoRetry(makeTransientError(502), setError);
    });

    expect(result.current.retryCountdown).toBe(10);
    expect(result.current.retryExhausted).toBe(false);
    expect(result.current.retryMessage).toBe("O servidor está se atualizando.");
  });

  it("AC3: first retry fires after 10s and increments attempt counter", () => {
    const { result } = renderHook(() => useSearchRetry());
    const setError = jest.fn();
    const mockBuscar = jest.fn();
    result.current.buscarRef.current = mockBuscar;

    act(() => {
      result.current.startAutoRetry(makeTransientError(502), setError);
    });

    act(() => {
      jest.advanceTimersByTime(10_000);
    });

    expect(result.current.retryAttemptRef.current).toBe(1);
    expect(mockBuscar).toHaveBeenCalledTimes(1);
    expect(result.current.retryCountdown).toBeNull();
  });

  it("AC3: second retry fires after 20s", () => {
    const { result } = renderHook(() => useSearchRetry());
    const setError = jest.fn();
    const mockBuscar = jest.fn();
    result.current.buscarRef.current = mockBuscar;

    // First retry — delay 10s
    act(() => {
      result.current.startAutoRetry(makeTransientError(502), setError);
    });
    act(() => { jest.advanceTimersByTime(10_000); });

    // Second retry — delay 20s
    act(() => {
      result.current.startAutoRetry(makeTransientError(502), setError);
    });

    expect(result.current.retryCountdown).toBe(20);

    act(() => { jest.advanceTimersByTime(20_000); });

    expect(result.current.retryAttemptRef.current).toBe(2);
    expect(mockBuscar).toHaveBeenCalledTimes(2);
  });

  it("AC3: third call sets retryExhausted — no 3rd fetch attempt fired", () => {
    const { result } = renderHook(() => useSearchRetry());
    const setError = jest.fn();
    const mockBuscar = jest.fn();
    result.current.buscarRef.current = mockBuscar;

    // Burn 2 retries
    act(() => { result.current.startAutoRetry(makeTransientError(502), setError); });
    act(() => { jest.advanceTimersByTime(10_000); });
    act(() => { result.current.startAutoRetry(makeTransientError(502), setError); });
    act(() => { jest.advanceTimersByTime(20_000); });

    // 3rd call: retryAttemptRef.current === 2 — exhausted path
    act(() => {
      result.current.startAutoRetry(makeTransientError(502), setError);
    });

    expect(result.current.retryExhausted).toBe(true);
    expect(result.current.retryCountdown).toBeNull();
    expect(mockBuscar).toHaveBeenCalledTimes(2); // still only 2 — no 3rd attempt
  });

  it("cancelRetry clears countdown and message without marking exhausted", () => {
    const { result } = renderHook(() => useSearchRetry());
    const setError = jest.fn();
    result.current.buscarRef.current = jest.fn();

    act(() => {
      result.current.startAutoRetry(makeTransientError(502), setError);
    });

    expect(result.current.retryCountdown).toBe(10);

    act(() => {
      result.current.cancelRetry();
    });

    expect(result.current.retryCountdown).toBeNull();
    expect(result.current.retryMessage).toBeNull();
    expect(result.current.retryExhausted).toBe(false);
  });

  it("non-transient error (400) does not start auto-retry", () => {
    const { result } = renderHook(() => useSearchRetry());
    const setError = jest.fn();
    result.current.buscarRef.current = jest.fn();

    const nonTransientError: SearchError = {
      message: "Requisição inválida",
      rawMessage: "Bad Request",
      errorCode: null,
      httpStatus: 400,
      searchId: null,
      correlationId: null,
      requestId: null,
      timestamp: new Date().toISOString(),
    };

    act(() => {
      result.current.startAutoRetry(nonTransientError, setError);
    });

    expect(result.current.retryCountdown).toBeNull();
    expect(result.current.retryExhausted).toBe(false);
    expect(result.current.buscarRef.current).not.toHaveBeenCalled();
  });

  it("resetForNewSearch: after auto-retry fires, first call clears flag, second call resets counter", () => {
    const { result } = renderHook(() => useSearchRetry());
    const setError = jest.fn();
    result.current.buscarRef.current = jest.fn();

    // Burn 1 retry
    act(() => { result.current.startAutoRetry(makeTransientError(502), setError); });
    act(() => { jest.advanceTimersByTime(10_000); });

    // After timer fires: autoRetryInProgressRef = true, retryAttemptRef = 1
    expect(result.current.retryAttemptRef.current).toBe(1);

    // First call (simulates buscar() being called by auto-retry): clears the flag only
    act(() => { result.current.resetForNewSearch(); });
    expect(result.current.retryAttemptRef.current).toBe(1); // flag was true → no reset yet

    // Second call (new user-initiated search): now resets everything
    act(() => { result.current.resetForNewSearch(); });
    expect(result.current.retryAttemptRef.current).toBe(0);
    expect(result.current.retryCountdown).toBeNull();
    expect(result.current.retryExhausted).toBe(false);
  });
});
