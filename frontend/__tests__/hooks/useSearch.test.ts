/**
 * useSearch Hook Tests
 *
 * Tests search logic, SSE progress, download, save/load, refresh
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useSearch } from '@/app/buscar/hooks/useSearch';
import type { UseSearchParams } from '@/app/buscar/hooks/useSearch';

// Mock dependencies
const mockRefreshQuota = jest.fn();
const mockTrackEvent = jest.fn();
const mockSaveNewSearch = jest.fn();
const mockSession = { access_token: 'mock-token' };

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    session: mockSession,
    user: { id: 'user-1', email: 'test@test.com' },
    loading: false,
  }),
}));

jest.mock('../../hooks/useQuota', () => ({
  useQuota: () => ({
    refresh: mockRefreshQuota,
  }),
}));

jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

jest.mock('../../hooks/useSavedSearches', () => ({
  useSavedSearches: () => ({
    saveNewSearch: mockSaveNewSearch,
    isMaxCapacity: false,
  }),
}));

jest.mock('../../hooks/useSearchProgress', () => ({
  useSearchProgress: () => ({
    currentEvent: null,
    sseAvailable: true,
  }),
}));

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock fetch
global.fetch = jest.fn();

// Mock crypto.randomUUID (already polyfilled in jest.setup.js but ensure it's available)
global.crypto = {
  ...global.crypto,
  randomUUID: () => 'mock-uuid-123',
};

const defaultFilters: UseSearchParams = {
  ufsSelecionadas: new Set(['SP', 'RJ']),
  dataInicial: '2026-02-01',
  dataFinal: '2026-02-10',
  searchMode: 'setor',
  setorId: 'vestuario',
  termosArray: [],
  status: 'recebendo_proposta',
  modalidades: [],
  valorMin: null,
  valorMax: null,
  esferas: [],
  municipios: [],
  ordenacao: 'data_desc',
  sectorName: 'Vestuário e Uniformes',
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

const mockSearchResult = {
  resumo: {
    total_oportunidades: 42,
    valor_total: 5000000,
    total_raw: 100,
  },
  download_id: 'download-123',
  total_filtrado: 42,
  total_raw: 100,
};

beforeEach(() => {
  jest.clearAllMocks();
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => mockSearchResult,
  });
});

describe('useSearch hook', () => {
  it('should initialize with default states', () => {
    const { result } = renderHook(() => useSearch(defaultFilters));

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.result).toBe(null);
    expect(result.current.downloadLoading).toBe(false);
  });

  describe('buscar function', () => {
    it('should perform search successfully', async () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      await act(async () => {
        await result.current.buscar();
      });

      await waitFor(() => {
        expect(result.current.result).toEqual(mockSearchResult);
        expect(result.current.loading).toBe(false);
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/buscar',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer mock-token',
          }),
        })
      );
    });

    it('should handle API errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ message: 'Server error' }),
      });

      const { result } = renderHook(() => useSearch(defaultFilters));

      await act(async () => {
        await result.current.buscar();
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
        expect(result.current.loading).toBe(false);
      });
    });

    it('should handle 403 quota error', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ message: 'Quota excedida' }),
      });

      const { result } = renderHook(() => useSearch(defaultFilters));

      await act(async () => {
        await result.current.buscar();
      });

      await waitFor(() => {
        expect(result.current.quotaError).toBe('Quota excedida');
      });
    });

    it('should track analytics events', async () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      await act(async () => {
        await result.current.buscar();
      });

      await waitFor(() => {
        expect(mockTrackEvent).toHaveBeenCalledWith('search_started', expect.any(Object));
        expect(mockTrackEvent).toHaveBeenCalledWith('search_completed', expect.any(Object));
      });
    });

    it('should refresh quota after successful search', async () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      await act(async () => {
        await result.current.buscar();
      });

      await waitFor(() => {
        expect(mockRefreshQuota).toHaveBeenCalled();
      });
    });

    it('should not search if canSearch is false', async () => {
      const { result } = renderHook(() => useSearch({ ...defaultFilters, canSearch: false }));

      await act(async () => {
        await result.current.buscar();
      });

      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('cancelSearch function', () => {
    it('should cancel ongoing search', async () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      act(() => {
        result.current.buscar();
      });

      act(() => {
        result.current.cancelSearch();
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('handleDownload function', () => {
    it('should download file successfully', async () => {
      const mockBlob = new Blob(['test'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob,
      });

      const { result } = renderHook(() => useSearch(defaultFilters));

      act(() => {
        result.current.setResult(mockSearchResult);
      });

      await act(async () => {
        await result.current.handleDownload();
      });

      await waitFor(() => {
        expect(result.current.downloadLoading).toBe(false);
        expect(mockTrackEvent).toHaveBeenCalledWith('download_started', expect.any(Object));
        expect(mockTrackEvent).toHaveBeenCalledWith('download_completed', expect.any(Object));
      });
    });

    it('should handle download with download_url', async () => {
      const mockBlobWithUrl = new Blob(['test'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlobWithUrl,
      });

      const resultWithUrl = { ...mockSearchResult, download_url: 'https://storage.example.com/file.xlsx' };
      const { result } = renderHook(() => useSearch(defaultFilters));

      act(() => {
        result.current.setResult(resultWithUrl);
      });

      await act(async () => {
        await result.current.handleDownload();
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('url=https%3A%2F%2Fstorage.example.com'),
          expect.any(Object)
        );
      });
    });

    it('should handle 404 expired file error', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      const { result } = renderHook(() => useSearch(defaultFilters));

      act(() => {
        result.current.setResult(mockSearchResult);
      });

      await act(async () => {
        await result.current.handleDownload();
      });

      await waitFor(() => {
        expect(result.current.downloadError).toBeTruthy();
        expect(result.current.downloadError).toContain('expirado');
      });
    });
  });

  describe('save search functionality', () => {
    it('should open save dialog', () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      act(() => {
        result.current.setResult(mockSearchResult);
      });

      act(() => {
        result.current.handleSaveSearch();
      });

      expect(result.current.showSaveDialog).toBe(true);
    });

    it('should save search with name', () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      act(() => {
        result.current.setResult(mockSearchResult);
        result.current.setSaveSearchName('Minha busca');
      });

      act(() => {
        result.current.confirmSaveSearch();
      });

      expect(mockSaveNewSearch).toHaveBeenCalledWith('Minha busca', expect.any(Object));
    });
  });

  describe('load search functionality', () => {
    it('should load saved search', () => {
      const savedSearch = {
        id: 'search-1',
        name: 'Saved Search',
        searchParams: {
          ufs: ['SP', 'RJ'],
          dataInicial: '2026-02-01',
          dataFinal: '2026-02-10',
          searchMode: 'setor' as const,
          setorId: 'vestuario',
        },
        createdAt: Date.now(),
      };

      const { result } = renderHook(() => useSearch(defaultFilters));

      act(() => {
        result.current.handleLoadSearch(savedSearch);
      });

      expect(defaultFilters.setUfsSelecionadas).toHaveBeenCalledWith(new Set(['SP', 'RJ']));
      expect(defaultFilters.setDataInicial).toHaveBeenCalledWith('2026-02-01');
      expect(defaultFilters.setDataFinal).toHaveBeenCalledWith('2026-02-10');
    });
  });

  describe('estimateSearchTime function', () => {
    it('should estimate search time based on UFs and date range', () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      const estimate = result.current.estimateSearchTime(5, 7);
      expect(estimate).toBeGreaterThan(0);
    });

    it('should increase estimate for longer date ranges', () => {
      const { result } = renderHook(() => useSearch(defaultFilters));

      const estimate7Days = result.current.estimateSearchTime(5, 7);
      const estimate30Days = result.current.estimateSearchTime(5, 30);

      expect(estimate30Days).toBeGreaterThan(estimate7Days);
    });
  });

  describe('custom terms search', () => {
    it('should switch to relevancia ordering for custom terms', async () => {
      const termFilters = {
        ...defaultFilters,
        searchMode: 'termos' as const,
        termosArray: ['uniforme', 'escolar'],
      };

      const { result } = renderHook(() => useSearch(termFilters));

      await act(async () => {
        await result.current.buscar();
      });

      await waitFor(() => {
        expect(defaultFilters.setOrdenacao).toHaveBeenCalledWith('relevancia');
      });
    });

    it('should track custom term search analytics', async () => {
      const termFilters = {
        ...defaultFilters,
        searchMode: 'termos' as const,
        termosArray: ['uniforme', 'escolar'],
      };

      const { result } = renderHook(() => useSearch(termFilters));

      await act(async () => {
        await result.current.buscar();
      });

      await waitFor(() => {
        expect(mockTrackEvent).toHaveBeenCalledWith('custom_term_search', expect.any(Object));
      });
    });
  });
});
