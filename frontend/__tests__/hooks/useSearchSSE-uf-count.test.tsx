/**
 * STORY-326 AC4/AC3: Verify useSearchSSE correctly reads `count` from
 * uf_status SSE events and sums ufTotalFound across UFs.
 *
 * Root cause: Frontend was reading `event.detail.items_found` (from emit_uf_complete)
 * instead of `event.detail.count` (from emit_uf_status). This caused the UF grid
 * to permanently show "0 oportunidades" even when sources returned data.
 */

import { renderHook, act } from '@testing-library/react';
import { useSearchSSE } from '../../hooks/useSearchSSE';

// Use shared MockEventSource (installed globally via jest.setup.js, STORY-368)
import { MockEventSource } from '../utils/mock-event-source';

// ---- Test suite ----

describe('STORY-326: useSearchSSE uf_status count field', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  // ---------------------------------------------------------------------------
  // AC4: uf_status event with detail.count populates ufStatuses correctly
  // ---------------------------------------------------------------------------

  it('AC4: uf_status with detail.count=42 sets ufStatuses.get("SP").count to 42', () => {
    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-326-01',
        enabled: true,
        selectedUfs: ['SP'],
      }),
    );

    // Connect
    act(() => {
      MockEventSource.instances[0]?.simulateOpen();
    });

    // Emit uf_status event with count field (as backend sends it)
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status',
        progress: 30,
        message: 'SP: success',
        detail: {
          uf: 'SP',
          uf_status: 'success',
          count: 42,
        },
      });
    });

    const spStatus = result.current.ufStatuses.get('SP');
    expect(spStatus).toBeDefined();
    expect(spStatus!.status).toBe('success');
    expect(spStatus!.count).toBe(42);
  });

  it('AC4: uf_status with detail.count=0 sets count to 0 (not undefined)', () => {
    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-326-02',
        enabled: true,
        selectedUfs: ['ES'],
      }),
    );

    act(() => { MockEventSource.instances[0]?.simulateOpen(); });

    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status',
        progress: 30,
        message: 'ES: success',
        detail: { uf: 'ES', uf_status: 'success', count: 0 },
      });
    });

    const esStatus = result.current.ufStatuses.get('ES');
    expect(esStatus).toBeDefined();
    expect(esStatus!.status).toBe('success');
    expect(esStatus!.count).toBe(0);
  });

  it('AC4: items_found field is NOT used for uf_status count', () => {
    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-326-03',
        enabled: true,
        selectedUfs: ['RJ'],
      }),
    );

    act(() => { MockEventSource.instances[0]?.simulateOpen(); });

    // Emit event with items_found (old wrong field) but no count
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status',
        progress: 30,
        message: 'RJ: success',
        detail: { uf: 'RJ', uf_status: 'success', items_found: 99 },
      });
    });

    const rjStatus = result.current.ufStatuses.get('RJ');
    expect(rjStatus).toBeDefined();
    // count should be undefined (not 99) because we read detail.count, not items_found
    expect(rjStatus!.count).toBeUndefined();
  });

  // ---------------------------------------------------------------------------
  // AC3: ufTotalFound sums correctly across multiple UFs
  // ---------------------------------------------------------------------------

  it('AC3: ufTotalFound sums count across UFs with success/recovered status', () => {
    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-326-04',
        enabled: true,
        selectedUfs: ['SP', 'RJ', 'MG', 'ES'],
      }),
    );

    act(() => { MockEventSource.instances[0]?.simulateOpen(); });

    // SP: success with 42
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 20, message: 'SP: success',
        detail: { uf: 'SP', uf_status: 'success', count: 42 },
      });
    });

    // RJ: success with 108
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 35, message: 'RJ: success',
        detail: { uf: 'RJ', uf_status: 'success', count: 108 },
      });
    });

    // MG: recovered with 25
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 45, message: 'MG: recovered',
        detail: { uf: 'MG', uf_status: 'recovered', count: 25 },
      });
    });

    // ES: failed (should NOT contribute to total)
    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 50, message: 'ES: failed',
        detail: { uf: 'ES', uf_status: 'failed', reason: 'timeout' },
      });
    });

    // Total = 42 + 108 + 25 = 175 (ES excluded)
    expect(result.current.ufTotalFound).toBe(175);
  });

  it('AC3: ufTotalFound is 0 when all UFs have 0 results', () => {
    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-326-05',
        enabled: true,
        selectedUfs: ['SP', 'RJ'],
      }),
    );

    act(() => { MockEventSource.instances[0]?.simulateOpen(); });

    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 30, message: 'SP: success',
        detail: { uf: 'SP', uf_status: 'success', count: 0 },
      });
    });

    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 50, message: 'RJ: success',
        detail: { uf: 'RJ', uf_status: 'success', count: 0 },
      });
    });

    expect(result.current.ufTotalFound).toBe(0);
  });

  // ---------------------------------------------------------------------------
  // Edge cases
  // ---------------------------------------------------------------------------

  it('onUfStatus callback receives correct count from detail.count', () => {
    const ufStatusEvents: Array<{ uf: string; count?: number }> = [];

    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-326-06',
        enabled: true,
        selectedUfs: ['SP'],
        onUfStatus: (ev) => ufStatusEvents.push({ uf: ev.uf, count: ev.count }),
      }),
    );

    act(() => { MockEventSource.instances[0]?.simulateOpen(); });

    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 30, message: 'SP: success',
        detail: { uf: 'SP', uf_status: 'success', count: 150 },
      });
    });

    expect(ufStatusEvents).toHaveLength(1);
    expect(ufStatusEvents[0].uf).toBe('SP');
    expect(ufStatusEvents[0].count).toBe(150);
  });

  it('retrying status with attempt number does not affect count', () => {
    const { result } = renderHook(() =>
      useSearchSSE({
        searchId: 'search-326-07',
        enabled: true,
        selectedUfs: ['MG'],
      }),
    );

    act(() => { MockEventSource.instances[0]?.simulateOpen(); });

    act(() => {
      MockEventSource.instances[0].simulateMessage({
        stage: 'uf_status', progress: 20, message: 'MG: retrying',
        detail: { uf: 'MG', uf_status: 'retrying', attempt: 2 },
      });
    });

    const mgStatus = result.current.ufStatuses.get('MG');
    expect(mgStatus!.status).toBe('retrying');
    expect(mgStatus!.attempt).toBe(2);
    expect(mgStatus!.count).toBeUndefined();
    // retrying should NOT contribute to total
    expect(result.current.ufTotalFound).toBe(0);
  });
});
