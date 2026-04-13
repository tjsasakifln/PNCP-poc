/**
 * Tests for lib/navSearchCache.ts — Navigation Search Cache
 * UX-432: Persist search results across intra-app navigation.
 */
import {
  saveNavSearch,
  restoreNavSearch,
  clearNavSearch,
  hasNavSearch,
  NavSearchCacheEntry,
  NavSearchMeta,
} from '@/lib/navSearchCache';
import type { SearchFormState } from '@/lib/navSearchCache';

// ── sessionStorage mock ───────────────────────────────────────────────────

const sessionStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

// ── Fixtures ──────────────────────────────────────────────────────────────

const mockFormState: SearchFormState = {
  ufs: ['SC', 'RS'],
  startDate: '2026-01-01',
  endDate: '2026-01-07',
  setor: 'uniformes',
};

const mockMeta: NavSearchMeta = {
  sectorName: 'Uniformes',
  ufsLabel: 'SC, RS',
};

const mockResult = {
  resumo: { total_oportunidades: 5, valor_total: 100000 },
  licitacoes: [{ numero: '001' }, { numero: '002' }],
};

const NAV_CACHE_KEY = 'smartlic_nav_search_state';

// ── Tests ─────────────────────────────────────────────────────────────────

describe('navSearchCache', () => {
  beforeEach(() => {
    sessionStorage.clear();
    jest.clearAllMocks();
    jest.useRealTimers();
  });

  // ── saveNavSearch ──────────────────────────────────────────────────────

  describe('saveNavSearch', () => {
    it('serializes and persists to sessionStorage', () => {
      const ok = saveNavSearch(mockResult, mockFormState, mockMeta);

      expect(ok).toBe(true);
      const raw = sessionStorage.getItem(NAV_CACHE_KEY);
      expect(raw).toBeTruthy();
      const entry: NavSearchCacheEntry = JSON.parse(raw!);
      expect(entry.result).toEqual(mockResult);
      expect(entry.formState).toEqual(mockFormState);
      expect(entry.meta).toEqual(mockMeta);
    });

    it('sets a 30-minute TTL', () => {
      const before = Date.now();
      saveNavSearch(mockResult, mockFormState, mockMeta);
      const after = Date.now();

      const raw = sessionStorage.getItem(NAV_CACHE_KEY);
      const entry: NavSearchCacheEntry = JSON.parse(raw!);

      expect(entry.expiresAt).toBeGreaterThanOrEqual(before + 1_800_000);
      expect(entry.expiresAt).toBeLessThanOrEqual(after + 1_800_000);
    });

    it('trims licitacoes to 100 items when result has more', () => {
      const bigResult = {
        resumo: { total_oportunidades: 200 },
        licitacoes: Array.from({ length: 200 }, (_, i) => ({ numero: String(i) })),
      };
      saveNavSearch(bigResult, mockFormState, mockMeta);

      const raw = sessionStorage.getItem(NAV_CACHE_KEY);
      const entry: NavSearchCacheEntry = JSON.parse(raw!);
      const result = entry.result as typeof bigResult;
      expect(result.licitacoes).toHaveLength(100);
      expect(result.licitacoes[0].numero).toBe('0');
      expect(result.licitacoes[99].numero).toBe('99');
    });

    it('keeps licitacoes intact when ≤100 items', () => {
      saveNavSearch(mockResult, mockFormState, mockMeta);

      const raw = sessionStorage.getItem(NAV_CACHE_KEY);
      const entry: NavSearchCacheEntry = JSON.parse(raw!);
      const result = entry.result as typeof mockResult;
      expect(result.licitacoes).toHaveLength(2);
    });

    it('returns false and does not throw when sessionStorage throws', () => {
      jest.spyOn(sessionStorage, 'setItem').mockImplementationOnce(() => {
        throw new DOMException('QuotaExceededError');
      });

      expect(() => {
        const ok = saveNavSearch(mockResult, mockFormState, mockMeta);
        expect(ok).toBe(false);
      }).not.toThrow();
    });
  });

  // ── restoreNavSearch ───────────────────────────────────────────────────

  describe('restoreNavSearch', () => {
    it('returns the saved entry', () => {
      saveNavSearch(mockResult, mockFormState, mockMeta);

      const entry = restoreNavSearch();

      expect(entry).not.toBeNull();
      expect(entry!.meta).toEqual(mockMeta);
      expect(entry!.formState).toEqual(mockFormState);
    });

    it('does NOT auto-clear on restore (multiple reads)', () => {
      saveNavSearch(mockResult, mockFormState, mockMeta);

      const first = restoreNavSearch();
      const second = restoreNavSearch();

      expect(first).not.toBeNull();
      expect(second).not.toBeNull();
      expect(second!.meta).toEqual(mockMeta);
    });

    it('returns null when nothing is saved', () => {
      expect(restoreNavSearch()).toBeNull();
    });

    it('returns null and clears when TTL has expired (AC4)', () => {
      jest.useFakeTimers();
      saveNavSearch(mockResult, mockFormState, mockMeta);

      // Advance time beyond 30 minutes
      jest.advanceTimersByTime(1_800_001);

      const entry = restoreNavSearch();
      expect(entry).toBeNull();
      expect(sessionStorage.getItem(NAV_CACHE_KEY)).toBeNull();
    });

    it('returns null and clears on corrupted JSON (AC4)', () => {
      sessionStorage.setItem(NAV_CACHE_KEY, '{ invalid json }}}');

      const entry = restoreNavSearch();

      expect(entry).toBeNull();
      expect(sessionStorage.getItem(NAV_CACHE_KEY)).toBeNull();
    });
  });

  // ── clearNavSearch ─────────────────────────────────────────────────────

  describe('clearNavSearch', () => {
    it('removes the entry from sessionStorage', () => {
      saveNavSearch(mockResult, mockFormState, mockMeta);
      expect(sessionStorage.getItem(NAV_CACHE_KEY)).not.toBeNull();

      clearNavSearch();

      expect(sessionStorage.getItem(NAV_CACHE_KEY)).toBeNull();
    });

    it('is idempotent when nothing is saved', () => {
      expect(() => clearNavSearch()).not.toThrow();
    });
  });

  // ── hasNavSearch ───────────────────────────────────────────────────────

  describe('hasNavSearch', () => {
    it('returns true when valid entry exists', () => {
      saveNavSearch(mockResult, mockFormState, mockMeta);
      expect(hasNavSearch()).toBe(true);
    });

    it('returns false when nothing is saved', () => {
      expect(hasNavSearch()).toBe(false);
    });

    it('returns false when entry has expired', () => {
      jest.useFakeTimers();
      saveNavSearch(mockResult, mockFormState, mockMeta);
      jest.advanceTimersByTime(1_800_001);
      expect(hasNavSearch()).toBe(false);
    });

    it('returns false on corrupted JSON', () => {
      sessionStorage.setItem(NAV_CACHE_KEY, '{ broken');
      expect(hasNavSearch()).toBe(false);
    });
  });
});
