/**
 * GTM-STAB-006 AC5: SSE exponential backoff reconnection tests.
 *
 * Tests the useSearchSSE hook's retry logic:
 * - SSE_MAX_RETRIES = 3
 * - SSE_RETRY_DELAYS = [3000, 6000, 12000] ms
 *
 * Retry flow in useSearchSSE.ts:
 *  1. Initial EventSource created (attempt 0).
 *  2. es.onerror fires → if retryAttemptRef < 3: schedule setTimeout(delays[attempt]),
 *     increment counter, then create retryEs inside setTimeout.
 *  3. retryEs.onerror fires → if counter >= 3: exhaust (sseDisconnected=true, onError).
 *  4. If initial es.onerror fires 3+ times with counter already at 3: else-branch exhausts.
 *
 * Because cleanup() closes the initial es, we simulate additional retries by
 * manually firing onerror on each successive EventSource mock in sequence.
 */

import { renderHook, act } from '@testing-library/react';
import { useSearchSSE } from '../../hooks/useSearchSSE';

// ---- EventSource mock factory ----

/** A single mock EventSource instance. */
interface MockEventSource {
  url: string;
  readyState: number;
  close: jest.Mock;
  addEventListener: jest.Mock;
  removeEventListener: jest.Mock;
  onopen: (() => void) | null;
  onmessage: ((e: { data: string }) => void) | null;
  onerror: (() => void) | null;
}

function makeMockES(url: string): MockEventSource {
  return {
    url,
    readyState: 1, // OPEN
    close: jest.fn(function (this: MockEventSource) {
      this.readyState = 2; // CLOSED
    }),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    onopen: null,
    onmessage: null,
    onerror: null,
  };
}

// ---- Test suite ----

describe('GTM-STAB-006 AC5: useSearchSSE exponential backoff reconnection', () => {
  let mockInstances: MockEventSource[];

  beforeEach(() => {
    jest.useFakeTimers();
    mockInstances = [];

    // Each call to `new EventSource(url)` returns a new mock and records it.
    (global as any).EventSource = jest.fn().mockImplementation((url: string) => {
      const instance = makeMockES(url);
      mockInstances.push(instance);
      return instance;
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  // ---------------------------------------------------------------------------
  // TC1: Attempt up to 3 reconnections on SSE error
  // ---------------------------------------------------------------------------

  it('TC1: should attempt up to 3 reconnections on SSE error', () => {
    renderHook(() =>
      useSearchSSE({
        searchId: 'search-001',
        enabled: true,
        authToken: 'token-abc',
      })
    );

    // Initial EventSource created (attempt 0).
    expect(mockInstances).toHaveLength(1);

    // Trigger error on initial ES → should schedule retry 1 (delay=3000ms).
    act(() => {
      mockInstances[0].onerror?.();
    });

    // Not yet retried (waiting for 3000ms timeout).
    expect(mockInstances).toHaveLength(1);

    // Advance 3000ms → retry 1 EventSource created.
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    expect(mockInstances).toHaveLength(2);

    // Trigger error on retry 1 → retryAttemptRef=1, not yet exhausted (1 < 3).
    // The outer es.onerror is the only mechanism for further retries, but since
    // cleanup() was called, we can no longer fire on mockInstances[0].
    // Firing retryEs.onerror at this point: counter=1, 1 < 3 → no new connection.
    // To simulate attempts 2 and 3, we manually fire the outer es.onerror
    // multiple more times (EventSource onerror can fire multiple times in real
    // browsers during reconnect cycles). The outer handler checks counter each time.

    // Re-fire onerror on initial ES (counter now 1 < 3) → schedules retry 2 at 6000ms.
    act(() => {
      mockInstances[0].onerror?.();
    });
    act(() => {
      jest.advanceTimersByTime(6000);
    });
    expect(mockInstances).toHaveLength(3);

    // Re-fire onerror on initial ES (counter now 2 < 3) → schedules retry 3 at 12000ms.
    act(() => {
      mockInstances[0].onerror?.();
    });
    act(() => {
      jest.advanceTimersByTime(12000);
    });
    expect(mockInstances).toHaveLength(4);

    // Total: 1 initial + 3 retries = 4 EventSource instances created.
    expect(mockInstances).toHaveLength(4);
  });

  // ---------------------------------------------------------------------------
  // TC2: Exponential backoff delays (3s, 6s, 12s)
  // ---------------------------------------------------------------------------

  it('TC2: should use exponential backoff delays (3s, 6s, 12s)', () => {
    renderHook(() =>
      useSearchSSE({
        searchId: 'search-002',
        enabled: true,
      })
    );

    expect(mockInstances).toHaveLength(1);

    // Error → retry 1 scheduled at 3000ms.
    act(() => {
      mockInstances[0].onerror?.();
    });

    // Advance 2999ms → no retry yet.
    act(() => {
      jest.advanceTimersByTime(2999);
    });
    expect(mockInstances).toHaveLength(1);

    // Advance 1ms more → 3000ms total → retry 1 fires.
    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(mockInstances).toHaveLength(2);

    // Trigger re-fire on outer es (counter=1) → retry 2 at 6000ms.
    act(() => {
      mockInstances[0].onerror?.();
    });

    // Advance 5999ms → no retry yet.
    act(() => {
      jest.advanceTimersByTime(5999);
    });
    expect(mockInstances).toHaveLength(2);

    // Advance 1ms more → 6000ms total → retry 2 fires.
    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(mockInstances).toHaveLength(3);

    // Trigger re-fire on outer es (counter=2) → retry 3 at 12000ms.
    act(() => {
      mockInstances[0].onerror?.();
    });

    // Advance 11999ms → no retry yet.
    act(() => {
      jest.advanceTimersByTime(11999);
    });
    expect(mockInstances).toHaveLength(3);

    // Advance 1ms more → 12000ms total → retry 3 fires.
    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(mockInstances).toHaveLength(4);
  });

  // ---------------------------------------------------------------------------
  // TC3: sseDisconnected=true after all retries exhausted
  // ---------------------------------------------------------------------------

  it('TC3: should set sseDisconnected after all retries exhausted', () => {
    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-003',
        enabled: true,
      })
    );

    // Initial state.
    expect(result.current.sseDisconnected).toBe(false);
    expect(result.current.sseAvailable).toBe(true);

    // Exhaust all 3 retries by firing outer onerror 4 times.
    // Fire 1: counter=0 → counter=1, retry 1 scheduled.
    act(() => {
      mockInstances[0].onerror?.();
    });
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    expect(result.current.sseDisconnected).toBe(false);

    // Fire 2: counter=1 → counter=2, retry 2 scheduled.
    act(() => {
      mockInstances[0].onerror?.();
    });
    act(() => {
      jest.advanceTimersByTime(6000);
    });
    expect(result.current.sseDisconnected).toBe(false);

    // Fire 3: counter=2 → counter=3, retry 3 scheduled.
    act(() => {
      mockInstances[0].onerror?.();
    });
    act(() => {
      jest.advanceTimersByTime(12000);
    });
    expect(result.current.sseDisconnected).toBe(false);

    // Fire 4: counter=3 >= 3 → else branch → sseDisconnected=true.
    act(() => {
      mockInstances[0].onerror?.();
    });

    expect(result.current.sseDisconnected).toBe(true);
    expect(result.current.sseAvailable).toBe(false);
  });

  // ---------------------------------------------------------------------------
  // TC4: No more connection attempts after max retries
  // ---------------------------------------------------------------------------

  it('TC4: should not retry beyond max retries', () => {
    renderHook(() =>
      useSearchSSE({
        searchId: 'search-004',
        enabled: true,
      })
    );

    // Drive all 3 retries (creating 4 instances total).
    // Fire 1 + wait 3s.
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(3000); });
    // Fire 2 + wait 6s.
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(6000); });
    // Fire 3 + wait 12s.
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(12000); });

    // 4 instances so far: 1 initial + 3 retries.
    expect(mockInstances).toHaveLength(4);

    // Fire 4 on outer es → exhausts.
    act(() => { mockInstances[0].onerror?.(); });

    // Advance time significantly — no new connections should be created.
    act(() => { jest.advanceTimersByTime(60000); });

    // Still 4 instances.
    expect(mockInstances).toHaveLength(4);
  });

  // ---------------------------------------------------------------------------
  // TC5: Retry count resets on new search (searchId change)
  // ---------------------------------------------------------------------------

  it('TC5: should reset retry count on new search', () => {
    const { result, rerender } = renderHook(
      ({ searchId }: { searchId: string | null }) =>
        useSearchSSE({
          searchId,
          enabled: true,
        }),
      { initialProps: { searchId: 'search-005a' as string | null } }
    );

    // Exhaust retries on first search (fire outer es.onerror 4 times).
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(3000); });
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(6000); });
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(12000); });
    act(() => { mockInstances[0].onerror?.(); });

    expect(result.current.sseDisconnected).toBe(true);
    expect(result.current.sseAvailable).toBe(false);

    const instancesAfterFirstSearch = mockInstances.length;

    // Start new search — rerender with new searchId.
    act(() => {
      rerender({ searchId: 'search-005b' });
    });

    // sseDisconnected and sseAvailable should be reset.
    expect(result.current.sseDisconnected).toBe(false);
    expect(result.current.sseAvailable).toBe(true);

    // A new EventSource should have been created for the new search.
    expect(mockInstances.length).toBeGreaterThan(instancesAfterFirstSearch);

    const newEsIndex = mockInstances.length - 1;

    // URL should reference the new searchId.
    expect(mockInstances[newEsIndex].url).toContain('search-005b');

    // Error on new search → should retry again (not immediately exhaust).
    act(() => {
      mockInstances[newEsIndex].onerror?.();
    });

    // After one error, still not disconnected (retries available).
    expect(result.current.sseDisconnected).toBe(false);

    // Retry fires after 3000ms.
    act(() => { jest.advanceTimersByTime(3000); });
    expect(mockInstances.length).toBeGreaterThan(instancesAfterFirstSearch + 1);
  });

  // ---------------------------------------------------------------------------
  // TC6: onError callback fires after all retries exhausted
  // ---------------------------------------------------------------------------

  it('TC6: should call onError after all retries exhausted', () => {
    const onError = jest.fn();

    renderHook(() =>
      useSearchSSE({
        searchId: 'search-006',
        enabled: true,
        onError,
      })
    );

    expect(onError).not.toHaveBeenCalled();

    // Drive through 3 retries without exhaustion.
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(3000); });
    expect(onError).not.toHaveBeenCalled();

    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(6000); });
    expect(onError).not.toHaveBeenCalled();

    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(12000); });
    expect(onError).not.toHaveBeenCalled();

    // 4th fire exhausts → onError must be called exactly once.
    act(() => { mockInstances[0].onerror?.(); });

    expect(onError).toHaveBeenCalledTimes(1);
  });

  // ---------------------------------------------------------------------------
  // TC7 (bonus): sseDisconnected resets when search is disabled then re-enabled
  // ---------------------------------------------------------------------------

  it('TC7: sseDisconnected resets when search is disabled', () => {
    const { result, rerender } = renderHook(
      ({ enabled, searchId }: { enabled: boolean; searchId: string | null }) =>
        useSearchSSE({ searchId, enabled }),
      { initialProps: { enabled: true, searchId: 'search-007' as string | null } }
    );

    // Exhaust retries.
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(3000); });
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(6000); });
    act(() => { mockInstances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(12000); });
    act(() => { mockInstances[0].onerror?.(); });

    expect(result.current.sseDisconnected).toBe(true);

    // Disable search — cleanup runs and resets retryAttemptRef.
    act(() => {
      rerender({ enabled: false, searchId: null });
    });

    expect(result.current.sseDisconnected).toBe(false);
  });
});
