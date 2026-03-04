/**
 * CRIT-052: SSE Progress Bar — Regression Tests
 *
 * Tests for:
 * - AC1: Frontend maintains high-water mark (progress never decreases)
 * - AC2: Reconnecting indicator shown during SSE reconnection
 * - AC3: Progress events with progress=-1 are ignored by progress bar
 * - AC4: Search completing during reconnection displays results normally
 * - AC5: Monotonic progress validation
 */

import { renderHook, act } from '@testing-library/react';
import { useSearchSSE } from '../../hooks/useSearchSSE';

// Use shared MockEventSource (installed globally via jest.setup.js, STORY-368)
import { MockEventSource } from '../utils/mock-event-source';

// ---- Test suite ----

describe('CRIT-052: SSE Progress Bar Regression', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  // ===========================================================================
  // AC1: High-water mark — progress never decreases
  // ===========================================================================

  describe('AC1: Progress high-water mark', () => {
    it('should never show progress lower than previously received value', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'hwm-001',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Send progress at 30%
      act(() => es.simulateMessage({ stage: 'fetching', progress: 30, message: 'Buscando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(30);

      // Send progress at 60%
      act(() => es.simulateMessage({ stage: 'fetching', progress: 60, message: 'Buscando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(60);

      // Send progress at 40% (lower!) — should be clamped to 60%
      act(() => es.simulateMessage({ stage: 'fetching', progress: 40, message: 'Buscando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(60);

      // Send progress at 80% — should pass through
      act(() => es.simulateMessage({ stage: 'filtering', progress: 80, message: 'Filtrando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(80);
    });

    it('should clamp progress to high-water mark after SSE reconnection', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'hwm-002',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Get progress to 55%
      act(() => es.simulateMessage({ stage: 'fetching', progress: 55, message: 'Buscando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(55);

      // Simulate SSE error and reconnection
      act(() => es.simulateError());

      // First retry is immediate (0ms delay)
      act(() => jest.advanceTimersByTime(0));

      // New EventSource created
      expect(MockEventSource.instances.length).toBeGreaterThanOrEqual(2);
      const retryEs = MockEventSource.instances[MockEventSource.instances.length - 1];
      act(() => retryEs.simulateOpen());

      // Backend sends progress at 10% on reconnection (replaying from start)
      act(() => retryEs.simulateMessage({ stage: 'connecting', progress: 10, message: 'Conectando...', detail: {} }));

      // Should still show 55% (high-water mark), not 10%
      expect(result.current.currentEvent?.progress).toBe(55);
    });

    it('should reset high-water mark when searchId changes (new search)', () => {
      const { result, rerender } = renderHook(
        (props: { searchId: string }) =>
          useSearchSSE({
            searchId: props.searchId,
            enabled: true,
          }),
        { initialProps: { searchId: 'hwm-003a' } }
      );

      const es1 = MockEventSource.instances[0];
      act(() => es1.simulateOpen());

      // Get progress to 80%
      act(() => es1.simulateMessage({ stage: 'filtering', progress: 80, message: 'Filtrando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(80);

      // Start new search
      rerender({ searchId: 'hwm-003b' });

      // New EventSource for new search
      const es2 = MockEventSource.instances[MockEventSource.instances.length - 1];
      act(() => es2.simulateOpen());

      // New search sends progress at 10% — should NOT be clamped to 80%
      act(() => es2.simulateMessage({ stage: 'connecting', progress: 10, message: 'Conectando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(10);
    });

    it('should maintain monotonically increasing progress across a full search lifecycle', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'hwm-monotonic',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      const progressValues: number[] = [];
      const events = [
        { stage: 'connecting', progress: 5, message: 'Connecting...', detail: {} },
        { stage: 'fetching', progress: 25, message: 'Fetching...', detail: {} },
        { stage: 'fetching', progress: 45, message: 'Fetching...', detail: {} },
        { stage: 'fetching', progress: 30, message: 'Out-of-order event', detail: {} },
        { stage: 'filtering', progress: 70, message: 'Filtering...', detail: {} },
        { stage: 'filtering', progress: 65, message: 'Another out-of-order', detail: {} },
        { stage: 'llm', progress: 90, message: 'LLM...', detail: {} },
        { stage: 'complete', progress: 100, message: 'Done!', detail: {} },
      ];

      for (const event of events) {
        act(() => es.simulateMessage(event));
        if (result.current.currentEvent) {
          progressValues.push(result.current.currentEvent.progress);
        }
      }

      // Verify strict monotonic increase (each value >= previous)
      for (let i = 1; i < progressValues.length; i++) {
        expect(progressValues[i]).toBeGreaterThanOrEqual(progressValues[i - 1]);
      }

      // Verify specific clamps
      expect(progressValues).toEqual([5, 25, 45, 45, 70, 70, 90, 100]);
    });
  });

  // ===========================================================================
  // AC2: Reconnecting indicator
  // ===========================================================================

  describe('AC2: Reconnecting indicator', () => {
    it('should set isReconnecting=true during SSE reconnection attempt', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'reconnect-001',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Initially not reconnecting
      expect(result.current.isReconnecting).toBe(false);

      // Trigger SSE error
      act(() => es.simulateError());

      // After error, should be reconnecting (first retry is immediate at 0ms)
      expect(result.current.isReconnecting).toBe(true);

      // Advance time for retry
      act(() => jest.advanceTimersByTime(0));

      // New EventSource connects successfully
      const retryEs = MockEventSource.instances[MockEventSource.instances.length - 1];
      act(() => retryEs.simulateOpen());

      // After successful reconnection, isReconnecting should be false
      expect(result.current.isReconnecting).toBe(false);
    });

    it('should not reset progress to 0 when entering reconnecting state', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'reconnect-002',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Get progress to 55%
      act(() => es.simulateMessage({ stage: 'fetching', progress: 55, message: 'Buscando...', detail: {} }));
      const progressBefore = result.current.currentEvent?.progress;

      // Trigger reconnection
      act(() => es.simulateError());

      // Progress should still be at 55% (currentEvent preserved)
      expect(result.current.currentEvent?.progress).toBe(progressBefore);
    });
  });

  // ===========================================================================
  // AC3: Progress events with progress=-1 are ignored
  // ===========================================================================

  describe('AC3: Events with progress=-1 do not affect progress bar', () => {
    it('should not update currentEvent for source_complete events (progress=-1)', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'meta-001',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Send normal progress event
      act(() => es.simulateMessage({ stage: 'fetching', progress: 40, message: 'Buscando...', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(40);
      expect(result.current.currentEvent?.stage).toBe('fetching');

      // Send source_complete with progress=-1
      act(() => es.simulateMessage({
        stage: 'source_complete',
        progress: -1,
        message: 'PNCP: success',
        detail: { source: 'PNCP', source_status: 'success', record_count: 42, duration_ms: 1500 },
      }));

      // currentEvent should NOT have changed (source_complete is metadata)
      expect(result.current.currentEvent?.progress).toBe(40);
      expect(result.current.currentEvent?.stage).toBe('fetching');

      // But source status should be updated
      expect(result.current.sourceStatuses.get('PNCP')?.status).toBe('success');
    });

    it('should not update currentEvent for source_error events (progress=-1)', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'meta-002',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Send normal progress event
      act(() => es.simulateMessage({ stage: 'fetching', progress: 50, message: 'Buscando...', detail: {} }));

      // Send source_error with progress=-1
      act(() => es.simulateMessage({
        stage: 'source_error',
        progress: -1,
        message: 'PCP: failed',
        detail: { source: 'PCP', error: 'timeout', duration_ms: 30000 },
      }));

      // currentEvent should stay at 50% fetching
      expect(result.current.currentEvent?.progress).toBe(50);
      expect(result.current.currentEvent?.stage).toBe('fetching');
    });

    it('should not update currentEvent for filter_summary events (progress=-1)', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'meta-003',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Send normal progress event
      act(() => es.simulateMessage({ stage: 'filtering', progress: 70, message: 'Filtrando...', detail: {} }));

      // Send filter_summary with progress=-1 (note: backend sends progress=70, but let's test -1 case)
      act(() => es.simulateMessage({
        stage: 'filter_summary',
        progress: -1,
        message: '15 relevantes de 42 analisadas',
        detail: { total_raw: 42, total_filtered: 15, rejected_keyword: 20, rejected_value: 5, rejected_llm: 2 },
      }));

      // currentEvent should stay at 70% filtering
      expect(result.current.currentEvent?.progress).toBe(70);
      expect(result.current.currentEvent?.stage).toBe('filtering');

      // But filter summary should be updated
      expect(result.current.filterSummary?.totalRaw).toBe(42);
      expect(result.current.filterSummary?.totalFiltered).toBe(15);
    });

    it('should not update currentEvent for pending_review events (progress=-1)', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'meta-004',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Send normal progress event
      act(() => es.simulateMessage({ stage: 'llm', progress: 90, message: 'IA...', detail: {} }));

      // Send pending_review with progress=-1
      act(() => es.simulateMessage({
        stage: 'pending_review',
        progress: -1,
        message: 'Reclassificação concluída',
        detail: { reclassified_count: 5, accepted_count: 3, rejected_count: 2 },
      }));

      // currentEvent should stay at 90% llm
      expect(result.current.currentEvent?.progress).toBe(90);
      expect(result.current.currentEvent?.stage).toBe('llm');

      // But pending review update should be available
      expect(result.current.pendingReviewUpdate?.reclassifiedCount).toBe(5);
    });

    it('should still process uf_status events (progress=-1) without affecting currentEvent', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'meta-005',
          enabled: true,
          selectedUfs: ['SP', 'RJ'],
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Send normal progress event
      act(() => es.simulateMessage({ stage: 'fetching', progress: 20, message: 'Buscando...', detail: {} }));

      // Send uf_status with progress=-1
      act(() => es.simulateMessage({
        stage: 'uf_status',
        progress: -1,
        message: 'UF SP: success',
        detail: { uf: 'SP', uf_status: 'success', count: 15 },
      }));

      // currentEvent should stay at 20% fetching
      expect(result.current.currentEvent?.progress).toBe(20);

      // UF status should be updated
      expect(result.current.ufStatuses.get('SP')?.status).toBe('success');
    });

    it('should still handle error events with progress=-1 as terminal events', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'meta-006',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Send normal progress event
      act(() => es.simulateMessage({ stage: 'fetching', progress: 40, message: 'Buscando...', detail: {} }));

      // Send error event (progress=-1 but should still be set as currentEvent)
      act(() => es.simulateMessage({
        stage: 'error',
        progress: -1,
        message: 'Erro na busca',
        detail: { error: 'timeout' },
      }));

      // Error events ARE terminal and should update currentEvent
      expect(result.current.currentEvent?.stage).toBe('error');
    });
  });

  // ===========================================================================
  // AC4: Search completing during reconnection
  // ===========================================================================

  describe('AC4: Search completes during reconnection', () => {
    it('should display complete event when received after reconnection', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'complete-001',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Get progress to 70%
      act(() => es.simulateMessage({ stage: 'filtering', progress: 70, message: 'Filtrando...', detail: {} }));

      // SSE disconnects
      act(() => es.simulateError());
      expect(result.current.isReconnecting).toBe(true);

      // Advance time for retry
      act(() => jest.advanceTimersByTime(0));

      // Reconnect succeeds
      const retryEs = MockEventSource.instances[MockEventSource.instances.length - 1];
      act(() => retryEs.simulateOpen());

      // Backend replays complete event
      act(() => retryEs.simulateMessage({
        stage: 'complete',
        progress: 100,
        message: 'Busca concluida!',
        detail: {},
      }));

      // Should show complete at 100%
      expect(result.current.currentEvent?.stage).toBe('complete');
      expect(result.current.currentEvent?.progress).toBe(100);
      expect(result.current.isReconnecting).toBe(false);
    });

    it('should display search_complete event when received after reconnection', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'complete-002',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      act(() => es.simulateMessage({ stage: 'fetching', progress: 50, message: 'Buscando...', detail: {} }));

      // Disconnect and reconnect
      act(() => es.simulateError());
      act(() => jest.advanceTimersByTime(0));

      const retryEs = MockEventSource.instances[MockEventSource.instances.length - 1];
      act(() => retryEs.simulateOpen());

      // Backend sends search_complete (async mode terminal event)
      act(() => retryEs.simulateMessage({
        stage: 'search_complete',
        progress: 100,
        message: 'Busca concluída — 42 resultados',
        detail: { search_id: 'complete-002', total_results: 42, has_results: true },
      }));

      expect(result.current.currentEvent?.stage).toBe('search_complete');
      expect(result.current.currentEvent?.progress).toBe(100);
    });
  });

  // ===========================================================================
  // AC5: Comprehensive monotonic progress validation
  // ===========================================================================

  describe('AC5: Monotonic progress validation', () => {
    it('should handle rapid out-of-order events without regression', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'mono-001',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Simulate rapid events that might arrive out of order
      const events = [
        { stage: 'connecting', progress: 5, message: 'msg', detail: {} },
        { stage: 'fetching', progress: 15, message: 'msg', detail: {} },
        { stage: 'fetching', progress: 10, message: 'msg', detail: {} }, // Out of order
        { stage: 'fetching', progress: 25, message: 'msg', detail: {} },
        { stage: 'fetching', progress: 35, message: 'msg', detail: {} },
        { stage: 'fetching', progress: 20, message: 'msg', detail: {} }, // Out of order
        { stage: 'filtering', progress: 60, message: 'msg', detail: {} },
        { stage: 'filtering', progress: 55, message: 'msg', detail: {} }, // Out of order
        { stage: 'llm', progress: 85, message: 'msg', detail: {} },
        { stage: 'excel', progress: 95, message: 'msg', detail: {} },
        { stage: 'complete', progress: 100, message: 'msg', detail: {} },
      ];

      let lastProgress = -1;
      for (const event of events) {
        act(() => es.simulateMessage(event));
        const currentProgress = result.current.currentEvent?.progress ?? 0;
        expect(currentProgress).toBeGreaterThanOrEqual(lastProgress);
        lastProgress = currentProgress;
      }
    });

    it('should handle interleaved metadata events without progress regression', () => {
      const { result } = renderHook(() =>
        useSearchSSE({
          searchId: 'mono-002',
          enabled: true,
        })
      );

      const es = MockEventSource.instances[0];
      act(() => es.simulateOpen());

      // Normal progress
      act(() => es.simulateMessage({ stage: 'fetching', progress: 40, message: 'msg', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(40);

      // Metadata event (progress=-1) — should not change currentEvent
      act(() => es.simulateMessage({
        stage: 'source_complete',
        progress: -1,
        message: 'PNCP done',
        detail: { source: 'PNCP', source_status: 'success', record_count: 10, duration_ms: 500 },
      }));
      expect(result.current.currentEvent?.progress).toBe(40);

      // Another metadata event — still no change
      act(() => es.simulateMessage({
        stage: 'source_error',
        progress: -1,
        message: 'PCP failed',
        detail: { source: 'PCP', error: 'timeout', duration_ms: 30000 },
      }));
      expect(result.current.currentEvent?.progress).toBe(40);

      // Normal progress continues
      act(() => es.simulateMessage({ stage: 'filtering', progress: 70, message: 'msg', detail: {} }));
      expect(result.current.currentEvent?.progress).toBe(70);
    });
  });
});
