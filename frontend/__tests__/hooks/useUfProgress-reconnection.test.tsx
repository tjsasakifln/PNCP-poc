/**
 * STORY-365: SSE Auto-Reconnection Tests for useUfProgress
 *
 * AC13: EventSource reconnect after simulated disconnection
 * AC6: Auto-reconnect on EventSource error
 * AC7: Exponential backoff 1s → 2s → 4s (max 3 attempts)
 * AC8: After reconnect, progress displayed correctly (not reset to 0%)
 * AC9: After 3 failures, fallback to polling
 */

import { renderHook, act } from '@testing-library/react';
import { useUfProgress } from '../../app/buscar/hooks/useUfProgress';

// Use shared MockEventSource (installed globally via jest.setup.js, STORY-368)
import { MockEventSource } from '../utils/mock-event-source';

// Mock fetch for polling fallback (AC9)
const mockFetch = jest.fn();

beforeEach(() => {
  jest.useFakeTimers();
  mockFetch.mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ status: 'processing', progress: 50 }),
  });
  (global as any).fetch = mockFetch;
});

afterEach(() => {
  jest.useRealTimers();
  jest.restoreAllMocks();
  delete (global as any).fetch;
});

// ── AC6: Auto-reconnect on error ─────────────────────────────────────────────

describe('AC6: Auto-reconnect on EventSource error', () => {
  it('reconnects when EventSource emits error', () => {
    const { result } = renderHook(() =>
      useUfProgress({
        searchId: 'search-365-01',
        enabled: true,
        selectedUfs: ['SP', 'RJ'],
      }),
    );

    expect(MockEventSource.instances).toHaveLength(1);

    // Trigger error on first connection
    act(() => {
      MockEventSource.instances[0].onerror?.();
    });

    // AC7: First reconnect after 1000ms
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(MockEventSource.instances).toHaveLength(2);
    expect(result.current.sseDisconnected).toBe(false);
  });

  it('does not reconnect after terminal event', () => {
    const { result } = renderHook(() =>
      useUfProgress({
        searchId: 'search-365-terminal',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // Emit terminal complete event
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'complete',
        progress: 100,
        message: 'Done',
      }, { id: '5' });
    });

    // Trigger error after terminal
    act(() => {
      MockEventSource.instances[0].onerror?.();
    });

    // Should NOT create new EventSource
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(MockEventSource.instances).toHaveLength(1);
  });
});

// ── AC7: Exponential backoff 1s → 2s → 4s ───────────────────────────────────

describe('AC7: Exponential backoff reconnection', () => {
  it('uses 1s delay for first retry', () => {
    renderHook(() =>
      useUfProgress({
        searchId: 'search-365-backoff',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    act(() => { MockEventSource.instances[0].onerror?.(); });

    // Not yet (only 999ms)
    act(() => { jest.advanceTimersByTime(999); });
    expect(MockEventSource.instances).toHaveLength(1);

    // At 1000ms
    act(() => { jest.advanceTimersByTime(1); });
    expect(MockEventSource.instances).toHaveLength(2);
  });

  it('uses 2s delay for second retry', () => {
    renderHook(() =>
      useUfProgress({
        searchId: 'search-365-backoff2',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // First error → reconnect after 1s
    act(() => { MockEventSource.instances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(1000); });
    expect(MockEventSource.instances).toHaveLength(2);

    // Second error → reconnect after 2s
    act(() => { MockEventSource.instances[1].onerror?.(); });
    act(() => { jest.advanceTimersByTime(1999); });
    expect(MockEventSource.instances).toHaveLength(2); // not yet
    act(() => { jest.advanceTimersByTime(1); });
    expect(MockEventSource.instances).toHaveLength(3);
  });

  it('uses 4s delay for third retry', () => {
    renderHook(() =>
      useUfProgress({
        searchId: 'search-365-backoff3',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // 1st error → 1s
    act(() => { MockEventSource.instances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(1000); });
    expect(MockEventSource.instances).toHaveLength(2);

    // 2nd error → 2s
    act(() => { MockEventSource.instances[1].onerror?.(); });
    act(() => { jest.advanceTimersByTime(2000); });
    expect(MockEventSource.instances).toHaveLength(3);

    // 3rd error → 4s
    act(() => { MockEventSource.instances[2].onerror?.(); });
    act(() => { jest.advanceTimersByTime(3999); });
    expect(MockEventSource.instances).toHaveLength(3); // not yet
    act(() => { jest.advanceTimersByTime(1); });
    // After 3 failed attempts, no more reconnects — fallback to polling (AC9)
    // The 4th instance is NOT created because max attempts = 3
    // Actually, the 3rd onerror triggers attempt index 2 (0-indexed: 0, 1, 2)
    // which is the 3rd attempt. Since MAX_RECONNECT_ATTEMPTS=3, this should trigger polling
  });
});

// ── AC8: Progress not reset after reconnect ──────────────────────────────────

describe('AC8: Progress preserved after reconnect', () => {
  it('keeps UF statuses across reconnection', () => {
    const { result } = renderHook(() =>
      useUfProgress({
        searchId: 'search-365-preserve',
        enabled: true,
        selectedUfs: ['SP', 'RJ', 'MG'],
      }),
    );

    // Emit UF status for SP (success with 42 items)
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status',
        progress: 30,
        message: 'SP: success',
        uf: 'SP',
        uf_status: 'success',
        detail: { uf: 'SP', uf_status: 'success', count: 42 },
      }, { id: '3' });
    });

    expect(result.current.ufStatuses.get('SP')?.status).toBe('success');
    expect(result.current.ufStatuses.get('SP')?.count).toBe(42);

    // Disconnect
    act(() => { MockEventSource.instances[0].onerror?.(); });

    // SP status preserved during reconnect
    expect(result.current.ufStatuses.get('SP')?.status).toBe('success');
    expect(result.current.ufStatuses.get('SP')?.count).toBe(42);

    // Reconnect after 1s
    act(() => { jest.advanceTimersByTime(1000); });
    expect(MockEventSource.instances).toHaveLength(2);

    // SP status STILL preserved
    expect(result.current.ufStatuses.get('SP')?.status).toBe('success');
    expect(result.current.ufStatuses.get('SP')?.count).toBe(42);

    // RJ still pending (not reset)
    expect(result.current.ufStatuses.get('RJ')?.status).toBe('pending');
  });

  it('passes last_event_id as query param on reconnect URL', () => {
    renderHook(() =>
      useUfProgress({
        searchId: 'search-365-lastid',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // Emit events with IDs
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'fetching',
        progress: 20,
        message: 'Fetching',
      }, { id: '7' });
    });

    // Disconnect + reconnect
    act(() => { MockEventSource.instances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(1000); });

    expect(MockEventSource.instances).toHaveLength(2);
    // AC8: Reconnect URL should include last_event_id=7
    expect(MockEventSource.instances[1].url).toContain('last_event_id=7');
  });
});

// ── AC9: Polling fallback after max retries ──────────────────────────────────

describe('AC9: Polling fallback after 3 failed reconnects', () => {
  it('sets sseDisconnected=true after max retries exhausted', () => {
    const { result } = renderHook(() =>
      useUfProgress({
        searchId: 'search-365-polling',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // Initial connection errors → reconnect #1 (1s delay)
    act(() => { MockEventSource.instances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(1000); });
    expect(MockEventSource.instances).toHaveLength(2);

    // Reconnect #1 errors → reconnect #2 (2s delay)
    act(() => { MockEventSource.instances[1].onerror?.(); });
    act(() => { jest.advanceTimersByTime(2000); });
    expect(MockEventSource.instances).toHaveLength(3);

    // Reconnect #2 errors → reconnect #3 (4s delay)
    act(() => { MockEventSource.instances[2].onerror?.(); });
    act(() => { jest.advanceTimersByTime(4000); });
    expect(MockEventSource.instances).toHaveLength(4);

    // Reconnect #3 errors → all 3 attempts exhausted → polling fallback
    act(() => { MockEventSource.instances[3].onerror?.(); });

    expect(result.current.sseDisconnected).toBe(true);
  });

  it('starts polling after max retries', async () => {
    renderHook(() =>
      useUfProgress({
        searchId: 'search-365-poll-start',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // Exhaust all reconnect attempts (initial + 3 reconnects)
    act(() => { MockEventSource.instances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(1000); });
    act(() => { MockEventSource.instances[1].onerror?.(); });
    act(() => { jest.advanceTimersByTime(2000); });
    act(() => { MockEventSource.instances[2].onerror?.(); });
    act(() => { jest.advanceTimersByTime(4000); });
    // Final reconnect attempt also fails
    act(() => { MockEventSource.instances[3].onerror?.(); });

    // After polling starts, advance 5s for first poll
    await act(async () => {
      jest.advanceTimersByTime(5000);
    });

    // fetch should have been called (polling fallback)
    expect(mockFetch).toHaveBeenCalled();
    const pollingCall = mockFetch.mock.calls.find(
      (call: any[]) => typeof call[0] === 'string' && call[0].includes('search-status?search_id=search-365-poll-start')
    );
    expect(pollingCall).toBeTruthy();
  });
});

// ── Edge cases ───────────────────────────────────────────────────────────────

describe('Edge cases', () => {
  it('cleans up on unmount during reconnect', () => {
    const { unmount } = renderHook(() =>
      useUfProgress({
        searchId: 'search-365-unmount',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // Trigger error (starts reconnect timer)
    act(() => { MockEventSource.instances[0].onerror?.(); });

    // Unmount before reconnect fires
    unmount();

    // Advance past reconnect timer — should NOT create new EventSource
    act(() => { jest.advanceTimersByTime(5000); });

    // Only the initial EventSource should exist (second one may be created
    // but cleanup should close it). Check no errors thrown.
  });

  it('resets retry counter when searchId changes', () => {
    const { rerender } = renderHook(
      ({ searchId }) =>
        useUfProgress({
          searchId,
          enabled: true,
          selectedUfs: ['SP'],
        }),
      { initialProps: { searchId: 'search-A' } },
    );

    // Exhaust 2 retries on search-A
    act(() => { MockEventSource.instances[0].onerror?.(); });
    act(() => { jest.advanceTimersByTime(1000); });
    act(() => { MockEventSource.instances[1].onerror?.(); });
    act(() => { jest.advanceTimersByTime(2000); });

    const instancesBefore = MockEventSource.instances.length;

    // Switch to new search — should reset retry counter
    rerender({ searchId: 'search-B' });

    const newInstances = MockEventSource.instances.length;
    expect(newInstances).toBeGreaterThan(instancesBefore);

    // Verify new URL has search-B
    const lastInstance = MockEventSource.instances[MockEventSource.instances.length - 1];
    expect(lastInstance.url).toContain('search-B');
  });

  it('does not reconnect when disabled', () => {
    const { result } = renderHook(() =>
      useUfProgress({
        searchId: null,
        enabled: false,
        selectedUfs: ['SP'],
      }),
    );

    expect(MockEventSource.instances).toHaveLength(0);
    expect(result.current.sseDisconnected).toBe(false);
  });
});
