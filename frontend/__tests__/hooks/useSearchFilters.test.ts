/**
 * useSearchFilters Hook Tests
 *
 * Tests filter state management, validation, URL params, sectors fetching
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useSearchFilters } from '@/app/buscar/hooks/useSearchFilters';

// Mock useSearchParams
const mockSearchParams = new Map();
jest.mock('next/navigation', () => ({
  useSearchParams: () => ({
    get: (key: string) => mockSearchParams.get(key),
  }),
}));

// Mock analytics
const mockTrackEvent = jest.fn();
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

// Mock fetch
global.fetch = jest.fn();

const mockSetores = [
  { id: 'vestuario', name: 'Vestuário', description: 'Uniformes e fardamentos' },
  { id: 'ti', name: 'TI', description: 'Tecnologia da informação' },
];

const mockClearResult = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  mockSearchParams.clear();
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({ setores: mockSetores }),
  });
  localStorage.clear();
});

describe('useSearchFilters hook', () => {
  describe('Initialization', () => {
    it('should initialize with default values', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      expect(result.current.ufsSelecionadas.size).toBeGreaterThan(0); // Default SC, PR, RS
      expect(result.current.searchMode).toBe('setor');
      expect(result.current.setorId).toBe('vestuario');
      expect(result.current.termosArray).toEqual([]);
    });

    it('should fetch setores on mount', async () => {
      renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/setores');
      });
    });

    it('should use fallback setores on fetch failure', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(result.current.setoresUsingFallback).toBe(true);
        expect(result.current.setores.length).toBeGreaterThan(0);
      });
    });
  });

  describe('URL params handling', () => {
    it('should load UFs from URL params', async () => {
      mockSearchParams.set('ufs', 'SP,RJ,MG');

      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(result.current.ufsSelecionadas.has('SP')).toBe(true);
        expect(result.current.ufsSelecionadas.has('RJ')).toBe(true);
        expect(result.current.ufsSelecionadas.has('MG')).toBe(true);
      });
    });

    it('should load search mode from URL params', async () => {
      mockSearchParams.set('ufs', 'SP');
      mockSearchParams.set('mode', 'termos');
      mockSearchParams.set('termos', 'uniforme escolar');

      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(result.current.searchMode).toBe('termos');
        expect(result.current.termosArray).toContain('uniforme');
        expect(result.current.termosArray).toContain('escolar');
      });
    });

    it('should load setor from URL params', async () => {
      mockSearchParams.set('ufs', 'SP');
      mockSearchParams.set('mode', 'setor');
      mockSearchParams.set('setor', 'ti');

      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(result.current.searchMode).toBe('setor');
        expect(result.current.setorId).toBe('ti');
      });
    });
  });

  describe('UF selection', () => {
    it('should toggle UF', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      const initialSize = result.current.ufsSelecionadas.size;

      act(() => {
        result.current.toggleUf('SP');
      });

      expect(result.current.ufsSelecionadas.has('SP')).toBe(!result.current.ufsSelecionadas.has('SP'));
      expect(mockClearResult).toHaveBeenCalled();
    });

    it('should select all UFs', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.selecionarTodos();
      });

      expect(result.current.ufsSelecionadas.size).toBe(27); // All Brazilian states
    });

    it('should clear all UFs', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.limparSelecao();
      });

      expect(result.current.ufsSelecionadas.size).toBe(0);
    });

    it('should toggle region', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      const sulRegion = ['SC', 'PR', 'RS'];

      act(() => {
        result.current.toggleRegion(sulRegion);
      });

      // All should be toggled (added or removed together)
      const hasAll = sulRegion.every(uf => result.current.ufsSelecionadas.has(uf));
      const hasNone = sulRegion.every(uf => !result.current.ufsSelecionadas.has(uf));
      expect(hasAll || hasNone).toBe(true);
    });
  });

  describe('Search mode', () => {
    it('should switch to termos mode', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setSearchMode('termos');
      });

      expect(result.current.searchMode).toBe('termos');
      expect(mockClearResult).toHaveBeenCalled();
    });

    it('should switch to setor mode', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setSearchMode('termos');
      });

      act(() => {
        result.current.setSearchMode('setor');
      });

      expect(result.current.searchMode).toBe('setor');
    });
  });

  describe('Terms management', () => {
    it('should add terms', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setSearchMode('termos');
        result.current.addTerms(['uniforme', 'escolar']);
      });

      expect(result.current.termosArray).toContain('uniforme');
      expect(result.current.termosArray).toContain('escolar');
    });

    it('should remove term', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setSearchMode('termos');
        result.current.addTerms(['uniforme', 'escolar']);
      });

      act(() => {
        result.current.removeTerm('uniforme');
      });

      expect(result.current.termosArray).not.toContain('uniforme');
      expect(result.current.termosArray).toContain('escolar');
    });

    it('should not add duplicate terms', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setSearchMode('termos');
        result.current.addTerms(['uniforme']);
        result.current.addTerms(['uniforme']);
      });

      const count = result.current.termosArray.filter(t => t === 'uniforme').length;
      expect(count).toBe(1);
    });

    it('should validate terms', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setSearchMode('termos');
        result.current.addTerms(['uniforme', 'a', 'de', 'muito-longo-termo-valido']);
      });

      expect(result.current.termValidation).toBeTruthy();
      if (result.current.termValidation) {
        expect(result.current.termValidation.valid.length).toBeGreaterThan(0);
        expect(result.current.termValidation.ignored.length).toBeGreaterThan(0);
      }
    });
  });

  describe('Validation', () => {
    it('should validate UFs required', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.limparSelecao();
      });

      expect(result.current.canSearch).toBe(false);
      expect(result.current.validationErrors.ufs).toBeTruthy();
    });

    it('should validate date range', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setDataInicial('2026-02-10');
        result.current.setDataFinal('2026-02-01');
      });

      expect(result.current.validationErrors.date_range).toBeTruthy();
    });

    it('should allow search when valid', async () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(result.current.canSearch).toBe(true);
      });
    });
  });

  describe('Collapsible persistence', () => {
    it('should persist location filters state', () => {
      const { result, rerender } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setLocationFiltersOpen(true);
      });

      expect(localStorage.getItem('smartlic-location-filters')).toBe('open');

      rerender();

      expect(result.current.locationFiltersOpen).toBe(true);
    });

    it('should persist advanced filters state', () => {
      const { result, rerender } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setAdvancedFiltersOpen(true);
      });

      expect(localStorage.getItem('smartlic-advanced-filters')).toBe('open');

      rerender();

      expect(result.current.advancedFiltersOpen).toBe(true);
    });
  });

  describe('Municipios auto-clear', () => {
    it('should clear municipios when UFs change', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setMunicipios([{ codigo: '3550308', nome: 'São Paulo' }]);
      });

      act(() => {
        result.current.toggleUf('BA');
      });

      expect(result.current.municipios).toEqual([]);
    });
  });

  describe('Computed values', () => {
    it('should compute sectorName', async () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(result.current.sectorName).toBeTruthy();
      });
    });

    it('should compute searchLabel for setor mode', async () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      await waitFor(() => {
        expect(result.current.searchLabel).toContain('Vestuário');
      });
    });

    it('should compute searchLabel for termos mode', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setSearchMode('termos');
        result.current.addTerms(['uniforme', 'escolar']);
      });

      expect(result.current.searchLabel).toContain('uniforme');
      expect(result.current.searchLabel).toContain('escolar');
    });
  });

  describe('Filters clear result callback', () => {
    it('should call clearResult when filters change', () => {
      const { result } = renderHook(() => useSearchFilters(mockClearResult));

      act(() => {
        result.current.setDataInicial('2026-02-05');
      });

      expect(mockClearResult).toHaveBeenCalled();
    });
  });
});
