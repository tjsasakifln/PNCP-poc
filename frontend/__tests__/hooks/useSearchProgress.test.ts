/**
 * Tests for useSearchProgress hook — GTM-RESILIENCE-A02 AC13
 * Test degraded SSE event handling and state management
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useSearchProgress } from '../../hooks/useSearchProgress';
import type { SearchProgressEvent } from '../../hooks/useSearchProgress';

describe('useSearchProgress - GTM-RESILIENCE-A02 Degraded Handling', () => {
  let mockEventSource: any;
  let eventListeners: Record<string, Function>;

  beforeEach(() => {
    jest.clearAllMocks();
    eventListeners = {};

    // Mock EventSource based on jest.setup.js pattern
    mockEventSource = {
      url: '',
      readyState: 0,
      onopen: null,
      onmessage: null,
      onerror: null,
      close: jest.fn(function(this: any) {
        this.readyState = 2;
      }),
      addEventListener: jest.fn((event: string, handler: Function) => {
        eventListeners[event] = handler;
      }),
      removeEventListener: jest.fn(),
    };

    // Override global EventSource
    (global as any).EventSource = jest.fn((url: string) => {
      mockEventSource.url = url;
      mockEventSource.readyState = 1; // OPEN
      // Don't auto-trigger onerror like jest.setup.js does (we want manual control)
      return mockEventSource;
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('AC13: isDegraded state transition', () => {
    it('should set isDegraded=true when SSE event stage="degraded"', async () => {
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
        })
      );

      // Simulate SSE connection open
      act(() => {
        mockEventSource.onopen?.();
      });

      expect(result.current.isConnected).toBe(true);
      expect(result.current.isDegraded).toBe(false);

      // Simulate degraded SSE event
      const degradedEvent: SearchProgressEvent = {
        stage: 'degraded',
        progress: 100,
        message: 'Dados de cache usado',
        detail: {
          reason: 'PNCP timeout',
          cache_age_hours: 3,
          cache_level: 'supabase',
          sources_failed: ['PNCP'],
          sources_ok: ['PCP'],
          coverage_pct: 60,
        },
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(degradedEvent),
        });
      });

      // Verify degraded state
      await waitFor(() => {
        expect(result.current.isDegraded).toBe(true);
      });

      expect(result.current.isConnected).toBe(false); // SSE closed
      expect(result.current.sseDisconnected).toBe(false); // Not a disconnect, just closed
      expect(result.current.currentEvent).toEqual(degradedEvent);
    });

    it('should set isDegraded=false when SSE event stage="complete"', async () => {
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
        })
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      // Send normal complete event
      const completeEvent: SearchProgressEvent = {
        stage: 'complete',
        progress: 100,
        message: 'Busca concluída',
        detail: {},
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(completeEvent),
        });
      });

      await waitFor(() => {
        expect(result.current.isDegraded).toBe(false);
      });

      expect(result.current.isConnected).toBe(false); // SSE closed (normal end)
      expect(result.current.sseDisconnected).toBe(false);
    });

    it('should preserve isDegraded=false for normal stages', async () => {
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
        })
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      // Send fetching event
      const fetchingEvent: SearchProgressEvent = {
        stage: 'fetching',
        progress: 50,
        message: 'Buscando dados',
        detail: { uf_index: 5, uf_total: 10 },
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(fetchingEvent),
        });
      });

      expect(result.current.isDegraded).toBe(false);
      expect(result.current.isConnected).toBe(true); // Still connected
    });
  });

  describe('AC13: degradedDetail metadata', () => {
    it('should populate degradedDetail from degraded event detail', async () => {
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
        })
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      const degradedEvent: SearchProgressEvent = {
        stage: 'degraded',
        progress: 100,
        message: 'Dados parciais disponíveis',
        detail: {
          reason: 'Multi-source failure',
          cache_age_hours: 12,
          cache_level: 'memory',
          sources_failed: ['PNCP', 'ComprasGov'],
          sources_ok: ['PCP'],
          coverage_pct: 30,
        },
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(degradedEvent),
        });
      });

      await waitFor(() => {
        expect(result.current.isDegraded).toBe(true);
      });

      expect(result.current.degradedDetail).toEqual(degradedEvent.detail);
    });

    it('should set degradedDetail=null for non-degraded events', async () => {
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
        })
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      const normalEvent: SearchProgressEvent = {
        stage: 'filtering',
        progress: 75,
        message: 'Filtrando resultados',
        detail: { total_filtered: 42 },
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(normalEvent),
        });
      });

      expect(result.current.degradedDetail).toBeNull();
    });

    it('should reset degraded state when new search starts', async () => {
      const { result, rerender } = renderHook(
        ({ searchId }) =>
          useSearchProgress({
            searchId,
            enabled: true,
          }),
        { initialProps: { searchId: 'search-1' } }
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      // First search ends degraded
      const degradedEvent: SearchProgressEvent = {
        stage: 'degraded',
        progress: 100,
        message: 'Dados degradados',
        detail: { reason: 'timeout' },
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(degradedEvent),
        });
      });

      await waitFor(() => {
        expect(result.current.isDegraded).toBe(true);
      });

      // Start new search
      rerender({ searchId: 'search-2' });

      // Verify degraded state was reset
      await waitFor(() => {
        expect(result.current.isDegraded).toBe(false);
        expect(result.current.degradedDetail).toBeNull();
      });
    });
  });

  describe('AC13: SSE connection lifecycle with degraded', () => {
    it('should close SSE connection when degraded event received', async () => {
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
        })
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      expect(result.current.isConnected).toBe(true);

      const degradedEvent: SearchProgressEvent = {
        stage: 'degraded',
        progress: 100,
        message: 'Cache usado',
        detail: { cache_level: 'local' },
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(degradedEvent),
        });
      });

      await waitFor(() => {
        expect(mockEventSource.close).toHaveBeenCalled();
        expect(result.current.isConnected).toBe(false);
      });
    });

    it('should NOT set sseDisconnected when degraded closes SSE', async () => {
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
        })
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      const degradedEvent: SearchProgressEvent = {
        stage: 'degraded',
        progress: 100,
        message: 'Cache usado',
        detail: {},
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(degradedEvent),
        });
      });

      await waitFor(() => {
        expect(result.current.isDegraded).toBe(true);
      });

      // AC7: "degraded" closes SSE but is NOT sseDisconnected (different from error)
      expect(result.current.sseDisconnected).toBe(false);
      expect(result.current.isConnected).toBe(false);
    });
  });

  describe('onEvent callback with degraded', () => {
    it('should call onEvent callback when degraded event received', async () => {
      const onEventMock = jest.fn();
      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-123',
          enabled: true,
          onEvent: onEventMock,
        })
      );

      act(() => {
        mockEventSource.onopen?.();
      });

      const degradedEvent: SearchProgressEvent = {
        stage: 'degraded',
        progress: 100,
        message: 'Dados parciais',
        detail: { cache_age_hours: 5 },
      };

      act(() => {
        mockEventSource.onmessage?.({
          data: JSON.stringify(degradedEvent),
        });
      });

      await waitFor(() => {
        expect(onEventMock).toHaveBeenCalledWith(degradedEvent);
      });
    });
  });
});
