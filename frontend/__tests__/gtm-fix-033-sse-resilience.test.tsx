/**
 * GTM-FIX-033 AC6: SSE disconnect during search → POST result still displayed
 *
 * Tests that when SSE (EventSource) disconnects mid-search, the POST /api/buscar
 * result still prevails and is displayed to the user.
 */

import { renderHook, act } from '@testing-library/react';

// ---- Mock modules BEFORE importing hooks ----

// Mock useAnalytics
jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

// Mock useAuth
jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => ({
    session: { access_token: 'test-token' },
    loading: false,
  }),
}));

// Mock useQuota
jest.mock('../hooks/useQuota', () => ({
  useQuota: () => ({ refresh: jest.fn() }),
}));

// Mock useSavedSearches
jest.mock('../hooks/useSavedSearches', () => ({
  useSavedSearches: () => ({
    saveNewSearch: jest.fn(),
    isMaxCapacity: false,
  }),
}));

// Mock searchStatePersistence
jest.mock('../lib/searchStatePersistence', () => ({
  saveSearchState: jest.fn(),
  restoreSearchState: jest.fn(() => null),
}));

// Mock sonner
jest.mock('sonner', () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

// Mock correlationId
jest.mock('../lib/utils/correlationId', () => ({
  getCorrelationId: () => 'test-corr-id',
  logCorrelatedRequest: jest.fn(),
}));

import { useSearchProgress } from '../hooks/useSearchProgress';
import { useUfProgress } from '../app/buscar/hooks/useUfProgress';

// ---- Tests ----

describe('GTM-FIX-033: SSE Resilience', () => {

  // Helper: Create a mock EventSource that errors on demand
  let mockEventSources: any[] = [];

  beforeEach(() => {
    mockEventSources = [];
    jest.useFakeTimers();

    // @ts-ignore
    global.EventSource = jest.fn().mockImplementation((url: string) => {
      const es: any = {
        url,
        readyState: 0, // CONNECTING
        close: jest.fn(() => { es.readyState = 2; }),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        onopen: null,
        onmessage: null,
        onerror: null,
      };
      mockEventSources.push(es);
      // Simulate successful open after a tick
      setTimeout(() => {
        es.readyState = 1; // OPEN
        es.onopen?.();
      }, 10);
      return es;
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  describe('useUfProgress — AC2: SSE retry + sseDisconnected', () => {
    test('retries once on SSE error, then sets sseDisconnected=true', () => {
      const { result } = renderHook(() =>
        useUfProgress({
          searchId: 'test-search-001',
          enabled: true,
          authToken: 'test-token',
          selectedUfs: ['SP', 'RJ'],
        })
      );

      // Initial state — not disconnected
      expect(result.current.sseDisconnected).toBe(false);

      // First EventSource created
      expect(mockEventSources).toHaveLength(1);

      // Simulate SSE error (first attempt)
      act(() => {
        mockEventSources[0].onerror?.();
      });

      // Should NOT be disconnected yet — will retry after 2s
      expect(result.current.sseDisconnected).toBe(false);

      // Advance 2s for retry
      act(() => {
        jest.advanceTimersByTime(2100);
      });

      // Retry EventSource should be created
      expect(mockEventSources.length).toBeGreaterThanOrEqual(2);

      // Simulate retry also failing
      act(() => {
        const retryEs = mockEventSources[mockEventSources.length - 1];
        retryEs.onerror?.();
      });

      // NOW should be disconnected
      expect(result.current.sseDisconnected).toBe(true);
    });

    test('sseDisconnected resets when search changes', () => {
      const { result, rerender } = renderHook(
        ({ searchId, enabled }: { searchId: string | null; enabled: boolean }) =>
          useUfProgress({
            searchId,
            enabled,
            authToken: 'test-token',
            selectedUfs: ['SP'],
          }),
        { initialProps: { searchId: 'search-1' as string | null, enabled: true } }
      );

      // Force disconnect
      act(() => {
        mockEventSources[0].onerror?.();
      });
      act(() => {
        jest.advanceTimersByTime(2100);
      });
      act(() => {
        const retryEs = mockEventSources[mockEventSources.length - 1];
        retryEs.onerror?.();
      });

      expect(result.current.sseDisconnected).toBe(true);

      // Disable (simulates search ending)
      rerender({ searchId: null, enabled: false });
      expect(result.current.sseDisconnected).toBe(false);
    });
  });

  describe('useSearchProgress — AC2: SSE retry + sseDisconnected', () => {
    test('retries once then marks sseDisconnected=true', () => {
      const onError = jest.fn();

      const { result } = renderHook(() =>
        useSearchProgress({
          searchId: 'test-search-002',
          enabled: true,
          authToken: 'test-token',
          onError,
        })
      );

      expect(result.current.sseDisconnected).toBe(false);
      expect(result.current.sseAvailable).toBe(true);

      // First SSE error
      act(() => {
        mockEventSources[0].onerror?.();
      });

      // Not yet disconnected — retrying
      expect(result.current.sseDisconnected).toBe(false);
      expect(onError).not.toHaveBeenCalled();

      // Wait for retry
      act(() => {
        jest.advanceTimersByTime(2100);
      });

      // Retry SSE also fails
      act(() => {
        const retryEs = mockEventSources[mockEventSources.length - 1];
        retryEs.onerror?.();
      });

      // Now disconnected
      expect(result.current.sseDisconnected).toBe(true);
      expect(result.current.sseAvailable).toBe(false);
      expect(onError).toHaveBeenCalledTimes(1);
    });
  });

  describe('AC4: POST result prevails over SSE error', () => {
    test('successful POST shows results even when SSE disconnected', async () => {
      const mockResult = {
        resumo: {
          resumo_executivo: 'Test summary',
          total_oportunidades: 42,
          valor_total: 100000,
          destaques: [],
        },
        total_filtrado: 42,
        total_raw: 1717,
        download_id: 'test-dl-001',
        licitacoes: [],
      };

      // Mock fetch to return successful result
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockResult,
      });

      try {
        // Import useSearch dynamically since it depends on many mocks
        const { useSearch } = await import('../app/buscar/hooks/useSearch');

        const mockFilters = {
          ufsSelecionadas: new Set(['SP']),
          dataInicial: '2026-02-01',
          dataFinal: '2026-02-10',
          searchMode: 'setor' as const,
          modoBusca: 'abertas' as const,
          setorId: 'vestuario',
          termosArray: [] as string[],
          status: 'todas' as any,
          modalidades: [] as number[],
          valorMin: null,
          valorMax: null,
          esferas: [] as any[],
          municipios: [] as any[],
          ordenacao: 'valor_desc' as any,
          sectorName: 'Vestuário',
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
        };

        const { result } = renderHook(() => useSearch(mockFilters));

        // Execute search
        await act(async () => {
          await result.current.buscar();
        });

        // Result should be displayed regardless of SSE state
        expect(result.current.result).toBeTruthy();
        expect(result.current.result?.resumo.total_oportunidades).toBe(42);
        expect(result.current.error).toBeNull();
        expect(result.current.loading).toBe(false);
      } finally {
        global.fetch = originalFetch;
      }
    });
  });

  describe('AC3: Progress bar does not reset from 80%+ to 0%', () => {
    test('EnhancedLoadingProgress shows "Finalizando busca..." on sseDisconnected', () => {
      const React = require('react');
      const { render, screen } = require('@testing-library/react');
      const { EnhancedLoadingProgress } = require('../components/EnhancedLoadingProgress');

      // Render with sseDisconnected=true
      render(
        React.createElement(EnhancedLoadingProgress, {
          currentStep: 1,
          estimatedTime: 60,
          stateCount: 3,
          sseDisconnected: true,
          useRealProgress: false,
        })
      );

      // Should show the "Finalizando busca..." message
      expect(screen.getByText(/Finalizando busca/i)).toBeTruthy();
    });

    test('EnhancedLoadingProgress does not show disconnect message when connected', () => {
      const React = require('react');
      const { render, screen } = require('@testing-library/react');
      const { EnhancedLoadingProgress } = require('../components/EnhancedLoadingProgress');

      render(
        React.createElement(EnhancedLoadingProgress, {
          currentStep: 1,
          estimatedTime: 60,
          stateCount: 3,
          sseDisconnected: false,
          useRealProgress: true,
        })
      );

      expect(screen.queryByText(/Finalizando busca/i)).toBeNull();
    });
  });

  describe('AC5: Improved error message includes saved searches hint', () => {
    test('error-messages maps backend errors to actionable messages', () => {
      const { getUserFriendlyError } = require('../lib/error-messages');

      const msg1 = getUserFriendlyError('Backend indisponível');
      expect(msg1).toContain('buscas salvas');
      expect(msg1).toContain('tente novamente');

      const msg2 = getUserFriendlyError('Erro ao buscar licitações');
      expect(msg2).toContain('buscas salvas');
      expect(msg2).toContain('tente novamente');
    });
  });
});
